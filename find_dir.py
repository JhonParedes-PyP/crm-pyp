import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

def run_cmd(ssh, cmd):
    print(f"--- Ejecutando: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    return out

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=10)
    
    print("Buscando manage.py...")
    result = run_cmd(ssh, "find / -type f -name 'manage.py' 2>/dev/null | grep -v 'site-packages'")
    print(f"Resultado:\n{result}")

except Exception as e:
    print(f"Error fatal: {e}")
finally:
    ssh.close()
