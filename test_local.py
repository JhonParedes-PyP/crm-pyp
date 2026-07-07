
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()
from django.test import Client
from django.contrib.auth.models import User
c = Client(HTTP_HOST='134.209.76.91')
user = User.objects.get(username='JPAREDES')
c.force_login(user)
try:
    response = c.get('/')
    if response.status_code == 500:
        print("DASHBOARD RETURNED 500!")
    else:
        print(f"DASHBOARD RETURNED {response.status_code}")
except Exception as e:
    import traceback
    traceback.print_exc()
