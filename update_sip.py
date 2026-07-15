import os
import django
import pandas as pd
import paramiko

# 1. Update local DB
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
    django.setup()
    from django.contrib.auth.models import User
    from cobranza.models import AgenteSIP

    try:
        user = User.objects.get(username__iexact='NIDROGO')
        sip = AgenteSIP.objects.get(user=user)
        sip.delete()
        print("[LOCAL] NIDROGO SIP profile deleted.")
    except Exception as e:
        print(f"[LOCAL] Could not delete NIDROGO SIP: {e}")
except Exception as e:
    print(f"Error initializing local django: {e}")


# 2. Update Excel
try:
    file_path = 'ANEXOS Y CLAVES.xlsx'
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()
    user_col = next(c for c in df.columns if 'USUARIO' in c and 'CRM' in c)
    df.loc[df[user_col] == 'NIDROGO', user_col] = 'MSANCHEZ'
    df.to_excel(file_path, index=False)
    print("Excel file updated.")
except Exception as e:
    print(f"Error updating Excel: {e}")


# 3. Update Remote DB
try:
    host = '134.209.76.91'
    user = 'root'
    password = 'Moises16Micaela12pyp'

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=10)

    python_code = """
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()
from django.contrib.auth.models import User
from cobranza.models import AgenteSIP

try:
    user = User.objects.get(username__iexact='NIDROGO')
    sip = AgenteSIP.objects.get(user=user)
    sip.delete()
    print("[REMOTE] Deleted NIDROGO SIP")
except Exception as e:
    print(f"[REMOTE] Could not delete: {e}")
"""
    with open("remote_del.py", "w", encoding="utf-8") as f:
        f.write(python_code)
    sftp = ssh.open_sftp()
    sftp.put("remote_del.py", "/root/crm_pyp/remote_del.py")
    sftp.close()
    
    cmd = f"cd /root/crm_pyp && /root/crm_pyp/venv/bin/python remote_del.py"
    print(f"Executing on remote: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    
    if out: print(out)
    if err: print(f"ERROR: {err}")
    ssh.close()
except Exception as e:
    print(f"Error executing remote script: {e}")
