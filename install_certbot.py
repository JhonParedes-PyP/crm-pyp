import paramiko
import time

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password)

def run(cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out: print("OUT:", out)
    if err: print("ERR:", err)

# 1. Update Nginx Config to use domain and remove self-signed SSL
nginx_config = """server {
    listen 80;
    server_name crm.pypsolucionesjuridicas.com 134.209.76.91;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /root/crm_pyp/static/;
    }

    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:8000;
    }
}"""

sftp = ssh.open_sftp()
with sftp.open('/etc/nginx/sites-available/crm_pyp', 'w') as f:
    f.write(nginx_config)
sftp.close()

# 2. Restart Nginx to apply plain HTTP on domain
run('systemctl restart nginx')

# 3. Install Certbot
run('apt-get update && apt-get install -y certbot python3-certbot-nginx')

# 4. Run Certbot
run('certbot --nginx -d crm.pypsolucionesjuridicas.com --non-interactive --agree-tos -m admin@pypsolucionesjuridicas.com --redirect')

# 5. Restart Nginx again
run('systemctl restart nginx')

ssh.close()
print("Certbot installed successfully!")
