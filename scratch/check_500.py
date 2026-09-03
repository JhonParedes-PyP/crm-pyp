import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)

    # We will curl the page and grab the HTML (which will be a 500 error page with traceback if debug=True, 
    # but debug is probably False. We will check django error log)
    
    # Run django dev server locally for a second to get the traceback
    script = """
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()

from django.test.client import Client
c = Client()
try:
    response = c.get('/judicial/dashboard/')
    print('Status Code:', response.status_code)
    if response.status_code == 500:
        print(response.content.decode('utf-8'))
except Exception as e:
    import traceback
    traceback.print_exc()
"""
    sftp = ssh.open_sftp()
    with sftp.file('/root/crm_pyp/get_500.py', 'w') as f:
        f.write(script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command('cd /root/crm_pyp && /root/crm_pyp/venv/bin/python get_500.py')
    print("STDOUT:")
    print(stdout.read().decode())
    print("STDERR:")
    print(stderr.read().decode())
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
