import json
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Q, Count
from django.utils import timezone

from .models import Deudor, Gestion, Convenio
from .views import es_gerente
from .ai_service import generar_estrategia_cartera

@login_required
def panel_estrategia_ia(request):
    if not es_gerente(request.user):
        return redirect('bandeja_gestor')
        
    # Extraer carteras únicas
    carteras = Deudor.objects.filter(activo=True).values_list('cartera', flat=True).distinct().order_by('cartera')
    carteras_limpias = [c for c in carteras if c and c.strip()]
    
    # Extraer mapa de agencias por cartera
    mapa_agencias = {}
    for c in carteras_limpias:
        ags = Deudor.objects.filter(cartera=c, activo=True).values_list('agencia', flat=True).distinct()
        mapa_agencias[c] = sorted([a for a in ags if a and a.strip()])
        
    return render(request, 'cobranza/estrategia_ia.html', {
        'carteras': carteras_limpias,
        'mapa_agencias': json.dumps(mapa_agencias),
        'es_gerente': True
    })

@login_required
@require_http_methods(["POST"])
def api_generar_estrategia(request):
    if not es_gerente(request.user):
        return JsonResponse({'error': 'No autorizado'}, status=403)
        
    try:
        data = json.loads(request.body)
        cartera = data.get('cartera')
        agencias = data.get('agencias', [])
        instrucciones = data.get('instrucciones', '')
        
        if not cartera:
            return JsonResponse({'error': 'Debe seleccionar una cartera'}, status=400)
            
        qs = Deudor.objects.filter(cartera=cartera, activo=True)
        if agencias and len(agencias) > 0:
            qs = qs.filter(agencia__in=agencias)
            
        total_deudores = qs.count()
        if total_deudores == 0:
            return JsonResponse({'error': 'No hay clientes en esta selección.'}, status=400)
            
        total_deuda = qs.aggregate(Sum('saldo_deuda'))['saldo_deuda__sum'] or 0
        
        # 1. Casos Críticos (Embargos / Judiciales)
        embargos = qs.filter(
            Q(proceso__icontains='embargo') | 
            Q(estado_proceso_principal__icontains='embargo') |
            Q(condicion__icontains='embargo') |
            Q(estado_medida_cautelar__icontains='embargo')
        )[:20]
        
        # 2. Deudas más altas (Top 30)
        top_deudas = qs.order_by('-saldo_deuda')[:30]
        
                # 3. Pagos recientes
        hace_30_dias = timezone.now().date() - timedelta(days=30)
        pagos_recientes = qs.filter(ultimo_dia_pago__gte=hace_30_dias).order_by('-ultimo_dia_pago')[:20]
        
        # --- NUEVA LOGICA: CONVENIOS ---
        qs_convenios = qs.exclude(negociacion__isnull=True).exclude(negociacion__exact='')\
                         .exclude(negociacion__iexact='nan').exclude(negociacion__iexact='none')\
                         .exclude(negociacion__iexact='null')\
                         .exclude(negociacion__iexact='SIN NEGOCIACIÓN')\
                         .exclude(negociacion__iexact='SIN NEGOCIACION')
                         
        hoy = timezone.now().date()
        mes_actual = hoy.month
        anio_actual = hoy.year
        
        lista_convenios = []
        for c in qs_convenios:
            al_dia = False
            dias_atraso = 0
            fecha_pago_str = 'NO REGISTRA'
            if c.ultimo_dia_pago:
                fecha_pago_str = c.ultimo_dia_pago.strftime('%d/%m/%Y')
                if c.ultimo_dia_pago.year > anio_actual or (c.ultimo_dia_pago.year == anio_actual and c.ultimo_dia_pago.month >= mes_actual):
                    al_dia = True
                else:
                    dias_atraso = (hoy - c.ultimo_dia_pago).days
                    if dias_atraso <= 0:
                        al_dia = True
                        dias_atraso = 0
            else:
                dias_atraso = 9999
                
            lista_convenios.append({
                'nombre_completo': c.nombre_completo,
                'saldo_deuda': float(c.saldo_deuda) if c.saldo_deuda else 0.0,
                'ultimo_dia_pago': fecha_pago_str,
                'dias_atraso': 'CLIENTE AL DIA' if al_dia else f"{dias_atraso} días",
                '_es_al_dia': al_dia,
                '_dias_atraso_num': dias_atraso
            })
            
        lista_convenios.sort(key=lambda x: (x['_es_al_dia'], -x['_dias_atraso_num']))
        
        # Quitar las llaves internas para no ensuciar el JSON de la IA
        for item in lista_convenios:
            del item['_es_al_dia']
            del item['_dias_atraso_num']
            
        # --- NUEVA LOGICA: PRODUCTOS (NORMAL VS OTROS) ---
        agrupacion_productos = list(qs.values('agencia', 'producto').annotate(
            total_clientes=Count('id'),
            suma_deuda=Sum('saldo_deuda')
        ).order_by('agencia', 'producto'))
        
        for item in agrupacion_productos:
            item['suma_deuda'] = float(item['suma_deuda']) if item['suma_deuda'] else 0.0

        # 4. Construir Diccionario con todo para la IA
        datos_agrupados = {
            'cartera': cartera,
            'agencias': agencias if agencias else 'Todas',
            'total_clientes': total_deudores,
            'total_deuda_acumulada_soles': float(total_deuda),
            'top_deudas': list(top_deudas.values('nombre_completo', 'saldo_deuda', 'distrito', 'telefono_principal')),
            'casos_embargo_judicial': list(embargos.values('nombre_completo', 'saldo_deuda', 'proceso', 'condicion')),
            'pagos_recientes': list(pagos_recientes.values('nombre_completo', 'ultimo_dia_pago', 'saldo_deuda')),
            'clientes_con_convenio': lista_convenios,
            'distribucion_por_producto': agrupacion_productos
        }
        
        if instrucciones:
            datos_agrupados['instrucciones_adicionales_gerente'] = instrucciones

        # Llamar a DeepSeek
        respuesta_md = generar_estrategia_cartera(datos_agrupados)
        
        return JsonResponse({'status': 'ok', 'estrategia_md': respuesta_md})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)
