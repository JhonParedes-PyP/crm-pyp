import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password)

cmd = 'grep -r "Traceback" /root/crm_pyp/ 2>/dev/null | head -n 50'
stdin, stdout, stderr = ssh.exec_command(cmd)
print("STDOUT:", stdout.read().decode())
print("STDERR:", stderr.read().decode())

ssh.close()
