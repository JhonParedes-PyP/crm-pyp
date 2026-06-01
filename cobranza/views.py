import pandas as pd
import openpyxl
import urllib.parse
import csv
import hashlib
import base64
import hmac
import requests
import time
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from urllib.parse import urlencode
from collections import OrderedDict
from decimal import Decimal
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect


# --- AQUÍ ESTÁ LA LÍNEA ACTUALIZADA CON LAS CAMPAÑAS ---
from .models import Deudor, Gestion, TelefonoExtra, AsignacionCartera, AsignacionDiaria, CampanaAsterisk, DetalleCampanaAsterisk, SeguimientoProgramado
from .asignaciones import aplicar_visibilidad_por_asignaciones

from django.db import models, transaction
from django.db.models import Q, Sum, Count, Max, OuterRef, Subquery, Case, When, Value, IntegerField, F, DateField, ExpressionWrapper
from django.db.models.expressions import RawSQL
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.urls import reverse

# --- FUNCIÓN PARA VERIFICAR SI ES GERENTE ---
def es_gerente(user):
    return user.groups.filter(name='GERENTE').exists() or user.is_superuser

def puede_depurar_telefonos(user):
    return bool(user and user.is_authenticated and user.is_superuser and user.username.upper() == 'JPAREDES')

def numero_repetido_en_cliente(conteo_numeros_cliente, numero):
    numero_normalizado = normalizar_telefono(numero)
    if not numero_normalizado:
        return False
    return conteo_numeros_cliente.get(numero_normalizado, 0) > 1

SUPERVISORES_CON_BANDEJA_AGENTE = {'JPAREDES'}

def puede_usar_modo_agente(user):
    return (not es_gerente(user)) or user.username.upper() in SUPERVISORES_CON_BANDEJA_AGENTE

def modo_agente_ve_todos_los_clientes(user):
    return user.is_superuser and user.username.upper() in SUPERVISORES_CON_BANDEJA_AGENTE

def normalizar_telefono(numero):
    return ''.join(ch for ch in str(numero or '') if ch.isdigit())

def buscar_telefono_duplicado(deudor_actual, numero_normalizado):
    if not numero_normalizado:
        return None

    telefonos_mismo_cliente = [
        ('telefono principal', deudor_actual.telefono_principal),
        ('telefono de aval', deudor_actual.tlf_celular_aval),
    ]
    for etiqueta, numero in telefonos_mismo_cliente:
        if normalizar_telefono(numero) == numero_normalizado:
            return f"El numero {numero_normalizado} ya esta registrado en este cliente como {etiqueta}."

    for telefono in TelefonoExtra.objects.filter(deudor=deudor_actual):
        if normalizar_telefono(telefono.numero) == numero_normalizado:
            return f"El numero {numero_normalizado} ya esta registrado en este cliente como telefono adicional ({telefono.descripcion})."

    for otro in Deudor.objects.exclude(id=deudor_actual.id).only('id', 'nombre_completo', 'documento', 'telefono_principal', 'tlf_celular_aval'):
        if normalizar_telefono(otro.telefono_principal) == numero_normalizado:
            return f"El numero {numero_normalizado} ya esta registrado en otro cliente: {otro.nombre_completo} ({otro.documento}) como telefono principal."
        if normalizar_telefono(otro.tlf_celular_aval) == numero_normalizado:
            return f"El numero {numero_normalizado} ya esta registrado en otro cliente: {otro.nombre_completo} ({otro.documento}) como telefono de aval."

    for telefono in TelefonoExtra.objects.exclude(deudor=deudor_actual).select_related('deudor'):
        if normalizar_telefono(telefono.numero) == numero_normalizado:
            return (
                f"El numero {numero_normalizado} ya esta registrado en otro cliente: "
                f"{telefono.deudor.nombre_completo} ({telefono.deudor.documento}) como telefono adicional ({telefono.descripcion})."
            )

    return None

@login_required
@require_http_methods(["GET"])
def verificar_telefono_duplicado(request, deudor_id):
    deudor = get_object_or_404(Deudor, id=deudor_id)
    numero = request.GET.get('numero', '').strip()
    numero_normalizado = normalizar_telefono(numero)

    if not numero_normalizado:
        return JsonResponse({'duplicado': False, 'mensaje': ''})

    mensaje = buscar_telefono_duplicado(deudor, numero_normalizado)
    return JsonResponse({
        'duplicado': bool(mensaje),
        'mensaje': mensaje or 'Numero disponible para registrar.',
    })

def aplicar_asignaciones_de_gestor(queryset, usuario):
    return aplicar_visibilidad_por_asignaciones(queryset, usuario)

# Usuarios con la notificación flotante de pagos próximos desactivada
USUARIOS_SIN_ALERTA_PAGO_PROXIMO = {'ASAAVEDRA'}

def obtener_alertas_pago_proximo(usuario):
    if not usuario or not usuario.is_authenticated:
        return []
    if usuario.username.upper() in USUARIOS_SIN_ALERTA_PAGO_PROXIMO:
        return []

    hoy = timezone.now().date()
    fecha_tope = hoy + timedelta(days=2)

    deudores_base = Deudor.objects.filter(ultimo_dia_pago__isnull=False).annotate(
        fecha_pago_calc=ExpressionWrapper(
            F('ultimo_dia_pago') + Value(timedelta(days=30)),
            output_field=DateField()
        ),
        fecha_inicio_alerta=ExpressionWrapper(
            F('ultimo_dia_pago') + Value(timedelta(days=28)),
            output_field=DateField()
        )
    ).filter(
        fecha_pago_calc__range=(hoy, fecha_tope)
    )

    if usuario.is_superuser and usuario.username.upper() == 'JPAREDES':
        deudores_visibles = deudores_base
    else:
        deudores_visibles = aplicar_visibilidad_por_asignaciones(deudores_base, usuario)

    deudores_visibles = deudores_visibles.exclude(
        gestion__gestor=usuario,
        gestion__fecha__date__gte=F('fecha_inicio_alerta')
    ).order_by('fecha_pago_calc', 'nombre_completo')

    return list(deudores_visibles)

# --- FUNCIÓN AUXILIAR PARA ENCRIPTAR (Asterisk - Formato Kubo) ---
def encode_md5_base64(valor):
    """
    Encripta un valor en formato MD5 truncado a 9 bytes + Base64 con padding
    Kubo usa el formato: jOGLf4Fl0Tc= (12 caracteres con = al final)
    """
    # Generar hash MD5 completo (16 bytes)
    md5_full = hashlib.md5(valor.encode()).digest()
    # Tomar solo los primeros 9 bytes
    md5_truncado = md5_full[:9]
    # Codificar a Base64
    codigo = base64.b64encode(md5_truncado).decode()
    # Tomar los primeros 11 caracteres y agregar '='
    # Esto asegura que siempre termine con '=' y tenga 12 caracteres
    codigo = codigo[:11] + '='
    return codigo

