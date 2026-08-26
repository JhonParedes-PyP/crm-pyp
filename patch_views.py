import os
import re

# 1. Modify dashboard_views.py
views_path = r"c:\CRM PYP\cobranza\dashboard_views.py"
with open(views_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Proempresa override logic
override_logic = """
    # Sobrescribir PROEMPRESA con la suma de imp_recup (Monto Recuperado Oficial)
    proempresa_recup = Deudor.objects.filter(
        cartera__icontains='PROEMPRESA',
        activo=True,
        imp_recup__gt=0
    ).aggregate(total=Sum('imp_recup'))['total'] or 0.0
    recuperacion_carteras['PROEMPRESA'] = float(proempresa_recup)

    # Cruce de Pagos No Registrados"""
content = content.replace("    # Cruce de Pagos No Registrados", override_logic.lstrip('\n'))

# Add pagos_no_reflejados_proempresa
proempresa_cruce = """
        pagos_no_reflejados_proempresa = Deudor.objects.filter(
            cartera__icontains='PROEMPRESA',
            imp_recup__gt=0
        ).annotate(
            tiene_gestion_pago=Exists(gestiones_pago_mes)
        ).filter(
            tiene_gestion_pago=False
        ).order_by('-imp_recup')[:100]

    import json
    
    # Cargar metas
    from django.conf import settings
    import os as ds_os
    metas_path = ds_os.path.join(settings.BASE_DIR, 'metas.json')
    metas_data = {
        'PROEMPRESA': 213674.00,
        'CAJA HUANCAYO': 457116.49,
        'FOCMAC': None
    }
    if ds_os.path.exists(metas_path):
        try:
            with open(metas_path, 'r', encoding='utf-8') as fm:
                metas_data = json.load(fm)
        except Exception:
            pass
"""
content = content.replace("    import json", proempresa_cruce.lstrip('\n'))

# Add to context
context_adds = """        'convenios_proximos': convenios_proximos,
        'pagos_no_reflejados_huancayo': pagos_no_reflejados_huancayo,
        'pagos_no_reflejados_proempresa': pagos_no_reflejados_proempresa if es_gerente_flag else [],
        'metas_json': json.dumps(metas_data),
        'recuperacion_carteras_json': json.dumps(recuperacion_carteras),"""
content = content.replace("        'convenios_proximos': convenios_proximos,\n        'pagos_no_reflejados_huancayo': pagos_no_reflejados_huancayo,\n        'recuperacion_carteras_json': json.dumps(recuperacion_carteras),", context_adds)

# Add guardar_metas view
endpoint_code = """
@login_required
def guardar_metas(request):
    from django.http import JsonResponse
    import json
    import os
    from django.conf import settings
    
    if not request.user.username == 'JPAREDES' and not request.user.groups.filter(name='Gerencia').exists():
        return JsonResponse({'error': 'No autorizado'}, status=403)
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            metas_path = os.path.join(settings.BASE_DIR, 'metas.json')
            with open(metas_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)
"""
if "def guardar_metas" not in content:
    content += "\n" + endpoint_code

with open(views_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated dashboard_views.py")
