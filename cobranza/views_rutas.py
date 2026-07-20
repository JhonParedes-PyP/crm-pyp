from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from datetime import timedelta
from django.utils.timezone import now
from .models import Convenio, Deudor
from .ai_service import optimizar_ruta_ia
import json

@login_required
def rutas_cobranza(request):
    if request.user.username != 'JPAREDES':
        return HttpResponseForbidden("Acceso denegado. Solo gerencia puede acceder a este módulo.")

    hoy = now().date()
    limite_proximos = hoy + timedelta(days=7)

    # Filtrar clientes con convenios atrasados o próximos (hasta 7 días)
    convenios = Convenio.objects.select_related('deudor').filter(
        fecha_pago__lte=limite_proximos
    ).order_by('fecha_pago')

    # Deudores prioritarios
    deudores = []
    ids_agregados = set()
    for c in convenios:
        if c.deudor.id not in ids_agregados:
            deudores.append({
                'id': c.deudor.id,
                'nombre': c.deudor.nombre_completo,
                'distrito': c.deudor.distrito or '',
                'direccion': c.deudor.dir_casa or '',
                'referencia': c.deudor.referencia or '',
                'link_gps': c.deudor.link_gps or '',
                'motivo': f'Convenio vencimiento: {c.fecha_pago.strftime("%d/%m/%Y")}' if c.fecha_pago else 'Convenio pendiente'
            })
            ids_agregados.add(c.deudor.id)

    return render(request, 'cobranza/rutas_cobranza.html', {
        'deudores': deudores
    })

@login_required
def guardar_coordenadas(request):
    if request.method == 'POST' and request.user.username == 'JPAREDES':
        try:
            data = json.loads(request.body)
            deudor_id = data.get('deudor_id')
            link_gps = data.get('link_gps')
            
            deudor = Deudor.objects.get(id=deudor_id)
            deudor.link_gps = link_gps
            deudor.save()
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Método no permitido o sin permisos'})

@login_required
def optimizar_ruta_ia_ajax(request):
    if request.method == 'POST' and request.user.username == 'JPAREDES':
        try:
            data = json.loads(request.body)
            clientes = data.get('clientes', [])
            
            if not clientes:
                return JsonResponse({'status': 'error', 'message': 'No hay clientes seleccionados'})
                
            recomendacion = optimizar_ruta_ia(clientes)
            return JsonResponse({'status': 'success', 'recomendacion': recomendacion})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'})
