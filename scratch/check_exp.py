import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)
    
    script = """
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()
from cobranza.models import ExpedienteJudicial
try:
    exp = ExpedienteJudicial.objects.get(numero_expediente='00622-2025-10-1866-JP-CI-02')
    print('NRO EXP:', exp.numero_expediente)
    print('NRO CAUTELAR:', exp.numero_cautelar)
    print('CODIGO CAU:', exp.codigo_cautelar)
    print('CONDICION:', exp.condicion_recuperabilidad)
    print('ESTADO CAUT:', exp.estado_cautelar)
except Exception as e:
    print('Error:', e)
"""
    sftp = ssh.open_sftp()
    with sftp.file('/root/crm_pyp/check_exp.py', 'w') as f:
        f.write(script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command('cd /root/crm_pyp && /root/crm_pyp/venv/bin/python check_exp.py')
    print("STDOUT:")
    print(stdout.read().decode())
    print("STDERR:")
    print(stderr.read().decode())
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
