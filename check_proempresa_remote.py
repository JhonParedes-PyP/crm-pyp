import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.209.76.91', username='root', password='Moises16Micaela12pyp')

python_code = """import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()
from cobranza.models import Deudor
from django.db.models import Sum
total = Deudor.objects.filter(cartera__icontains='PROEMPRESA', imp_recup__gt=0).aggregate(Sum('imp_recup'))
count = Deudor.objects.filter(cartera__icontains='PROEMPRESA', imp_recup__gt=0).count()
print(f"Total Proempresa imp_recup: {total}, Count: {count}")
"""

sftp = ssh.open_sftp()
with open("chk.py", "w") as f: f.write(python_code)
sftp.put("chk.py", "/root/crm_pyp/chk.py")
sftp.close()

stdin, stdout, stderr = ssh.exec_command("/root/crm_pyp/venv/bin/python /root/crm_pyp/chk.py")
print(stdout.read().decode())
