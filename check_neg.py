import paramiko
import os

key_path = os.path.expanduser('~/.ssh/id_rsa')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('161.35.13.167', username='root', key_filename=key_path)

cmd = '''cd /root/crm_pyp && /root/crm_pyp/venv/bin/python manage.py shell -c "from cobranza.models import Deudor; print(list(Deudor.objects.values_list('negociacion', flat=True).distinct()[:10]))"'''
stdin, stdout, stderr = client.exec_command(cmd)
print("OUT:", stdout.read().decode())
print("ERR:", stderr.read().decode())
client.close()
