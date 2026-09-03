import pandas as pd
import uuid
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from decimal import Decimal
import numpy as np

def safe_date_judicial(val):
    if pd.isna(val) or str(val).strip() in ('', 'nan', 'NaT', 'None'):
        return None
    try:
        if isinstance(val, str) and len(val) >= 10:
            from datetime import datetime
            return datetime.strptime(val[:10], '%d/%m/%Y').date()
    except:
        pass
    try:
        return pd.to_datetime(val).date()
    except:
        return None

@login_required
def subir_excel_judicial(request):
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
                    mensajes = "ADVERTENCIA: El Excel no tiene columna 'CUENTA' ni 'DNI TITULAR'. El cotejo fallará."

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
                    
                    expedientes_creados = 0
                    actos_creados = 0
                    
                    with transaction.atomic():
                        for index, row in df.iterrows():
                            cuenta_val = str(row.get('CUENTA', '')).strip()
                            dni_val = str(row.get('DNI TITULAR', '')).strip()
                            
                            deudor = None
                            if cuenta_val and cuenta_val not in ('nan', '-'):
                                deudor = Deudor.objects.filter(cuenta=cuenta_val).first()
                            if not deudor and dni_val and dni_val not in ('nan', '-'):
                                deudor = Deudor.objects.filter(documento=dni_val).first()
                                
                            if deudor:
                                # Data Judicial
                                num_exp = str(row.get('NRO. DE EXPEDIENTE PRINCIPAL', '')).strip()
                                num_cau = str(row.get('N° DE EXPEDIENTE CAUTELAR', '')).strip()
                                
                                if num_exp or num_cau:
                                    exp, created = ExpedienteJudicial.objects.update_or_create(
                                        deudor=deudor,
                                        defaults={
                                            'numero_expediente': num_exp,
                                            'numero_cautelar': num_cau,
                                            'materia': str(row.get('PRETENSION', '')).strip(),
                                            'distrito_judicial': str(row.get('DISTRITO JUDICIAL', '')).strip(),
                                            'sede_judicial': str(row.get('SEDE', '')).strip(),
                                            'condicion_recuperabilidad': str(row.get('CONDICIÓN: RECUPERABLE / IRRECUPERABLE', '')).strip(),
                                            'probabilidad_recuperacion': str(row.get('PROBABILIDAD DE RECUPERACION', '')).strip(),
                                            'detalle_bien': str(row.get('DETALLE DEL BIEN', '')).strip(),
                                            'codigo_cautelar': str(row.get('CODIGO CAUTELAR', '')).strip(),
                                            'tipo_medida_cautelar': str(row.get('TIPO MEDIDA CAUTELAR', '')).strip(),
                                            'estado_cautelar': str(row.get('ESTADO DE MEDIDA CAUTELAR', '')).strip(),
                                            'fecha_cautelar': safe_date_judicial(row.get('FECHA DE PRESENTACION DE LA CAUTELAR')),
                                            'monto_demandado': Decimal(str(row.get('MONTO DEMANDADO', '0')).strip()) if str(row.get('MONTO DEMANDADO', '0')).strip() not in ('', 'nan', 'None') else None,
                                            'juzgado': str(row.get('SEDE JUDICIAL / JUZGADO', '')).strip(),
                                            'especialista_legal': str(row.get('ESPECIALISTA', '')).strip(),
                                            'fecha_inicio': safe_date_judicial(row.get('FECHA PRESENTACION DE DEMANDA PRINCIPAL')),
                                        }
                                    )
                                    if created:
                                        expedientes_creados += 1
                                        
                                    # Seg principal
                                    seg_prin = str(row.get('SEGUIMIENTO DEL CUADERNO PRINCIPAL', '')).strip()
                                    if seg_prin and seg_prin not in ('nan', '-'):
                                        ActoProcesal.objects.get_or_create(
                                            expediente=exp,
                                            descripcion='Historial Importado (Drive)',
                                            sumilla=seg_prin,
                                            cuaderno='PRINCIPAL',
                                            defaults={
                                                'registrado_por': request.user
                                            }
                                        )
                                        actos_creados += 1
                                        
                                    # Seg cautelar
                                    seg_cau = str(row.get('SEGUIMIENTO DEL CUAD CAU', '')).strip()
                                    if seg_cau and seg_cau not in ('nan', '-'):
                                        ActoProcesal.objects.get_or_create(
                                            expediente=exp,
                                            descripcion='Historial Importado (Drive)',
                                            sumilla=seg_cau,
                                            cuaderno='CAUTELAR',
                                            defaults={
                                                'registrado_por': request.user
                                            }
                                        )
                                        actos_creados += 1
                                
                    os.remove(file_path)
                    mensajes = f"¡Carga Exitosa! Se crearon/actualizaron {expedientes_creados} expedientes y se importaron {actos_creados} seguimientos."
                except Exception as e:
                    mensajes = f"Error al procesar archivo final: {e}"

    return render(request, 'cobranza/judicial/subir_excel.html', {'mensajes': mensajes})
