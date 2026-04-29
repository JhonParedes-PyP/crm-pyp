import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password)

# 1. Generate SSL
cmd1 = 'openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/nginx-selfsigned.key -out /etc/ssl/certs/nginx-selfsigned.crt -subj "/C=PE/ST=Lima/L=Lima/O=PyP/CN=134.209.76.91"'
stdin, stdout, stderr = ssh.exec_command(cmd1)
print(stdout.read().decode())
print(stderr.read().decode())

# 2. Update Nginx Config
nginx_config = """server {
    listen 80;
    listen 443 ssl;
    server_name 134.209.76.91;

    ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;

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

# 3. Restart Nginx
stdin, stdout, stderr = ssh.exec_command('systemctl restart nginx')
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
print("SSL config applied successfully!")
