import os

file_path = r"c:\CRM PYP\cobranza\models.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# I will find all occurrences of the score field that are right before class Meta:
bad_field = """    # CAMPO DE IA SCORING
    score = models.IntegerField(default=10, help_text="Puntaje AI de Probabilidad de Pago")

    class Meta:"""

# Split by the bad field
parts = content.split(bad_field)

# Only keep it for the first one which is Deudor
new_content = parts[0] + bad_field + "    class Meta:".join(parts[1:])

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
    
print("models.py cleaned up!")