# --- FUNCIÓN AUXILIAR: CONVERTIR FECHA SIN EXPLOTAR CON NaT ---
def safe_date(valor):
    """Convierte un string a date. Devuelve None si está vacío o es inválido."""
    raw = str(valor).strip()
    if raw in ('', 'nan', 'None', 'NaT'):
        return None
    try:
        resultado = pd.to_datetime(raw, dayfirst=True, errors='coerce')
        if pd.isna(resultado):
            return None
        return resultado.date()
    except Exception:
        return None

# --- SEGURIDAD ---
@require_http_methods(["POST"])
def salir_sistema(request):
    try:
        logout(request)
        request.session.flush()
    except Exception:
        pass
    return redirect('login')

# --- CARGA DE CARTERA ---
@login_required
def subir_excel(request):
    if not es_gerente(request.user):
        return HttpResponse("Acceso Denegado. Solo Gerencia puede cargar carteras.", status=403)
    mensajes = ""
    columnas_detectadas = []
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        try:
            archivo = request.FILES['archivo_excel']
            df = pd.read_excel(archivo, dtype=str).fillna('')
            columnas_detectadas = list(df.columns)

            # Buscar columna de último día de pago con variantes de nombre
            VARIANTES_FECHA = [
                'FEC_ULT_PAGO_ACTUAL',
                'ULTIMO_DIA_PAGO', 'ULTIMO DIA PAGO', 'ULTIMO_DIA_DE_PAGO',
                'FEC_ULTIMO_PAGO', 'FECHA_ULTIMO_PAGO', 'FECHA ULTIMO PAGO',
                'FEC_ULT_PAGO', 'ULT_PAGO', 'ULTIMO_PAGO',
            ]
            col_fecha = None
            cols_upper = {c.strip().upper(): c for c in df.columns}
            for variante in VARIANTES_FECHA:
                if variante in cols_upper:
                    col_fecha = cols_upper[variante]
                    break

            dni_en_excel = set()

            # Envolver en transacción atómica para evitar auto-commit por fila
            # (mejora de rendimiento 5-10x en cargas masivas)
            with transaction.atomic():
              for index, row in df.iterrows():
                cap_str = str(row.get('DEUDA_CAP', '0')).strip()
                tot_str = str(row.get('DEUDA_TOTAL', '0')).strip()
                cap = Decimal(cap_str) if cap_str else Decimal('0')
                tot = Decimal(tot_str) if tot_str else Decimal('0')

                documento_val = str(row.get('DOC_DNI_RUC', '')).strip()

                ultimo_dia_pago_val = None
                if col_fecha:
                    raw = str(row.get(col_fecha, '')).strip()
                    if raw and raw not in ('', 'nan', 'None'):
                        ultimo_dia_pago_val = safe_date(raw)

                if documento_val:
                    dni_en_excel.add(documento_val)
                    cuenta_val = str(row.get('COD_CREDITO', 'N/A')).strip()
                    Deudor.objects.update_or_create(
                          documento=documento_val,
                          cuenta=cuenta_val,
                          defaults={
                              'cartera': str(row.get('CARTERA', 'GENERAL')).strip(),
                              'nombre_completo': str(row.get('NOM_CLI', 'SIN NOMBRE')).strip(),
                              'telefono_principal': str(row.get('TLF_CELULAR_CLIENTE', '')).strip(),
                              'agencia': str(row.get('NOM_AGENCIA', 'N/A')).strip(),
                              'monto_capital': cap,
                              'saldo_deuda': tot,
                              'dir_casa': str(row.get('DIR_CASA', '')).strip(),
                              'distrito': str(row.get('DISTRITO', '')).strip(),
                              'nom_conyuge': str(row.get('NOM_CONYUGE', '')).strip(),
                              'nom_aval': str(row.get('NOM_AVAL', '')).strip(),
                              'tlf_celular_aval': str(row.get('TLF_CELULAR_AVAL', '')).strip(),
                              'nom_conyuge_aval': str(row.get('NOM_CONYUGE_AVAL', '')).strip(),
                              'rango_dias_mora': str(row.get('RANGO_DIAS_MORA', '')).strip(),
                              'ultimo_dia_pago': ultimo_dia_pago_val,
                              # Datos aval extendidos
                              'aval_direccion': str(row.get('DIR_CASA_AVAL', '')).strip(),
                              'aval_distrito': str(row.get('DISTRITO_AVAL', '')).strip(),
                              # Datos judiciales
                              'expediente': str(row.get('EXPEDIENTE', '')).strip(),
                              'juzgado': str(row.get('JUZGADO', '')).strip(),
                              'condicion': str(row.get('CONDICION', row.get('SITUACION', ''))).strip(),
                              'referencia': str(row.get('REFERENCIA', '')).strip(),
                              'proceso': str(row.get('PROCESO_JUDICIAL', '')).strip(),
                              'fec_demanda': safe_date(row.get('FEC_DEMANDA', '')),
                              'monto_demanda': Decimal(str(row.get('MONTO_DEMANDA', '0')).strip()) if str(row.get('MONTO_DEMANDA', '0')).strip() not in ('', 'nan', 'None') else None,
                              'ingreso_judicial': safe_date(row.get('FEC_INGRESO_JUDICIAL', '')),
                              # Campos requeridos por _CAMPO_MAP (app móvil)
                              'producto': str(row.get('PRODUCTO', '')).strip(),
                              'nmes': str(row.get('NMES', '')).strip(),
                              'departamento': str(row.get('DEPARTAMENTO', '')).strip(),
                              'provincia': str(row.get('PROVINCIA', '')).strip(),
                              'dir_negocio': str(row.get('DIR_NEGOCIO', '')).strip(),
                              'imp_recup': Decimal(str(row.get('IMP_RECUP', '0')).strip()) if str(row.get('IMP_RECUP', '0')).strip() not in ('', 'nan', 'None') else None,
                              'imp_capital_rec': Decimal(str(row.get('IMP_CAPITAL_REC', '0')).strip()) if str(row.get('IMP_CAPITAL_REC', '0')).strip() not in ('', 'nan', 'None') else None,
                              'num_doc_conyuge': str(row.get('NUM_DOC_CONYUGE', '')).strip(),
                              'num_doc_aval': str(row.get('NUM_DOC_AVAL', '')).strip(),
                              'zona': str(row.get('ZONA', '')).strip(),
                              'negociacion': str(row.get('NEGOCIACION', '')).strip(),
                          }
                      )

            # Eliminar clientes que NO vienen en el nuevo Excel
            eliminados, _ = Deudor.objects.exclude(documento__in=dni_en_excel).delete()

            resumen = f"{len(dni_en_excel)} clientes cargados/actualizados. {eliminados} eliminados (no estaban en el archivo)."
            if col_fecha:
                mensajes = f"¡Cartera sincronizada! {resumen} Columna de fecha: '{col_fecha}'"
            else:
                mensajes = f"¡Cartera sincronizada! {resumen} ADVERTENCIA: No se encontró columna de fecha de pago."
        except Exception as e:
            mensajes = f"Error al procesar el Excel: {e}"
    return render(request, 'cobranza/subir_excel.html', {'mensajes': mensajes, 'columnas_detectadas': columnas_detectadas})

