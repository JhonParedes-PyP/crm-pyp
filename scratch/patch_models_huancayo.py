import os

file_path = r'c:\CRM PYP\cobranza\models.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    if "negociacion = models.TextField(null=True, blank=True)" in line:
        new_lines.append("    # CAMPOS CONVENIO CAJA HUANCAYO\n")
        new_lines.append("    cuota_pendiente = models.CharField(max_length=50, null=True, blank=True)\n")
        new_lines.append("    total_cuotas = models.CharField(max_length=50, null=True, blank=True)\n")
        new_lines.append("    fecha_pago_cuota_pendiente = models.DateField(null=True, blank=True)\n")
        new_lines.append("    monto_cuota_atrasada = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)\n")
        new_lines.append("    credito_al_dia = models.CharField(max_length=50, null=True, blank=True)\n")
        new_lines.append("    dias_atraso_cuota = models.IntegerField(null=True, blank=True)\n")

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("PATCH MODELS SUCCESS")
