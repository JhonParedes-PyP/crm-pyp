import re

file_path = r'c:\CRM PYP\cobranza\views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r"(        return redirect\(f\"\{reverse\('asignaciones_diarias'\)\}\?\{redirect_params\}\"\)\n\n    )deudores = Deudor\.objects\.all\(\)"

replacement = r"\1if q:\n        deudores = Deudor.objects.all()\n    else:\n        deudores = Deudor.objects.filter(activo=True)"

new_content = re.sub(pattern, replacement, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Patch applied")
