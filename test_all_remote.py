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

from cobranza.models import AgenteSIP

agents = AgenteSIP.objects.all().select_related('user')
for s in agents:
    clave_db = s.clave
    if clave_db.startswith('0b') and len(clave_db) > 22:
        real = clave_db[2:-20]
    else:
        real = clave_db
    print(f"User: {s.user.username:<10} Anexo: {s.anexo:<5} ClaveDB_Len: {len(clave_db):<3} RealPwd_Len: {len(real):<3} ClaveDB: {clave_db}")
"""

with open("remote_check.py", "w", encoding="utf-8") as f:
    f.write(python_code)

sftp = ssh.open_sftp()
sftp.put("remote_check.py", "/root/crm_pyp/remote_check.py")
sftp.close()

cmd = "/root/crm_pyp/venv/bin/python /root/crm_pyp/remote_check.py"
stdin, stdout, stderr = ssh.exec_command(cmd)

print("OUT:\n", stdout.read().decode())
err = stderr.read().decode()
if err: print("ERR:\n", err)

ssh.close()
