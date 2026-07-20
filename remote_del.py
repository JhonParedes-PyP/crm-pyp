
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
