import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

# Find the gunicorn process to see how it's started
cmd = "ps aux | grep gunicorn"
stdin, stdout, stderr = ssh.exec_command(cmd)
print("Processes:\n", stdout.read().decode())

cmd2 = "systemctl list-units --type=service | grep gunicorn"
stdin2, stdout2, stderr2 = ssh.exec_command(cmd2)
print("Services:\n", stdout2.read().decode())

cmd3 = "systemctl restart gunicorn"
stdin3, stdout3, stderr3 = ssh.exec_command(cmd3)
print("Restart output:\n", stdout3.read().decode())
print("Restart errors:\n", stderr3.read().decode())

ssh.close()
