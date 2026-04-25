"""Diagnostic script - runs on production server via deploy helper"""
import paramiko, os

diag_code = r"""
import traceback, sys, os
os.chdir('/root/crm_pyp')
sys.path.insert(0, '/root/crm_pyp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')

import django
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User, Group
from cobranza.dashboard_views import agenda_diaria

print("Grupos existentes:", list(Group.objects.values_list('name', flat=True)))
print("Superusuarios:", list(User.objects.filter(is_superuser=True).values_list('username', flat=True)))
print("Todos los usuarios:", list(User.objects.values_list('username', 'is_superuser')))

# Buscar gerente: superuser o grupo GERENTE
u = User.objects.filter(is_superuser=True).first()
if not u:
    g_qs = Group.objects.filter(name__icontains='GERENTE')
    if g_qs.exists():
        u = User.objects.filter(groups=g_qs.first()).first()

print("Usuario gerente seleccionado:", repr(u))
if not u:
    print("ERROR: No se encontro ningun gerente")
    sys.exit(1)

from cobranza.views import es_gerente as eg
print("es_gerente():", eg(u))

try:
    f = RequestFactory()
    r = f.get('/agenda/')
    r.user = u
    resp = agenda_diaria(r)
    print("Status:", resp.status_code)
    print("OK - sin error")
except Exception as e:
    traceback.print_exc()
"""

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=10)

sftp = client.open_sftp()
with sftp.open('/tmp/diag_agenda.py', 'w') as f:
    f.write(diag_code)
sftp.close()

stdin, stdout, stderr = client.exec_command(
    'cd /root/crm_pyp && /root/crm_pyp/venv/bin/python /tmp/diag_agenda.py 2>&1'
)
output = stdout.read().decode()
print(output)
client.close()
