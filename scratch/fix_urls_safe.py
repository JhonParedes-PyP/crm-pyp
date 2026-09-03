import re
import os

file_path = r'c:\CRM PYP\crm_pyp_config\urls.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacement = """
    # --- MÓDULO JUDICIAL ---
    path('judicial/dashboard/', judicial_views.dashboard_judicial, name='dashboard_judicial'),
    path('judicial/buscar/', judicial_views.buscar_expediente, name='buscar_expediente'),
    path('judicial/expediente/<int:expediente_id>/', judicial_views.detalle_expediente, name='detalle_expediente'),
    path('judicial/subir-excel/', judicial_views.subir_excel_judicial, name='subir_excel_judicial'),
"""

# I will be extremely careful and NOT use .* with re.DOTALL across the whole file!
# Instead I will just replace the exact line for detalle_expediente.
target = "path('judicial/expediente/<int:expediente_id>/', judicial_views.detalle_expediente, name='detalle_expediente'),"
replacement = "path('judicial/expediente/<int:expediente_id>/', judicial_views.detalle_expediente, name='detalle_expediente'),\n    path('judicial/subir-excel/', judicial_views.subir_excel_judicial, name='subir_excel_judicial'),"

content = content.replace(target, replacement)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('urls fixed safely')
