import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.209.76.91', username='root', password='Moises16Micaela12pyp')
stdin, stdout, stderr = ssh.exec_command("grep guardar_metas /var/log/nginx/access.log | tail -n 20")
print("access:", stdout.read().decode())
