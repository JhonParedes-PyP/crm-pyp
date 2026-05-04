from django.db.models import Q
from django.utils import timezone

from .models import AsignacionCartera, AsignacionDiaria


def obtener_ids_asignaciones_diarias(usuario, fecha=None):
    fecha = fecha or timezone.now().date()
    return AsignacionDiaria.objects.filter(
        gestor=usuario,
        fecha_asignada=fecha,
    ).values_list('deudor_id', flat=True)


def construir_filtro_visibilidad(usuario, related_prefix='', fecha=None):
    asignaciones = AsignacionCartera.objects.filter(gestor=usuario)
    carteras_asignadas = asignaciones.filter(tipo='cartera').values_list('valor', flat=True)
    agencias_asignadas = asignaciones.filter(tipo='agencia').values_list('valor', flat=True)
    ids_diarios = obtener_ids_asignaciones_diarias(usuario, fecha=fecha)

    condiciones = Q()
    if carteras_asignadas.exists():
        condiciones |= Q(**{f'{related_prefix}cartera__in': carteras_asignadas})
    if agencias_asignadas.exists():
        condiciones |= Q(**{f'{related_prefix}agencia__in': agencias_asignadas})
    if ids_diarios.exists():
        condiciones |= Q(**{f'{related_prefix}id__in': ids_diarios})

    return condiciones


def aplicar_visibilidad_por_asignaciones(queryset, usuario, related_prefix='', fecha=None):
    condiciones = construir_filtro_visibilidad(usuario, related_prefix=related_prefix, fecha=fecha)
    return queryset.filter(condiciones) if condiciones else queryset.none()
