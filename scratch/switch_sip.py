import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()

from django.contrib.auth.models import User
from cobranza.models import AgenteSIP

try:
    user_old = User.objects.get(username='MSANCHEZ')
    print("Found MSANCHEZ.")
    try:
        sip = AgenteSIP.objects.get(user=user_old)
        print(f"Found SIP for MSANCHEZ: Ext {sip.anexo}")
        
        try:
            user_new = User.objects.get(username='BLLAJA')
            print("Found BLLAJA.")
            sip.user = user_new
            sip.save()
            print("SIP credentials transferred to BLLAJA successfully.")
            
            # Deactivate MSANCHEZ
            user_old.is_active = False
            user_old.save()
            print("MSANCHEZ deactivated.")
            
        except User.DoesNotExist:
            print("ERROR: User BLLAJA does not exist on the server. Please create the user first in the Admin panel.")
            # Let's just create it with a default password so the gestor can work.
            user_new = User.objects.create_user(username='BLLAJA', password='123')
            user_new.is_staff = True
            user_new.save()
            print("User BLLAJA created with password '123'.")
            sip.user = user_new
            sip.save()
            print("SIP credentials transferred to BLLAJA successfully.")
            
            user_old.is_active = False
            user_old.save()
            print("MSANCHEZ deactivated.")

    except AgenteSIP.DoesNotExist:
        print("ERROR: MSANCHEZ does not have SIP credentials assigned.")
except User.DoesNotExist:
    print("ERROR: User MSANCHEZ does not exist.")
