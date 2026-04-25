import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

# Write a Python script to server and run it
check_script = '''
import sys, django, os
sys.path.insert(0, '/root/crm_pyp')
os.environ['DJANGO_SETTINGS_MODULE'] = 'crm_pyp_config.settings'
django.setup()
from cobranza.models import Deudor
from django.conf import settings

qs = Deudor.objects.exclude(foto_evidencia='')
print('Registros con foto no vacia:', qs.count())
for d in qs[:5]:
    nombre = d.foto_evidencia.name if d.foto_evidencia else ''
    url = settings.SITE_URL + d.foto_evidencia.url if d.foto_evidencia else ''
    print(f"ID:{d.id} | path:{repr(nombre)} | URL:{url}")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_fotos.py', 'w') as f:
    f.write(check_script)
sftp.close()

print("=== Fotos en BD ===")
stdin, stdout, stderr = ssh.exec_command('cd /root/crm_pyp && DJANGO_SETTINGS_MODULE=crm_pyp_config.settings venv/bin/python /tmp/check_fotos.py')
stdout.channel.recv_exit_status()
print(stdout.read().decode())
err = stderr.read().decode()
if err: print("ERR:", err)

ssh.close()
