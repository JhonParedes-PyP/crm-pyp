import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\judicial\detalle.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

modal_html = """
<!-- Modal Editar Expediente -->
<div id="editExpedienteModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000;">
    <div style="background: white; width: 600px; margin: 50px auto; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); overflow: hidden; max-height: 90vh; display: flex; flex-direction: column;">
        <div style="background: #003366; color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0; font-size: 18px;">Editar Datos del Expediente</h3>
            <span onclick="document.getElementById('editExpedienteModal').style.display='none'" style="cursor: pointer; font-weight: bold; font-size: 20px;">&times;</span>
        </div>
        <div style="padding: 20px; overflow-y: auto;">
            <form method="POST">
                {% csrf_token %}
                <input type="hidden" name="action" value="edit_expediente">
                
                <h4 style="color: #003366; border-bottom: 2px solid #eee; padding-bottom: 5px; margin-top: 0;">Datos Principales</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
                    <div><label style="font-size: 12px; font-weight: bold;">N&deg; Expediente</label><input type="text" name="numero_expediente" value="{{ expediente.numero_expediente|default:'' }}" style="width:100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"></div>
                    <div><label style="font-size: 12px; font-weight: bold;">Materia</label><input type="text" name="materia" value="{{ expediente.materia|default:'' }}" style="width:100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"></div>
                    <div><label style="font-size: 12px; font-weight: bold;">Juzgado</label><input type="text" name="juzgado" value="{{ expediente.juzgado|default:'' }}" style="width:100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"></div>
                    <div><label style="font-size: 12px; font-weight: bold;">Sede Judicial</label><input type="text" name="sede_judicial" value="{{ expediente.sede_judicial|default:'' }}" style="width:100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"></div>
                    <div><label style="font-size: 12px; font-weight: bold;">Distrito Judicial</label><input type="text" name="distrito_judicial" value="{{ expediente.distrito_judicial|default:'' }}" style="width:100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"></div>
                    <div><label style="font-size: 12px; font-weight: bold;">Monto Demandado</label><input type="number" step="0.01" name="monto_demandado" value="{{ expediente.monto_demandado|default:'' }}" style="width:100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"></div>
                    <div><label style="font-size: 12px; font-weight: bold;">Condici&oacute;n</label><input type="text" name="condicion_recuperabilidad" value="{{ expediente.condicion_recuperabilidad|default:'' }}" style="width:100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"></div>
                    <div>
                        <label style="font-size: 12px; font-weight: bold;">Estado Proceso</label>
                        <select name="estado_proceso" style="width:100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="ACTIVO" {% if expediente.estado_proceso == 'ACTIVO' %}selected{% endif %}>Activo</option>
                            <option value="ARCHIVO" {% if expediente.estado_proceso == 'ARCHIVO' %}selected{% endif %}>Archivo Provisional</option>
                            <option value="CONCLUIDO" {% if expediente.estado_proceso == 'CONCLUIDO' %}selected{% endif %}>Concluido</option>
                        </select>
                    </div>
                </div>

                <h4 style="color: #ffc107; border-bottom: 2px solid #eee; padding-bottom: 5px;">Medida Cautelar</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px;">
                    <div><label style="font-size: 12px; font-weight: bold;">N&deg; Cautelar</label><input type="text" name="numero_cautelar" value="{{ expediente.numero_cautelar|default:'' }}" style="width:100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"></div>
                    <div><label style="font-size: 12px; font-weight: bold;">C&oacute;digo Cautelar</label><input type="text" name="codigo_cautelar" value="{{ expediente.codigo_cautelar|default:'' }}" style="width:100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"></div>
                    <div><label style="font-size: 12px; font-weight: bold;">Tipo Medida</label><input type="text" name="tipo_medida_cautelar" value="{{ expediente.tipo_medida_cautelar|default:'' }}" style="width:100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"></div>
                    <div><label style="font-size: 12px; font-weight: bold;">Estado Cautelar</label><input type="text" name="estado_cautelar" value="{{ expediente.estado_cautelar|default:'' }}" style="width:100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"></div>
                    <div><label style="font-size: 12px; font-weight: bold;">Fecha Cautelar</label><input type="date" name="fecha_cautelar" value="{{ expediente.fecha_cautelar|date:'Y-m-d' }}" style="width:100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"></div>
                </div>
                
                <div style="text-align: right;">
                    <button type="button" onclick="document.getElementById('editExpedienteModal').style.display='none'" style="background: #ccc; color: #333; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer; font-weight: bold; margin-right: 10px;">Cancelar</button>
                    <button type="submit" style="background: #0056b3; color: white; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer; font-weight: bold;">Guardar Cambios</button>
                </div>
            </form>
        </div>
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

button_html = """            <button onclick="document.getElementById('editExpedienteModal').style.display='block'" class="btn btn-warning">
                <i class="fas fa-edit"></i> Editar Datos
            </button>
"""

# Insert button next to "Ver Ficha de Cobranza"
old_buttons = """        <div>
            <a href="{% url 'registrar_gestion' expediente.deudor.id %}" class="btn btn-outline-primary">
                <i class="fas fa-user"></i> Ver Ficha de Cobranza
            </a>"""

content = content.replace(old_buttons, old_buttons + "\n" + button_html)
content = content + modal_html

# Insert messages after h2 container
old_header = """    </div>

    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">"""

content = content.replace(old_header, "    </div>\n" + messages_html + "\n    <div style=\"display: grid; grid-template-columns: 2fr 1fr; gap: 20px;\">")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("PATCH DETALLE.HTML SUCCESS")
