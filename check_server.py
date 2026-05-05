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

run_cmd('systemctl status gunicorn --no-pager')
run_cmd('journalctl -u gunicorn -n 20 --no-pager')
run_cmd('ls -la /root/crm_pyp/')
ssh.close()
