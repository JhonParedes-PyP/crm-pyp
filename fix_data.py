import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

py_script = """
from cobranza.models import Deudor

# Find all records where correlativo is empty but expediente has data
qs = Deudor.objects.filter(cartera='CAJA HUANCAYO').exclude(expediente__isnull=True).exclude(expediente__exact='')

count = 0
for d in qs:
    if not d.correlativo:  # If correlativo is empty
        d.correlativo = d.expediente
        d.expediente = ''
        d.save()
        count += 1

print(f"Fixed {count} records in the database.")
"""
cmd = f'cd /root/crm_pyp && /root/crm_pyp/venv/bin/python manage.py shell -c "{py_script}"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print("OUT:\n", stdout.read().decode())
print("ERR:\n", stderr.read().decode())
ssh.close()
