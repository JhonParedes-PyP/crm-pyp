import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

script = """
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()

from django.contrib.auth.models import User
try:
    u = User.objects.get(username='jparedes')
    print('Superuser:', u.is_superuser)
    print('Groups:', [g.name for g in u.groups.all()])
except Exception as e:
    print(e)
"""

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)

    sftp = ssh.open_sftp()
    with sftp.file('/root/crm_pyp/check_user.py', 'w') as f:
        f.write(script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command('cd /root/crm_pyp && /root/crm_pyp/venv/bin/python check_user.py')
    print("STDOUT:", stdout.read().decode())
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
