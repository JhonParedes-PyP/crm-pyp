import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()

from cobranza.models import AgenteSIP

agents = AgenteSIP.objects.all().select_related('user')
for s in agents:
    clave_db = s.clave
    if clave_db.startswith('0b') and len(clave_db) > 22:
        real = clave_db[2:-20]
    else:
        real = clave_db
    print(f"User: {s.user.username:<10} Anexo: {s.anexo:<5} ClaveDB_Len: {len(clave_db):<3} RealPwd_Len: {len(real):<3} ClaveDB: {clave_db}")