# --- FUNCIÓN BASE: OBTENER QUERYSET UNIFICADO PARA BANDEJA ---
def obtener_queryset_bandeja(request, usuario, usar_sesion_fallback=False, forzar_asignaciones=False):
    q = request.GET.get('q', '') 
    cartera_filtro = request.GET.get('cartera', '')
    agencia_filtro = request.GET.get('agencia', '')
    fecha_pago_desde = request.GET.get('fecha_pago_desde', '')
    fecha_pago_hasta = request.GET.get('fecha_pago_hasta', '')
    rango_deuda = request.GET.get('rango_deuda', '')
    orden = request.GET.get('orden', '')

    if usar_sesion_fallback and not any([q, cartera_filtro, agencia_filtro, fecha_pago_desde, fecha_pago_hasta, rango_deuda, orden]):
        filtros_sesion = request.session.get('filtros_bandeja', {})
        q = filtros_sesion.get('q', '')
        cartera_filtro = filtros_sesion.get('cartera', '')
        agencia_filtro = filtros_sesion.get('agencia', '')
        fecha_pago_desde = filtros_sesion.get('fecha_pago_desde', '')
        fecha_pago_hasta = filtros_sesion.get('fecha_pago_hasta', '')
        rango_deuda = filtros_sesion.get('rango_deuda', '')
        orden = filtros_sesion.get('orden', '')

    deudores = Deudor.objects.annotate(ultima_llamada=Max('gestion__fecha'))

    # Si es modo agente o no es gerente, ocultar los que ya gestionó hoy
    if forzar_asignaciones or not es_gerente(usuario):
        deudores = aplicar_asignaciones_de_gestor(deudores, usuario)
        # Ocultar los que el agente ya gestionó el día de hoy
        hoy_date = timezone.now().date()
        deudores = deudores.exclude(
            gestion__gestor=usuario,
            gestion__fecha__date=hoy_date
        )

    if q: 
        deudores = deudores.filter(
            Q(documento__icontains=q) | 
            Q(nombre_completo__icontains=q) |
            Q(telefono_principal__icontains=q) |
            Q(tlf_celular_aval__icontains=q) |
            Q(telefonoextra__numero__icontains=q)
        ).distinct()
    if cartera_filtro: 
        deudores = deudores.filter(cartera=cartera_filtro)
    if agencia_filtro: 
        deudores = deudores.filter(agencia=agencia_filtro)
    if fecha_pago_desde:
        from django.utils.dateparse import parse_date
        d = parse_date(fecha_pago_desde)
        if d: deudores = deudores.filter(ultimo_dia_pago__gte=d)
    if fecha_pago_hasta:
        from django.utils.dateparse import parse_date
        d = parse_date(fecha_pago_hasta)
        if d: deudores = deudores.filter(ultimo_dia_pago__lte=d)
    if rango_deuda == '0-1000':
        deudores = deudores.filter(saldo_deuda__gte=0, saldo_deuda__lt=1000)
    elif rango_deuda == '1000-5000':
        deudores = deudores.filter(saldo_deuda__gte=1000, saldo_deuda__lt=5000)
    elif rango_deuda == '5000-10000':
        deudores = deudores.filter(saldo_deuda__gte=5000, saldo_deuda__lt=10000)
    elif rango_deuda == '10000+':
        deudores = deudores.filter(saldo_deuda__gte=10000)

    hoy = timezone.now().date()

    ultima_promesa_subquery = Gestion.objects.filter(
        deudor=OuterRef('pk'),
        resultado__icontains='PROMESA',
        fecha_promesa__gte=hoy,
    ).order_by('-fecha_promesa').values('fecha_promesa')[:1]

    # Fecha de creación de la promesa vencida más reciente del deudor
    ultima_promesa_vencida_fecha_subq = Gestion.objects.filter(
        deudor=OuterRef('pk'),
        resultado__icontains='PROMESA',
        fecha_promesa__lt=hoy,
    ).order_by('-fecha').values('fecha')[:1]

    # ¿Existe un PAGÓ registrado después de esa promesa vencida?
    pago_tras_promesa_subq = Gestion.objects.filter(
        deudor=OuterRef('pk'),
        resultado__icontains='PAGÓ',
        fecha__gt=Subquery(
            Gestion.objects.filter(
                deudor=OuterRef(OuterRef('pk')),
                resultado__icontains='PROMESA',
                fecha_promesa__lt=hoy,
            ).order_by('-fecha').values('fecha')[:1]
        ),
    ).values('id')[:1]

    deudores = deudores.annotate(
        ultima_promesa_fecha=Subquery(ultima_promesa_subquery),
        ultima_promesa_vencida_fecha=Subquery(ultima_promesa_vencida_fecha_subq),
        pago_tras_promesa=Subquery(pago_tras_promesa_subq),
    )

    hoy_datetime = timezone.now()
    hace_3_dias = hoy_datetime - timedelta(days=3)
    hace_1_dia = hoy_datetime - timedelta(days=1)

    prioridad_annotation = Case(
        When(ultima_promesa_vencida_fecha__isnull=False, pago_tras_promesa__isnull=True, then=Value(0)),
        When(ultima_llamada__isnull=True, then=Value(1)),
        When(ultima_llamada__lte=hace_3_dias, then=Value(1)),
        When(ultima_llamada__lte=hace_1_dia, then=Value(2)),
        default=Value(3),
        output_field=IntegerField()
    )

    deudores = deudores.annotate(prioridad=prioridad_annotation)

    if orden == 'nombre': deudores = deudores.order_by('nombre_completo')
    elif orden == '-nombre': deudores = deudores.order_by('-nombre_completo')
    elif orden == 'agencia': deudores = deudores.order_by('agencia')
    elif orden == '-agencia': deudores = deudores.order_by('-agencia')
    elif orden == 'ultimo_dia_pago': deudores = deudores.order_by(F('ultimo_dia_pago').asc(nulls_last=True))
    elif orden == '-ultimo_dia_pago': deudores = deudores.order_by(F('ultimo_dia_pago').desc(nulls_last=True))
    elif orden == 'deuda_total': deudores = deudores.order_by(F('saldo_deuda').asc(nulls_last=True))
    elif orden == '-deuda_total': deudores = deudores.order_by(F('saldo_deuda').desc(nulls_last=True))
    else:
        deudores = deudores.order_by('prioridad', F('ultima_llamada').asc(nulls_first=True))

    filtros = {
        'q': q, 'cartera': cartera_filtro, 'agencia': agencia_filtro,
        'fecha_pago_desde': fecha_pago_desde, 'fecha_pago_hasta': fecha_pago_hasta,
        'rango_deuda': rango_deuda, 'orden': orden
    }
    return deudores, filtros

# --- FUNCIÓN AUXILIAR PARA OBTENER LISTA DE DEUDORES CON FILTROS Y ASIGNACIÓN ---
def obtener_lista_deudores_filtrados(request, usuario=None, ids_seleccionados=None):
    deudores, _ = obtener_queryset_bandeja(request, usuario, usar_sesion_fallback=True)
    if ids_seleccionados:
        return list(deudores.filter(id__in=ids_seleccionados).values_list('id', flat=True))
    return list(deudores.values_list('id', flat=True))

