import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\judicial\buscar.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_form = """    <form method="GET" style="display: flex; gap: 10px;">
        <input type="text" name="q" value="{{ query }}" placeholder="Buscar por N° de Expediente, DNI o Nombre del Cliente..." style="flex: 1; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px;">
        <button type="submit" style="background: #0056b3; color: white; padding: 12px 25px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold;">Buscar</button>
    </form>"""

new_form = """    <form method="GET" style="display: flex; gap: 10px; flex-wrap: wrap;">
        <input type="text" name="q" value="{{ query }}" placeholder="Buscar por N° de Expediente, DNI o Nombre del Cliente..." style="flex: 2; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; min-width: 300px;">
        
        <select name="cartera" style="flex: 1; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; min-width: 150px;">
            <option value="">-- Todas las Carteras --</option>
            {% for c in carteras %}
                {% if c and c != 'nan' %}
                    <option value="{{ c }}" {% if cartera_q == c %}selected{% endif %}>{{ c }}</option>
                {% endif %}
            {% endfor %}
        </select>

        <select name="agencia" style="flex: 1; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; min-width: 150px;">
            <option value="">-- Todas las Agencias --</option>
            {% for a in agencias %}
                {% if a and a != 'nan' %}
                    <option value="{{ a }}" {% if agencia_q == a %}selected{% endif %}>{{ a }}</option>
                {% endif %}
            {% endfor %}
        </select>

        <button type="submit" style="background: #0056b3; color: white; padding: 12px 25px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold;">Buscar</button>
    </form>"""

content = content.replace(old_form, new_form)

# Also fix {% if query %} to {% if query or cartera_q or agencia_q %}
content = content.replace('{% if query %}', '{% if query or cartera_q or agencia_q %}')

# And change the empty state message
old_empty = 'No se encontraron expedientes con la búsqueda "{{ query }}".'
new_empty = 'No se encontraron expedientes con los filtros aplicados.'
content = content.replace(old_empty, new_empty)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('buscar.html updated')
