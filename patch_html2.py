import os

html_path = r"c:\CRM PYP\cobranza\templates\cobranza\dashboard.html"
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("var metas = JSON.parse('{{ metas_json|escapejs }}');", "var metas = {{ metas_json|safe }};")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated dashboard.html")
