import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\gestionar.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """                {% if c.negociacion %}
                <p style="margin: 3px 0; font-size: 12px; color: #555;">
                    <strong>Negociaci&oacute;n:</strong> 
                    {% if 'CON NEGOCIACI' in c.negociacion %}
                        <span style="color: #155724; background-color: #d4edda; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{{ c.negociacion }}</span>
                    {% elif 'SIN NEGOCIACI' in c.negociacion %}
                        <span style="color: #721c24; background-color: #f8d7da; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{{ c.negociacion }}</span>
                    {% else %}
                        <span style="color: #0c5460; background-color: #d1ecf1; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{{ c.negociacion }}</span>
                    {% endif %}
                </p>
                {% endif %}"""

new_block = """                {% if c.negociacion %}
                <p style="margin: 3px 0; font-size: 12px; color: #555;">
                    <strong>Negociaci&oacute;n:</strong> 
                    {% if 'CON NEGOCIACI' in c.negociacion.upper %}
                        <span style="color: #155724; background-color: #d4edda; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{{ c.negociacion }}</span>
                    {% elif 'SIN NEGOCIACI' in c.negociacion.upper %}
                        <span style="color: #721c24; background-color: #f8d7da; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{{ c.negociacion }}</span>
                    {% else %}
                        <span style="color: #0c5460; background-color: #d1ecf1; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{{ c.negociacion }}</span>
                    {% endif %}
                </p>
                {% endif %}"""

content = content.replace(old_block, new_block)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("PATCH 4 SUCCESS")
