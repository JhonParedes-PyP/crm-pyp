import os
import sys
import django

# Add project directory to python path
sys.path.append(r'c:\CRM PYP')

# Set django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp.settings')
try:
    django.setup()
except Exception:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
    django.setup()

from django.contrib.auth.models import User
from cobranza.models import AlertaJudicial, ExpedienteJudicial
from cobranza.asignaciones import aplicar_visibilidad_por_asignaciones
import traceback

print("Testing with JPAREDES:")
try:
    user = User.objects.filter(username='JPAREDES').first()
    qs_alertas = aplicar_visibilidad_por_asignaciones(AlertaJudicial.objects.all(), user, related_prefix='expediente__deudor__')
    print("Alertas:", qs_alertas.count())
    qs_exp = aplicar_visibilidad_por_asignaciones(ExpedienteJudicial.objects.all(), user, related_prefix='deudor__')
    print("Expedientes:", qs_exp.count())
except Exception as e:
    traceback.print_exc()

print("\nTesting with EPACHAS:")
try:
    user = User.objects.filter(username='EPACHAS').first()
    if user:
        qs_alertas = aplicar_visibilidad_por_asignaciones(AlertaJudicial.objects.all(), user, related_prefix='expediente__deudor__')
        print("Alertas:", qs_alertas.count())
        qs_exp = aplicar_visibilidad_por_asignaciones(ExpedienteJudicial.objects.all(), user, related_prefix='deudor__')
        print("Expedientes:", qs_exp.count())
    else:
        print("EPACHAS no existe localmente")
except Exception as e:
    traceback.print_exc()
