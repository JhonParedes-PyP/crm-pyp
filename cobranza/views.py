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
from .models import Deudor, Gestion, TelefonoExtra, AsignacionCartera, CampanaAsterisk, DetalleCampanaAsterisk, SeguimientoProgramado

from django.db import models
from django.db.models import Q, Sum, Count, Max, OuterRef, Subquery, Case, When, Value, IntegerField, F
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
@require_http_methods(["GET", "POST"])
def salir_sistema(request):
    logout(request)
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
                    Deudor.objects.update_or_create(
                        documento=documento_val,
                        defaults={
                            'cartera': str(row.get('CARTERA', 'GENERAL')).strip(),
                            'nombre_completo': str(row.get('NOM_CLI', 'SIN NOMBRE')).strip(),
                            'telefono_principal': str(row.get('TLF_CELULAR_CLIENTE', '')).strip(),
                            'cuenta': str(row.get('COD_CREDITO', 'N/A')).strip(),
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
def obtener_queryset_bandeja(request, usuario, usar_sesion_fallback=False):
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

    if not es_gerente(usuario):
        asignaciones = AsignacionCartera.objects.filter(gestor=usuario)
        carteras_asignadas = asignaciones.filter(tipo='cartera').values_list('valor', flat=True)
        agencias_asignadas = asignaciones.filter(tipo='agencia').values_list('valor', flat=True)
        
        condiciones = Q()
        if carteras_asignadas.exists():
            condiciones |= Q(cartera__in=carteras_asignadas)
        if agencias_asignadas.exists():
            condiciones |= Q(agencia__in=agencias_asignadas)
        
        if condiciones:
            deudores = deudores.filter(condiciones)
        else:
            deudores = deudores.none()

    if q: 
        deudores = deudores.filter(Q(documento__icontains=q) | Q(nombre_completo__icontains=q))
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
    ).exclude(
        deudor__gestion__resultado__icontains='PAGO',
        deudor__gestion__fecha__gt=models.F('fecha')
    ).order_by('-fecha_promesa').values('fecha_promesa')[:1]
    
    promesa_vencida_subquery = Gestion.objects.filter(
        deudor=OuterRef('pk'),
        resultado__icontains='PROMESA',
        fecha_promesa__lt=hoy,
    ).exclude(
        deudor__gestion__resultado__icontains='PAGO',
        deudor__gestion__fecha__gt=models.F('fecha')
    ).values('id')[:1]
    
    deudores = deudores.annotate(
        ultima_promesa_fecha=Subquery(ultima_promesa_subquery),
        tiene_promesa_vencida=Subquery(promesa_vencida_subquery)
    )

    hoy_datetime = timezone.now()
    hace_3_dias = hoy_datetime - timedelta(days=3)
    hace_1_dia = hoy_datetime - timedelta(days=1)

    prioridad_annotation = Case(
        When(tiene_promesa_vencida__isnull=False, then=Value(0)),
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
    
    # 1. Obtener el QuerySet delegado a Base de Datos
    deudores, filtros = obtener_queryset_bandeja(request, request.user, usar_sesion_fallback=False)
    
    # 2. Obtener opciones para los Combos (filtros visuales)
    if es_gerente_flag:
        deudores_base = Deudor.objects.all()
    else:
        asignaciones = AsignacionCartera.objects.filter(gestor=request.user)
        carteras_asignadas = asignaciones.filter(tipo='cartera').values_list('valor', flat=True)
        agencias_asignadas = asignaciones.filter(tipo='agencia').values_list('valor', flat=True)
        cond = Q()
        if carteras_asignadas.exists(): cond |= Q(cartera__in=carteras_asignadas)
        if agencias_asignadas.exists(): cond |= Q(agencia__in=agencias_asignadas)
        deudores_base = Deudor.objects.filter(cond) if cond else Deudor.objects.none()

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
        
        d.alerta_promesa = d.tiene_promesa_vencida is not None
        d.proxima_promesa = d.ultima_promesa_fecha

    # 5. Guardar sesión para navegación (< Anterior / Siguiente >)
    lista_ids_filtrados = list(deudores.values_list('id', flat=True))
    request.session['lista_ids_navegacion'] = lista_ids_filtrados
    
    filtros['page'] = page_number
    request.session['filtros_bandeja'] = filtros
    
    return render(request, 'cobranza/bandeja.html', {
        'deudores': deudores_paginados,
        'lista_carteras': lista_carteras,
        'lista_agencias': lista_agencias,
        'mapa_cartera_agencias': json.dumps(mapa_cartera_agencias),
        'q': filtros['q'],
        'cartera_filtro': filtros['cartera'],
        'agencia_filtro': filtros['agencia'],
        'fecha_pago_desde': filtros['fecha_pago_desde'],
        'fecha_pago_hasta': filtros['fecha_pago_hasta'],
        'rango_deuda': filtros['rango_deuda'],
        'orden_actual': filtros['orden'],
        'es_gerente': es_gerente_flag,
    })


# --- ASIGNACIÓN DE CARTERAS Y AGENCIAS ---
@login_required
@user_passes_test(es_gerente)
def asignar_carteras(request):
    gestores = User.objects.exclude(groups__name='GERENTE').exclude(is_superuser=True)
    
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

# --- FICHA DE GESTIÓN CON NAVEGACIÓN ---
@login_required
def registrar_gestion(request, deudor_id):
    deudor = get_object_or_404(Deudor, id=deudor_id)
    historial = Gestion.objects.filter(deudor=deudor).order_by('-fecha')
    telefonos_adicionales = TelefonoExtra.objects.filter(deudor=deudor)
    
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
    
    parametros_url = '&'.join(params) if params else ''
    
    todos_los_numeros = []
    lista_contactos = []
    msg_base = f"Hola {deudor.nombre_completo}, de P&P Jurídicas."
    
    if deudor.telefono_principal and deudor.telefono_principal != 'Sin número':
        todos_los_numeros.append(deudor.telefono_principal)
        lista_contactos.append({
            'numero': deudor.telefono_principal, 'tipo': 'TITULAR',
            'link_call': f"tel:{deudor.telefono_principal}",
            'link_wa': f"https://web.whatsapp.com/send?phone=51{deudor.telefono_principal}&text={urllib.parse.quote(msg_base)}"
        })
    
    if deudor.tlf_celular_aval:
        todos_los_numeros.append(deudor.tlf_celular_aval)
        lista_contactos.append({
            'numero': deudor.tlf_celular_aval, 'tipo': 'AVAL',
            'link_call': f"tel:{deudor.tlf_celular_aval}",
            'link_wa': f"https://web.whatsapp.com/send?phone=51{deudor.tlf_celular_aval}&text={urllib.parse.quote(msg_base)}"
        })

    for tel in telefonos_adicionales:
        todos_los_numeros.append(tel.numero)
        lista_contactos.append({
            'numero': tel.numero, 'tipo': tel.descripcion.upper(),
            'link_call': f"tel:{tel.numero}",
            'link_wa': f"https://web.whatsapp.com/send?phone=51{tel.numero}&text={urllib.parse.quote(msg_base)}"
        })

    if request.method == 'POST':
        if 'guardar_nuevo_telefono' in request.POST:
            nuevo_tel = request.POST.get('nuevo_telefono')
            desc_tel = request.POST.get('desc_nuevo_telefono', 'ADICIONAL')
            if nuevo_tel and nuevo_tel.strip():
                TelefonoExtra.objects.create(deudor=deudor, numero=nuevo_tel.strip(), descripcion=desc_tel)
                Gestion.objects.create(
                    deudor=deudor,
                    gestor=request.user,
                    resultado="NUEVO TELÉFONO",
                    observacion=f"Se registró un nuevo número de contacto: {nuevo_tel.strip()} ({desc_tel})",
                    monto_pago=Decimal('0')
                )
            url = reverse('registrar_gestion', args=[deudor.id])
            if parametros_url:
                url = f"{url}?{parametros_url}"
            return redirect(url)
            
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
            
            obs_final = f"[Tel: {tel_contactado}] " + request.POST.get('observacion')
            
            Gestion.objects.create(
                deudor=deudor, 
                gestor=request.user, 
                resultado=resultado_final, 
                observacion=obs_final, 
                fecha_promesa=request.POST.get('fecha_promesa') or None,
                monto_pago=monto_decimal
            )
            
            if "PAGO" in resultado_final and monto_decimal > 0:
                if monto_decimal > deudor.saldo_deuda:
                    monto_decimal = deudor.saldo_deuda
                deudor.saldo_deuda -= monto_decimal
                deudor.save()

            # --- GUARDAR SEGUIMIENTO PROGRAMADO (si el gestor lo marcó) ---
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
                            motivo=motivo_seg[:200],
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
    })

