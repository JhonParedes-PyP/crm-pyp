from django.conf import settings


def zadarma_token(request):
    """
    Inyecta variables de Zadarma en todos los templates:
    - zadarma_api_token  → token para /api/webrtc-key/
    - zadarma_sip        → extensión SIP del agente
    """
    return {
        'zadarma_api_token': getattr(settings, 'API_TOKEN_ZADARMA', ''),
        'zadarma_sip': getattr(settings, 'ZADARMA_SIP', ''),
    }
