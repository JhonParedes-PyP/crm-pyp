import os
import re

file_path = r"c:\CRM PYP\cobranza\dashboard_views.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the block dynamically using regex to avoid mojibake mismatches
pattern = r"    pagos_no_reflejados_huancayo = \[\]\s*if es_gerente_flag:\s*gestiones_pago_mes = Gestion\.objects\.filter\("
replacement = r"    pagos_no_reflejados_huancayo = []\n    if True:\n        gestiones_pago_mes = Gestion.objects.filter("

content = re.sub(pattern, replacement, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed unbound variable!")
