import os

file_path = r"c:\CRM PYP\cobranza\dashboard_views.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace sorting logic in asignaciones_del_dia
old_sort = ".order_by('-deudor__saldo_deuda', 'deudor__nombre_completo')"
new_sort = ".order_by('-deudor__score', '-deudor__saldo_deuda')"

if old_sort in content:
    content = content.replace(old_sort, new_sort)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("dashboard_views.py sorting patched!")
else:
    print("Sorting code not found!")
