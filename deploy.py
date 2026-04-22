import paramiko
import os

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

def run_cmd(ssh, cmd):
    print(f"--- Ejecutando: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    # Wait for the command to finish
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    
    if out: print(out)
    if err: print(f"ERROR: {err}")
    return exit_status, out

try:
    print("Conectando al servidor...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=10)
    print("[OK] Conectado exitosamente")

    project_dir = "/root/crm_pyp"
    print(f"Ruta del proyecto: {project_dir}")
    
    # 2. Descargar código
    run_cmd(ssh, f"cd {project_dir} && git config --global --add safe.directory {project_dir} && git pull origin main")
    
    # 3. Leer el .env local y subirlo
    print("Subiendo .env al servidor...")
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            env_content = f.read()
            
        sftp = ssh.open_sftp()
        with sftp.open(f"{project_dir}/.env", "w") as remote_env:
            remote_env.write(env_content)
        sftp.close()
        print("[OK] Archivo .env guardado en el servidor")
    except Exception as e:
        print(f"[ERROR] subiendo .env: {e}")

    # 4. Reiniciar el servicio
    print("Reiniciando el servidor web...")
    run_cmd(ssh, "systemctl restart gunicorn 2>/dev/null || systemctl restart crm-pyp 2>/dev/null || systemctl restart crm_pyp 2>/dev/null")
    
    print("[OK] Despliegue completado con exito!")

except Exception as e:
    print(f"Error fatal: {e}")
finally:
    try:
        ssh.close()
    except:
        pass
