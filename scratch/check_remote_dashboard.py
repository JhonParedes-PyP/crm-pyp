import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)

    stdin, stdout, stderr = ssh.exec_command('cat /root/crm_pyp/cobranza/templates/cobranza/judicial/dashboard.html | head -n 30')
    print("STDOUT:", stdout.read().decode())
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
