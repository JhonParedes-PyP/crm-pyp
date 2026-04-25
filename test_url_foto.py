import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.209.76.91', username='root', password='Moises16Micaela12pyp', timeout=10)

url = "https://crm.pypsolucionesjuridicas.com/media/evidencias/HN_EIRL_20260421_000000_1nOe7zT.jpg"
_, s, e = ssh.exec_command(f'curl -sk -o /dev/null -w "HTTP %{{http_code}} size:%{{size_download}}" {url}')
s.channel.recv_exit_status()
print("Resultado:", s.read().decode())
err = e.read().decode()
if err:
    print("ERR:", err)

ssh.close()
