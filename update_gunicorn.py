import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

def run_cmd(cmd):
    print(f'--- {cmd}')
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(out)
    if err: print('ERROR:', err)

service_file = """[Unit]
Description=Motor Gunicorn para CRM PyP
After=network.target

[Service]
User=root
WorkingDirectory=/root/crm_pyp
ExecStart=/root/crm_pyp/venv/bin/gunicorn --workers 3 --timeout 120 --bind 127.0.0.1:8000 crm_pyp_config.wsgi:application

[Install]
WantedBy=multi-user.target
"""

run_cmd(f"echo '{service_file}' > /etc/systemd/system/gunicorn.service")
run_cmd("systemctl daemon-reload")
run_cmd("systemctl restart gunicorn")

ssh.close()
print("Gunicorn configuration updated successfully.")
