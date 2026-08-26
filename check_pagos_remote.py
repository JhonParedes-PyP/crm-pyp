import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.209.76.91', username='root', password='Moises16Micaela12pyp')

python_code = """import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()
from cobranza.models import Deudor, Gestion
from django.db.models import Exists, OuterRef
from django.utils.timezone import now

hoy = now()
gestiones_pago_mes = Gestion.objects.filter(
    deudor=OuterRef('pk'),
    resultado__icontains='PAG',
    fecha__year=hoy.year,
    fecha__month=hoy.month
)

pagos_no_reflejados = Deudor.objects.filter(
    cartera__icontains='PROEMPRESA',
    imp_recup__gt=0
).annotate(
    tiene_gestion_pago=Exists(gestiones_pago_mes)
).filter(
    tiene_gestion_pago=False
).count()

print(f"Pagos no reflejados Proempresa count: {pagos_no_reflejados}")
"""
sftp = ssh.open_sftp()
with open("chk.py", "w") as f: f.write(python_code)
sftp.put("chk.py", "/root/crm_pyp/chk.py")
sftp.close()

stdin, stdout, stderr = ssh.exec_command("/root/crm_pyp/venv/bin/python /root/crm_pyp/chk.py")
print(stdout.read().decode())
