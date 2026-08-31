import os
import django
from datetime import date
import sys

# Setup Django environment
sys.path.append(r'c:\CRM PYP')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()

from cobranza.models import Deudor

deudores = Deudor.objects.all()
print(f"Calculando score para {deudores.count()} deudores...")

updated_count = 0
for d in deudores:
    puntaje = 10
    c_upper = str(d.condicion).upper()
    if 'CONVENIO' in c_upper or (d.negociacion and len(d.negociacion.strip()) > 3):
        puntaje += 40
    if d.ultimo_dia_pago:
        dias = (date.today() - d.ultimo_dia_pago).days
        if dias <= 30:
            puntaje += 40
        elif dias <= 60:
            puntaje += 20
    score = min(puntaje, 100)
    
    if d.score != score:
        d.score = score
        d.save(update_fields=['score'])
        updated_count += 1

print(f"Completado. Se actualizaron {updated_count} deudores.")
