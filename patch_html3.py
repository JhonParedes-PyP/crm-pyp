import os
html_path = r"c:\CRM PYP\cobranza\templates\cobranza\dashboard.html"

with open(html_path, 'r', encoding='latin-1') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if "Recuperac" in line and "Metas por Cartera" in line and "<h3" in line:
        new_lines.append(f"""    <h3 style="color: #003366; margin-bottom: 15px; margin-top: 0; display: flex; align-items: center;">
        📊 Recuperación y Metas por Cartera (Mes Actual)
        {{% if es_gerente %}}
        <button onclick="abrirModalMetas()" style="margin-left: 10px; background: none; border: none; cursor: pointer; font-size: 18px;" title="Editar Metas">✏️</button>
        {{% endif %}}
    </h3>
""")
    else:
        new_lines.append(line)

with open(html_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Updated line!")
