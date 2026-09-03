import re
import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\judicial\dashboard.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacement = """
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
    <h1 style="color: #003366; margin: 0;">⚖️ Panel de Gestión Judicial</h1>
    <div>
        <a href="{% url 'subir_excel_judicial' %}" style="background: #28a745; color: white; padding: 10px 15px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-right: 10px;">
            📥 Subir Cartera Judicial
        </a>
        <a href="{% url 'buscar_expediente' %}" style="background: #0056b3; color: white; padding: 10px 15px; border-radius: 6px; text-decoration: none; font-weight: bold;">
            🔍 Buscar Expediente
        </a>
    </div>
</div>
"""

content = re.sub(r'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">.*?</div>', replacement.strip(), content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('dashboard fixed properly')
