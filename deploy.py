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
    run_cmd(ssh, f"cd {project_dir} && git config --global --add safe.directory {project_dir} && git fetch origin && git reset --hard origin/main")

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

    try:
        sftp = ssh.open_sftp()
        print("Subiendo import_sip.py y Excel al servidor...")
        sftp.put('import_sip.py', f"{project_dir}/import_sip.py")
        sftp.put('ANEXOS Y CLAVES.xlsx', f"{project_dir}/ANEXOS Y CLAVES.xlsx")

        print("Subiendo archivos actualizados del CRM...")
        archivos_a_subir = [
            ('cobranza/views.py', f"{project_dir}/cobranza/views.py"),
            ('cobranza/models.py', f"{project_dir}/cobranza/models.py"),
            ('cobranza/admin.py', f"{project_dir}/cobranza/admin.py"),
            ('cobranza/api_views.py', f"{project_dir}/cobranza/api_views.py"),
            ('cobranza/dashboard_views.py', f"{project_dir}/cobranza/dashboard_views.py"),
            ('cobranza/asignaciones.py', f"{project_dir}/cobranza/asignaciones.py"),
            ('cobranza/migrations/0017_asignaciondiaria.py', f"{project_dir}/cobranza/migrations/0017_asignaciondiaria.py"),
            ('cobranza/templates/cobranza/bandeja.html', f"{project_dir}/cobranza/templates/cobranza/bandeja.html"),
            ('cobranza/templates/cobranza/base.html', f"{project_dir}/cobranza/templates/cobranza/base.html"),
            ('cobranza/templates/cobranza/asignaciones_diarias.html', f"{project_dir}/cobranza/templates/cobranza/asignaciones_diarias.html"),
            ('crm_pyp_config/context_processors.py', f"{project_dir}/crm_pyp_config/context_processors.py"),
            ('crm_pyp_config/urls.py', f"{project_dir}/crm_pyp_config/urls.py"),
        ]
        for origen, destino in archivos_a_subir:
            sftp.put(origen, destino)

        sftp.close()
        print("Ejecutando import_sip.py en el servidor...")
        run_cmd(ssh, f"cd {project_dir} && {project_dir}/venv/bin/python import_sip.py")
        
        sftp = ssh.open_sftp()
        sftp.remove(f"{project_dir}/ANEXOS Y CLAVES.xlsx")
        sftp.close()
        print("[OK] Excel de claves eliminado por seguridad")
    except Exception as e:
        print(f"[ERROR] importando SIP: {e}")

    # 4. Instalar dependencias nuevas (ej: Pillow para ImageField)
    print("Instalando dependencias...")
    run_cmd(ssh, f"{project_dir}/venv/bin/pip install -r {project_dir}/requirements.txt -q")

    # 5. Aplicar migraciones de base de datos
    print("Aplicando migraciones...")
    run_cmd(ssh, f"{project_dir}/venv/bin/python {project_dir}/manage.py migrate --noinput")

    # 6. Recolectar archivos estáticos
    print("Recolectando archivos estáticos...")
    run_cmd(ssh, f"{project_dir}/venv/bin/python {project_dir}/manage.py collectstatic --noinput")

    # 7. Crear carpeta media si no existe
    run_cmd(ssh, f"mkdir -p {project_dir}/media/evidencias && chmod 755 {project_dir}/media/evidencias")

    # 8. Reiniciar el servicio
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
