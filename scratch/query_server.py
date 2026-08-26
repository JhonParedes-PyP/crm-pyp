import paramiko
import os
from dotenv import load_dotenv

load_dotenv()
host = os.environ.get('VPS_HOST')
user = os.environ.get('VPS_USER')
password = os.environ.get('VPS_PASSWORD')
port = int(os.environ.get('VPS_PORT', 22))

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, port, user, password)

cmd = """
cd /root/crm_pyp
/root/crm_pyp/venv/bin/python manage.py shell -c "from cobranza.models import Deudor; print([(d.id, repr(d.documento), repr(d.cartera), d.activo, d.ultimo_dia_pago) for d in Deudor.objects.filter(nombre_completo__icontains='KIM IMPORT')])"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print("OUT:", stdout.read().decode())
print("ERR:", stderr.read().decode())
ssh.close()
