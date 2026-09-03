import re
import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\judicial\detalle.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the H2
content = re.sub(
    r'<h2>⚖️ Expediente Judicial:.*?</h2>',
    r'<h2>⚖️ Cliente: {{ expediente.deudor.nombre_completo }} | Cuenta: {{ expediente.deudor.cuenta|default:"-" }}</h2>',
    content
)

# Replace the content of the Principal box
# We need to add the N° Expediente and remove the Cliente
principal_html_old = """
                    <div style="background: #003366; color: white; padding: 15px 20px;">
                        <h4 style="margin: 0;">Cuaderno Principal</h4>
                    </div>
                    <div style="padding: 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div>
                            <small style="color: #666; font-weight: bold; text-transform: uppercase;">Cliente</small>
                            <p style="margin: 5px 0 0;">{{ expediente.deudor.nombre_completo }}<br><small style="color: #888;">DNI: {{ expediente.deudor.documento }}</small></p>
                        </div>
"""
principal_html_new = """
                    <div style="background: #003366; color: white; padding: 15px 20px;">
                        <h4 style="margin: 0;">Cuaderno Principal</h4>
                    </div>
                    <div style="padding: 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div>
                            <small style="color: #666; font-weight: bold; text-transform: uppercase;">N° Expediente</small>
                            <p style="margin: 5px 0 0; font-weight: bold;">{{ expediente.numero_expediente|default:"-" }}</p>
                        </div>
"""
content = content.replace(principal_html_old, principal_html_new)

# For the yellow box (Cautelar), let's ensure we are showing it even if it's empty, as the user requested "SI TIENE NO TIENE CAUTELAR PUES EN BLANCO". It's already doing this if it just renders empty vars.

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('detalle.html UI updated')
