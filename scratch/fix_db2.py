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
malos = Deudor.objects.filter(cartera='CAJA HUANCAYO', documento__in=['-', '--'])
c = malos.count()
print(f'Borrando {c} clientes malos con guiones...')
malos.delete()

buenos = Deudor.objects.filter(cartera='CAJA HUANCAYO')
b = buenos.update(activo=True)
print(f'Reactivando {b} clientes por si acaso...')
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print("OUT:", stdout.read().decode())
print("ERR:", stderr.read().decode())
ssh.close()
