import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print("Conectando al servidor...")
    ssh.connect(host, username=user, password=password, timeout=10)
    
    cmd = """
    cat << 'EOF' | /root/crm_pyp/venv/bin/python /root/crm_pyp/manage.py shell
from django.contrib.auth.models import User
try:
    u = User.objects.get(username='JPAREDES')
    u.set_password('Jparedes2026')
    u.save()
    print("SUCCESS")
except Exception as e:
    print("ERROR", str(e))
EOF
    """
    
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    print("OUT:", stdout.read().decode().strip())
    print("ERR:", stderr.read().decode().strip())
    
finally:
    ssh.close()
