import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

script_content = """
import sys
import django
import traceback
from django.test import Client
from django.contrib.auth.models import User

try:
    c = Client()
    user = User.objects.get(username='EPACHAS')
    c.force_login(user)
    print("Testing /judicial/dashboard/ as EPACHAS")
    resp = c.get('/judicial/dashboard/')
    print("Status:", resp.status_code)
    if resp.status_code == 500:
        print("CONTENT:")
        print(resp.content.decode())
    
    print("Testing /judicial/buscar/ as EPACHAS")
    resp = c.get('/judicial/buscar/?q=test')
    print("Status:", resp.status_code)
    if resp.status_code == 500:
        print(resp.content.decode())
        
except Exception as e:
    traceback.print_exc()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password)

sftp = ssh.open_sftp()
with sftp.file('/root/crm_pyp/test_views.py', 'w') as f:
    f.write(script_content)
sftp.close()

cmd = 'cd /root/crm_pyp && /root/crm_pyp/venv/bin/python manage.py shell < /root/crm_pyp/test_views.py'
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
