import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

script = """
import sys; sys.path.append('/root/crm_pyp'); import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings'); import django; django.setup();
from cobranza.models import Deudor
print(list(Deudor.objects.values_list('score', flat=True)[:50]))
"""

stdin, stdout, stderr = ssh.exec_command(f'cd /root/crm_pyp && ./venv/bin/python -c "{script}"')
print(stdout.read().decode(errors='replace'))
print(stderr.read().decode(errors='replace'))
