import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

script = """
import sys; sys.path.append('/root/crm_pyp'); import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings'); import django; django.setup();
from cobranza.models import Deudor
from django.db.models import Sum

count = Deudor.objects.filter(cartera__icontains='PROEMPRESA', activo=True, imp_recup__gt=0).count()
total = Deudor.objects.filter(cartera__icontains='PROEMPRESA', activo=True, imp_recup__gt=0).aggregate(total=Sum('imp_recup'))['total']
print(f"Hay {count} deudores activos de PROEMPRESA con imp_recup > 0. Total: {total}")

# Si el usuario quiere que esté en cero por el inicio de mes, los reseteamos.
updated = Deudor.objects.filter(cartera__icontains='PROEMPRESA').update(imp_recup=0.0)
print(f"Se resetearon a 0 los imp_recup de {updated} deudores de PROEMPRESA.")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/reset_proempresa.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('cd /root/crm_pyp && ./venv/bin/python /tmp/reset_proempresa.py')
print(stdout.read().decode())
print(stderr.read().decode())
