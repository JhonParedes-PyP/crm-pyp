import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\gestionar.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

judicial_btn = '''
            {% if deudor.expedientes_judiciales.exists %}
            <div style="margin-top: 15px;">
                <a href="{% url 'detalle_expediente' deudor.expedientes_judiciales.first.id %}" target="_blank" style="background: #dc3545; color: white; padding: 8px 12px; border-radius: 6px; text-decoration: none; font-weight: bold; display: inline-block; font-size: 13px;">⚖️ Ver Expediente Judicial</a>
            </div>
            {% endif %}
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">'''

if 'Ver Expediente Judicial' not in content:
    content = content.replace('<hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">', judicial_btn, 1)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Button added to gestionar.html')
