import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\base.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

judicial_menu = '''
            <!-- GESTIÓN JUDICIAL -->
            {% if request.user.username == 'JPAREDES' or request.user.is_superuser %}
            <details class="menu-group">
                <summary class="group-title">⚖️ Gestión Judicial</summary>
                <a href="{% url 'dashboard_judicial' %}">📊 Panel Judicial</a>
                <a href="{% url 'buscar_expediente' %}">🔍 Buscar Expediente</a>
            </details>
            {% endif %}
            
            <!-- OPERACIONES (Gerencia) -->'''

if 'Gestión Judicial' not in content:
    content = content.replace('<!-- OPERACIONES (Gerencia) -->', judicial_menu)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Menu added.')
