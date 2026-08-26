import os
import re

urls_path = r"c:\CRM PYP\crm_pyp_config\urls.py"

with open(urls_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add whatsapp_views import
import_line = "from cobranza import views, api_views, campanas_views, dashboard_views, views_rutas, estrategia_ia_views, whatsapp_views"
content = content.replace("from cobranza import views, api_views, campanas_views, dashboard_views, views_rutas, estrategia_ia_views", import_line)

# Add URL patterns
urls_to_add = """
    # --- 📲 WHATSAPP MASIVO ---
    path('whatsapp-masivo/', whatsapp_views.panel_whatsapp_masivo, name='panel_whatsapp_masivo'),
    path('whatsapp-masivo/exportar/', whatsapp_views.exportar_whatsapp_excel, name='exportar_whatsapp_excel'),
"""

content = content.replace("] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)", urls_to_add + "\n] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)")

with open(urls_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("urls.py patched.")
