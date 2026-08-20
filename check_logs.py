import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.209.76.91', username='root', password='Moises16Micaela12pyp')
cmd = "journalctl -u gunicorn --since '10 minutes ago' | grep 'MultipleObjectsReturned'"
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
