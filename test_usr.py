import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()
from django.contrib.auth.models import User
for u in User.objects.all(): print(f"'{u.username}'")
