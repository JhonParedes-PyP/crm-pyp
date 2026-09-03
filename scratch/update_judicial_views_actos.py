import re
import os

file_path = r'c:\CRM PYP\cobranza\judicial_views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add cuaderno support and delete action
old_post = """    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_acto':
            ActoProcesal.objects.create(
                expediente=expediente,
                numero_resolucion=request.POST.get('numero_resolucion'),
                fecha_resolucion=request.POST.get('fecha_resolucion'),
                fecha_notificacion=request.POST.get('fecha_notificacion') or None,
                descripcion=request.POST.get('descripcion'),
                sumilla=request.POST.get('sumilla'),
                fojas=request.POST.get('fojas') or None,
                registrado_por=request.user
            )
        elif action == 'add_alerta':"""

new_post = """    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_acto':
            ActoProcesal.objects.create(
                expediente=expediente,
                cuaderno=request.POST.get('cuaderno', 'PRINCIPAL'),
                numero_resolucion=request.POST.get('numero_resolucion'),
                fecha_resolucion=request.POST.get('fecha_resolucion'),
                fecha_notificacion=request.POST.get('fecha_notificacion') or None,
                descripcion=request.POST.get('descripcion'),
                sumilla=request.POST.get('sumilla'),
                fojas=request.POST.get('fojas') or None,
                registrado_por=request.user
            )
        elif action == 'delete_acto':
            if request.user.is_superuser or request.user.groups.filter(name='Gerencia').exists():
                acto_id = request.POST.get('acto_id')
                ActoProcesal.objects.filter(id=acto_id).delete()
        elif action == 'add_alerta':"""
content = content.replace(old_post, new_post)

# Pass es_gerencia to template
old_render = """    return render(request, 'cobranza/judicial/detalle.html', {
        'expediente': expediente,
        'actos': actos,
        'alertas': alertas
    })"""
new_render = """    es_gerencia = request.user.is_superuser or request.user.groups.filter(name='Gerencia').exists()
    return render(request, 'cobranza/judicial/detalle.html', {
        'expediente': expediente,
        'actos': actos,
        'alertas': alertas,
        'es_gerencia': es_gerencia
    })"""
content = content.replace(old_render, new_render)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("judicial_views.py updated successfully.")
