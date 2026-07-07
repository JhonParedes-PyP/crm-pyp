import re
from .models import *
from .views import SUPERVISORES_CON_BANDEJA_AGENTE, es_gerente, puede_usar_modo_agente
from .views import obtener_alertas_pago_proximo
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, Max, F, OuterRef, Subquery, DecimalField, Exists
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
import csv
import openpyxl
from .asignaciones import aplicar_visibilidad_por_asignaciones

@login_required
def buscar_cliente_rapido(request):
    if not es_gerente(request.user):
        return redirect('bandeja_gestor')
        
    q = request.GET.get('q', '').strip()
    if not q:
        return redirect('dashboard_gerente')
        
    deudores = Deudor.objects.filter(Q(documento__icontains=q) | Q(nombre_completo__icontains=q) | Q(cuenta__icontains=q))
    if deudores.count() == 1:
        return redirect('registrar_gestion', deudor_id=deudores.first().id)
        
    return render(request, 'cobranza/resultados_busqueda.html', {'deudores': deudores[:50], 'q': q})

@login_required
def dashboard_gerente(request):
    hoy = timezone.now().date()
    inicio_mes_actual = hoy.replace(day=1)
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
    
    filtro_periodo = Q(fecha__date=hoy) if periodo == 'hoy' else Q(fecha__date__gte=fecha_inicio)
    filtro_periodo_gestion = Q(gestion__fecha__date=hoy) if periodo == 'hoy' else Q(gestion__fecha__date__gte=fecha_inicio)
    
    total_deudores = Deudor.objects.count()
    total_cartera = Deudor.objects.aggregate(Sum('saldo_deuda'))['saldo_deuda__sum'] or 0
    total_recuperado = Gestion.objects.filter(
        fecha__date__gte=inicio_mes_actual,
        fecha__date__lte=hoy,
        resultado__icontains='PAGÓ'
    ).aggregate(Sum('monto_pago'))['monto_pago__sum'] or 0
    
    stats_pago = Gestion.objects.filter(
        resultado__icontains='PAGÓ',
    ).filter(
        filtro_periodo
    ).count()
    
    stats_promesa = Gestion.objects.filter(
        resultado__icontains='PROMESA',
    ).filter(
        filtro_periodo
    ).count()
    
    productividad = User.objects.annotate(
        total_gestiones=Count('gestion', filter=filtro_periodo_gestion),
        total_pagos=Count('gestion', filter=filtro_periodo_gestion & Q(gestion__resultado__icontains='PAGÓ')),
        total_promesas=Count('gestion', filter=filtro_periodo_gestion & Q(gestion__resultado__icontains='PROMESA')),
        monto_recuperado=Sum('gestion__monto_pago', filter=filtro_periodo_gestion & Q(gestion__resultado__icontains='PAGÓ'))
    ).filter(total_gestiones__gt=0).order_by('-total_gestiones')
    
    gestores_nombres = [g.username.upper() for g in productividad]
    gestores_gestiones = [g.total_gestiones for g in productividad]
    gestores_montos = [float(g.monto_recuperado or 0) for g in productividad]
    
    # --- USUARIOS EN LÍNEA (Solo para JPAREDES o gerentes) ---
    usuarios_online = []
    if request.user.username == 'JPAREDES' or es_gerente_flag:
        from django.core.cache import cache
        
        for u in User.objects.filter(is_active=True).order_by('username'):
            if cache.get(f'seen_{u.username}'):
                usuarios_online.append(u)
    
    # --- ÚLTIMAS GESTIONES ---
    ultimas_gestiones = []
    if es_gerente_flag:
        ultimas_gestiones = Gestion.objects.select_related('gestor', 'deudor').order_by('-fecha')[:15]

    return render(request, 'cobranza/dashboard.html', {
        'es_gerente': es_gerente_flag,
        'total_cartera': total_cartera,
        'total_recuperado': total_recuperado,
        'inicio_mes_actual': inicio_mes_actual,
        'total_deudores': total_deudores,
        'productividad': productividad,
        'grafico_labels': ['Pagos', 'Promesas'],
        'usuarios_online': usuarios_online,
        'ultimas_gestiones': ultimas_gestiones,
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

    gestiones_todas = Gestion.objects.select_related('gestor', 'deudor').all().order_by('-fecha')

    wb = openpyxl.Workbook()

    # ── Hoja 1: GESTIONES (monto = 0) ──────────────────────────────────────
    ws_gestiones = wb.active
    ws_gestiones.title = 'GESTIONES'
    ws_gestiones.append(['CARTERA', 'AGENCIA', 'CUENTA', 'CLIENTE', 'RESULTADO DE GESTION'])
    for g in gestiones_todas:
        es_pago = g.monto_pago and g.monto_pago > 0 and 'PAG' in g.resultado.upper()
        if es_pago:
            continue
        deudor = g.deudor
        obs_limpia = re.sub(r'^\[.*?\]\s*', '', g.observacion or '').strip()
        resultado_gestion = f'CON FECHA {g.fecha.strftime("%d/%m/%Y")} "{obs_limpia}"'
        ws_gestiones.append([
            deudor.cartera if deudor else 'N/A',
            deudor.agencia if deudor else 'N/A',
            deudor.cuenta if deudor else 'N/A',
            deudor.nombre_completo if deudor else 'N/A',
            resultado_gestion,
        ])

    # ── Hoja 2: PAGOS (monto > 0) ──────────────────────────────────────────
    ws_pagos = wb.create_sheet(title='PAGOS')
    ws_pagos.append(['FECHA', 'GESTOR', 'DNI', 'CLIENTE', 'RESULTADO', 'MONTO'])
    for g in gestiones_todas:
        es_pago = g.monto_pago and g.monto_pago > 0 and 'PAG' in g.resultado.upper()
        if not es_pago:
            continue
        ws_pagos.append([
            g.fecha.strftime('%d/%m/%Y'),
            g.gestor.username.upper() if g.gestor else 'Sin gestor',
            g.deudor.documento if g.deudor else 'N/A',
            g.deudor.nombre_completo if g.deudor else 'N/A',
            g.resultado,
            float(g.monto_pago),
        ])

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
    agente_id = request.GET.get('agente')  # Gerente puede filtrar por agente
    modo_agente = es_gerente_flag and puede_usar_modo_agente(request.user) and request.GET.get('modo') == 'agente'

    # ══════════════════════════════════════════════════════════════════════
    # MODO SUPERVISIÓN — Gerente ve panel por agente (no clientes directos)
    # ══════════════════════════════════════════════════════════════════════
    if request.user.is_superuser and not agente_id and not modo_agente:
        gestores_base = User.objects.exclude(groups__name='GERENTE').exclude(is_superuser=True)
        supervisores_agentes = User.objects.filter(username__in=SUPERVISORES_CON_BANDEJA_AGENTE)
        monto_semana_subquery = Gestion.objects.filter(
            gestor=OuterRef('pk'),
            fecha__date__gte=hoy - timedelta(days=7)
        ).values('gestor').annotate(
            total=Sum('monto_pago')
        ).values('total')[:1]

        promesas_vencidas_subq = Gestion.objects.filter(
            gestor=OuterRef('pk'),
            resultado__icontains='PROMESA',
            fecha_promesa__lt=hoy
        ).annotate(
            tiene_pago=Exists(
                Gestion.objects.filter(
                    deudor=OuterRef('deudor'),
                    resultado__icontains='PAGÓ',
                    fecha__gt=OuterRef('fecha')
                )
            )
        ).filter(tiene_pago=False).values('gestor').annotate(total=Count('id')).values('total')
        
        agentes = (gestores_base | supervisores_agentes).distinct().annotate(
            promesas_vencidas=Subquery(promesas_vencidas_subq, output_field=DecimalField()),
            promesas_hoy=Count('gestion', filter=Q(
                gestion__resultado__icontains='PROMESA',
                gestion__fecha_promesa=hoy
            ), distinct=True),
            seguimientos_pendientes=Count('seguimientos', filter=Q(
                seguimientos__completado=False,
                seguimientos__fecha_programada__lte=hoy
            ), distinct=True),
            gestiones_hoy=Count('gestion', filter=Q(
                gestion__fecha__date=hoy
            ), distinct=True),
            gestiones_semana=Count('gestion', filter=Q(
                gestion__fecha__date__gte=hoy - timedelta(days=7)
            ), distinct=True),
            monto_semana=Subquery(monto_semana_subquery, output_field=DecimalField()),
        ).order_by('-gestiones_hoy', 'username')

        total_prom_vencidas = sum((a.promesas_vencidas or 0) for a in agentes)
        total_prom_hoy = sum((a.promesas_hoy or 0) for a in agentes)
        total_seg_pendientes = sum((a.seguimientos_pendientes or 0) for a in agentes)
        total_alertas = total_prom_vencidas + total_prom_hoy + total_seg_pendientes

        alerta_pago_proximo = obtener_alertas_pago_proximo(request.user)

        return render(request, 'cobranza/agenda.html', {
            'modo': 'supervision',
            'hoy': hoy,
            'agentes': agentes,
            'total_alertas': total_alertas,
            'total_prom_vencidas': total_prom_vencidas,
            'total_prom_hoy': total_prom_hoy,
            'total_seg_pendientes': total_seg_pendientes,
            'es_gerente': True,
            'dias_sin_contacto': dias_sin_contacto,
            'alerta_pago_proximo': alerta_pago_proximo,
            'alerta_pago_proximo_count': len(alerta_pago_proximo),
        })

    # ══════════════════════════════════════════════════════════════════════
    # MODO AGENDA PERSONAL — Agente ve SUS pendientes / Gerente filtra por agente
    # ══════════════════════════════════════════════════════════════════════
    usuario = request.user
    agente_seleccionado = None
    alerta_pago_proximo = obtener_alertas_pago_proximo(request.user)

    if es_gerente_flag and agente_id:
        try:
            agente_seleccionado = User.objects.get(id=agente_id)
            usuario = agente_seleccionado
        except User.DoesNotExist:
            pass

    # ── Promesas ───────────────────────────────────────────────────────────
    base_promesas = Gestion.objects.filter(
        gestor=usuario,
        resultado__icontains='PROMESA'
    ).select_related('deudor', 'gestor')
    base_promesas = aplicar_visibilidad_por_asignaciones(base_promesas, usuario, related_prefix='deudor__')

    promesas_vencidas_q = base_promesas.filter(
        fecha_promesa__lt=hoy
    ).annotate(
        tiene_pago=Exists(
            Gestion.objects.filter(
                deudor=OuterRef('deudor'),
                resultado__icontains='PAGÓ',
                fecha__gt=OuterRef('fecha')
            )
        )
    ).filter(tiene_pago=False).order_by('fecha_promesa')
    
    promesas_hoy = base_promesas.filter(
        fecha_promesa=hoy
    ).annotate(
        tiene_pago=Exists(
            Gestion.objects.filter(
                deudor=OuterRef('deudor'),
                resultado__icontains='PAGÓ',
                fecha__gt=OuterRef('fecha')
            )
        )
    ).filter(tiene_pago=False).order_by('-deudor__saldo_deuda')
    
    promesas_manana = base_promesas.filter(
        fecha_promesa=manana
    ).annotate(
        tiene_pago=Exists(
            Gestion.objects.filter(
                deudor=OuterRef('deudor'),
                resultado__icontains='PAGÓ',
                fecha__gt=OuterRef('fecha')
            )
        )
    ).filter(tiene_pago=False).order_by('-deudor__saldo_deuda')

    # ── Seguimientos ───────────────────────────────────────────────────────
    base_seg = SeguimientoProgramado.objects.filter(
        gestor=usuario,
        completado=False
    ).select_related('deudor', 'gestor')

    seguimientos_vencidos = base_seg.filter(fecha_programada__lt=hoy).order_by('fecha_programada')
    seguimientos_hoy      = base_seg.filter(fecha_programada=hoy).order_by('-deudor__saldo_deuda')
    seguimientos_manana   = base_seg.filter(fecha_programada=manana).order_by('-deudor__saldo_deuda')

    # ── Sin contacto ───────────────────────────────────────────────────────
    fecha_limite = hoy - timedelta(days=dias_sin_contacto)
    deudores_base = Deudor.objects.annotate(ultima_gestion=Max('gestion__fecha'))
    deudores_base = aplicar_visibilidad_por_asignaciones(deudores_base, usuario)

    sin_contacto = deudores_base.filter(
        Q(ultima_gestion__date__lte=fecha_limite) | Q(ultima_gestion__isnull=True)
    ).order_by(F('ultima_gestion').asc(nulls_first=True))[:50]

    asignaciones_del_dia = AsignacionDiaria.objects.filter(
        gestor=usuario,
        fecha_asignada=hoy,
    ).exclude(
        deudor__gestion__gestor=usuario,
        deudor__gestion__fecha__date=hoy
    ).select_related('deudor', 'gestor').order_by('-deudor__saldo_deuda', 'deudor__nombre_completo')

    deudores_ya_visibles = set()
    for grupo in (promesas_vencidas_q, promesas_hoy, promesas_manana):
        deudores_ya_visibles.update(grupo.values_list('deudor_id', flat=True))
    for grupo in (seguimientos_vencidos, seguimientos_hoy, seguimientos_manana):
        deudores_ya_visibles.update(grupo.values_list('deudor_id', flat=True))
    deudores_ya_visibles.update(sin_contacto.values_list('id', flat=True))

    asignaciones_restantes = asignaciones_del_dia.exclude(deudor_id__in=deudores_ya_visibles)

    total_urgente = (
        promesas_vencidas_q.count()
        + promesas_hoy.count()
        + seguimientos_vencidos.count()
        + seguimientos_hoy.count()
    )

    return render(request, 'cobranza/agenda.html', {
        'modo': 'agenda',
        'hoy': hoy,
        'manana': manana,
        'promesas_hoy': promesas_hoy,
        'promesas_manana': promesas_manana,
        'promesas_vencidas': promesas_vencidas_q,
        'seguimientos_hoy': seguimientos_hoy,
        'seguimientos_vencidos': seguimientos_vencidos,
        'seguimientos_manana': seguimientos_manana,
        'sin_contacto': sin_contacto,
        'asignaciones_del_dia': asignaciones_del_dia,
        'asignaciones_restantes': asignaciones_restantes,
        'dias_sin_contacto': dias_sin_contacto,
        'es_gerente': es_gerente_flag,
        'total_urgente': total_urgente,
        'alerta_pago_proximo': alerta_pago_proximo,
        'alerta_pago_proximo_count': len(alerta_pago_proximo),
        'agente_seleccionado': agente_seleccionado,
        'modo_agente': modo_agente,
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

@login_required
@require_http_methods(["GET"])
def comprobar_alertas_seguimiento(request):
    """
    Retorna los seguimientos pendientes para hoy cuya hora programada
    es menor o igual a la actual, o seguimientos de días anteriores.
    """
    hoy = timezone.now().date()
    hora_actual = timezone.now().time()
    
    alertas = SeguimientoProgramado.objects.filter(
        Q(gestor=request.user, completado=False),
        Q(fecha_programada__lt=hoy) | Q(fecha_programada=hoy, hora_programada__lte=hora_actual, hora_programada__isnull=False)
    ).select_related('deudor').order_by('fecha_programada', 'hora_programada')
    
    data = []
    for a in alertas:
        data.append({
            'id': a.id,
            'deudor_id': a.deudor.id,
            'cliente': a.deudor.nombre_completo,
            'hora': a.hora_programada.strftime('%H:%M') if a.hora_programada else 'Pendiente',
            'fecha': a.fecha_programada.strftime('%d/%m/%Y'),
            'motivo': a.motivo
        })
        
    return JsonResponse({'alertas': data})
