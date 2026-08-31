import os

file_path = r"c:\CRM PYP\cobranza\models.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("convenio_set", "convenios")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("models.py fixed related_name!")
