from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from datetime import timedelta
from django.utils.timezone import now
from .models import Convenio, Deudor
from .ai_service import optimizar_ruta_ia
from .views import es_gerente, puede_usar_modo_agente
import json

@login_required
def rutas_cobranza(request):
    # Obtener todos los deudores
    todos_deudores = Deudor.objects.all().prefetch_related('convenios')

    deudores = []
    carteras = set()
    agencias = set()
    
    for d in todos_deudores:
        if d.cartera: carteras.add(d.cartera.strip())
        if d.agencia: agencias.add(d.agencia.strip())
        
        # Determinar motivo (si tiene convenio próximo/vencido)
        convenios = d.convenios.all()
        motivo = "Gestión / Visita"
        if convenios:
            c = convenios.order_by('fecha_pago').first()
            if c and c.fecha_pago:
                motivo = f'Convenio: {c.fecha_pago.strftime("%d/%m/%Y")}'
        
        deudores.append({
            'id': d.id,
            'nombre': d.nombre_completo,
            'documento': d.documento,
            'telefono': d.telefono_principal,
            'cartera': d.cartera or '',
            'agencia': d.agencia or '',
            'distrito': d.distrito or '',
            'direccion': d.dir_casa or '',
            'referencia': d.referencia or '',
            'link_gps': d.link_gps or '',
            'motivo': motivo
        })

    return render(request, 'cobranza/rutas_cobranza.html', {
        'deudores': deudores,
        'carteras': sorted(list(carteras)),
        'agencias': sorted(list(agencias)),
        'es_gerente': es_gerente(request.user),
        'puede_modo_agente': puede_usar_modo_agente(request.user)
    })

@login_required
def guardar_coordenadas(request):
    if request.method == 'POST':
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
    if request.method == 'POST':
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
