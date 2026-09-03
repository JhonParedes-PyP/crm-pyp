import re

file_path = r'c:\CRM PYP\cobranza\judicial_views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's extract everything before def subir_excel_judicial(request):
pattern_func = r"def subir_excel_judicial\(request\):.*"
content_before = re.sub(pattern_func, '', content, flags=re.DOTALL)

new_func = """def subir_excel_judicial(request):
    if not request.user.is_superuser and not request.user.groups.filter(name='Gerencia').exists():
        return HttpResponse("Acceso Denegado. Solo Gerencia puede cargar carteras judiciales.", status=403)
        
    mensajes = ""
    columnas_detectadas = []
    
    if request.method == 'POST':
        accion = request.POST.get('accion', 'previsualizar')
        
        if accion == 'previsualizar' and request.FILES.get('archivo_excel'):
            try:
                archivo = request.FILES['archivo_excel']
                temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
                os.makedirs(temp_dir, exist_ok=True)
                fs = FileSystemStorage(location=temp_dir)
                filename = fs.save(f"{uuid.uuid4()}_{archivo.name}", archivo)
                file_path = fs.path(filename)
                
                df = pd.read_excel(file_path, nrows=5, dtype=str)
                columnas_detectadas = list(df.columns)
                
                # Check for CUENTA or DNI
                if 'CUENTA' not in columnas_detectadas and 'DNI TITULAR' not in columnas_detectadas:
                    mensajes = "ADVERTENCIA: El Excel no tiene columna 'CUENTA' ni 'DNI TITULAR'. El cotejo fallarǭ."

                return render(request, 'cobranza/judicial/subir_excel.html', {
                    'vista_previa': True,
                    'file_path': file_path,
                    'columnas_detectadas': columnas_detectadas,
                    'mensajes': mensajes
                })
            except Exception as e:
                mensajes = f"Error al previsualizar: {e}"
                
        elif accion == 'confirmar':
            file_path = request.POST.get('file_path')
            if file_path and os.path.exists(file_path):
                try:
                    df = pd.read_excel(file_path, dtype=str).fillna('')
                    
                    import unicodedata
                    def normalize_col(name):
                        s = str(name).strip().upper()
                        s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
                        s = s.replace('N°', 'NRO').replace('N.', 'NRO').replace('NRO.', 'NRO').strip()
                        if s.startswith('N '): s = 'NRO ' + s[2:]
                        if s == 'N DE EXPEDIENTE CAUTELAR': s = 'NRO DE EXPEDIENTE CAUTELAR'
                        return s
                        
                    col_map = {normalize_col(c): c for c in df.columns}
                    
                    def get_val(row, possible_names):
                        for name in possible_names:
                            norm_name = normalize_col(name)
                            if norm_name in col_map:
                                val = str(row.get(col_map[norm_name], '')).strip()
                                if val not in ('nan', 'None', '-'):
                                    return val
                        return ''

                    expedientes_creados = 0
                    actos_creados = 0
                    
                    with transaction.atomic():
                        for index, row in df.iterrows():
                            cuenta_val = get_val(row, ['CUENTA'])
                            dni_val = get_val(row, ['DNI TITULAR', 'DNI'])
                            
                            deudor = None
                            if cuenta_val:
                                deudor = Deudor.objects.filter(cuenta=cuenta_val).first()
                            if not deudor and dni_val:
                                deudor = Deudor.objects.filter(documento=dni_val).first()
                                
                            if deudor:
                                num_exp = get_val(row, ['NRO DE EXPEDIENTE PRINCIPAL', 'EXPEDIENTE PRINCIPAL', 'NRO. DE EXPEDIENTE PRINCIPAL'])
                                num_cau = get_val(row, ['NRO DE EXPEDIENTE CAUTELAR', 'EXPEDIENTE CAUTELAR', 'N DE EXPEDIENTE CAUTELAR'])
                                
                                if num_exp or num_cau:
                                    defaults_dict = {
                                        'numero_expediente': num_exp,
                                        'numero_cautelar': num_cau,
                                        'materia': get_val(row, ['PRETENSION', 'MATERIA']),
                                        'distrito_judicial': get_val(row, ['DISTRITO JUDICIAL']),
                                        'sede_judicial': get_val(row, ['SEDE', 'SEDE JUDICIAL']),
                                        'condicion_recuperabilidad': get_val(row, ['CONDICION: RECUPERABLE / IRRECUPERABLE', 'CONDICION']),
                                        'probabilidad_recuperacion': get_val(row, ['PROBABILIDAD DE RECUPERACION']),
                                        'detalle_bien': get_val(row, ['DETALLE DEL BIEN']),
                                        'codigo_cautelar': get_val(row, ['CODIGO CAUTELAR']),
                                        'tipo_medida_cautelar': get_val(row, ['TIPO MEDIDA CAUTELAR']),
                                        'estado_cautelar': get_val(row, ['ESTADO DE MEDIDA CAUTELAR']),
                                        'fecha_cautelar': safe_date_judicial(get_val(row, ['FECHA DE PRESENTACION DE LA CAUTELAR'])),
                                        'juzgado': get_val(row, ['SEDE JUDICIAL / JUZGADO', 'JUZGADO']),
                                        'especialista_legal': get_val(row, ['ESPECIALISTA', 'ESPECIALISTA LEGAL']),
                                        'fecha_inicio': safe_date_judicial(get_val(row, ['FECHA PRESENTACION DE DEMANDA PRINCIPAL'])),
                                    }
                                    
                                    monto_str = get_val(row, ['MONTO DEMANDADO'])
                                    if monto_str:
                                        try:
                                            defaults_dict['monto_demandado'] = Decimal(monto_str.replace(',',''))
                                        except:
                                            defaults_dict['monto_demandado'] = None
                                    else:
                                        defaults_dict['monto_demandado'] = None
                                        
                                    exp, created = ExpedienteJudicial.objects.update_or_create(
                                        deudor=deudor,
                                        defaults=defaults_dict
                                    )
                                    if created:
                                        expedientes_creados += 1
                                        
                                    seg_prin = get_val(row, ['SEGUIMIENTO DEL CUADERNO PRINCIPAL'])
                                    if seg_prin:
                                        ActoProcesal.objects.get_or_create(
                                            expediente=exp,
                                            descripcion='Historial Importado (Drive)',
                                            sumilla=seg_prin,
                                            cuaderno='PRINCIPAL',
                                            defaults={'registrado_por': request.user}
                                        )
                                        actos_creados += 1
                                        
                                    seg_cau = get_val(row, ['SEGUIMIENTO DEL CUAD CAU', 'SEGUIMIENTO DEL CUADERNO CAUTELAR'])
                                    if seg_cau:
                                        ActoProcesal.objects.get_or_create(
                                            expediente=exp,
                                            descripcion='Historial Cautelar Importado (Drive)',
                                            sumilla=seg_cau,
                                            cuaderno='CAUTELAR',
                                            defaults={'registrado_por': request.user}
                                        )
                                        actos_creados += 1
                    
                    mensajes = f"Exito: {expedientes_creados} expedientes creados/actualizados, {actos_creados} actos procesales insertados."
                except Exception as e:
                    mensajes = f"Error al procesar: {e}"
                    
    return render(request, 'cobranza/judicial/subir_excel.html', {
        'mensajes': mensajes
    })
"""

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content_before + new_func)

print('Rewrite complete')
