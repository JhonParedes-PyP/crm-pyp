import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('134.209.76.91', username='root', password='Moises16Micaela12pyp', timeout=10)

def run(cmd):
    _, s, e = client.exec_command(cmd)
    s.channel.recv_exit_status()
    out = s.read().decode().strip()
    err = e.read().decode().strip()
    if out: print(out)
    if err: print("ERR:", err)

print("=== Permisos /root/ ===")
run("stat /root/ | head -5")

print("\n=== Nginx user ===")
run("grep -i '^user' /etc/nginx/nginx.conf | head -3")

print("\n=== Test acceso www-data a media ===")
run("sudo -u www-data ls /root/crm_pyp/media/evidencias/ 2>&1")

print("\n=== URL foto real en BD ===")
script = (
    "import django, os; "
    "os.environ['DJANGO_SETTINGS_MODULE']='crm_pyp_config.settings'; "
    "django.setup(); "
    "from cobranza.models import Deudor; "
    "qs=Deudor.objects.exclude(foto_evidencia=''); "
    "print('Total con foto:', qs.count()); "
    "d=qs.first(); "
    "print('Path BD:', repr(d.foto_evidencia.name) if d else 'Sin fotos')"
)
run(f"cd /root/crm_pyp && venv/bin/python -c \"{script}\"")

print("\n=== Curl prueba URL foto ===")
run("curl -s -o /dev/null -w '%{http_code}' https://crm.pypsolucionesjuridicas.com/media/evidencias/HN_EIRL_20260421_000000.jpg")

client.close()
