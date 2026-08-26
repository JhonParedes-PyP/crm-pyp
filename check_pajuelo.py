import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

python_code = """import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()

from cobranza.models import Deudor, Convenio

deudores = Deudor.objects.filter(nombre_completo__icontains='PAJUELO SOTO')
print(f"Encontrados {deudores.count()} deudores con PAJUELO SOTO")
for d in deudores:
    print(f" - ID: {d.id} | Nombre: {d.nombre_completo} | Cuenta: {d.cuenta} | Neg: {d.negociacion}")
    convenios = Convenio.objects.filter(deudor=d)
    print(f"   Convenios: {convenios.count()}")
    for c in convenios:
        print(f"     -> Fecha Pago: {c.fecha_pago} | Cuota Pend: {c.cuota_pendiente} | Monto: {c.monto_cuota}")
"""

with open("test_pajuelo.py", "w", encoding="utf-8") as f:
    f.write(python_code)

sftp = ssh.open_sftp()
sftp.put("test_pajuelo.py", "/root/crm_pyp/test_pajuelo.py")
sftp.close()

cmd = "/root/crm_pyp/venv/bin/python /root/crm_pyp/test_pajuelo.py"
stdin, stdout, stderr = ssh.exec_command(cmd)

print("OUT:\n", stdout.read().decode())
err = stderr.read().decode()
if err: print("ERR:\n", err)

ssh.close()
