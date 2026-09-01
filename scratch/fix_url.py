import os

file_path = r"c:\CRM PYP\cobranza\templates\cobranza\dashboard.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("fetch('/cobranza/dashboard/guardar_metas/', {", "fetch(\"{% url 'guardar_metas' %}\", {")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("URL in fetch fixed")
