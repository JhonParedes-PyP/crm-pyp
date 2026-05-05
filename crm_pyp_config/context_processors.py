from django.conf import settings
from django.utils import timezone


def zadarma_token(request):
    """
    Inyecta variables de Zadarma en todos los templates:
    - zadarma_api_token  → token para /api/webrtc-key/
    - zadarma_sip        → extensión SIP del agente
    """
    return {
        'zadarma_api_token': getattr(settings, 'API_TOKEN_ZADARMA', ''),
        'zadarma_sip': getattr(settings, 'ZADARMA_SIP', ''),
    }


def agenda_alertas(request):
    """
    Inyecta en todos los templates el total de alertas de agenda del día:
    - Promesas que vencen HOY (sin pago posterior)
    - Seguimientos programados para HOY o vencidos (no completados)
    Usado para el badge rojo en el menú de navegación.
    """
    if not request.user.is_authenticated:
        return {'agenda_alertas_count': 0, 'pagos_proximos_count': 0, 'puede_modo_agente': False}

    try:
        from cobranza.models import Gestion, SeguimientoProgramado
        from cobranza.asignaciones import aplicar_visibilidad_por_asignaciones

        hoy = timezone.now().date()

        # Determinar si es gerente
        es_gerente_flag = (
            request.user.groups.filter(name='GERENTE').exists()
            or request.user.is_superuser
        )

        # --- Promesas vencidas HOY ---
        promesas_q = Gestion.objects.filter(
            fecha_promesa=hoy,
            resultado__icontains='PROMESA'
        )
        if not es_gerente_flag:
            promesas_q = aplicar_visibilidad_por_asignaciones(promesas_q, request.user, related_prefix='deudor__')

        # --- Seguimientos pendientes (hoy o vencidos) ---
        seg_q = SeguimientoProgramado.objects.filter(
            fecha_programada__lte=hoy,
            completado=False
        )
        if not es_gerente_flag:
            seg_q = seg_q.filter(gestor=request.user)

        # --- Pagos Próximos a Vencer (2 días) ---
        from cobranza.models import Deudor
        from django.db.models import F, Value, DateField, ExpressionWrapper
        from datetime import timedelta
        
        fecha_tope = hoy + timedelta(days=2)
        deudores_base = Deudor.objects.filter(ultimo_dia_pago__isnull=False).annotate(
            fecha_pago_calc=ExpressionWrapper(
                F('ultimo_dia_pago') + Value(timedelta(days=30)),
                output_field=DateField()
            )
        ).filter(
            fecha_pago_calc__range=(hoy, fecha_tope)
        )

        if request.user.is_superuser and request.user.username.upper() == 'JPAREDES':
            deudores_visibles = deudores_base
        else:
            deudores_visibles = aplicar_visibilidad_por_asignaciones(deudores_base, request.user)

        deudores_visibles = deudores_visibles.exclude(
            gestion__gestor=request.user,
            gestion__fecha__date=hoy
        )
        from cobranza.views import USUARIOS_SIN_ALERTA_PAGO_PROXIMO
        if request.user.username.upper() in USUARIOS_SIN_ALERTA_PAGO_PROXIMO:
            pagos_proximos_count = 0
        else:
            pagos_proximos_count = deudores_visibles.count()

        total = promesas_q.count() + seg_q.count()
        return {
            'agenda_alertas_count': total,
            'pagos_proximos_count': pagos_proximos_count,
            'puede_modo_agente': request.user.username.upper() == 'JPAREDES',
        }

    except Exception:
        return {
            'agenda_alertas_count': 0,
            'pagos_proximos_count': 0,
            'puede_modo_agente': request.user.username.upper() == 'JPAREDES',
        }

