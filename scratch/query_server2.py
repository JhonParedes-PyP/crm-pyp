import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

cmd = """
cd /root/crm_pyp
/root/crm_pyp/venv/bin/python manage.py shell -c "
from cobranza.models import Deudor
kim = Deudor.objects.filter(nombre_completo__icontains='KIM IMPORT')
for d in kim:
    print(d.id, repr(d.documento), d.activo, d.ultimo_dia_pago, repr(d.cartera))
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print("OUT:", stdout.read().decode())
print("ERR:", stderr.read().decode())
ssh.close()
