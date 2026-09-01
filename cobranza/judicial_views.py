from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
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
    expedientes = []
    if query:
        expedientes = ExpedienteJudicial.objects.filter(
            Q(numero_expediente__icontains=query) |
            Q(deudor__nombre_completo__icontains=query) |
            Q(deudor__documento__icontains=query)
        )
    return render(request, 'cobranza/judicial/buscar.html', {'expedientes': expedientes, 'query': query})

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
                numero_resolucion=request.POST.get('numero_resolucion'),
                fecha_resolucion=request.POST.get('fecha_resolucion'),
                fecha_notificacion=request.POST.get('fecha_notificacion') or None,
                descripcion=request.POST.get('descripcion'),
                sumilla=request.POST.get('sumilla'),
                fojas=request.POST.get('fojas') or None,
                registrado_por=request.user
            )
        elif action == 'add_alerta':
            AlertaJudicial.objects.create(
                expediente=expediente,
                tipo_alerta=request.POST.get('tipo_alerta'),
                fecha_vencimiento=request.POST.get('fecha_vencimiento'),
                creado_por=request.user
            )
        return redirect('detalle_expediente', expediente_id=expediente.id)

    return render(request, 'cobranza/judicial/detalle.html', {
        'expediente': expediente,
        'actos': actos,
        'alertas': alertas
    })
