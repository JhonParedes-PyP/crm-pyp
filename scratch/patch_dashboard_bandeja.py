import os
import re

file_path = r"c:\CRM PYP\cobranza\templates\cobranza\dashboard.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix the scope of abrirModalMetas by moving it out or moving var metas out
# Right now, `var metas = ...` is inside `document.addEventListener("DOMContentLoaded", function() {`
# Let's declare `window.metas` inside DOMContentLoaded so it's globally available.
content = content.replace("var metas = JSON.parse", "window.metas = JSON.parse")
content = content.replace("metas['CAJA HUANCAYO']", "window.metas['CAJA HUANCAYO']")
content = content.replace("metas['PROEMPRESA']", "window.metas['PROEMPRESA']")
content = content.replace("metas[cartera]", "window.metas[cartera]")

# We also need to fix `var metas` in the iteration: `Object.keys(window.metas)` if it was used? No, the chart script used `metas[cartera]`.
content = content.replace("var meta = metas[cartera]", "var meta = window.metas[cartera]")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("dashboard.html JS scope patched")

file_path_bandeja = r"c:\CRM PYP\cobranza\templates\cobranza\bandeja.html"
with open(file_path_bandeja, "r", encoding="utf-8") as f:
    bandeja = f.read()

old_badge = """{% if d.negociacion %}
                            <span style="background: #e3f2fd; color: #0056b3; padding: 3px 6px; border-radius: 4px; font-weight: bold; font-size: 10px;">{{ d.negociacion }}</span>"""

new_badge = """{% if d.negociacion %}
                            {% if d.negociacion == 'CON NEGOCIACIÓN' or d.negociacion == 'CON NEGOCIACION' %}
                                {% if 'HUANCAYO' in d.cartera or 'huancayo' in d.cartera|lower %}
                                    <span style="background: #28a745; color: white; padding: 3px 6px; border-radius: 4px; font-weight: bold; font-size: 10px;">{{ d.negociacion }}</span>
                                {% else %}
                                    <span style="background: #e3f2fd; color: #0056b3; padding: 3px 6px; border-radius: 4px; font-weight: bold; font-size: 10px;">{{ d.negociacion }}</span>
                                {% endif %}
                            {% else %}
                                <span style="background: #e3f2fd; color: #0056b3; padding: 3px 6px; border-radius: 4px; font-weight: bold; font-size: 10px;">{{ d.negociacion }}</span>
                            {% endif %}"""

bandeja = bandeja.replace(old_badge, new_badge)

with open(file_path_bandeja, "w", encoding="utf-8") as f:
    f.write(bandeja)
print("bandeja.html patched")