# --- BANDEJA DE TRABAJO ---
@login_required
def bandeja_gestor(request):
    es_gerente_flag = es_gerente(request.user)
    modo_agente = es_gerente_flag and puede_usar_modo_agente(request.user) and request.GET.get('modo') == 'agente'
    
    # 1. Obtener el QuerySet delegado a Base de Datos
    deudores, filtros = obtener_queryset_bandeja(
        request,
        request.user,
        usar_sesion_fallback=False,
        forzar_asignaciones=modo_agente and not modo_agente_ve_todos_los_clientes(request.user)
    )
    
    # 2. Obtener opciones para los Combos (filtros visuales)
    if (es_gerente_flag and not modo_agente) or (modo_agente and modo_agente_ve_todos_los_clientes(request.user)):
        deudores_base = Deudor.objects.all()
    else:
        deudores_base = aplicar_asignaciones_de_gestor(Deudor.objects.all(), request.user)

    carteras_crudas = deudores_base.values_list('cartera', flat=True).distinct()
    agencias_crudas = deudores_base.values_list('agencia', flat=True).distinct()
    lista_carteras = sorted([str(c) for c in carteras_crudas if c and str(c).strip() != ''])
    lista_agencias = sorted([str(a) for a in agencias_crudas if a and str(a).strip() != ''])

    pares = deudores_base.values_list('cartera', 'agencia').distinct()
    mapa_cartera_agencias = {}
    for cartera_val, agencia_val in pares:
        c = str(cartera_val).strip() if cartera_val else ''
        a = str(agencia_val).strip() if agencia_val else ''
        if c and a:
            mapa_cartera_agencias.setdefault(c, set()).add(a)
    mapa_cartera_agencias = {k: sorted(v) for k, v in mapa_cartera_agencias.items()}

    # 3. Paginar Directamente (solo ejecuta COUNT y FETCH 20 en Postgres)
    paginator = Paginator(deudores, 20)
    page_number = request.GET.get('page')
    deudores_paginados = paginator.get_page(page_number)
    
    # 4. Establecer atributos visuales solo a los 20 objetos cargados
    for d in deudores_paginados:
        if getattr(d, 'prioridad', 3) == 1:
            d.color = 'rojo'
        elif getattr(d, 'prioridad', 3) == 2:
            d.color = 'amarillo'
        elif getattr(d, 'prioridad', 3) == 3:
            d.color = 'verde'
        else: # Prioridad 0
            if not d.ultima_llamada: 
                d.color = "rojo"
            else:
                dias = (timezone.now() - d.ultima_llamada).days
                d.color = "rojo" if dias >= 3 else ("amarillo" if dias >= 1 else "verde")
        
        d.alerta_promesa = d.ultima_promesa_vencida_fecha is not None and d.pago_tras_promesa is None
        d.proxima_promesa = d.ultima_promesa_fecha

    # 5. Guardar sesión para navegación (< Anterior / Siguiente >)
    # Limitar a 2000 IDs para evitar sesiones enormes en la BD
    MAX_NAV_IDS = 2000
    lista_ids_filtrados = list(deudores.values_list('id', flat=True)[:MAX_NAV_IDS])
    request.session['lista_ids_navegacion'] = lista_ids_filtrados
    
    filtros['page'] = page_number
    filtros['modo'] = 'agente' if modo_agente else ''
    request.session['filtros_bandeja'] = filtros
    
    if request.session.get('alerta_pago_mostrada', False):
        alerta_pago_proximo = []
    else:
        alerta_pago_proximo = obtener_alertas_pago_proximo(request.user)
        request.session['alerta_pago_mostrada'] = True

    return render(request, 'cobranza/bandeja.html', {
        'deudores': deudores_paginados,
        'lista_carteras': lista_carteras,
        'lista_agencias': lista_agencias,
        'alerta_pago_proximo': alerta_pago_proximo,
        'alerta_pago_proximo_count': len(alerta_pago_proximo),
        'mapa_cartera_agencias': json.dumps(mapa_cartera_agencias),
        'q': filtros['q'],
        'cartera_filtro': filtros['cartera'],
        'agencia_filtro': filtros['agencia'],
        'fecha_pago_desde': filtros['fecha_pago_desde'],
        'fecha_pago_hasta': filtros['fecha_pago_hasta'],
        'rango_deuda': filtros['rango_deuda'],
        'orden_actual': filtros['orden'],
        'es_gerente': es_gerente_flag,
        'modo_bandeja_agente': modo_agente,
        'puede_modo_agente': puede_usar_modo_agente(request.user),
    })


# --- ASIGNACIÓN DE CARTERAS Y AGENCIAS ---
@login_required
@user_passes_test(es_gerente)
def asignar_carteras(request):
    gestores = User.objects.exclude(groups__name='GERENTE').exclude(is_superuser=True)
    supervisores_agentes = User.objects.filter(username__in=SUPERVISORES_CON_BANDEJA_AGENTE)
    gestores = (gestores | supervisores_agentes).distinct().order_by('username')
    
    todas_carteras = Deudor.objects.values_list('cartera', flat=True).distinct()
    todas_carteras = sorted([c for c in todas_carteras if c and str(c).strip() != ''])
    
    todas_agencias = Deudor.objects.values_list('agencia', flat=True).distinct()
    todas_agencias = sorted([a for a in todas_agencias if a and str(a).strip() != ''])
    
    asignaciones = AsignacionCartera.objects.all()
    
    carteras_por_gestor = {}
    agencias_por_gestor = {}
    for gestor in gestores:
        carteras_por_gestor[gestor.id] = set(
            asignaciones.filter(gestor=gestor, tipo='cartera').values_list('valor', flat=True)
        )
        agencias_por_gestor[gestor.id] = set(
            asignaciones.filter(gestor=gestor, tipo='agencia').values_list('valor', flat=True)
        )
    
    if request.method == 'POST':
        AsignacionCartera.objects.all().delete()
        
        for gestor in gestores:
            carteras_seleccionadas = request.POST.getlist(f'carteras_{gestor.id}')
            for cartera in carteras_seleccionadas:
                if cartera:
                    AsignacionCartera.objects.create(
                        gestor=gestor, 
                        tipo='cartera', 
                        valor=cartera
                    )
        
        for gestor in gestores:
            agencias_seleccionadas = request.POST.getlist(f'agencias_{gestor.id}')
            for agencia in agencias_seleccionadas:
                if agencia:
                    AsignacionCartera.objects.create(
                        gestor=gestor, 
                        tipo='agencia', 
                        valor=agencia
                    )
        
        return redirect('asignar_carteras')
    
    return render(request, 'cobranza/asignar_carteras.html', {
        'gestores': gestores,
        'todas_carteras': todas_carteras,
        'todas_agencias': todas_agencias,
        'carteras_por_gestor': carteras_por_gestor,
        'agencias_por_gestor': agencias_por_gestor,
    })

