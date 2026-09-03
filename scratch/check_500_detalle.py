import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)
    
    script = """
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()

from django.test.client import Client
from django.contrib.auth.models import User
from cobranza.models import ExpedienteJudicial

c = Client(SERVER_NAME='crm.pypsolucionesjuridicas.com')
user = User.objects.get(username='JPAREDES')
c.force_login(user)

try:
    exp = ExpedienteJudicial.objects.first()
    if not exp:
        print("No expedientes found.")
    else:
        url = f'/judicial/expediente/{exp.id}/'
        response = c.get(url)
        print('Status Code:', response.status_code)
        if response.status_code == 500:
            print(response.content.decode('utf-8', errors='ignore'))
except Exception as e:
    import traceback
    traceback.print_exc()
"""
    sftp = ssh.open_sftp()
    with sftp.file('/root/crm_pyp/get_500_detalle.py', 'w') as f:
        f.write(script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command('cd /root/crm_pyp && /root/crm_pyp/venv/bin/python get_500_detalle.py')
    print("STDOUT:")
    print(stdout.read().decode())
    print("STDERR:")
    print(stderr.read().decode())
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
