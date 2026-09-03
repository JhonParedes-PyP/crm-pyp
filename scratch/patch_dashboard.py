import re
import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\judicial\dashboard.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacement = """
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>⚖️ Panel de Gestión Judicial</h2>
        <div>
            {% if request.user.is_superuser or request.user.groups.all.0.name == 'Gerencia' %}
            <a href="{% url 'subir_excel_judicial' %}" class="btn btn-success me-2">
                <i class="fas fa-file-excel"></i> Subir Cartera Judicial
            </a>
            {% endif %}
            <a href="{% url 'buscar_expediente' %}" class="btn btn-primary">
                <i class="fas fa-search"></i> Buscar Expediente
            </a>
        </div>
    </div>
"""

content = re.sub(r'<div class="d-flex justify-content-between align-items-center mb-4">.*?</div>', replacement.strip(), content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('dashboard.html updated')
