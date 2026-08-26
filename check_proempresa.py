import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()

from cobranza.models import Deudor
from django.db.models import Sum

total = Deudor.objects.filter(cartera__icontains='PROEMPRESA', imp_recup__gt=0).aggregate(Sum('imp_recup'))
count = Deudor.objects.filter(cartera__icontains='PROEMPRESA', imp_recup__gt=0).count()
print(f"Total Proempresa imp_recup: {total}, Count: {count}")
