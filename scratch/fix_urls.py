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

content = re.sub(r'# --- M.*DULO JUDICIAL ---.*?path\(\'judicial/expediente/<int:expediente_id>/\', judicial_views\.detalle_expediente, name=\'detalle_expediente\'\),', replacement.strip(), content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('urls fixed')
