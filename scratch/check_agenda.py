import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

stdin, stdout, stderr = ssh.exec_command('cat /root/crm_pyp/cobranza/templates/cobranza/agenda.html | grep ALTO')
print(stdout.read().decode())
print(stderr.read().decode())
