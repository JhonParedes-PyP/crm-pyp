import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password)

cmd = 'journalctl -u gunicorn -n 50 --no-pager'
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
