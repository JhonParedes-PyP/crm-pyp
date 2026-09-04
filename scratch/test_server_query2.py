import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

script_content = """
import sys
import django
import traceback

try:
    from django.contrib.auth.models import User
    from cobranza.models import AlertaJudicial, ExpedienteJudicial
    from cobranza.asignaciones import aplicar_visibilidad_por_asignaciones

    print("TESTING EPACHAS")
    user = User.objects.get(username='EPACHAS')
    qs_alertas = aplicar_visibilidad_por_asignaciones(AlertaJudicial.objects.all(), user, related_prefix='expediente__deudor__')
    print("Alertas:", qs_alertas.count())
    qs_exp = aplicar_visibilidad_por_asignaciones(ExpedienteJudicial.objects.all(), user, related_prefix='deudor__')
    print("Expedientes:", qs_exp.count())
except Exception as e:
    traceback.print_exc()
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password)

# Write to file on server
sftp = ssh.open_sftp()
with sftp.file('/root/crm_pyp/test_query_remote.py', 'w') as f:
    f.write(script_content)
sftp.close()

cmd = 'cd /root/crm_pyp && /root/crm_pyp/venv/bin/python manage.py shell < /root/crm_pyp/test_query_remote.py'
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
