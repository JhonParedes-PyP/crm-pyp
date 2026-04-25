import paramiko
import os

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

def run_cmd(ssh, cmd):
    print(f"--- CMD: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(out)
    if err: print(f"ERR: {err}")
    return exit_status, out

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)
print("[OK] Conectado")

print("\n=== 1. Permisos de /root/ ===")
run_cmd(ssh, "stat /root/ 2>&1 | grep Access:")

print("\n=== 2. Usuario de nginx ===")
run_cmd(ssh, "grep -i '^user' /etc/nginx/nginx.conf 2>&1")

print("\n=== 3. Nginx puede leer /root/crm_pyp/media/ ===")
run_cmd(ssh, "sudo -u www-data test -r /root/crm_pyp/media/evidencias/HN_EIRL_20260421_000000.jpg && echo 'SI puede leer' || echo 'NO puede leer'")

print("\n=== 4. Curl HTTP test ===")
run_cmd(ssh, "curl -sk -o /dev/null -w 'HTTP %{http_code}' https://crm.pypsolucionesjuridicas.com/media/evidencias/HN_EIRL_20260421_000000.jpg")

print("\n=== 5. Nginx error log ===")
run_cmd(ssh, "tail -5 /var/log/nginx/error.log 2>&1")

ssh.close()
