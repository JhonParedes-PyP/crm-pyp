import os

views_path = r"c:\CRM PYP\cobranza\dashboard_views.py"
with open(views_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Move metas_data load out of if es_gerente_flag, to the top level context
# The current code has:
#    import json
#    
#    # Cargar metas
#    from django.conf import settings
#    import os as ds_os
#    metas_path = ds_os.path.join(settings.BASE_DIR, 'metas.json')
#    metas_data = {
#        'PROEMPRESA': 213674.00,
#        'CAJA HUANCAYO': 457116.49,
#        'FOCMAC': None
#    }
#    if ds_os.path.exists(metas_path):
#        try:
#            with open(metas_path, 'r', encoding='utf-8') as fm:
#                metas_data = json.load(fm)
#        except Exception:
#            pass

# We will just redefine it right before return render

fix_code = """
    # -- INICIO RECALCULO Y METAS --
    import json
    from django.conf import settings
    import os as ds_os
    
    # Asegurar que metas_data siempre exista y tenga los defaults
    metas_path = ds_os.path.join(settings.BASE_DIR, 'metas.json')
    metas_data = {
        'PROEMPRESA': 213674.00,
        'CAJA HUANCAYO': 457116.49,
        'FOCMAC': None
    }
    if ds_os.path.exists(metas_path):
        try:
            with open(metas_path, 'r', encoding='utf-8') as fm:
                loaded = json.load(fm)
                metas_data.update(loaded) # Mezclar para no perder llaves
        except Exception:
            pass

    # Recalcular total_recuperado sumando los valores de recuperacion_carteras
    total_recuperado = sum(recuperacion_carteras.values())
    
    # -- FIN RECALCULO --
    return render(request, 'cobranza/dashboard.html', {
"""

content = content.replace("    return render(request, 'cobranza/dashboard.html', {", fix_code)

with open(views_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated dashboard_views.py")
