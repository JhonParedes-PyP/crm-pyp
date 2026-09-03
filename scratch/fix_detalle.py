import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\judicial\detalle.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("{% url 'detalle_deudor' expediente.deudor.id %}", "{% url 'registrar_gestion' expediente.deudor.id %}")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('detalle.html fixed')
