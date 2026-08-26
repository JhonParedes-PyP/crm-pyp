import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.209.76.91', username='root', password='Moises16Micaela12pyp')
stdin, stdout, stderr = ssh.exec_command("cat /root/crm_pyp/crm_pyp_config/urls.py | grep guardar_metas")
print("urls:", stdout.read().decode())
