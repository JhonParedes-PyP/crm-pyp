import os

file_path = r"c:\CRM PYP\cobranza\templates\cobranza\dashboard.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Remove the modal JS block
target_js = """<!-- Modal para Editar Metas -->
<div id="modalMetas" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; align-items: center; justify-content: center;">
    <div style="background: white; padding: 25px; border-radius: 12px; width: 400px; max-width: 90%;">
        <h3 style="margin-top: 0; color: #003366;">Actualizar Metas (Mes Actual)</h3>
        <form id="formMetas" onsubmit="event.preventDefault(); guardarMetas();">
            <div id="metasInputs" style="max-height: 300px; overflow-y: auto; margin-bottom: 15px;">
                <!-- Se llenará vía JS -->
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 10px;">
                <button type="button" onclick="cerrarModalMetas()" style="padding: 8px 15px; border: 1px solid #ccc; border-radius: 6px; cursor: pointer;">Cancelar</button>
                <button type="submit" style="padding: 8px 15px; background: #28a745; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">Guardar</button>
            </div>
        </form>
    </div>
</div>

<script>
function abrirModalMetas() {
    // Cargar metas actuales
    fetch("{% url 'api_metas_cartera' %}")
        .then(r => r.json())
        .then(data => {
            const div = document.getElementById('metasInputs');
            div.innerHTML = '';
            data.forEach(m => {
                div.innerHTML += `
                    <div style="margin-bottom: 10px;">
                        <label style="display: block; font-size: 12px; font-weight: bold; color: #555;">${m.cartera}</label>
                        <input type="number" id="meta_${m.cartera}" value="${m.meta_soles}" step="0.01" style="width: 100%; padding: 6px; border: 1px solid #ccc; border-radius: 4px;">
                    </div>
                `;
            });
            document.getElementById('modalMetas').style.display = 'flex';
        });
}

function cerrarModalMetas() {
    document.getElementById('modalMetas').style.display = 'none';
}

function guardarMetas() {
    alert("Función en desarrollo. Las metas se actualizarán pronto.");
    cerrarModalMetas();
}
</script>"""

if target_js in content:
    content = content.replace(target_js, "")

# 2. Remove the edit button
target_button = """        {% if es_gerente %}
        <button onclick="abrirModalMetas()" style="margin-left: 10px; background: none; border: none; cursor: pointer; font-size: 18px;" title="Editar Metas">✏️</button>
        {% endif %}"""

if target_button in content:
    content = content.replace(target_button, "")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Modal removed.")
