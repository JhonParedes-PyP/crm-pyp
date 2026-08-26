import os

html_path = r"c:\CRM PYP\cobranza\templates\cobranza\dashboard.html"
with open(html_path, 'r', encoding='latin-1') as f:
    lines = f.readlines()

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
            'Content-Type': 'application/json'
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

# Append just before {% endblock %} if it exists
inserted = False
for i, line in enumerate(lines):
    if "{% endblock %}" in line:
        lines.insert(i, modal_code + "\n")
        inserted = True
        break

if not inserted:
    lines.append(modal_code + "\n")

with open(html_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Injected modal!")
