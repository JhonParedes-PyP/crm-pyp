import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\gestionar.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """                <p style="margin: 3px 0; color: #444;"><strong>Cónyuge Aval 1:</strong><br> {% if c.nom_conyuge_aval %}{{ c.nom_conyuge_aval }}{% else %}--{% endif %}</p>
            </div>"""

new_content = """                <p style="margin: 3px 0; color: #444;"><strong>Cónyuge Aval 1:</strong><br> {% if c.nom_conyuge_aval %}{{ c.nom_conyuge_aval }}{% else %}--{% endif %}</p>
            </div>
            
            <!-- BOTON IMPRIMIR CARTAS -->
            <div style="margin-bottom: 15px;">
                <a href="{% url 'generar_cartas' %}?descargar=1&cliente_dni={{ c.documento|urlencode }}" 
                   style="display: block; width: 100%; text-align: center; background: #6c757d; color: white; padding: 10px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 13px; box-sizing: border-box; transition: background 0.2s;"
                   onmouseover="this.style.background='#5a6268'"
                   onmouseout="this.style.background='#6c757d'">
                    📄 Imprimir Carta(s) de este Cliente
                </a>
            </div>"""

# Ensure character encoding issues don't happen with "Cónyuge" by using regex
import re
pattern = re.compile(r'(<p style="margin: 3px 0; color: #444;"><strong>C[^n]+nyuge Aval 1:</strong>.*?</div>)', re.DOTALL)

match = pattern.search(content)
if match:
    block = match.group(1)
    content = content.replace(block, block + """
            
            <!-- BOTON IMPRIMIR CARTAS -->
            <div style="margin-bottom: 15px;">
                <a href="{% url 'generar_cartas' %}?descargar=1&cliente_dni={{ c.documento|urlencode }}" 
                   style="display: block; width: 100%; text-align: center; background: #6c757d; color: white; padding: 10px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 13px; box-sizing: border-box; transition: background 0.2s;"
                   onmouseover="this.style.background='#5a6268'"
                   onmouseout="this.style.background='#6c757d'">
                    📄 Imprimir Carta(s) de este Cliente
                </a>
            </div>""")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("PATCH GESTIONAR SUCCESS")
