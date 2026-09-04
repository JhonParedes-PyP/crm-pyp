import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\base.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_menu = """            <!-- GESTIÓN JUDICIAL -->
            {% if request.user.username == 'JPAREDES' or request.user.is_superuser %}
            <details class="menu-group">
                <summary class="group-title">⚖️ Gestión Judicial</summary>
                <a href="{% url 'dashboard_judicial' %}">📊 Panel Judicial</a>
                <a href="{% url 'buscar_expediente' %}">🔍 Buscar Expediente</a>
            </details>
            {% endif %}"""

new_menu = """            <!-- GESTIÓN JUDICIAL -->
            {% if user.is_authenticated %}
            <details class="menu-group">
                <summary class="group-title">⚖️ Gestión Judicial</summary>
                <a href="{% url 'dashboard_judicial' %}">📊 Panel Judicial</a>
                <a href="{% url 'buscar_expediente' %}">🔍 Buscar Expediente</a>
            </details>
            {% endif %}"""

if old_menu in content:
    content = content.replace(old_menu, new_menu)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("base.html updated successfully.")
else:
    print("Could not find the menu block to replace!")