@login_required
@user_passes_test(es_gerente)
def asignaciones_diarias(request):
    from django.utils.dateparse import parse_date

    gestores = User.objects.exclude(groups__name='GERENTE').exclude(is_superuser=True)
    supervisores_agentes = User.objects.filter(username__in=SUPERVISORES_CON_BANDEJA_AGENTE)
    gestores = (gestores | supervisores_agentes).distinct().order_by('username')

    hoy = timezone.now().date()
    fecha_texto = request.GET.get('fecha') or request.POST.get('fecha') or hoy.isoformat()
    fecha_seleccionada = parse_date(fecha_texto) or hoy
    gestor_id = request.GET.get('gestor') or request.POST.get('gestor') or ''
    q = (request.GET.get('q') or '').strip()
    cartera = (request.GET.get('cartera') or '').strip()
    agencia = (request.GET.get('agencia') or '').strip()
    fecha_pago_desde = (request.GET.get('fecha_pago_desde') or '').strip()
    fecha_pago_hasta = (request.GET.get('fecha_pago_hasta') or '').strip()
    condicion_negociacion = (request.GET.get('condicion_negociacion') or '').strip()
    orden = (request.GET.get('orden') or '').strip()
    mensaje = request.session.pop('asignaciones_diarias_msg', '')
    tipo_mensaje = request.session.pop('asignaciones_diarias_msg_tipo', 'ok')

    if request.method == 'POST':
        accion = request.POST.get('accion')
        fecha_post = parse_date(request.POST.get('fecha', '')) or hoy
        gestor_post = request.POST.get('gestor', '').strip()
        redirect_params = urlencode({
            'fecha': fecha_post.isoformat(),
            'gestor': gestor_post,
            'q': request.POST.get('q', '').strip(),
            'cartera': request.POST.get('cartera', '').strip(),
            'agencia': request.POST.get('agencia', '').strip(),
            'fecha_pago_desde': request.POST.get('fecha_pago_desde', '').strip(),
            'fecha_pago_hasta': request.POST.get('fecha_pago_hasta', '').strip(),
            'condicion_negociacion': request.POST.get('condicion_negociacion', '').strip(),
            'orden': request.POST.get('orden', '').strip(),
        })

        if accion == 'asignar':
            ids_deudores = [int(i) for i in request.POST.getlist('deudor_ids') if str(i).isdigit()]
            gestor_obj = User.objects.filter(id=gestor_post).first() if gestor_post else None

            if not gestor_obj:
                request.session['asignaciones_diarias_msg'] = 'Seleccione un gestor antes de asignar.'
                request.session['asignaciones_diarias_msg_tipo'] = 'error'
            elif not ids_deudores:
                request.session['asignaciones_diarias_msg'] = 'Seleccione al menos un cliente para la asignacion diaria.'
                request.session['asignaciones_diarias_msg_tipo'] = 'error'
            else:
                existentes = set(
                    AsignacionDiaria.objects.filter(
                        gestor=gestor_obj,
                        fecha_asignada=fecha_post,
                        deudor_id__in=ids_deudores,
                    ).values_list('deudor_id', flat=True)
                )
                nuevos = [
                    AsignacionDiaria(gestor=gestor_obj, deudor_id=deudor_id, fecha_asignada=fecha_post)
                    for deudor_id in ids_deudores
                    if deudor_id not in existentes
                ]
                AsignacionDiaria.objects.bulk_create(nuevos)
                request.session['asignaciones_diarias_msg'] = f'{len(nuevos)} clientes asignados para {gestor_obj.username.upper()} el {fecha_post.strftime("%d/%m/%Y")}.'
                request.session['asignaciones_diarias_msg_tipo'] = 'ok'
        elif accion == 'eliminar':
            asignacion_id = request.POST.get('asignacion_id', '').strip()
            asignacion = AsignacionDiaria.objects.filter(id=asignacion_id).first() if asignacion_id.isdigit() else None
            if asignacion:
                gestor_nombre = asignacion.gestor.username.upper()
                cliente_nombre = asignacion.deudor.nombre_completo
                asignacion.delete()
                request.session['asignaciones_diarias_msg'] = f'Se quito la asignacion diaria de {cliente_nombre} para {gestor_nombre}.'
                request.session['asignaciones_diarias_msg_tipo'] = 'ok'

        return redirect(f"{reverse('asignaciones_diarias')}?{redirect_params}")

    deudores = Deudor.objects.all()
    if q:
        deudores = deudores.filter(
            Q(documento__icontains=q) |
            Q(nombre_completo__icontains=q) |
            Q(telefono_principal__icontains=q)
        )
    if cartera:
        deudores = deudores.filter(cartera=cartera)
    if agencia:
        deudores = deudores.filter(agencia=agencia)
    if fecha_pago_desde:
        fecha_pago_desde_val = parse_date(fecha_pago_desde)
        if fecha_pago_desde_val:
            deudores = deudores.filter(ultimo_dia_pago__gte=fecha_pago_desde_val)
    if fecha_pago_hasta:
        fecha_pago_hasta_val = parse_date(fecha_pago_hasta)
        if fecha_pago_hasta_val:
            deudores = deudores.filter(ultimo_dia_pago__lte=fecha_pago_hasta_val)
    if condicion_negociacion == 'si':
        deudores = deudores.exclude(condicion__isnull=True).exclude(condicion__exact='')
    elif condicion_negociacion == 'no':
        deudores = deudores.filter(Q(condicion__isnull=True) | Q(condicion__exact=''))
    if orden == 'nombre':
        deudores = deudores.order_by('nombre_completo')
    elif orden == '-nombre':
        deudores = deudores.order_by('-nombre_completo')
    elif orden == 'ultimo_pago':
        deudores = deudores.order_by(F('ultimo_dia_pago').asc(nulls_last=True), 'nombre_completo')
    elif orden == '-ultimo_pago':
        deudores = deudores.order_by(F('ultimo_dia_pago').desc(nulls_last=True), 'nombre_completo')
    else:
        deudores = deudores.order_by('-saldo_deuda', 'nombre_completo')

    paginator = Paginator(deudores, 30)
    page_number = request.GET.get('page')
    deudores_paginados = paginator.get_page(page_number)

    gestor_actual = User.objects.filter(id=gestor_id).first() if gestor_id else None
    ids_asignados_actuales = set()
    if gestor_actual:
        ids_asignados_actuales = set(
            AsignacionDiaria.objects.filter(
                gestor=gestor_actual,
                fecha_asignada=fecha_seleccionada,
            ).values_list('deudor_id', flat=True)
        )

    asignaciones_del_dia = AsignacionDiaria.objects.filter(
        fecha_asignada=fecha_seleccionada
    ).select_related('gestor', 'deudor')
    if gestor_actual:
        asignaciones_del_dia = asignaciones_del_dia.filter(gestor=gestor_actual)

    todas_carteras = Deudor.objects.values_list('cartera', flat=True).distinct()
    todas_carteras = sorted([c for c in todas_carteras if c and str(c).strip() != ''])
    todas_agencias = Deudor.objects.values_list('agencia', flat=True).distinct()
    todas_agencias = sorted([a for a in todas_agencias if a and str(a).strip() != ''])

    resumen_por_gestor = asignaciones_del_dia.values('gestor__username').annotate(total=Count('id')).order_by('-total', 'gestor__username')

    return render(request, 'cobranza/asignaciones_diarias.html', {
        'es_gerente': True,
        'gestores': gestores,
        'fecha_seleccionada': fecha_seleccionada,
        'gestor_id': gestor_id,
        'q': q,
        'cartera_filtro': cartera,
        'agencia_filtro': agencia,
        'fecha_pago_desde': fecha_pago_desde,
        'fecha_pago_hasta': fecha_pago_hasta,
        'condicion_negociacion': condicion_negociacion,
        'orden_actual': orden,
        'todas_carteras': todas_carteras,
        'todas_agencias': todas_agencias,
        'deudores': deudores_paginados,
        'ids_asignados_actuales': ids_asignados_actuales,
        'asignaciones_del_dia': asignaciones_del_dia,
        'resumen_por_gestor': resumen_por_gestor,
        'mensaje': mensaje,
        'tipo_mensaje': tipo_mensaje,
    })

