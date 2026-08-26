import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()

from cobranza.models import AgenteSIP
from django.contrib.auth.models import User

sips = AgenteSIP.objects.all().select_related('user')
print("--- ALL SIP AGENTS ---")
for s in sips:
    clave_db = s.clave
    if clave_db.startswith("0b") and len(clave_db) > 22:
        real_password = clave_db[2:-20]
    else:
        real_password = clave_db
        
    basura = "ABCDEFGHIJKLMNOPQRSTUV"
    clave_ofuscada = basura + real_password
    print(f"User: {s.user.username:<15} Anexo: {s.anexo:<5} Clave DB: {clave_db[:15]:<15}... Real Pwd len: {len(real_password)}")
