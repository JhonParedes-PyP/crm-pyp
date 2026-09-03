import re
import os

file_path = r'c:\CRM PYP\cobranza\judicial_views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_post = """        elif action == 'add_alerta':
            AlertaJudicial.objects.create(
                expediente=expediente,
                tipo_alerta=request.POST.get('tipo_alerta'),
                fecha_vencimiento=request.POST.get('fecha_vencimiento'),
                creado_por=request.user
            )"""

new_post = """        elif action == 'add_alerta':
            AlertaJudicial.objects.create(
                expediente=expediente,
                tipo_alerta=request.POST.get('tipo_alerta'),
                fecha_vencimiento=request.POST.get('fecha_vencimiento'),
                creado_por=request.user
            )
        elif action == 'complete_alerta':
            alerta_id = request.POST.get('alerta_id')
            alerta = AlertaJudicial.objects.filter(id=alerta_id, expediente=expediente).first()
            if alerta:
                alerta.estado = 'COMPLETADO'
                alerta.save()"""

if "elif action == 'add_alerta':" in content:
    content = content.replace(old_post, new_post)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("judicial_views.py updated successfully.")
else:
    print("Could not find the block to replace!")
