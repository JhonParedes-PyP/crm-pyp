import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

script = """
import sys; sys.path.append('/root/crm_pyp'); import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings'); import django; django.setup();
from django.contrib.auth.models import User
print("Superusers:", list(User.objects.filter(is_superuser=True).values_list('username', flat=True)))
print("Users in GERENTE group:", list(User.objects.filter(groups__name='GERENTE').values_list('username', flat=True)))
print("All groups:", list(User.objects.values_list('groups__name', flat=True).distinct()))
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_users.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('cd /root/crm_pyp && ./venv/bin/python /tmp/check_users.py')
print(stdout.read().decode())
print(stderr.read().decode())
