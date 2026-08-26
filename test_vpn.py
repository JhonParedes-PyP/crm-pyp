import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

cmd = "ping -c 4 192.168.199.129"
stdin, stdout, stderr = ssh.exec_command(cmd)
print("PING 192.168.199.129:\n", stdout.read().decode())

cmd2 = "ip a"
stdin, stdout, stderr = ssh.exec_command(cmd2)
print("IP INTERFACES:\n", stdout.read().decode())

ssh.close()
