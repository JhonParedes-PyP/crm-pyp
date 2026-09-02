import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()

from cobranza.models import Deudor, ExpedienteJudicial

print("Iniciando migración de expedientes judiciales...")
deudores_con_expediente = Deudor.objects.exclude(expediente='').exclude(expediente__isnull=True)
count = 0
for d in deudores_con_expediente:
    if d.expediente.strip():
        # Clean up process/materia
        materia_val = d.proceso.strip() if d.proceso else 'NO ESPECIFICADO'
        juzgado_val = d.juzgado.strip() if d.juzgado else 'NO ESPECIFICADO'
        
        obj, created = ExpedienteJudicial.objects.get_or_create(
            deudor=d,
            numero_expediente=d.expediente.strip(),
            defaults={
                'juzgado': juzgado_val,
                'materia': materia_val,
                'fecha_inicio': d.fec_demanda
            }
        )
        if created:
            count += 1

print(f"Migración completada. Se crearon {count} Expedientes Judiciales.")
