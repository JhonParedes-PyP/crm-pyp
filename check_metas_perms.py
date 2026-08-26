import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.209.76.91', username='root', password='Moises16Micaela12pyp')
stdin, stdout, stderr = ssh.exec_command("ls -la /root/crm_pyp/metas.json")
print("ls:", stdout.read().decode())
print("err:", stderr.read().decode())
stdin, stdout, stderr = ssh.exec_command("ps aux | grep gunicorn")
print("gunicorn:", stdout.read().decode())
