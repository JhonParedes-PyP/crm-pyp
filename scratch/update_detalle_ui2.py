import re
import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\judicial\detalle.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the H2
content = re.sub(
    r'<h2>.*?Expediente Judicial:.*?</h2>',
    r'<h2>⚖️ Cliente: {{ expediente.deudor.nombre_completo }} | Cuenta: {{ expediente.deudor.cuenta|default:"-" }}</h2>',
    content
)

# Replace the Cliente box inside Cuaderno Principal
content = content.replace(
    '<div><strong style="color: #666; font-size: 12px; text-transform: uppercase;">Cliente</strong><div style="font-weight: 500;">{{ expediente.deudor.nombre_completo }}</div></div>',
    '<div><strong style="color: #666; font-size: 12px; text-transform: uppercase;">N° Expediente</strong><div style="font-weight: 500; color: #003366;">{{ expediente.numero_expediente|default:"-" }}</div></div>'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('detalle.html UI updated')
