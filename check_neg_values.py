import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

py_script = """
from cobranza.models import Deudor
qs = Deudor.objects.filter(cartera='CAJA HUANCAYO', activo=True)
valores = qs.values_list('negociacion', flat=True).distinct()
for v in valores:
    print(repr(v))
"""
cmd = f'cd /root/crm_pyp && /root/crm_pyp/venv/bin/python manage.py shell -c "{py_script}"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print("OUT:\n", stdout.read().decode())
ssh.close()
