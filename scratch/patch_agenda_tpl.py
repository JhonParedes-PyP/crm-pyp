import os

file_path = r"c:\CRM PYP\cobranza\templates\cobranza\agenda.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# I want to inject the score badge right below the name in the "Clientes asignados HOY" block.
# Finding:
# <div class="ci-nom">{{ item.deudor.nombre_completo }}</div>

old_html = '<div class="ci-nom">{{ item.deudor.nombre_completo }}</div>'
new_html = """<div class="ci-nom" style="display: flex; align-items: center; gap: 8px;">
                    {{ item.deudor.nombre_completo }}
                    {% if item.deudor.score >= 70 %}
                        <span style="background: #28a745; color: white; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: bold;">🟩 ALTO ({{ item.deudor.score }})</span>
                    {% elif item.deudor.score >= 40 %}
                        <span style="background: #ffc107; color: black; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: bold;">🟨 MEDIO ({{ item.deudor.score }})</span>
                    {% else %}
                        <span style="background: #dc3545; color: white; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: bold;">🟥 BAJO ({{ item.deudor.score }})</span>
                    {% endif %}
                </div>"""

if old_html in content:
    content = content.replace(old_html, new_html)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("agenda.html patched!")
else:
    print("HTML not found!")
