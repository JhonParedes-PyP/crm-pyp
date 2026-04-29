import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password)

cmd = """echo "from django.contrib.auth.models import User
from cobranza.models import AgenteSIP
u = User.objects.filter(username__iexact='JPAREDES').first()
if u:
    sip = AgenteSIP.objects.filter(user=u).first()
    if sip:
        sip.clave = '7VcD9fP'
        sip.save()
        print('Password updated to 7VcD9fP')
" | /root/crm_pyp/venv/bin/python /root/crm_pyp/manage.py shell"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print("OUT:", stdout.read().decode())
print("ERR:", stderr.read().decode())
ssh.close()
