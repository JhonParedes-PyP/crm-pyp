import os
import re

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\gestionar.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r'\{\% if c\.negociacion \%\}<p style="margin: 3px 0; font-size: 12px; color: #555;"><strong>Negociación:</strong> \{\{ c\.negociacion \}\}</p>\{\% endif \%\}')

replacement = """{% if c.negociacion %}
                <p style="margin: 3px 0; font-size: 12px; color: #555;">
                    <strong>Negociacin:</strong> 
                    {% if 'CON NEGOCIACI' in c.negociacion %}
                        <span style="color: #155724; background-color: #d4edda; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{{ c.negociacion }}</span>
                    {% elif 'SIN NEGOCIACI' in c.negociacion %}
                        <span style="color: #721c24; background-color: #f8d7da; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{{ c.negociacion }}</span>
                    {% else %}
                        <span style="color: #0c5460; background-color: #d1ecf1; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{{ c.negociacion }}</span>
                    {% endif %}
                </p>
                {% endif %}"""

# Let's replace the utf-8 characters properly
replacement = replacement.replace("Negociacin", "Negociación")

if pattern.search(content):
    content = pattern.sub(replacement, content)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("PATCH SUCCESS")
else:
    # Try an exact line replacement
    print("PATCH FAILED WITH REGEX. Trying manual replacement...")
