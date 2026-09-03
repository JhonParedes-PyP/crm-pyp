import os
import re

file_path = r'c:\CRM PYP\crm_pyp_config\urls.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add the import and url path
if 'subir_excel_judicial' not in content:
    content = content.replace(
        'from cobranza.judicial_views import dashboard_judicial, buscar_expediente, detalle_expediente', 
        'from cobranza.judicial_views import dashboard_judicial, buscar_expediente, detalle_expediente, subir_excel_judicial'
    )
    content = content.replace(
        "path('judicial/detalle/<int:expediente_id>/', detalle_expediente, name='detalle_expediente'),", 
        "path('judicial/detalle/<int:expediente_id>/', detalle_expediente, name='detalle_expediente'),\n    path('judicial/subir-excel/', subir_excel_judicial, name='subir_excel_judicial'),"
    )

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('urls.py updated')
