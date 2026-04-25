from .models import *
from .views import es_gerente
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, Max, F
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
import csv
import openpyxl

@login_required
def dashboard_gerente(request):
    hoy = timezone.now().date()
    es_gerente_flag = es_gerente(request.user)
    
    periodo = request.GET.get('periodo', 'hoy')
    
    if periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=7)
        periodo_texto = "Últimos 7 días"
    elif periodo == 'mes':
        fecha_inicio = hoy - timedelta(days=30)
        periodo_texto = "Últimos 30 días"
    else:
        fecha_inicio = hoy
        periodo_texto = "Hoy"
    
    total_deudores = Deudor.objects.count()
    total_cartera = Deudor.objects.aggregate(Sum('saldo_deuda'))['saldo_deuda__sum'] or 0
    total_recuperado = Gestion.objects.aggregate(Sum('monto_pago'))['monto_pago__sum'] or 0
    
    stats_pago = Gestion.objects.filter(
        resultado__icontains='PAGO',
        fecha__date__gte=fecha_inicio
    ).count()
    
    stats_promesa = Gestion.objects.filter(
        resultado__icontains='PROMESA',
        fecha__date__gte=fecha_inicio
    ).count()
    
    productividad = User.objects.annotate(
        total_gestiones=Count('gestion', filter=Q(gestion__fecha__date__gte=fecha_inicio)),
        total_pagos=Count('gestion', filter=Q(gestion__fecha__date__gte=fecha_inicio, gestion__resultado__icontains='PAGO')),
        total_promesas=Count('gestion', filter=Q(gestion__fecha__date__gte=fecha_inicio, gestion__resultado__icontains='PROMESA')),
        monto_recuperado=Sum('gestion__monto_pago', filter=Q(gestion__fecha__date__gte=fecha_inicio))
    ).filter(total_gestiones__gt=0).order_by('-total_gestiones')
    
    gestores_nombres = [g.username.upper() for g in productividad]
    gestores_gestiones = [g.total_gestiones for g in productividad]
    gestores_montos = [float(g.monto_recuperado or 0) for g in productividad]
    
    return render(request, 'cobranza/dashboard.html', {
        'es_gerente': es_gerente_flag,
        'total_cartera': total_cartera,
        'total_recuperado': total_recuperado,
        'total_deudores': total_deudores,
        'productividad': productividad,
        'grafico_labels': ['Pagos', 'Promesas'],
        'grafico_data': [stats_pago, stats_promesa],
        'periodo': periodo,
        'periodo_texto': periodo_texto,
        'gestores_nombres': gestores_nombres,
        'gestores_gestiones': gestores_gestiones,
        'gestores_montos': gestores_montos,
    })

@login_required
def exportar_gestiones_excel(request):
    if not es_gerente(request.user):
        return HttpResponse("Acceso Denegado.", status=403)
    gestiones = Gestion.objects.all().order_by('-fecha')
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['FECHA', 'GESTOR', 'DNI', 'CLIENTE', 'RESULTADO', 'MONTO'])
    for g in gestiones:
        ws.append([g.fecha.strftime('%d/%m/%Y'), g.gestor.username, g.deudor.documento, g.deudor.nombre_completo, g.resultado, g.monto_pago])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Reporte_PP.xlsx'
    wb.save(response)
    return response


