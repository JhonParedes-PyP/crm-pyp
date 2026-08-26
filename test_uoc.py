import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()
from cobranza.models import Deudor, Convenio
d = Deudor.objects.get(id=908)
try:
    c, created = Convenio.objects.update_or_create(deudor=d, defaults={'cuenta': d.cuenta})
    print(c)
except Exception as e:
    print(type(e), e)
