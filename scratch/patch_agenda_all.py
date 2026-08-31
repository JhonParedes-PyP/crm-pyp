import re

file_path = r"c:\CRM PYP\cobranza\templates\cobranza\agenda.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

badge_html = """<div class="ci-nom" style="display: flex; align-items: center; gap: 8px;">
                    {0}
                    {{% if {1}.score >= 70 %}}
                        <span style="background: #28a745; color: white; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: bold;">🟩 ALTO ({{{{ {1}.score }}}})</span>
                    {{% elif {1}.score >= 40 %}}
                        <span style="background: #ffc107; color: black; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: bold;">🟨 MEDIO ({{{{ {1}.score }}}})</span>
                    {{% else %}}
                        <span style="background: #dc3545; color: white; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: bold;">🟥 BAJO ({{{{ {1}.score }}}})</span>
                    {{% endif %}}
                </div>"""

# Replacements
content = content.replace('<div class="ci-nom">{{ g.deudor.nombre_completo }}</div>', badge_html.format("{{ g.deudor.nombre_completo }}", "g.deudor"))
content = content.replace('<div class="ci-nom">{{ seg.deudor.nombre_completo }}</div>', badge_html.format("{{ seg.deudor.nombre_completo }}", "seg.deudor"))
content = content.replace('<div class="ci-nom">{{ d.nombre_completo }}</div>', badge_html.format("{{ d.nombre_completo }}", "d"))

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("agenda.html fully patched!")
