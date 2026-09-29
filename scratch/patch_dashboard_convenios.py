import os

file_path = r'c:\CRM PYP\cobranza\dashboard_views.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Original string
target = """    convenios_base = Convenio.objects.select_related('deudor').annotate(
        ya_pago=Exists(gestiones_recientes_pago)
    ).filter(ya_pago=False)"""

# New string
new_content = """    convenios_base = Convenio.objects.select_related('deudor').annotate(
        ya_pago=Exists(gestiones_recientes_pago)
    ).filter(ya_pago=False, deudor__activo=True)"""

content = content.replace(target, new_content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("PATCH DASHBOARD SUCCESS")
