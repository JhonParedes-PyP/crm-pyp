import paramiko
import os

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

def run_cmd(ssh, cmd):
    print(f'--- Ejecutando: {cmd}')
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode().strip())
    print(stderr.read().decode().strip())

run_cmd(ssh, 'cd /root/crm_pyp && python3 -m venv venv && /root/crm_pyp/venv/bin/pip install -r requirements.txt && /root/crm_pyp/venv/bin/python manage.py makemigrations && /root/crm_pyp/venv/bin/python manage.py migrate')
ssh.close()
