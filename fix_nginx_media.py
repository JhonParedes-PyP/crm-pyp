import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('134.209.76.91', username='root', password='Moises16Micaela12pyp', timeout=10)

def run(cmd):
    _, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(out)
    if err: print("ERR:", err)
    return out

# Read current config
_, stdout, _ = client.exec_command('cat /etc/nginx/sites-enabled/default')
current = stdout.read().decode()

if 'location /media/' in current:
    print("[OK] El bloque /media/ ya existe en nginx")
else:
    # Add /media/ block after /static/ block
    new_config = current.replace(
        '    location /static/ {\n        alias /root/crm_pyp/staticfiles/;\n    }',
        '    location /static/ {\n        alias /root/crm_pyp/staticfiles/;\n    }\n\n    location /media/ {\n        alias /root/crm_pyp/media/;\n    }'
    )
    if new_config == current:
        print("[ERROR] No se pudo encontrar el bloque /static/ exacto. Config actual:")
        print(current)
    else:
        # Write via SFTP
        sftp = client.open_sftp()
        with sftp.file('/etc/nginx/sites-enabled/default', 'w') as f:
            f.write(new_config)
        sftp.close()
        print("[OK] Bloque /media/ agregado a nginx")

# Verify
print("\n=== Verificacion /media/ en nginx ===")
run("grep -A3 'media' /etc/nginx/sites-enabled/default")

# Test nginx config
print("\n=== nginx -t ===")
run("nginx -t 2>&1")

# Reload nginx
print("\n=== Reload nginx ===")
run("systemctl reload nginx")
print("[OK] Nginx recargado")

client.close()
