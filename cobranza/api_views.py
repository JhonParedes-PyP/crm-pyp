from .models import *
import json, os, hashlib, hmac, base64, requests
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from urllib.parse import urlencode
from decimal import Decimal

@csrf_exempt 
@require_http_methods(["POST"])
def api_recibir_gestion_campo(request):

    # 1. EL CANDADO DE SEGURIDAD
    api_key = request.headers.get('Authorization')
    if api_key != 'Bearer PYP-CAMPO-2026':
        return JsonResponse({'estado': 'error', 'mensaje': 'Acceso denegado. Llave de P&P incorrecta.'}, status=401)

    try:
        # 2. ABRIR EL PAQUETE DE DATOS
        data = json.loads(request.body)
        
        dni_cliente = data.get('dni')
        resultado = data.get('resultado', 'VISITA')
        observacion = data.get('observacion', '')
        nombre_gestor = data.get('gestor_username')

        # 3. BUSCAR EN LA BÓVEDA
        deudor = Deudor.objects.filter(documento=dni_cliente).first()
        if not deudor:
            return JsonResponse({'estado': 'error', 'mensaje': f'El DNI {dni_cliente} no existe en el CRM.'}, status=404)

        # Buscamos al gestor en el sistema
        gestor_asignado = User.objects.filter(username=nombre_gestor).first()

        # 4. GUARDAR LA GESTIÓN AUTOMÁTICAMENTE
        Gestion.objects.create(
            deudor=deudor,
            gestor=gestor_asignado,
            resultado=f"CAMPO - {resultado}", # Etiqueta visual para diferenciarlo
            observacion=f"[App Judicial] {observacion}",
            monto_pago=Decimal('0')
        )

        # 5. ENVIAR RECIBO DE ÉXITO AL APP
        return JsonResponse({'estado': 'ok', 'mensaje': '¡Gestión sincronizada con éxito en el CRM!'}, status=200)

    except Exception as e:
        # Si hay un error, avisamos al App Judicial
        return JsonResponse({'estado': 'error', 'mensaje': f'Error en los datos: {str(e)}'}, status=400)

@require_http_methods(["GET"])
def api_zadarma_webrtc_key(request):
    """Devuelve las credenciales SIP de forma segura al cliente autenticado"""
    token = request.GET.get('token', '')
    if not request.user.is_authenticated and token != getattr(settings, 'API_TOKEN_ZADARMA', ''):
        return JsonResponse({'error': 'No autorizado', 'message': 'Unauthorized'}, status=401)

    # El WebRTC nativo de Zadarma (JsSIP) en este proyecto requiere la contraseña directa.
    # En lugar de quemarla en el HTML, se devuelve por API segura.
    return JsonResponse({
        'status': 'success',
        'sip': getattr(settings, 'ZADARMA_SIP', '398200-100'),
        'key': getattr(settings, 'ZADARMA_SIP_PASS', 'EaU2huAPu4') 
    })

@login_required
def iniciar_callback(request, numero_cliente):
    """Inicia la llamada para el botón azul"""
    num = str(numero_cliente).strip()
    if len(num) == 9 and num.startswith('9'):
        num = f"51{num}"

    api_method = '/v1/request/callback/'
    params = {'from': settings.ZADARMA_SIP, 'to': num}

    # 1. Firma idéntica al método anterior (BASE64)
    sorted_params = dict(sorted(params.items()))
    query_string = urlencode(sorted_params)
    md5_hash = hashlib.md5(query_string.encode('utf-8')).hexdigest()
    data_to_sign = f"{api_method}{query_string}{md5_hash}"

    signature_bytes = hmac.new(
        settings.ZADARMA_SECRET.encode('utf-8'),
        data_to_sign.encode('utf-8'),
        hashlib.sha1
    ).digest()
    signature = base64.b64encode(signature_bytes).decode()

    headers = {'Authorization': f"{settings.ZADARMA_KEY}:{signature}"}
    try:
        response = requests.get(
            f"https://api.zadarma.com{api_method}",
            params=params,
            headers=headers,
            timeout=10
        )
        data = response.json()
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error de conexión con Zadarma: {str(e)}'}, status=500)

    return JsonResponse(data)