# --- FICHA DE GESTIÓN CON NAVEGACIÓN ---
@login_required
def registrar_gestion(request, deudor_id):
    deudor = get_object_or_404(Deudor, id=deudor_id)
    historial = Gestion.objects.filter(deudor=deudor).order_by('-fecha')
    telefonos_adicionales = TelefonoExtra.objects.filter(deudor=deudor)
    telefono_alerta = None
    nuevo_telefono_valor = ''
    desc_nuevo_telefono_valor = ''
    
    es_gerente_flag = es_gerente(request.user)
    
    lista_ids = request.session.get('lista_ids_navegacion', [])
    posicion_actual = -1
    cliente_anterior_id = None
    cliente_siguiente_id = None
    
    if lista_ids and deudor_id in lista_ids:
        posicion_actual = lista_ids.index(deudor_id)
        if posicion_actual > 0:
            cliente_anterior_id = lista_ids[posicion_actual - 1]
        if posicion_actual < len(lista_ids) - 1:
            cliente_siguiente_id = lista_ids[posicion_actual + 1]
    
    filtros = request.session.get('filtros_bandeja', {})
    params = []
    if filtros.get('q'): params.append(f"q={filtros['q']}")
    if filtros.get('cartera'): params.append(f"cartera={filtros['cartera']}")
    if filtros.get('agencia'): params.append(f"agencia={filtros['agencia']}")
    if filtros.get('fecha_pago_desde'): params.append(f"fecha_pago_desde={filtros['fecha_pago_desde']}")
    if filtros.get('fecha_pago_hasta'): params.append(f"fecha_pago_hasta={filtros['fecha_pago_hasta']}")
    if filtros.get('rango_deuda'): params.append(f"rango_deuda={filtros['rango_deuda']}")
    if filtros.get('page'): params.append(f"page={filtros['page']}")
    if filtros.get('orden'): params.append(f"orden={filtros['orden']}")
    if filtros.get('modo'): params.append(f"modo={filtros['modo']}")
    
    parametros_url = '&'.join(params) if params else ''
    
    todos_los_numeros = []
    lista_contactos = []
    msg_base = f"Hola {deudor.nombre_completo}, de P&P Jurídicas."
    conteo_numeros_cliente = {}

    def registrar_numero_cliente(numero):
        numero_normalizado = normalizar_telefono(numero)
        if not numero_normalizado:
            return
        conteo_numeros_cliente[numero_normalizado] = conteo_numeros_cliente.get(numero_normalizado, 0) + 1

    if deudor.telefono_principal and deudor.telefono_principal != 'Sin número':
        registrar_numero_cliente(deudor.telefono_principal)

    if deudor.tlf_celular_aval:
        registrar_numero_cliente(deudor.tlf_celular_aval)

    for tel in telefonos_adicionales:
        registrar_numero_cliente(tel.numero)
    
    if deudor.telefono_principal and deudor.telefono_principal != 'Sin número':
        todos_los_numeros.append(deudor.telefono_principal)
        lista_contactos.append({
            'numero': deudor.telefono_principal, 'tipo': 'TITULAR',
            'link_call': f"tel:{deudor.telefono_principal}",
            'link_wa': f"https://web.whatsapp.com/send?phone=51{deudor.telefono_principal}&text={urllib.parse.quote(msg_base)}",
            'puede_eliminar': puede_depurar_telefonos(request.user) and numero_repetido_en_cliente(conteo_numeros_cliente, deudor.telefono_principal),
            'url_eliminar': reverse('eliminar_contacto_cliente', args=[deudor.id, 'titular']),
        })
    
    if deudor.tlf_celular_aval:
        todos_los_numeros.append(deudor.tlf_celular_aval)
        lista_contactos.append({
            'numero': deudor.tlf_celular_aval, 'tipo': 'AVAL',
            'link_call': f"tel:{deudor.tlf_celular_aval}",
            'link_wa': f"https://web.whatsapp.com/send?phone=51{deudor.tlf_celular_aval}&text={urllib.parse.quote(msg_base)}",
            'puede_eliminar': puede_depurar_telefonos(request.user) and numero_repetido_en_cliente(conteo_numeros_cliente, deudor.tlf_celular_aval),
            'url_eliminar': reverse('eliminar_contacto_cliente', args=[deudor.id, 'aval']),
        })

    for tel in telefonos_adicionales:
        todos_los_numeros.append(tel.numero)
        lista_contactos.append({
            'numero': tel.numero, 'tipo': tel.descripcion.upper(),
            'link_call': f"tel:{tel.numero}",
            'link_wa': f"https://web.whatsapp.com/send?phone=51{tel.numero}&text={urllib.parse.quote(msg_base)}",
            'puede_eliminar': puede_depurar_telefonos(request.user) and numero_repetido_en_cliente(conteo_numeros_cliente, tel.numero),
            'url_eliminar': reverse('eliminar_telefono_extra', args=[tel.id]),
        })

    if request.method == 'POST':
        if 'guardar_nuevo_telefono' in request.POST:
            nuevo_tel = request.POST.get('nuevo_telefono', '').strip()
            desc_tel = request.POST.get('desc_nuevo_telefono', 'ADICIONAL').strip() or 'ADICIONAL'
            nuevo_telefono_valor = nuevo_tel
            desc_nuevo_telefono_valor = desc_tel
            telefono_duplicado = buscar_telefono_duplicado(deudor, normalizar_telefono(nuevo_tel))
            if nuevo_tel and not telefono_duplicado:
                TelefonoExtra.objects.create(deudor=deudor, numero=nuevo_tel, descripcion=desc_tel)
                Gestion.objects.create(
                    deudor=deudor,
                    gestor=request.user,
                    resultado="NUEVO TELÉFONO",
                    observacion=f"Se registró un nuevo número de contacto: {nuevo_tel} ({desc_tel})",
                    monto_pago=Decimal('0')
                )
                url = reverse('registrar_gestion', args=[deudor.id])
                if parametros_url:
                    url = f"{url}?{parametros_url}"
                return redirect(url)

            if telefono_duplicado:
                telefono_alerta = telefono_duplicado
            
        else:
            resultado_principal = request.POST.get('resultado_principal')
            sub_resultado = request.POST.get('sub_resultado')
            
            if resultado_principal == 'CONTACTO CON TITULAR' and sub_resultado:
                resultado_final = f"{resultado_principal} - {sub_resultado}"
            else:
                resultado_final = resultado_principal

            tel_contactado = request.POST.get('telefono_contactado', 'Sin número')
            monto_str = request.POST.get('monto_pago', '0')
            monto_decimal = Decimal(monto_str) if (monto_str and monto_str != '0') else Decimal('0')
            
            obs_final = f"[Tel: {tel_contactado}] " + request.POST.get('observacion', '')
            
            Gestion.objects.create(
                deudor=deudor, 
                gestor=request.user, 
                resultado=resultado_final, 
                observacion=obs_final, 
                fecha_promesa=request.POST.get('fecha_promesa') or None,
                hora_promesa=request.POST.get('hora_promesa') or None,
                monto_pago=monto_decimal
            )
            
            # --- MARCAR SEGUIMIENTOS COMO COMPLETADOS AUTOMÁTICAMENTE ---
            SeguimientoProgramado.objects.filter(
                deudor=deudor, 
                gestor=request.user, 
                completado=False
            ).update(completado=True)
            
            if "PAGO" in resultado_final and monto_decimal > 0:
                if monto_decimal > deudor.saldo_deuda:
                    monto_decimal = deudor.saldo_deuda
                deudor.saldo_deuda -= monto_decimal
                deudor.save()

            # --- GUARDAR SEGUIMIENTO PROGRAMADO (si el gestor lo marcó) ---
            seguimiento_creado = False
            if request.POST.get('programar_seguimiento'):
                fecha_seg_raw = request.POST.get('fecha_seguimiento', '').strip()
                motivo_seg = request.POST.get('motivo_seguimiento', '').strip() or resultado_final
                if fecha_seg_raw:
                    from django.utils.dateparse import parse_date
                    fecha_seg = parse_date(fecha_seg_raw)
                    if fecha_seg:
                        SeguimientoProgramado.objects.create(
                            deudor=deudor,
                            gestor=request.user,
                            fecha_programada=fecha_seg,
                            hora_programada=request.POST.get('hora_seguimiento') or None,
                            motivo=motivo_seg[:200],
                        )
                        seguimiento_creado = True
                        
            # --- AUTO-PROGRAMAR SEGUIMIENTO SI ES PROMESA DE PAGO ---
            if not seguimiento_creado and "PROMESA" in resultado_final.upper() and request.POST.get('fecha_promesa'):
                fecha_prom_raw = request.POST.get('fecha_promesa', '').strip()
                hora_prom_raw = request.POST.get('hora_promesa', '').strip()
                if fecha_prom_raw:
                    from django.utils.dateparse import parse_date
                    fecha_prom = parse_date(fecha_prom_raw)
                    if fecha_prom:
                        SeguimientoProgramado.objects.create(
                            deudor=deudor,
                            gestor=request.user,
                            fecha_programada=fecha_prom,
                            hora_programada=hora_prom_raw or None,
                            motivo=f"Alerta automática: Verificar {resultado_final}",
                        )
            
            # --- NUEVA LÓGICA DE REDIRECCIÓN AL SIGUIENTE ---
            siguiente_id_post = request.POST.get('siguiente_id')

            if siguiente_id_post:
                # Si el HTML nos mandó un ID siguiente, saltamos a ese cliente
                url = reverse('registrar_gestion', args=[siguiente_id_post])
            else:
                # Si no hay siguiente (es el último), volvemos a la bandeja
                url = reverse('bandeja_gestor')

            if parametros_url:
                url = f"{url}?{parametros_url}"
            
            return redirect(url)

    cuentas_asociadas = []
    if deudor.documento and deudor.documento.strip():
        cuentas_asociadas = list(Deudor.objects.filter(documento=deudor.documento).order_by('id'))

    return render(request, 'cobranza/gestionar.html', {
        'deudor': deudor, 
        'historial': historial, 
        'lista_contactos': lista_contactos, 
        'todos_los_numeros': todos_los_numeros, 
        'es_gerente': es_gerente_flag,
        'cliente_anterior_id': cliente_anterior_id,
        'cliente_siguiente_id': cliente_siguiente_id,
        'posicion_actual': posicion_actual,
        'total_clientes': len(lista_ids),
        'parametros_url': parametros_url,
        'telefono_alerta': telefono_alerta,
        'nuevo_telefono_valor': nuevo_telefono_valor,
        'desc_nuevo_telefono_valor': desc_nuevo_telefono_valor,
        'puede_depurar_telefonos': puede_depurar_telefonos(request.user),
        'cuentas_asociadas': cuentas_asociadas,
    })

