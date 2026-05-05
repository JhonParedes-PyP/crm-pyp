import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

cmd = "/root/crm_pyp/venv/bin/python /root/crm_pyp/manage.py shell -c \"from django.contrib.auth.models import User; from cobranza.models import AgenteSIP; u=User.objects.filter(username='EPACHAS').first(); p=AgenteSIP.objects.filter(user=u).first(); print('ANEXO:', p.anexo if p else 'NONE'); print('CLAVE:', bool(p.clave) if p else 'NONE')\""

stdin, stdout, stderr = ssh.exec_command(cmd)
print("OUT:", stdout.read().decode())
print("ERR:", stderr.read().decode())
ssh.close()
