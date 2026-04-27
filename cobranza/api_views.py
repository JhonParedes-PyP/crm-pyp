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
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autorizado', 'message': 'Unauthorized'}, status=401)

    try:
        sip_profile = request.user.sip_profile
        return JsonResponse({
            'status': 'success',
            'sip': sip_profile.anexo,
            'key': sip_profile.clave
        })
    except Exception:
        return JsonResponse({'error': 'Sin perfil SIP', 'message': 'No SIP profile found'}, status=404)

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
        # Si es superusuario, ve toda la cartera
        usuario = User.objects.filter(username=agente).first()
        if usuario and (usuario.is_superuser or usuario.groups.filter(name='GERENTE').exists()):
            deudores = Deudor.objects.all()
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

    # --- Paginación para evitar cargar toda la cartera en un solo JSON ---
    total_count = deudores.count()
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        page_size = min(500, max(1, int(request.GET.get('page_size', 100))))
    except (ValueError, TypeError):
        page_size = 100

    offset = (page - 1) * page_size
    deudores_pagina = deudores[offset:offset + page_size]

    data = []
    for d in deudores_pagina:
        data.append({
            'fila_id': d.id,
            'agencia': d.agencia or '',
            'cuenta': d.cuenta or '',
            'nombre': d.nombre_completo or '',
            'dni': d.documento or '',
            'cartera': d.cartera or '',
            'producto': d.producto or '',
            'nmes': d.nmes or '',
            'departamento': d.departamento or '',
            'provincia': d.provincia or '',
            'zona': d.zona or '',
            'ultimo_pago': str(d.ultimo_dia_pago) if d.ultimo_dia_pago else '',
            'capital': str(d.monto_capital),
            'total': str(d.saldo_deuda),
            'imp_recup': str(d.imp_recup) if d.imp_recup is not None else '',
            'imp_capital_rec': str(d.imp_capital_rec) if d.imp_capital_rec is not None else '',
            'direccion': d.dir_casa or '',
            'dir_negocio': d.dir_negocio or '',
            'distrito': d.distrito or '',
            'telefono': d.telefono_principal or '',
            'nom_conyuge': d.nom_conyuge or '',
            'num_doc_conyuge': d.num_doc_conyuge or '',
            'nom_aval': d.nom_aval or '',
            'num_doc_aval': d.num_doc_aval or '',
            'aval_direccion': d.aval_direccion or '',
            'aval_distrito': d.aval_distrito or '',
            'aval_telefono': d.tlf_celular_aval or '',
            'nom_conyuge_aval': d.nom_conyuge_aval or '',
            'expediente': d.expediente or '',
            'juzgado': d.juzgado or '',
            'fec_demanda': str(d.fec_demanda) if d.fec_demanda else '',
            'monto_demanda': str(d.monto_demanda) if d.monto_demanda is not None else '',
            'ingreso_judicial': str(d.ingreso_judicial) if d.ingreso_judicial else '',
            'condicion': d.condicion or '',
            'referencia': d.referencia or '',
            'proceso': d.proceso or '',
            'detalle_bien': d.detalle_bien or '',
            'estado_medida_cautelar': d.estado_medida_cautelar or '',
            'seguimiento_cautelar': d.seguimiento_cautelar or '',
            'estado_proceso_principal': d.estado_proceso_principal or '',
            'seguimiento_principal': d.seguimiento_principal or '',
            'codigo_cautelar': d.codigo_cautelar or '',
            'gestion_extra': d.gestion_extra or '',
            'link_gps': d.link_gps or '',
            'link_gps_aval': d.link_gps_aval or '',
            'foto_evidencia': settings.SITE_URL + d.foto_evidencia.url if d.foto_evidencia else '',
        })

    return JsonResponse({
        'success': True,
        'data': data,
        'total': total_count,
        'page': page,
        'page_size': page_size,
        'has_more': (offset + page_size) < total_count,
    }, status=200)

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

    # Django solo parsea multipart automáticamente para POST.
    # Para PATCH, hay que forzar el parseo manualmente.
    if request.method == 'PATCH':
        content_type = request.content_type or ''
        if 'multipart/form-data' in content_type:
            from django.http.multipartparser import MultiPartParser
            try:
                post_data, files = MultiPartParser(
                    request.META, request, request.upload_handlers
                ).parse()
            except Exception:
                post_data, files = request.POST, request.FILES
        else:
            post_data, files = request.POST, request.FILES
    else:
        post_data, files = request.POST, request.FILES

    if 'link_gps' in post_data:
        deudor.link_gps = post_data['link_gps']
        campos_actualizados.append('link_gps')

    if 'link_gps_aval' in post_data:
        deudor.link_gps_aval = post_data['link_gps_aval']
        campos_actualizados.append('link_gps_aval')

    if 'foto_evidencia' in files:
        deudor.foto_evidencia = files['foto_evidencia']
        campos_actualizados.append('foto_evidencia')

    if not campos_actualizados:
        return JsonResponse({'success': False, 'detail': 'No se enviaron campos válidos. Permitidos: link_gps, link_gps_aval, foto_evidencia.'}, status=400)

    deudor.save(update_fields=campos_actualizados)

    foto_url = settings.SITE_URL + deudor.foto_evidencia.url if deudor.foto_evidencia else ''
    return JsonResponse({'success': True, 'foto_url': foto_url}, status=200)

