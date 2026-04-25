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
        return {'agenda_alertas_count': 0}

    try:
        from cobranza.models import Gestion, SeguimientoProgramado, AsignacionCartera
        from django.db.models import Q

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
            asignaciones = AsignacionCartera.objects.filter(gestor=request.user)
            carteras = asignaciones.filter(tipo='cartera').values_list('valor', flat=True)
            agencias = asignaciones.filter(tipo='agencia').values_list('valor', flat=True)
            cond = Q()
            if carteras.exists():
                cond |= Q(deudor__cartera__in=carteras)
            if agencias.exists():
                cond |= Q(deudor__agencia__in=agencias)
            if cond:
                promesas_q = promesas_q.filter(cond)
            else:
                promesas_q = promesas_q.none()

        # --- Seguimientos pendientes (hoy o vencidos) ---
        seg_q = SeguimientoProgramado.objects.filter(
            fecha_programada__lte=hoy,
            completado=False
        )
        if not es_gerente_flag:
            seg_q = seg_q.filter(gestor=request.user)

        total = promesas_q.count() + seg_q.count()
        return {'agenda_alertas_count': total}

    except Exception:
        return {'agenda_alertas_count': 0}

