import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password)

sftp = ssh.open_sftp()
sftp.put('cobranza/templates/cobranza/base.html', '/root/crm_pyp/cobranza/templates/cobranza/base.html')
sftp.close()

stdin, stdout, stderr = ssh.exec_command('systemctl restart gunicorn')
print("Uploaded base.html and restarted gunicorn")
ssh.close()
