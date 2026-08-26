import paramiko
import os

key_path = os.path.expanduser('~/.ssh/id_rsa')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('161.35.13.167', username='root', key_filename=key_path)

cmd = 'df -h'
stdin, stdout, stderr = client.exec_command(cmd)
print("OUT:\n", stdout.read().decode())
print("ERR:\n", stderr.read().decode())
client.close()
