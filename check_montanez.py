import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

py_script = """
from cobranza.models import Deudor
qs = Deudor.objects.filter(nombre_completo__icontains='MONTAÑEZ ACUÑA')
for c in qs:
    print(f"ID: {c.id}")
    print(f"Nombre: {c.nombre_completo}")
    print(f"Cartera: {c.cartera}")
    print(f"Negociacion: {repr(c.negociacion)}")
    print("---")
"""
cmd = f'cd /root/crm_pyp && /root/crm_pyp/venv/bin/python manage.py shell -c "{py_script}"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print("OUT:\n", stdout.read().decode())
print("ERR:\n", stderr.read().decode())
ssh.close()
