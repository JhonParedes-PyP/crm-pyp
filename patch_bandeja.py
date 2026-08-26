import os

html_path = r"c:\CRM PYP\cobranza\templates\cobranza\bandeja.html"
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the incorrect pagination parameter
old_str = "{% if agencia_filtro %}&agencia={{ agencia_filtro }}{% endif %}"
new_str = "{% for ag in agencia_filtro %}&agencia={{ ag|urlencode }}{% endfor %}"

content = content.replace(old_str, new_str)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched bandeja.html pagination!")
