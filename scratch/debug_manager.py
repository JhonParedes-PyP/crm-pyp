import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

script = """
import sys; sys.path.append('/root/crm_pyp'); import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings'); import django; django.setup();
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models import OuterRef, Subquery, Sum, Exists, Count, IntegerField, DecimalField
from django.db.models.functions import Coalesce
from cobranza.models import Gestion, Deudor, SeguimientoProgramado

hoy = timezone.now().date()
gestores_base = User.objects.exclude(groups__name='GERENTE').exclude(is_superuser=True)

monto_semana_subquery = Gestion.objects.filter(
    gestor=OuterRef('pk'),
    fecha__date__gte=hoy - timedelta(days=7)
).values('gestor').annotate(
    total=Sum('monto_pago')
).values('total')[:1]

promesas_vencidas_subq = Gestion.objects.filter(
    gestor=OuterRef('pk'),
    resultado__icontains='PROMESA',
    fecha_promesa__lt=hoy
).annotate(
    tiene_pago=Exists(
        Gestion.objects.filter(
            deudor=OuterRef('deudor'),
            fecha__gt=OuterRef('fecha'),
            monto_pago__gt=0
        )
    )
).filter(tiene_pago=False).values('gestor').annotate(
    cnt=Count('id')
).values('cnt')[:1]

gestores = gestores_base.annotate(
    monto_semana=Coalesce(Subquery(monto_semana_subquery, output_field=DecimalField()), 0.0),
    promesas_vencidas_cnt=Coalesce(Subquery(promesas_vencidas_subq, output_field=IntegerField()), 0)
)
print("Gestores count:", gestores.count())
print("First gestor:", gestores.first())
"""

stdin, stdout, stderr = ssh.exec_command(f'cd /root/crm_pyp && ./venv/bin/python -c "{script}"')
print(stdout.read().decode(errors='replace'))
print(stderr.read().decode(errors='replace'))
