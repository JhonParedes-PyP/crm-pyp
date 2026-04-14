import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()

from django.conf import settings
from collections import OrderedDict
import urllib.parse
import hashlib
import base64
import hmac

api_url = "/v1/webrtc/get_key/"
params = {'sip': settings.ZADARMA_SIP}

ordered_params = OrderedDict(sorted(params.items()))
query_string = urllib.parse.urlencode(ordered_params)

print("=== DEBUG ZADARMA ===")
print("[1] API URL: " + api_url)
print("[2] SIP: " + settings.ZADARMA_SIP)
print("[3] Query String: " + query_string)

md5_string = hashlib.md5(query_string.encode('utf-8')).hexdigest()
print("[4] MD5 Hash: " + md5_string)

data_to_sign = api_url + query_string + md5_string
print("[5] Data to Sign: " + data_to_sign)

signature = base64.b64encode(
    hmac.new(
        settings.ZADARMA_SECRET.encode('utf-8'),
        data_to_sign.encode('utf-8'),
        hashlib.sha1
    ).digest()
).decode()
print("[6] Signature: " + signature)

auth_header = f"{settings.ZADARMA_KEY}:{signature}"
print("[7] Auth Header: " + auth_header[:50] + "...")

full_url = f"https://api.zadarma.com{api_url}?{query_string}"
print("\n[->] Full URL: " + full_url)
print("[->] Authorization: " + auth_header)
