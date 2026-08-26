import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.209.76.91', username='root', password='Moises16Micaela12pyp')
python_code = """import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()
from django.contrib.auth.models import User
for u in User.objects.all(): print(f"'{u.username}'")
"""
sftp = ssh.open_sftp()
with open("test_usr.py", "w") as f: f.write(python_code)
sftp.put("test_usr.py", "/root/crm_pyp/test_usr.py")
sftp.close()
stdin, stdout, stderr = ssh.exec_command("/root/crm_pyp/venv/bin/python /root/crm_pyp/test_usr.py")
print(stdout.read().decode())
