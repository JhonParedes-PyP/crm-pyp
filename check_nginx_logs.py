import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.209.76.91', username='root', password='Moises16Micaela12pyp', timeout=10)

def run(cmd):
    _, s, e = ssh.exec_command(cmd)
    s.channel.recv_exit_status()
    print(s.read().decode().strip() or e.read().decode().strip())

print("=== Ultimas 20 lineas de acceso nginx (media) ===")
run("tail -30 /var/log/nginx/access.log | grep media")

print("\n=== Todos los errores recientes (404 en media) ===")
run("grep 'media' /var/log/nginx/access.log | grep ' 404 ' | tail -10")

print("\n=== PATCH requests recientes al API ===")
run("grep 'PATCH /api' /var/log/nginx/access.log | tail -10")

ssh.close()
