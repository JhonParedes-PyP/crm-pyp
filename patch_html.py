import os

html_path = r"c:\CRM PYP\cobranza\templates\cobranza\dashboard.html"
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace hardcoded metas with context
content = content.replace("""    var metas = {
        'PROEMPRESA': 213674.00,
        'CAJA HUANCAYO': 457116.49,
        'FOCMAC': null // Libre
    };""", "    var metas = JSON.parse('{{ metas_json|escapejs }}');")

# Add the edit button
edit_btn = """<h3 style="color: #003366; margin-bottom: 15px; margin-top: 0; display: flex; align-items: center;">
        📊 Recuperación y Metas por Cartera (Mes Actual)
        {% if es_gerente %}
        <button onclick="abrirModalMetas()" style="margin-left: 10px; background: none; border: none; cursor: pointer; font-size: 18px;" title="Editar Metas">✏️</button>
        {% endif %}
    </h3>"""
content = content.replace('<h3 style="color: #003366; margin-bottom: 15px; margin-top: 0;">📊 Recuperación y Metas por Cartera (Mes Actual)</h3>', edit_btn)

# Add the edit modal
modal_code = """
<!-- Modal Editar Metas -->
<div id="modalMetas" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; justify-content: center; align-items: center;">
    <div style="background: white; padding: 25px; border-radius: 8px; width: 400px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
        <h3 style="margin-top: 0; color: #003366;">✏️ Editar Metas</h3>
        
        <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #555;">PROEMPRESA (S/):</label>
            <input type="number" step="0.01" id="metaProempresa" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;">
        </div>
        
        <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #555;">CAJA HUANCAYO (S/):</label>
            <input type="number" step="0.01" id="metaHuancayo" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;">
        </div>
        
        <div style="margin-bottom: 25px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #555;">FOCMAC (S/):</label>
            <input type="number" step="0.01" id="metaFocmac" placeholder="Dejar vacío para Libre" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;">
        </div>
        
        <div style="display: flex; justify-content: flex-end; gap: 10px;">
            <button onclick="document.getElementById('modalMetas').style.display='none'" style="padding: 8px 15px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">Cancelar</button>
            <button onclick="guardarMetas()" style="padding: 8px 15px; background: #003366; color: white; border: none; border-radius: 4px; cursor: pointer;">Guardar</button>
        </div>
    </div>
</div>

<script>
function abrirModalMetas() {
    document.getElementById('metaProempresa').value = metas['PROEMPRESA'] || '';
    document.getElementById('metaHuancayo').value = metas['CAJA HUANCAYO'] || '';
    document.getElementById('metaFocmac').value = metas['FOCMAC'] || '';
    
    var modal = document.getElementById('modalMetas');
    modal.style.display = 'flex';
}

function guardarMetas() {
    var payload = {
        'PROEMPRESA': parseFloat(document.getElementById('metaProempresa').value) || null,
        'CAJA HUANCAYO': parseFloat(document.getElementById('metaHuancayo').value) || null,
        'FOCMAC': parseFloat(document.getElementById('metaFocmac').value) || null
    };
    
    fetch("{% url 'guardar_metas' %}", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: JSON.stringify(payload)
    }).then(res => {
        if(res.ok) {
            window.location.reload();
        } else {
            alert("Error al guardar las metas.");
        }
    }).catch(err => {
        alert("Error de conexión.");
    });
}
</script>
"""
if "abrirModalMetas" not in content:
    content = content.replace("</body>", modal_code + "\n</body>")

# Add Proempresa no reflejados table
proempresa_table = """
    {% if es_gerente and pagos_no_reflejados_proempresa %}
    <div style="background: white; border-radius: 8px; padding: 20px; margin-top: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-left: 4px solid #dc3545;">
        <h3 style="color: #dc3545; margin-bottom: 15px; margin-top: 0; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 20px;">⚠️</span> Pagos No Reflejados Proempresa (Mes Actual)
        </h3>
        <p style="font-size: 13px; color: #666; margin-top: -10px; margin-bottom: 15px;">Clientes cuya base indica que realizaron un pago este mes (IMP RECUP > 0), pero que aún no cuentan con una gestión de PAGÓ registrada en el sistema.</p>
        
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <thead style="background-color: #f8f9fa;">
                    <tr>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Cliente</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Documento</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Gestor Asignado</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">IMP RECUP</th>
                        <th style="padding: 10px; text-align: center; border-bottom: 2px solid #dee2e6;">Acción</th>
                    </tr>
                </thead>
                <tbody>
                    {% for p in pagos_no_reflejados_proempresa %}
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px;">{{ p.nombre_completo }}</td>
                        <td style="padding: 10px;">{{ p.documento }}</td>
                        <td style="padding: 10px;">
                            {% if p.gestores_actuales.all %}
                                {% for ag in p.gestores_actuales.all %}
                                    <span style="display: inline-block; background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-size: 11px;">{{ ag.gestor.username }}</span>
                                {% endfor %}
                            {% else %}
                                <span style="color: #999; font-style: italic;">Sin asignar</span>
                            {% endif %}
                        </td>
                        <td style="padding: 10px; font-weight: bold; color: #28a745;">
                            S/ {{ p.imp_recup|default:"0.00" }}
                        </td>
                        <td style="padding: 10px; text-align: center;">
                            <a href="{% url 'historial_gestiones' deudor_id=p.id %}" target="_blank" style="background: #003366; color: white; padding: 4px 10px; text-decoration: none; border-radius: 4px; font-size: 12px;">Revisar</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}
"""
if "Pagos No Reflejados Proempresa" not in content:
    # Insert after huancayo table
    huancayo_table_end = """    {% endif %}
    
</div>"""
    content = content.replace(huancayo_table_end, "    {% endif %}\n" + proempresa_table + "\n</div>")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated dashboard.html")
