import os
import re

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\gestionar.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """                {% endif %}
                {% if c.rango_dias_mora %}"""

new_code = """                {% endif %}
                {% if c.cuota_pendiente or c.total_cuotas or c.monto_cuota_atrasada %}
                <div style="margin-top: 5px; padding: 8px; background: #eef2f5; border-left: 3px solid #0056b3; border-radius: 4px; font-size: 11px;">
                    <p style="margin: 0 0 3px 0; font-weight: bold; color: #0056b3;">Detalles de Convenio / Cuotas:</p>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">
                        {% if c.cuota_pendiente %}<div><strong>Cuota:</strong> {{ c.cuota_pendiente }} / {{ c.total_cuotas|default:"-" }}</div>{% endif %}
                        {% if c.fecha_pago_cuota_pendiente %}<div><strong>Fec. Pago:</strong> {{ c.fecha_pago_cuota_pendiente|date:"d/m/Y" }}</div>{% endif %}
                        {% if c.monto_cuota_atrasada %}<div><strong>Atrasada:</strong> S/ {{ c.monto_cuota_atrasada|floatformat:2|intcomma }}</div>{% endif %}
                        {% if c.dias_atraso_cuota != None %}<div><strong>Días Atraso:</strong> <span style="color: {% if c.dias_atraso_cuota > 0 %}red{% else %}green{% endif %}; font-weight: bold;">{{ c.dias_atraso_cuota }}</span></div>{% endif %}
                        {% if c.credito_al_dia %}<div><strong>¿Al día?:</strong> 
                            <span style="color: {% if c.credito_al_dia == 'SI' %}green{% else %}red{% endif %}; font-weight: bold;">{{ c.credito_al_dia }}</span>
                        </div>{% endif %}
                    </div>
                </div>
                {% endif %}
                {% if c.rango_dias_mora %}"""

if target in content:
    content = content.replace(target, new_code)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("PATCH GESTIONAR.HTML SUCCESS")
else:
    print("TARGET NOT FOUND")
