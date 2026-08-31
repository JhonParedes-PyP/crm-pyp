import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

print("Connecting...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

sftp = ssh.open_sftp()
print("Uploading script...")
sftp.put(r'C:\CRM PYP\scratch\update_scores2.py', '/root/crm_pyp/scratch/update_scores2.py')
sftp.close()

print("Executing script remotely...")
stdin, stdout, stderr = ssh.exec_command('cd /root/crm_pyp && ./venv/bin/python scratch/update_scores2.py')
exit_status = stdout.channel.recv_exit_status()
out = stdout.read().decode()
err = stderr.read().decode()

print(out)
if err: print("ERRORS:", err)
