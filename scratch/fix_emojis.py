import os

file_path = r"c:\CRM PYP\cobranza\templates\cobranza\dashboard.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace any occurrence of the mojibake with the magnifying glass
content = content.replace("Y\"?", "🔍")
content = content.replace("s?", "⚠️")

# Fix missing utf-8 chars
content = content.replace("aǧn", "aún")
content = content.replace("gestin", "gestión")
content = content.replace("sltima", "Última")
content = content.replace("Accin", "Acción")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed emojis!")
