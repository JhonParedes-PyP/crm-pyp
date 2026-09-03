from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from datetime import date, timedelta
from django.db.models import Count, Q
from .models import Deudor, ExpedienteJudicial, ActoProcesal, AlertaJudicial

@login_required
def dashboard_judicial(request):
    if not request.user.is_superuser and not request.user.groups.filter(name='Gerencia').exists():
        pass # Depending on auth, might allow legal assistants too

    hoy = date.today()
    fin_semana = hoy + timedelta(days=7)

    alertas_hoy = AlertaJudicial.objects.filter(estado='PENDIENTE', fecha_vencimiento__lte=hoy).count()
    alertas_semana = AlertaJudicial.objects.filter(estado='PENDIENTE', fecha_vencimiento__gt=hoy, fecha_vencimiento__lte=fin_semana).count()
    total_activos = ExpedienteJudicial.objects.filter(estado_proceso='ACTIVO').count()

    # List pending alerts
    alertas_pendientes = AlertaJudicial.objects.filter(estado='PENDIENTE').select_related('expediente__deudor').order_by('fecha_vencimiento')

    context = {
        'alertas_hoy': alertas_hoy,
        'alertas_semana': alertas_semana,
        'total_activos': total_activos,
        'alertas_pendientes': alertas_pendientes,
        'hoy': hoy
    }
    return render(request, 'cobranza/judicial/dashboard.html', context)

@login_required
def buscar_expediente(request):
    query = request.GET.get('q', '')
    cartera_q = request.GET.get('cartera', '')
    agencia_q = request.GET.get('agencia', '')
    
    expedientes = []
    
    # We only show results if a search or filter was applied
    if query or cartera_q or agencia_q:
        qs = ExpedienteJudicial.objects.all()
        if query:
            qs = qs.filter(
                Q(numero_expediente__icontains=query) |
                Q(deudor__nombre_completo__icontains=query) |
                Q(deudor__documento__icontains=query)
            )
        if cartera_q:
            qs = qs.filter(deudor__cartera=cartera_q)
        if agencia_q:
            qs = qs.filter(deudor__agencia=agencia_q)
        expedientes = qs
        
    carteras = Deudor.objects.filter(expedientes_judiciales__isnull=False).values_list('cartera', flat=True).distinct()
    agencias = Deudor.objects.filter(expedientes_judiciales__isnull=False).values_list('agencia', flat=True).distinct()
    
    return render(request, 'cobranza/judicial/buscar.html', {
        'expedientes': expedientes,
        'query': query,
        'cartera_q': cartera_q,
        'agencia_q': agencia_q,
        'carteras': carteras,
        'agencias': agencias,
    })

@login_required
def detalle_expediente(request, expediente_id):
    expediente = get_object_or_404(ExpedienteJudicial, id=expediente_id)
    actos = expediente.actos_procesales.all()
    alertas = expediente.alertas.filter(estado='PENDIENTE')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_acto':
            ActoProcesal.objects.create(
                expediente=expediente,
                cuaderno=request.POST.get('cuaderno', 'PRINCIPAL'),
                numero_resolucion=request.POST.get('numero_resolucion'),
                fecha_resolucion=request.POST.get('fecha_resolucion'),
                fecha_notificacion=request.POST.get('fecha_notificacion') or None,
                descripcion=request.POST.get('descripcion'),
                sumilla=request.POST.get('sumilla'),
                fojas=request.POST.get('fojas') or None,
                registrado_por=request.user
            )
        elif action == 'delete_acto':
            if request.user.is_superuser or request.user.groups.filter(name='Gerencia').exists():
                acto_id = request.POST.get('acto_id')
                ActoProcesal.objects.filter(id=acto_id).delete()
        elif action == 'add_alerta':
            AlertaJudicial.objects.create(
                expediente=expediente,
                tipo_alerta=request.POST.get('tipo_alerta'),
                fecha_vencimiento=request.POST.get('fecha_vencimiento'),
                creado_por=request.user
            )
        elif action == 'complete_alerta':
            alerta_id = request.POST.get('alerta_id')
            alerta = AlertaJudicial.objects.filter(id=alerta_id, expediente=expediente).first()
            if alerta:
                alerta.estado = 'COMPLETADO'
                alerta.save()
        return redirect('detalle_expediente', expediente_id=expediente.id)

    es_gerencia = request.user.is_superuser or request.user.groups.filter(name='Gerencia').exists()
    return render(request, 'cobranza/judicial/detalle.html', {
        'expediente': expediente,
        'actos': actos,
        'alertas': alertas,
        'es_gerencia': es_gerencia
    })


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
                                        
                                    exp = ExpedienteJudicial.objects.filter(deudor=deudor).first()
                                    if not exp:
                                        exp = ExpedienteJudicial(deudor=deudor)
                                        expedientes_creados += 1
                                        
                                    for field, value in defaults_dict.items():
                                        setattr(exp, field, value)
                                    exp.save()
                                        
                                    seg_prin = get_val(row, ['SEGUIMIENTO DEL CUADERNO PRINCIPAL'])
                                    if seg_prin:
                                        fecha_prin = safe_date_judicial(get_val(row, ['FECHA DE ULTIMO ACTUADO PROCESAL'])) or timezone.now().date()
                                        ActoProcesal.objects.get_or_create(
                                            expediente=exp,
                                            descripcion='Historial Importado (Drive)',
                                            sumilla=seg_prin,
                                            cuaderno='PRINCIPAL',
                                            defaults={
                                                'registrado_por': request.user,
                                                'fecha_resolucion': fecha_prin
                                            }
                                        )
                                        actos_creados += 1
                                        
                                    seg_cau = get_val(row, ['SEGUIMIENTO DEL CUAD CAU', 'SEGUIMIENTO DEL CUADERNO CAUTELAR'])
                                    if seg_cau:
                                        fecha_cau = safe_date_judicial(get_val(row, ['FECHA DEL ULTMO ACTUADO CAUTELAR', 'FECHA DE ULTIMO ACTUADO CAUTELAR'])) or timezone.now().date()
                                        ActoProcesal.objects.get_or_create(
                                            expediente=exp,
                                            descripcion='Historial Cautelar Importado (Drive)',
                                            sumilla=seg_cau,
                                            cuaderno='CAUTELAR',
                                            defaults={
                                                'registrado_por': request.user,
                                                'fecha_resolucion': fecha_cau
                                            }
                                        )
                                        actos_creados += 1
                    
                    mensajes = f"Exito: {expedientes_creados} expedientes creados/actualizados, {actos_creados} actos procesales insertados."
                except Exception as e:
                    mensajes = f"Error al procesar: {e}"
                    
    return render(request, 'cobranza/judicial/subir_excel.html', {
        'mensajes': mensajes
    })
