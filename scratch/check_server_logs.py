import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)

    stdin, stdout, stderr = ssh.exec_command('tail -n 50 /var/log/syslog | grep gunicorn')
    print("SYSLOG GUNICORN:")
    print(stdout.read().decode())
    
    stdin, stdout, stderr = ssh.exec_command('journalctl -u gunicorn -n 50 --no-pager')
    print("JOURNALCTL:")
    print(stdout.read().decode())
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
