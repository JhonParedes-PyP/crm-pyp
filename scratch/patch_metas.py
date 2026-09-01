import os

file_path = r"c:\CRM PYP\cobranza\templates\cobranza\dashboard.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add Edit button
old_title = '<h3 style="color: #003366; margin-bottom: 15px; margin-top: 0; display: flex; align-items: center;">\n        🎯 Recuperación y Metas por Cartera (Mes Actual)\n\n    </h3>'
if '🎯 Recuperación y Metas' in content and 'button onclick="abrirModalMetas()"' not in content:
    # Let's just find the h3
    import re
    h3_pattern = re.compile(r'(<h3 style="color: #003366; margin-bottom: 15px; margin-top: 0; display: flex; align-items: center;">\s*🎯 Recuperación y Metas por Cartera \(Mes Actual\)\s*</h3>)')
    
    new_h3 = """<h3 style="color: #003366; margin-bottom: 15px; margin-top: 0; display: flex; align-items: center; justify-content: space-between;">
        <span>🎯 Recuperación y Metas por Cartera (Mes Actual)</span>
        {% if request.user.username == 'JPAREDES' or request.user.is_superuser %}
        <button onclick="abrirModalMetas()" style="background: #0056b3; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold;">✏️ Editar Metas</button>
        {% endif %}
    </h3>"""
    
    content = h3_pattern.sub(new_h3, content)

# 2. Add Modal HTML at the end of the file before </div> or <script>
modal_html = """
<!-- Modal Metas -->
<div id="modalMetas" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center;">
    <div style="background: white; padding: 25px; border-radius: 8px; width: 400px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
        <h3 style="margin-top: 0; color: #003366;">✏️ Editar Metas</h3>
        <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Meta CAJA HUANCAYO (S/)</label>
            <input type="number" id="metaCajaHuancayo" step="0.01" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
        </div>
        <div style="margin-bottom: 20px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Meta PROEMPRESA (S/)</label>
            <input type="number" id="metaProempresa" step="0.01" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 10px;">
            <button onclick="cerrarModalMetas()" style="padding: 8px 15px; border: 1px solid #ccc; background: white; border-radius: 4px; cursor: pointer;">Cancelar</button>
            <button onclick="guardarMetas()" style="padding: 8px 15px; border: none; background: #28a745; color: white; border-radius: 4px; cursor: pointer; font-weight: bold;">Guardar</button>
        </div>
    </div>
</div>
"""
if 'id="modalMetas"' not in content:
    content = content.replace('<script>', modal_html + '\n<script>')

# 3. Replace hardcoded metas with variable and add functions
script_pattern = re.compile(r"var metas = \{\s*'PROEMPRESA': 213674\.00,\s*'CAJA HUANCAYO': 457116\.49,\s*'FOCMAC': null // Libre\s*\};", re.MULTILINE)
if script_pattern.search(content):
    content = script_pattern.sub('var metas = JSON.parse(\'{{ metas_json|escapejs }}\' || "{}");', content)
elif "var metas = {" in content: # fallback
    # find where var metas is defined
    start = content.find("var metas = {")
    end = content.find("};", start) + 2
    if start != -1 and end != -1:
        content = content[:start] + 'var metas = JSON.parse(\'{{ metas_json|escapejs }}\' || "{}");' + content[end:]

# Add JS functions for modal
js_funcs = """
function abrirModalMetas() {
    document.getElementById('metaCajaHuancayo').value = metas['CAJA HUANCAYO'] || '';
    document.getElementById('metaProempresa').value = metas['PROEMPRESA'] || '';
    document.getElementById('modalMetas').style.display = 'flex';
}
function cerrarModalMetas() {
    document.getElementById('modalMetas').style.display = 'none';
}
function guardarMetas() {
    var data = {
        'CAJA HUANCAYO': parseFloat(document.getElementById('metaCajaHuancayo').value) || null,
        'PROEMPRESA': parseFloat(document.getElementById('metaProempresa').value) || null,
        'FOCMAC': null
    };
    fetch('/cobranza/dashboard/guardar_metas/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: JSON.stringify(data)
    }).then(res => res.json()).then(res => {
        if(res.status === 'ok') {
            window.location.reload();
        } else {
            alert('Error al guardar: ' + (res.error || 'Desconocido'));
        }
    }).catch(err => {
        alert('Error de conexión');
    });
}
"""
if 'function abrirModalMetas()' not in content:
    content = content.replace('document.addEventListener("DOMContentLoaded", function() {', js_funcs + '\ndocument.addEventListener("DOMContentLoaded", function() {')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("dashboard.html patched for metas!")
