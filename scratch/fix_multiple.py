import os

file_path = r'c:\CRM PYP\cobranza\judicial_views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """                                    exp, created = ExpedienteJudicial.objects.update_or_create(
                                        deudor=deudor,
                                        defaults=defaults_dict
                                    )
                                    if created:
                                        expedientes_creados += 1"""

new_block = """                                    exp = ExpedienteJudicial.objects.filter(deudor=deudor).first()
                                    if not exp:
                                        exp = ExpedienteJudicial(deudor=deudor)
                                        expedientes_creados += 1
                                        
                                    for field, value in defaults_dict.items():
                                        setattr(exp, field, value)
                                    exp.save()"""

content = content.replace(old_block, new_block)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed update_or_create')
