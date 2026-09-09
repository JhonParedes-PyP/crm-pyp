import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\judicial\buscar.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

modal_html = """
<div id="addExpedienteModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000;">
    <div style="background: white; width: 500px; margin: 100px auto; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); overflow: hidden;">
        <div style="background: #003366; color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0; font-size: 18px;">Agregar Expediente Nuevo</h3>
            <span onclick="document.getElementById('addExpedienteModal').style.display='none'" style="cursor: pointer; font-weight: bold; font-size: 20px;">&times;</span>
        </div>
        <form method="POST" style="padding: 20px;">
            {% csrf_token %}
            <input type="hidden" name="action" value="crear_expediente">
            <div style="margin-bottom: 15px;">
                <label style="display: block; font-size: 13px; font-weight: bold; margin-bottom: 5px;">DNI o Cuenta del Cliente (*)</label>
                <input type="text" name="doc_or_cuenta" required style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box;">
            </div>
            <div style="margin-bottom: 15px;">
                <label style="display: block; font-size: 13px; font-weight: bold; margin-bottom: 5px;">N&deg; Expediente Principal (*)</label>
                <input type="text" name="numero_expediente" required style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box;">
            </div>
            <div style="margin-bottom: 15px;">
                <label style="display: block; font-size: 13px; font-weight: bold; margin-bottom: 5px;">Materia (*)</label>
                <input type="text" name="materia" required style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box;">
            </div>
            <div style="margin-bottom: 25px;">
                <label style="display: block; font-size: 13px; font-weight: bold; margin-bottom: 5px;">Juzgado (*)</label>
                <input type="text" name="juzgado" required style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box;">
            </div>
            <div style="text-align: right;">
                <button type="button" onclick="document.getElementById('addExpedienteModal').style.display='none'" style="background: #ccc; color: #333; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer; margin-right: 10px; font-weight: bold;">Cancelar</button>
                <button type="submit" style="background: #28a745; color: white; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer; font-weight: bold;">Crear Expediente</button>
            </div>
        </form>
    </div>
</div>
"""

messages_html = """
{% if messages %}
    {% for message in messages %}
        <div style="padding: 15px; margin-bottom: 20px; border-radius: 6px; background: {% if message.tags == 'error' %}#f8d7da{% else %}#d4edda{% endif %}; color: {% if message.tags == 'error' %}#721c24{% else %}#155724{% endif %};">
            {{ message }}
        </div>
    {% endfor %}
{% endif %}
"""

button_html = """
    <div>
        <button onclick="document.getElementById('addExpedienteModal').style.display='block'" style="background: #28a745; color: white; padding: 10px 15px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; margin-right: 10px;"><i class="fas fa-plus"></i> Nuevo Expediente</button>
        <a href="{% url 'dashboard_judicial' %}" style="background: #6c757d; color: white; padding: 10px 15px; border-radius: 6px; text-decoration: none; font-weight: bold;">Volver al Panel</a>
    </div>
"""

# Replace the div with the links
old_div = """    <div>
        <a href="{% url 'dashboard_judicial' %}" style="background: #6c757d; color: white; padding: 10px 15px; border-radius: 6px; text-decoration: none; font-weight: bold;">Volver al Panel</a>
    </div>"""

content = content.replace(old_div, button_html)
content = content + modal_html

# Insert messages after h1 div
old_header = """</div>

<div style="background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 30px;">"""

content = content.replace(old_header, "</div>\n" + messages_html + "\n<div style=\"background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 30px;\">")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("PATCH BUSCAR.HTML SUCCESS")
