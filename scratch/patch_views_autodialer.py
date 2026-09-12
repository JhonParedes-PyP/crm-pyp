import re
import os

file_path = r'c:\CRM PYP\cobranza\views.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add auto_dialer to parametros_url
pattern = r"if filtros\.get\('modo'\): params\.append\(f\"modo=\{filtros\['modo'\]\}\"\)"
replacement = r"""if filtros.get('modo'): params.append(f"modo={filtros['modo']}")
    
    if request.GET.get('auto_dialer'):
        params.append('auto_dialer=1')"""

content = re.sub(pattern, replacement, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("PATCH VIEWS SUCCESS")
