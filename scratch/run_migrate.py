import paramiko
import sys

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)

    sftp = ssh.open_sftp()
    sftp.put(r'c:\CRM PYP\scratch\migrate_expedientes.py', '/root/crm_pyp/migrate_expedientes.py')
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command('cd /root/crm_pyp && /root/crm_pyp/venv/bin/python migrate_expedientes.py')
    print("STDOUT:", stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
