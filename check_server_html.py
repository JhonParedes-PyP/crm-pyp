import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

cmd = "grep 'btn-excel' /root/crm_pyp/cobranza/templates/cobranza/generar_cartas.html"
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode()
if out:
    print("Found on server:\n", out)
else:
    print("Not found on server!")
ssh.close()
