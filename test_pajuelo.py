import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()

from cobranza.models import Deudor, Convenio

deudores = Deudor.objects.filter(nombre_completo__icontains='PAJUELO SOTO')
print(f"Encontrados {deudores.count()} deudores con PAJUELO SOTO")
for d in deudores:
    print(f" - ID: {d.id} | Nombre: {d.nombre_completo} | Cuenta: {d.cuenta} | Neg: {d.negociacion}")
    convenios = Convenio.objects.filter(deudor=d)
    print(f"   Convenios: {convenios.count()}")
    for c in convenios:
        print(f"     -> Fecha Pago: {c.fecha_pago} | Cuota Pend: {c.cuota_pendiente} | Monto: {c.monto_cuota}")
