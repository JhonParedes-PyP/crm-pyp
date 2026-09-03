import os

file_path = r'c:\CRM PYP\cobranza\judicial_views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# We need to add timezone imported if not present
if 'from django.utils import timezone' not in content:
    content = 'from django.utils import timezone\n' + content

# Replace the ActoProcesal creation
# seg_prin block
old_prin = """                                    seg_prin = get_val(row, ['SEGUIMIENTO DEL CUADERNO PRINCIPAL'])
                                    if seg_prin:
                                        ActoProcesal.objects.get_or_create(
                                            expediente=exp,
                                            descripcion='Historial Importado (Drive)',
                                            sumilla=seg_prin,
                                            cuaderno='PRINCIPAL',
                                            defaults={'registrado_por': request.user}
                                        )"""
new_prin = """                                    seg_prin = get_val(row, ['SEGUIMIENTO DEL CUADERNO PRINCIPAL'])
                                    if seg_prin:
                                        fecha_prin = safe_date_judicial(get_val(row, ['FECHA DE ULTIMO ACTUADO PROCESAL'])) or timezone.now().date()
                                        ActoProcesal.objects.get_or_create(
                                            expediente=exp,
                                            descripcion='Historial Importado (Drive)',
                                            sumilla=seg_prin,
                                            cuaderno='PRINCIPAL',
                                            defaults={
                                                'registrado_por': request.user,
                                                'fecha_resolucion': fecha_prin
                                            }
                                        )"""
content = content.replace(old_prin, new_prin)

# seg_cau block
old_cau = """                                    seg_cau = get_val(row, ['SEGUIMIENTO DEL CUAD CAU', 'SEGUIMIENTO DEL CUADERNO CAUTELAR'])
                                    if seg_cau:
                                        ActoProcesal.objects.get_or_create(
                                            expediente=exp,
                                            descripcion='Historial Cautelar Importado (Drive)',
                                            sumilla=seg_cau,
                                            cuaderno='CAUTELAR',
                                            defaults={'registrado_por': request.user}
                                        )"""
new_cau = """                                    seg_cau = get_val(row, ['SEGUIMIENTO DEL CUAD CAU', 'SEGUIMIENTO DEL CUADERNO CAUTELAR'])
                                    if seg_cau:
                                        fecha_cau = safe_date_judicial(get_val(row, ['FECHA DEL ULTMO ACTUADO CAUTELAR', 'FECHA DE ULTIMO ACTUADO CAUTELAR'])) or timezone.now().date()
                                        ActoProcesal.objects.get_or_create(
                                            expediente=exp,
                                            descripcion='Historial Cautelar Importado (Drive)',
                                            sumilla=seg_cau,
                                            cuaderno='CAUTELAR',
                                            defaults={
                                                'registrado_por': request.user,
                                                'fecha_resolucion': fecha_cau
                                            }
                                        )"""
content = content.replace(old_cau, new_cau)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed missing fecha_resolucion in upload script')