# --- ELIMINAR CLIENTE ---
@login_required
@require_http_methods(["POST"])
def eliminar_cliente(request, deudor_id):
    if not es_gerente(request.user):
        return HttpResponse("Acceso Denegado. Solo la Gerencia puede eliminar registros.", status=403)
    
    deudor = get_object_or_404(Deudor, id=deudor_id)
    if request.method == 'POST':
        deudor.delete()
        filtros = request.session.get('filtros_bandeja', {})
        url = reverse('bandeja_gestor')
        params = []
        
        if filtros.get('q'): params.append(f"q={filtros['q']}")
        if filtros.get('cartera'): params.append(f"cartera={filtros['cartera']}")
        if filtros.get('agencia'): params.append(f"agencia={filtros['agencia']}")
        if filtros.get('mora'): params.append(f"rango_dias_mora={filtros['mora']}")
        if filtros.get('orden'): params.append(f"orden={filtros['orden']}")
        if filtros.get('modo'): params.append(f"modo={filtros['modo']}")
        
        if params:
            url = f"{url}?{'&'.join(params)}"
        
        return redirect(url)
    return redirect('registrar_gestion', deudor_id=deudor.id)


# --- BUSCAR POR DNI ---
@login_required
def buscar_por_dni(request, dni):
    deudor = get_object_or_404(Deudor, documento=dni)
    return redirect('registrar_gestion', deudor_id=deudor.id)


