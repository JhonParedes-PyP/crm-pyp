import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()

from django.conf import settings
import hashlib
import base64
import hmac
import requests

api_method = '/v1/request/callback/'
params = {
    'from': settings.ZADARMA_SIP,
    'to': '51987654321',  # Ejemplo de numero
}

sorted_dict = dict(sorted(params.items()))
params_string = '&'.join([f'{k}={v}' for k, v in sorted_dict.items()])

md5_params = hashlib.md5(params_string.encode('utf-8')).hexdigest()
data_to_sign = f"{api_method}{params_string}{md5_params}"

signature = base64.b64encode(
    hmac.new(
        settings.ZADARMA_SECRET.encode('utf-8'),
        data_to_sign.encode('utf-8'),
        hashlib.sha1
    ).digest()
).decode()

headers = {
    'Authorization': f"{settings.ZADARMA_KEY}:{signature}"
}

print("=== TESTING CLICK-TO-CALL ===")
print("[1] API Method: " + api_method)
print("[2] From (SIP): " + settings.ZADARMA_SIP)
print("[3] To (Phone): " + params['to'])
print("[4] Params String: " + params_string)
print("[5] Signature: " + signature)
print("\n[->] Enviando request a Zadarma...")

try:
    response = requests.get(
        f"https://api.zadarma.com{api_method}",
        params=params,
        headers=headers,
        timeout=10
    )
    print("[OK] HTTP Status: " + str(response.status_code))
    data = response.json()
    print("[Response] " + str(data))

    if data.get('status') == 'success':
        print("[SUCCESS] Callback request accepted!")
    else:
        print("[ERROR] " + str(data.get('message', 'Unknown error')))
except Exception as e:
    print("[ERROR] " + str(type(e).__name__) + ": " + str(e))