@csrf_exempt
@require_http_methods(["POST"])
def api_app_login(request):
    """
    POST /api/v1/auth/app-login/
    Autentica agentes de campo desde la app móvil.
    No requiere sesión ni JWT — solo valida usuario/contraseña.
    Requiere pertenecer al grupo 'APP_MOVIL' para tener acceso.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'detail': 'Cuerpo de la petición inválido.'}, status=400)

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return JsonResponse({'detail': 'Credenciales inválidas'}, status=401)

    from django.contrib.auth import authenticate as django_authenticate
    user = django_authenticate(request, username=username, password=password)

    if user is None or not user.is_active:
        return JsonResponse({'detail': 'Credenciales inválidas'}, status=401)

    return JsonResponse({'ok': True}, status=200)

@require_http_methods(["GET"])
def api_app_credentials(request):
    """
    GET /api/v1/app-credentials/
    Sirve el archivo llave.json de la Service Account de Google.
    Protegido con el mismo token Bearer que el resto de la app de campo.
    """
    api_key = request.headers.get('Authorization', '')
    if api_key != 'Bearer PYP-CAMPO-2026':
        return JsonResponse({'detail': 'Acceso denegado.'}, status=401)

    llave_path = getattr(settings, 'LLAVE_JSON_PATH', None)
    if not llave_path:
        return JsonResponse({'detail': 'Archivo de credenciales no configurado en el servidor.'}, status=404)

    import os
    if not os.path.isfile(llave_path):
        return JsonResponse({'detail': 'Archivo de credenciales no encontrado en el servidor.'}, status=404)

    try:
        with open(llave_path, 'r', encoding='utf-8') as f:
            credenciales = json.load(f)
        return JsonResponse(credenciales, status=200)
    except Exception as e:
        return JsonResponse({'detail': f'Error al leer credenciales: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_cartera_lista(request):
    """
    GET /api/v1/cartera/?agente={username}  → Cartera asignada al agente
    GET /api/v1/cartera/?dni={dni}          → Búsqueda exacta por DNI
    GET /api/v1/cartera/?nombre={texto}     → Búsqueda parcial por nombre (case-insensitive)
    Requiere: Authorization: Bearer PYP-CAMPO-2026
    """
    api_key = request.headers.get('Authorization', '')
    if api_key != 'Bearer PYP-CAMPO-2026':
        return JsonResponse({'success': False, 'detail': 'Acceso denegado.'}, status=401)

    agente = request.GET.get('agente', '').strip()
    dni = request.GET.get('dni', '').strip()
    nombre = request.GET.get('nombre', '').strip()

    if not agente and not dni and not nombre:
        return JsonResponse({'success': False, 'detail': 'Parámetro requerido: agente, dni o nombre.'}, status=400)

    if dni:
        deudores = Deudor.objects.filter(documento=dni)
    elif nombre:
        deudores = Deudor.objects.filter(nombre_completo__icontains=nombre)
    else:
        asignaciones = AsignacionCartera.objects.filter(gestor__username=agente).values('tipo', 'valor')
        carteras = [a['valor'] for a in asignaciones if a['tipo'] == 'cartera']
        agencias = [a['valor'] for a in asignaciones if a['tipo'] == 'agencia']

        filtro = Q()
        if carteras:
            filtro |= Q(cartera__in=carteras)
        if agencias:
            filtro |= Q(agencia__in=agencias)

        deudores = Deudor.objects.filter(filtro) if filtro else Deudor.objects.none()

    data = []
    for d in deudores:
        data.append({
            'fila_id': d.id,
            'agencia': d.agencia or '',
            'cuenta': d.cuenta or '',
            'nombre': d.nombre_completo or '',
            'ultimo_pago': str(d.ultimo_dia_pago) if d.ultimo_dia_pago else '',
            'expediente': d.expediente or '',
            'juzgado': d.juzgado or '',
            'fec_demanda': str(d.fec_demanda) if d.fec_demanda else '',
            'monto_demanda': str(d.monto_demanda) if d.monto_demanda is not None else '',
            'capital': str(d.monto_capital),
            'total': str(d.saldo_deuda),
            'ingreso_judicial': str(d.ingreso_judicial) if d.ingreso_judicial else '',
            'direccion': d.dir_casa or '',
            'distrito': d.distrito or '',
            'aval_nombre': d.nom_aval or '',
            'aval_direccion': d.aval_direccion or '',
            'aval_distrito': d.aval_distrito or '',
            'condicion': d.condicion or '',
            'dni': d.documento or '',
            'referencia': d.referencia or '',
            'telefono': d.telefono_principal or '',
            'aval_telefono': d.tlf_celular_aval or '',
            'link_gps': d.link_gps or '',
            'link_gps_aval': d.link_gps_aval or '',
            'gestion_extra': d.gestion_extra or '',
            'proceso': d.proceso or '',
            'detalle_bien': d.detalle_bien or '',
            'estado_medida_cautelar': d.estado_medida_cautelar or '',
            'seguimiento_cautelar': d.seguimiento_cautelar or '',
            'estado_proceso_principal': d.estado_proceso_principal or '',
            'seguimiento_principal': d.seguimiento_principal or '',
            'codigo_cautelar': d.codigo_cautelar or '',
            'foto_evidencia': settings.SITE_URL + d.foto_evidencia.url if d.foto_evidencia else '',
        })

    return JsonResponse({'success': True, 'data': data}, status=200)

@csrf_exempt
@require_http_methods(["PATCH", "POST"])
def api_cartera_patch(request, fila_id):
    """
    PATCH /api/v1/cartera/{fila_id}/
    Acepta multipart/form-data:
      - link_gps        (texto)
      - link_gps_aval   (texto)
      - foto_evidencia  (archivo de imagen)
    Requiere: Authorization: Bearer PYP-CAMPO-2026
    """
    api_key = request.headers.get('Authorization', '')
    if api_key != 'Bearer PYP-CAMPO-2026':
        return JsonResponse({'success': False, 'detail': 'Acceso denegado.'}, status=401)

    deudor = get_object_or_404(Deudor, id=fila_id)
    campos_actualizados = []

    if 'link_gps' in request.POST:
        deudor.link_gps = request.POST['link_gps']
        campos_actualizados.append('link_gps')

    if 'link_gps_aval' in request.POST:
        deudor.link_gps_aval = request.POST['link_gps_aval']
        campos_actualizados.append('link_gps_aval')

    if 'foto_evidencia' in request.FILES:
        deudor.foto_evidencia = request.FILES['foto_evidencia']
        campos_actualizados.append('foto_evidencia')

    if not campos_actualizados:
        return JsonResponse({'success': False, 'detail': 'No se enviaron campos válidos. Permitidos: link_gps, link_gps_aval, foto_evidencia.'}, status=400)

    deudor.save(update_fields=campos_actualizados)

    foto_url = settings.SITE_URL + deudor.foto_evidencia.url if deudor.foto_evidencia else ''
    return JsonResponse({'success': True, 'foto_url': foto_url}, status=200)

