import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.209.76.91', username='root', password='Moises16Micaela12pyp')
python_code = """import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()
from django.test import Client
from django.contrib.auth.models import User
import json

c = Client(SERVER_NAME='134.209.76.91')
user = User.objects.get(username='JPAREDES')
c.force_login(user)
resp = c.post('/dashboard/guardar_metas/', 
              json.dumps({"PROEMPRESA": 100}), 
              content_type="application/json")
print("Status Code:", resp.status_code)
print("Content:", resp.content)
"""
sftp = ssh.open_sftp()
with open("test_req.py", "w") as f: f.write(python_code)
sftp.put("test_req.py", "/root/crm_pyp/test_req.py")
sftp.close()
stdin, stdout, stderr = ssh.exec_command("/root/crm_pyp/venv/bin/python /root/crm_pyp/test_req.py")
print(stdout.read().decode())
