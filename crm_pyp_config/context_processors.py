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
        return {'agenda_alertas_count': 0, 'puede_modo_agente': False}

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

        total = promesas_q.count() + seg_q.count()
        return {
            'agenda_alertas_count': total,
            'puede_modo_agente': request.user.username.upper() == 'JPAREDES',
        }

    except Exception:
        return {
            'agenda_alertas_count': 0,
            'puede_modo_agente': request.user.username.upper() == 'JPAREDES',
        }

