import os
import re

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\judicial\detalle.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """        <div>
            <a href="{% url 'registrar_gestion' expediente.deudor.id %}" class="btn btn-outline-primary">
                <i class="fas fa-user"></i> Ver Ficha de Cobranza
            </a>
            <button onclick="document.getElementById('editExpedienteModal').style.display='block'" class="btn btn-warning">
                <i class="fas fa-edit"></i> Editar Datos
            </button>

            <a href="{% url 'dashboard_judicial' %}" class="btn btn-secondary">
                <i class="fas fa-arrow-left"></i> Volver al Panel
            </a>
        </div>"""

new_block = """        <div style="display: flex; gap: 12px; align-items: center;">
            <a href="{% url 'registrar_gestion' expediente.deudor.id %}" style="background-color: #f8f9fa; color: #0056b3; border: 1px solid #0056b3; padding: 10px 16px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 14px; display: inline-flex; align-items: center; transition: 0.2s;" onmouseover="this.style.backgroundColor='#0056b3'; this.style.color='white';" onmouseout="this.style.backgroundColor='#f8f9fa'; this.style.color='#0056b3';">
                <i class="fas fa-user-circle" style="margin-right: 6px; font-size: 16px;"></i> Ficha de Cobranza
            </a>
            <button onclick="document.getElementById('editExpedienteModal').style.display='block'" style="background-color: #ffc107; color: #212529; border: none; padding: 10px 16px; border-radius: 6px; font-weight: 600; font-size: 14px; display: inline-flex; align-items: center; cursor: pointer; transition: 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" onmouseover="this.style.backgroundColor='#e0a800';" onmouseout="this.style.backgroundColor='#ffc107';">
                <i class="fas fa-edit" style="margin-right: 6px; font-size: 16px;"></i> Editar Datos
            </button>
        </div>"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("PATCH BUTTONS SUCCESS")
else:
    print("BLOCK NOT FOUND!")
    