# ══════════════════════════════════════════════════════════════════════════════
# AGENDA DIARIA DEL GESTOR
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def agenda_diaria(request):
    hoy = timezone.now().date()
    manana = hoy + timedelta(days=1)
    dias_sin_contacto = int(request.GET.get('dias', 3))
    es_gerente_flag = es_gerente(request.user)

    # --- Filtros de cartera para gestores no gerentes ---
    def _get_cartera_filter(prefix='deudor__'):
        """Devuelve un Q con la cartera/agencia del gestor, o None si es gerente."""
        if es_gerente_flag:
            return None
        asignaciones = AsignacionCartera.objects.filter(gestor=request.user)
        carteras = list(asignaciones.filter(tipo='cartera').values_list('valor', flat=True))
        agencias = list(asignaciones.filter(tipo='agencia').values_list('valor', flat=True))
        cond = Q()
        if carteras:
            cond |= Q(**{f'{prefix}cartera__in': carteras})
        if agencias:
            cond |= Q(**{f'{prefix}agencia__in': agencias})
        return cond if cond else Q(pk__in=[])  # ninguna asignación → sin resultados

    # ── 1. PROMESAS QUE VENCEN HOY ─────────────────────────────────────────
    base_promesas = Gestion.objects.filter(
        resultado__icontains='PROMESA'
    ).select_related('deudor', 'gestor')

    cartera_q = _get_cartera_filter(prefix='deudor__')

    promesas_hoy = base_promesas.filter(fecha_promesa=hoy)
    promesas_manana = base_promesas.filter(fecha_promesa=manana)
    promesas_vencidas = base_promesas.filter(fecha_promesa__lt=hoy)

    if cartera_q is not None:
        promesas_hoy = promesas_hoy.filter(cartera_q)
        promesas_manana = promesas_manana.filter(cartera_q)
        promesas_vencidas = promesas_vencidas.filter(cartera_q)

    promesas_hoy = promesas_hoy.order_by('-deudor__saldo_deuda')
    promesas_manana = promesas_manana.order_by('-deudor__saldo_deuda')
    promesas_vencidas = promesas_vencidas.order_by('fecha_promesa')

    # ── 2. SEGUIMIENTOS PROGRAMADOS ────────────────────────────────────────
    base_seg = SeguimientoProgramado.objects.filter(completado=False).select_related('deudor', 'gestor')
    if not es_gerente_flag:
        base_seg = base_seg.filter(gestor=request.user)

    seguimientos_hoy = base_seg.filter(fecha_programada=hoy).order_by('-deudor__saldo_deuda')
    seguimientos_vencidos = base_seg.filter(fecha_programada__lt=hoy).order_by('fecha_programada')
    seguimientos_manana = base_seg.filter(fecha_programada=manana).order_by('-deudor__saldo_deuda')

    # ── 3. DEUDORES SIN CONTACTO EN X DÍAS ────────────────────────────────
    fecha_limite = hoy - timedelta(days=dias_sin_contacto)

    deudores_base = Deudor.objects.annotate(ultima_gestion=Max('gestion__fecha'))

    if not es_gerente_flag:
        asignaciones = AsignacionCartera.objects.filter(gestor=request.user)
        carteras = list(asignaciones.filter(tipo='cartera').values_list('valor', flat=True))
        agencias = list(asignaciones.filter(tipo='agencia').values_list('valor', flat=True))
        cond_deudor = Q()
        if carteras:
            cond_deudor |= Q(cartera__in=carteras)
        if agencias:
            cond_deudor |= Q(agencia__in=agencias)
        deudores_base = deudores_base.filter(cond_deudor) if cond_deudor else Deudor.objects.none()

    sin_contacto = deudores_base.filter(
        Q(ultima_gestion__date__lte=fecha_limite) | Q(ultima_gestion__isnull=True)
    ).order_by(F('ultima_gestion').asc(nulls_first=True))[:50]

    # ── Totales de alertas urgentes ────────────────────────────────────────
    total_urgente = (
        promesas_hoy.count()
        + promesas_vencidas.count()
        + seguimientos_hoy.count()
        + seguimientos_vencidos.count()
    )

    return render(request, 'cobranza/agenda.html', {
        'hoy': hoy,
        'manana': manana,
        'promesas_hoy': promesas_hoy,
        'promesas_manana': promesas_manana,
        'promesas_vencidas': promesas_vencidas,
        'seguimientos_hoy': seguimientos_hoy,
        'seguimientos_vencidos': seguimientos_vencidos,
        'seguimientos_manana': seguimientos_manana,
        'sin_contacto': sin_contacto,
        'dias_sin_contacto': dias_sin_contacto,
        'es_gerente': es_gerente_flag,
        'total_urgente': total_urgente,
    })


@login_required
@require_http_methods(["POST"])
def marcar_seguimiento_completado(request, seguimiento_id):
    """Marca un seguimiento como completado (llamada AJAX)."""
    seg = get_object_or_404(SeguimientoProgramado, id=seguimiento_id)
    if seg.gestor != request.user and not es_gerente(request.user):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    seg.completado = True
    seg.save()
    return JsonResponse({'ok': True})
