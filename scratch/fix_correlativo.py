import paramiko

host = '134.209.76.91'
user = 'root'
password = 'Moises16Micaela12pyp'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

# The DB is PostgreSQL (default for django usually, or sqlite? Let's check settings)
# Let's run a Django management shell script remotely to execute the raw SQL

script = """
import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()

with connection.cursor() as cursor:
    try:
        cursor.execute("ALTER TABLE cobranza_deudor ADD COLUMN correlativo VARCHAR(100) NULL;")
        print("Column 'correlativo' added successfully!")
    except Exception as e:
        print("Error adding column (maybe it already exists?):", e)
"""

# Upload the script
sftp = ssh.open_sftp()
with sftp.file('/root/crm_pyp/fix_db_column.py', 'w') as f:
    f.write(script)
sftp.close()

# Run the script
cmd = "cd /root/crm_pyp && /root/crm_pyp/venv/bin/python fix_db_column.py"
stdin, stdout, stderr = ssh.exec_command(cmd)
print("OUT:", stdout.read().decode())
print("ERR:", stderr.read().decode())
ssh.close()
