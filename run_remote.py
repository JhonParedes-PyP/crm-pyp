import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

py_script = """from cobranza.models import Deudor
qs = Deudor.objects.filter(nombre_completo__icontains='MONTAÑEZ ACUÑA')
for c in qs:
    print('ID:', c.id)
    print('Nombre:', c.nombre_completo)
    print('Cartera:', c.cartera)
    print('Negociacion:', repr(c.negociacion))
    print('---')
"""

sftp = ssh.open_sftp()
with sftp.open('/root/crm_pyp/check_db.py', 'w') as f:
    f.write(py_script)
sftp.close()

cmd = 'cd /root/crm_pyp && /root/crm_pyp/venv/bin/python manage.py shell < /root/crm_pyp/check_db.py'
stdin, stdout, stderr = ssh.exec_command(cmd)
print("OUT:\n", stdout.read().decode())
print("ERR:\n", stderr.read().decode())

ssh.close()
