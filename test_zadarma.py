import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()

from django.conf import settings
from cobranza.models import AgenteSIP
import requests
import hashlib
import hmac
import base64
from urllib.parse import urlencode

print("--- ZADARMA CONFIG ---")
print("ZADARMA_KEY:", getattr(settings, 'ZADARMA_KEY', 'NOT SET'))
print("ZADARMA_SECRET:", getattr(settings, 'ZADARMA_SECRET', 'NOT SET'))
print("ZADARMA_SIP:", getattr(settings, 'ZADARMA_SIP', 'NOT SET'))

print("\n--- SIP AGENTS ---")
agents = AgenteSIP.objects.all()
for a in agents:
    print(f"User: {a.usuario.username}, Anexo: {a.anexo}, Clave (en BD): {a.clave[:10]}...")

print("\n--- ZADARMA CONNECTION TEST ---")
api_method = '/v1/info/balance/'
params = {}
sorted_params = dict(sorted(params.items()))
query_string = urlencode(sorted_params)
md5_hash = hashlib.md5(query_string.encode('utf-8')).hexdigest()
data_to_sign = f"{api_method}{query_string}{md5_hash}"

secret = getattr(settings, 'ZADARMA_SECRET', '')
key = getattr(settings, 'ZADARMA_KEY', '')
if secret and key:
    signature_bytes = hmac.new(
        secret.encode('utf-8'),
        data_to_sign.encode('utf-8'),
        hashlib.sha1
    ).digest()
    signature = base64.b64encode(signature_bytes).decode()
    headers = {'Authorization': f"{key}:{signature}"}

    try:
        r = requests.get(f"https://api.zadarma.com{api_method}", params=params, headers=headers, timeout=10)
        print("Status code:", r.status_code)
        print("Response:", r.text)
    except Exception as e:
        print("Error:", str(e))
else:
    print("Cannot test, missing Zadarma credentials.")