# --- CARGA MASIVA DE TELÉFONOS ---
@login_required
@user_passes_test(es_gerente)
def cargar_telefonos(request):
    mensajes = []
    errores = []
    exitosos = 0
    fallidos = 0
    repetidos = 0
    
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        try:
            archivo = request.FILES['archivo_excel']
            df = pd.read_excel(archivo, dtype=str).fillna('')
            
            columnas_requeridas = ['DNI', 'TELEFONO']
            for col in columnas_requeridas:
                if col not in df.columns:
                    return render(request, 'cobranza/cargar_telefonos.html', {
                        'mensajes': f"Error: El archivo debe tener la columna '{col}'",
                        'exitosos': 0,
                        'fallidos': 0,
                        'repetidos': 0,
                        'errores': []
                    })
            
            for index, row in df.iterrows():
                dni = str(row.get('DNI', '')).strip()
                telefono = str(row.get('TELEFONO', '')).strip()
                descripcion = str(row.get('DESCRIPCION', 'ADICIONAL')).strip()
                
                if not dni:
                    errores.append(f"Fila {index+2}: DNI vacío")
                    fallidos += 1
                    continue
                
                deudores = Deudor.objects.filter(documento=dni)
                if not deudores.exists():
                    errores.append(f"Fila {index+2}: DNI {dni} no encontrado en la base de datos")
                    fallidos += 1
                    continue
                deudor = deudores.first()
                
                telefono_limpio = ''.join(filter(str.isdigit, telefono))
                if len(telefono_limpio) != 9:
                    errores.append(f"Fila {index+2}: Teléfono {telefono} no es válido (debe tener 9 dígitos)")
                    fallidos += 1
                    continue
                
                duplicado_msg = buscar_telefono_duplicado(deudor, telefono_limpio)
                if duplicado_msg:
                    errores.append(f"Fila {index+2}: {duplicado_msg}")
                    fallidos += 1
                    repetidos += 1
                    continue
                
                TelefonoExtra.objects.create(
                    deudor=deudor,
                    numero=telefono_limpio,
                    descripcion=descripcion[:50]
                )
                exitosos += 1
            
            mensajes = (
                f"Proceso completado: {exitosos} teléfonos cargados correctamente, "
                f"{repetidos} rechazados por repetidos y {fallidos - repetidos} fallidos por otros motivos."
            )
            
        except Exception as e:
            mensajes = f"Error al procesar el archivo: {e}"
    
    return render(request, 'cobranza/cargar_telefonos.html', {
        'mensajes': mensajes,
        'exitosos': exitosos,
        'fallidos': fallidos,
        'repetidos': repetidos,
        'errores': errores[:20]
    })

@login_required
def subir_gestiones_masivas(request):
    if request.user.username != 'JPAREDES' and not request.user.is_superuser:
        return HttpResponse("Acceso Denegado. Solo JPAREDES puede realizar esta acción.", status=403)

    mensajes = []
    exitosos = 0
    fallidos = 0
    errores = []

    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        try:
            archivo = request.FILES['archivo_excel']
            df = pd.read_excel(archivo, dtype=str).fillna('')
            df.columns = df.columns.str.strip()
            
            columnas_requeridas = ['CUENTA', 'RESULTADO DE GESTIÓN', 'USUARIO']
            faltantes = [c for c in columnas_requeridas if c not in df.columns]
            if faltantes:
                return render(request, 'cobranza/subir_gestiones_masivas.html', {
                    'mensajes': f"Error: Faltan las columnas requeridas: {', '.join(faltantes)}",
                    'errores': []
                })

            for index, row in df.iterrows():
                cuenta = str(row.get('CUENTA', '')).strip()
                resultado_gestion = str(row.get('RESULTADO DE GESTIÓN', '')).strip()
                usuario_str = str(row.get('USUARIO', '')).strip()
                
                if not cuenta or not resultado_gestion:
                    errores.append(f"Fila {index+2}: Falta CUENTA o RESULTADO DE GESTIÓN")
                    fallidos += 1
                    continue
                
                deudor = Deudor.objects.filter(cuenta=cuenta).first()
                if not deudor:
                    errores.append(f"Fila {index+2}: Deudor no encontrado con cuenta {cuenta}")
                    fallidos += 1
                    continue
                
                gestor = None
                if usuario_str:
                    gestor = User.objects.filter(username__iexact=usuario_str).first()
                if not gestor:
                    gestor = request.user 

                Gestion.objects.create(
                    deudor=deudor,
                    gestor=gestor,
                    resultado="CARGA MASIVA",
                    observacion=resultado_gestion,
                    monto_pago=Decimal('0')
                )
                
                exitosos += 1
                
            mensajes = f"Proceso completado: {exitosos} gestiones subidas correctamente, {fallidos} fallidas."
            
        except Exception as e:
            mensajes = f"Error al procesar el archivo: {e}"

    return render(request, 'cobranza/subir_gestiones_masivas.html', {
        'mensajes': mensajes,
        'exitosos': exitosos,
        'fallidos': fallidos,
        'errores': errores[:30]
    })



from django.views.decorators.http import require_POST

# --- RUTA SECRETA: ELIMINAR GESTIÓN (SOLO GERENTES) ---
@login_required
@require_POST
def eliminar_gestion(request, gestion_id):
    # 1. Bloqueo de seguridad: Si no es gerente, lo rechaza
    if not es_gerente(request.user):
        return HttpResponse("Acceso Denegado. Acción exclusiva para Gerencia.", status=403)
    
    # 2. Busca la gestión exacta en la base de datos
    gestion = get_object_or_404(Gestion, id=gestion_id)
    
    # 3. Guardamos el ID del deudor para saber a qué pantalla regresar
    deudor_id = gestion.deudor.id
    
    # 4. Eliminamos el registro para siempre
    gestion.delete()
    
    # 5. Redirigimos de vuelta a la ficha del cliente
    return redirect('registrar_gestion', deudor_id=deudor_id)

@login_required
@require_POST
def eliminar_contacto_cliente(request, deudor_id, tipo_contacto):
    if not puede_depurar_telefonos(request.user):
        return HttpResponse("Acceso Denegado. Accion exclusiva para JPAREDES.", status=403)

    deudor = get_object_or_404(Deudor, id=deudor_id)
    parametros_url = request.POST.get('parametros_url', '').strip()

    if tipo_contacto == 'titular':
        numero = deudor.telefono_principal
        deudor.telefono_principal = ''
        etiqueta = 'telefono titular'
    elif tipo_contacto == 'aval':
        numero = deudor.tlf_celular_aval
        deudor.tlf_celular_aval = ''
        etiqueta = 'telefono aval'
    else:
        return HttpResponse("Tipo de contacto no valido.", status=400)

    deudor.save(update_fields=['telefono_principal', 'tlf_celular_aval'])
    Gestion.objects.create(
        deudor=deudor,
        gestor=request.user,
        resultado="TELÉFONO ELIMINADO",
        observacion=f"JPAREDES eliminó el {etiqueta}: {numero}.",
        monto_pago=Decimal('0')
    )

    url = reverse('registrar_gestion', args=[deudor.id])
    if parametros_url:
        url = f"{url}?{parametros_url}"
    return redirect(url)

@login_required
@require_POST
def eliminar_telefono_extra(request, telefono_id):
    if not puede_depurar_telefonos(request.user):
        return HttpResponse("Acceso Denegado. Accion exclusiva para JPAREDES.", status=403)

    telefono = get_object_or_404(TelefonoExtra.objects.select_related('deudor'), id=telefono_id)
    deudor = telefono.deudor
    numero = telefono.numero
    descripcion = telefono.descripcion
    parametros_url = request.POST.get('parametros_url', '').strip()

    telefono.delete()
    Gestion.objects.create(
        deudor=deudor,
        gestor=request.user,
        resultado="TELÉFONO ELIMINADO",
        observacion=f"JPAREDES eliminó el teléfono manual {numero} ({descripcion}).",
        monto_pago=Decimal('0')
    )

    url = reverse('registrar_gestion', args=[deudor.id])
    if parametros_url:
        url = f"{url}?{parametros_url}"
    return redirect(url)

# --- MÓDULO: TELEFONÍA ZADARMA (SINCRONIZADO) ---










@login_required
def webphone_popup(request):
    return render(request, 'cobranza/webphone.html')

