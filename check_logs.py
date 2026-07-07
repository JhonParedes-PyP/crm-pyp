import paramiko
ssh=paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.209.76.91', username='root', password='Moises16Micaela12pyp')
# get the last 200 lines and grep for traceback or error
stdin, stdout, stderr = ssh.exec_command('journalctl -u gunicorn -n 200 --no-pager')
print(stdout.read().decode())
