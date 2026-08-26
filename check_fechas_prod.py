import paramiko
import os

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

py_script = """
from cobranza.models import Deudor
qs = Deudor.objects.filter(cartera='CAJA HUANCAYO', activo=True)
qs_convenio = qs.exclude(negociacion__isnull=True).exclude(negociacion__exact='').exclude(negociacion__iexact='nan').exclude(negociacion__iexact='none').exclude(negociacion__iexact='null')

total = qs.count()
c_total = qs_convenio.count()
c_with = qs_convenio.exclude(ultimo_dia_pago__isnull=True).count()
c_without = qs_convenio.filter(ultimo_dia_pago__isnull=True).count()

print(f"Total Caja Huancayo: {total}")
print(f"Con Convenio: {c_total}")
print(f"Convenio CON Fecha Pago: {c_with}")
print(f"Convenio SIN Fecha Pago: {c_without}")
"""

# Escapar comillas dobles
py_script = py_script.replace('"', '\\"')

cmd = f'cd /root/crm_pyp && /root/crm_pyp/venv/bin/python manage.py shell -c "{py_script}"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print("OUT:\n", stdout.read().decode())
print("ERR:\n", stderr.read().decode())
ssh.close()
