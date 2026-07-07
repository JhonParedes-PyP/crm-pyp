import paramiko
ssh=paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.209.76.91', username='root', password='Moises16Micaela12pyp')
stdin, stdout, stderr = ssh.exec_command('cd /root/crm_pyp && /root/crm_pyp/venv/bin/python -m py_compile cobranza/middleware.py cobranza/dashboard_views.py crm_pyp_config/settings.py')
print("STDOUT:", stdout.read().decode())
print("STDERR:", stderr.read().decode())
