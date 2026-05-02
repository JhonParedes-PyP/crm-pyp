import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()

from django.db.models import Count, OuterRef, Exists, Func, Subquery
from django.utils import timezone
from cobranza.models import Deudor, Gestion
from django.contrib.auth.models import User

hoy = timezone.now().date()

promesas_vencidas_subq = Gestion.objects.filter(
    gestor=OuterRef('pk'),
    resultado__icontains='PROMESA',
    fecha_promesa__lt=hoy
).annotate(
    tiene_pago=Exists(
        Gestion.objects.filter(
            deudor=OuterRef('deudor'),
            resultado__icontains='PAGÓ',
            fecha__gt=OuterRef('fecha')
        )
    )
).filter(tiene_pago=False).values('gestor').annotate(total=Count('id')).values('total')

agentes = User.objects.all().annotate(
    prom_vencidas=Subquery(promesas_vencidas_subq)
)
for a in agentes:
    print(a.username, a.prom_vencidas)