# --- ELIMINAR CLIENTE ---
@login_required
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
                
                try:
                    deudor = Deudor.objects.get(documento=dni)
                except Deudor.DoesNotExist:
                    errores.append(f"Fila {index+2}: DNI {dni} no encontrado en la base de datos")
                    fallidos += 1
                    continue
                
                telefono_limpio = ''.join(filter(str.isdigit, telefono))
                if len(telefono_limpio) != 9:
                    errores.append(f"Fila {index+2}: Teléfono {telefono} no es válido (debe tener 9 dígitos)")
                    fallidos += 1
                    continue
                
                telefono_existente = TelefonoExtra.objects.filter(deudor=deudor, numero=telefono_limpio).exists()
                if telefono_existente:
                    errores.append(f"Fila {index+2}: Teléfono {telefono_limpio} ya existe para {deudor.nombre_completo}")
                    fallidos += 1
                    continue
                
                if deudor.telefono_principal == telefono_limpio:
                    errores.append(f"Fila {index+2}: Teléfono {telefono_limpio} es el teléfono principal de {deudor.nombre_completo}")
                    fallidos += 1
                    continue
                
                TelefonoExtra.objects.create(
                    deudor=deudor,
                    numero=telefono_limpio,
                    descripcion=descripcion[:50]
                )
                exitosos += 1
            
            mensajes = f"Proceso completado: {exitosos} teléfonos cargados correctamente, {fallidos} fallidos."
            
        except Exception as e:
            mensajes = f"Error al procesar el archivo: {e}"
    
    return render(request, 'cobranza/cargar_telefonos.html', {
        'mensajes': mensajes,
        'exitosos': exitosos,
        'fallidos': fallidos,
        'errores': errores[:20]
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

# --- MÓDULO: TELEFONÍA ZADARMA (SINCRONIZADO) ---









