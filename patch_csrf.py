import os
views_path = r"c:\CRM PYP\cobranza\dashboard_views.py"
with open(views_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "@login_required\ndef guardar_metas(request):",
    "from django.views.decorators.csrf import csrf_exempt\n\n@login_required\n@csrf_exempt\ndef guardar_metas(request):"
)

with open(views_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Added csrf_exempt")
