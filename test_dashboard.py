import paramiko
ssh=paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.209.76.91', username='root', password='Moises16Micaela12pyp')
script = """
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()
from django.test import Client
from django.contrib.auth.models import User
c = Client(HTTP_HOST='134.209.76.91')
user = User.objects.get(username='JPAREDES')
c.force_login(user)
try:
    response = c.get('/')
    if response.status_code == 500:
        print("DASHBOARD RETURNED 500!")
    else:
        print(f"DASHBOARD RETURNED {response.status_code}")
except Exception as e:
    import traceback
    traceback.print_exc()
"""
with open('test_local.py', 'w') as f:
    f.write(script)

sftp = ssh.open_sftp()
sftp.put('test_local.py', '/root/crm_pyp/test_local.py')

stdin, stdout, stderr = ssh.exec_command('cd /root/crm_pyp && /root/crm_pyp/venv/bin/python test_local.py')
print("STDOUT:", stdout.read().decode())
print("STDERR:", stderr.read().decode())
