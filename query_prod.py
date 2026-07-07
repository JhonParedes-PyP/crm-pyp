import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

cmd = """cd /root/crm_pyp && /root/crm_pyp/venv/bin/python -c "import django, os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings'); django.setup(); from cobranza.models import Deudor; print(list(Deudor.objects.filter(nombre_completo__icontains='ARZAPALO PAREDES').values('id', 'cuenta', 'documento', 'nombre_completo')))" """

stdin, stdout, stderr = ssh.exec_command(cmd)
print("OUT:", stdout.read().decode())
print("ERR:", stderr.read().decode())
ssh.close()
