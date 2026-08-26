import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.209.76.91', username='root', password='Moises16Micaela12pyp')
python_code = """import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()
from cobranza.models import Deudor, Convenio
d = Deudor.objects.get(id=908)
try:
    c, created = Convenio.objects.update_or_create(deudor=d, defaults={'cuenta': d.cuenta})
    print(c)
except Exception as e:
    print(type(e), e)
"""
sftp = ssh.open_sftp()
with open("test_uoc.py", "w") as f: f.write(python_code)
sftp.put("test_uoc.py", "/root/crm_pyp/test_uoc.py")
sftp.close()
stdin, stdout, stderr = ssh.exec_command("/root/crm_pyp/venv/bin/python /root/crm_pyp/test_uoc.py")
print(stdout.read().decode())
