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

print("=== NGINX - bloque /media/ ===")
run("grep -n -A5 'media' /etc/nginx/sites-enabled/crm_pyp 2>/dev/null || echo 'No encontrado en sites-enabled'")

print("\n=== DIRECTORIO MEDIA/EVIDENCIAS ===")
run("ls -la /root/crm_pyp/media/evidencias/ 2>&1 | head -20")

print("\n=== FOTO EN BD ===")
run("cd /root/crm_pyp && venv/bin/python -c \"import django, os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','crm_pyp_config.settings'); django.setup(); from cobranza.models import Deudor; qs=Deudor.objects.filter(foto_evidencia__isnull=False); print('Con foto:', qs.count()); d=qs.first(); print('Nombre archivo:', d.foto_evidencia.name if d else 'Ninguno')\"")

print("\n=== PERMISOS MEDIA ===")
run("stat /root/crm_pyp/media/ 2>&1")

client.close()
