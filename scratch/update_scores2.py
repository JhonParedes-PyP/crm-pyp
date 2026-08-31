import os
import django
from datetime import date
import sys

# Setup Django environment
if os.name == 'nt': # Windows local
    sys.path.append(r'c:\CRM PYP')
else:
    sys.path.append('/root/crm_pyp')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()

from cobranza.models import Deudor

deudores = Deudor.objects.prefetch_related('convenios').all()
print(f"Calculando score para {deudores.count()} deudores...")

updated_count = 0
for d in deudores:
    puntaje = 10
    
    c_upper = str(d.condicion).upper()
    tiene_convenio = d.convenios.exists()
    
    if tiene_convenio or 'CONVENIO' in c_upper or (d.negociacion and len(d.negociacion.strip()) > 3):
        puntaje += 40
        
    if d.ultimo_dia_pago:
        dias_desde_pago = (date.today() - d.ultimo_dia_pago).days
        if dias_desde_pago <= 60:
            puntaje += 40
        elif dias_desde_pago <= 180:
            puntaje += 20
        else:
            puntaje += 10
            
    score = min(puntaje, 100)
    
    if d.score != score:
        d.score = score
        d.save(update_fields=['score'])
        updated_count += 1

print(f"Completado. Se actualizaron {updated_count} deudores.")
