import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()
from django.test import Client
from django.contrib.auth.models import User
import json

c = Client(SERVER_NAME='134.209.76.91')
user = User.objects.get(username='JPAREDES')
c.force_login(user)
resp = c.post('/dashboard/guardar_metas/', 
              json.dumps({"PROEMPRESA": 100}), 
              content_type="application/json")
print("Status Code:", resp.status_code)
print("Content:", resp.content)
