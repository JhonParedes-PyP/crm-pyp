import os

file_path = r'c:\CRM PYP\cobranza\judicial_views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

if "from .asignaciones import aplicar_visibilidad_por_asignaciones" not in content:
    content = content.replace("from django.db.models import Count, Q", "from django.db.models import Count, Q\nfrom .asignaciones import aplicar_visibilidad_por_asignaciones")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Import added successfully.")
else:
    print("Import already exists.")
