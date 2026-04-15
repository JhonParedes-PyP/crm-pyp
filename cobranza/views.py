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
from .models import Deudor, Gestion, TelefonoExtra, AsignacionCartera, CampanaAsterisk, DetalleCampanaAsterisk

from django.db import models
from django.db.models import Q, Sum, Count, Max, OuterRef, Subquery
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

# --- SEGURIDAD ---
@require_http_methods(["GET", "POST"])
def salir_sistema(request):
    logout(request)
    return redirect('login')

# --- CARGA DE CARTERA ---
@login_required
def subir_excel(request):
    mensajes = ""
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        try:
            archivo = request.FILES['archivo_excel']
            df = pd.read_excel(archivo, dtype=str).fillna('') 
            
            for index, row in df.iterrows():
                cap_str = str(row.get('DEUDA_CAP', '0')).strip()
                tot_str = str(row.get('DEUDA_TOTAL', '0')).strip()
                cap = Decimal(cap_str) if cap_str else Decimal('0')
                tot = Decimal(tot_str) if tot_str else Decimal('0')
                
                documento_val = str(row.get('DOC_DNI_RUC', '')).strip()
                
                if documento_val:
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
                        }
                    )
            mensajes = "¡Excelente! La cartera multicliente se subió y actualizó con éxito."
        except Exception as e:
            mensajes = f"Error al procesar el Excel: {e}"
    return render(request, 'cobranza/subir_excel.html', {'mensajes': mensajes})

# --- FUNCIÓN AUXILIAR PARA OBTENER LISTA DE DEUDORES CON FILTROS Y ASIGNACIÓN ---
def obtener_lista_deudores_filtrados(request, usuario=None, ids_seleccionados=None):
    q = request.GET.get('q', '') 
    cartera_filtro = request.GET.get('cartera', '')
    agencia_filtro = request.GET.get('agencia', '')
    mora_filtro = request.GET.get('rango_dias_mora', '')
    orden = request.GET.get('orden', '')
    
    if not any([q, cartera_filtro, agencia_filtro, mora_filtro, orden]):
        filtros_sesion = request.session.get('filtros_bandeja', {})
        q = filtros_sesion.get('q', '')
        cartera_filtro = filtros_sesion.get('cartera', '')
        agencia_filtro = filtros_sesion.get('agencia', '')
        mora_filtro = filtros_sesion.get('mora', '')
        orden = filtros_sesion.get('orden', '')
    
    deudores = Deudor.objects.annotate(ultima_llamada=Max('gestion__fecha'))
    
    if usuario and not es_gerente(usuario):
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
            deudores = deudores.filter(id__in=[])
    
    if q: 
        deudores = deudores.filter(Q(documento__icontains=q) | Q(nombre_completo__icontains=q))
    if cartera_filtro: 
        deudores = deudores.filter(cartera=cartera_filtro)
    if agencia_filtro: 
        deudores = deudores.filter(agencia=agencia_filtro)
    if mora_filtro: 
        deudores = deudores.filter(rango_dias_mora=mora_filtro)
    
    if orden == 'nombre': deudores = deudores.order_by('nombre_completo')
    elif orden == '-nombre': deudores = deudores.order_by('-nombre_completo')
    elif orden == 'agencia': deudores = deudores.order_by('agencia')
    elif orden == '-agencia': deudores = deudores.order_by('-agencia')
    elif orden == 'mora': deudores = deudores.order_by('rango_dias_mora')
    elif orden == '-mora': deudores = deudores.order_by('-rango_dias_mora')
    elif orden == 'deuda_total': deudores = deudores.order_by('saldo_deuda')
    elif orden == '-deuda_total': deudores = deudores.order_by('-saldo_deuda')

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
    
    lista_deudores = []
    for d in deudores:
        if not d.ultima_llamada: 
            color = "rojo"
        else:
            dias = (timezone.now() - d.ultima_llamada).days
            color = "rojo" if dias >= 3 else ("amarillo" if dias >= 1 else "verde")
        
        alerta_promesa = d.tiene_promesa_vencida is not None
        
        lista_deudores.append({
            'id': d.id,
            'color': color,
            'alerta_promesa': alerta_promesa
        })
    
    if not orden:
        def prioridad(item):
            if item['alerta_promesa']:
                return 0
            orden_color = {"rojo": 1, "amarillo": 2, "verde": 3}
            return orden_color.get(item['color'], 4)
        lista_deudores.sort(key=prioridad)
    
    ids = [item['id'] for item in lista_deudores]
    
    if ids_seleccionados:
        ids = [id for id in ids if id in ids_seleccionados]
    
    return ids

# --- BANDEJA DE TRABAJO ---
@login_required
def bandeja_gestor(request):
    q = request.GET.get('q', '') 
    cartera_filtro = request.GET.get('cartera', '')
    agencia_filtro = request.GET.get('agencia', '')
    mora_filtro = request.GET.get('rango_dias_mora', '')
    orden = request.GET.get('orden', '')

    es_gerente_flag = es_gerente(request.user)

    if es_gerente_flag:
        carteras_crudas = Deudor.objects.values_list('cartera', flat=True).distinct()
        agencias_crudas = Deudor.objects.values_list('agencia', flat=True).distinct()
        moras_crudas = Deudor.objects.values_list('rango_dias_mora', flat=True).distinct()
    else:
        asignaciones = AsignacionCartera.objects.filter(gestor=request.user)
        carteras_asignadas = asignaciones.filter(tipo='cartera').values_list('valor', flat=True)
        agencias_asignadas = asignaciones.filter(tipo='agencia').values_list('valor', flat=True)
        
        condiciones = Q()
        if carteras_asignadas.exists():
            condiciones |= Q(cartera__in=carteras_asignadas)
        if agencias_asignadas.exists():
            condiciones |= Q(agencia__in=agencias_asignadas)
        
        if condiciones:
            deudores_base = Deudor.objects.filter(condiciones)
        else:
            deudores_base = Deudor.objects.filter(id__in=[])
        
        carteras_crudas = deudores_base.values_list('cartera', flat=True).distinct()
        agencias_crudas = deudores_base.values_list('agencia', flat=True).distinct()
        moras_crudas = deudores_base.values_list('rango_dias_mora', flat=True).distinct()
    
    lista_carteras = sorted([str(c) for c in carteras_crudas if c and str(c).strip() != ''])
    lista_agencias = sorted([str(a) for a in agencias_crudas if a and str(a).strip() != ''])
    lista_moras = sorted([str(m) for m in moras_crudas if m and str(m).strip() != ''])

    deudores = Deudor.objects.annotate(ultima_llamada=Max('gestion__fecha'))

    if not es_gerente_flag:
        asignaciones = AsignacionCartera.objects.filter(gestor=request.user)
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
            deudores = deudores.filter(id__in=[])

    if q: 
        deudores = deudores.filter(Q(documento__icontains=q) | Q(nombre_completo__icontains=q))
    if cartera_filtro: 
        deudores = deudores.filter(cartera=cartera_filtro)
    if agencia_filtro: 
        deudores = deudores.filter(agencia=agencia_filtro)
    if mora_filtro: 
        deudores = deudores.filter(rango_dias_mora=mora_filtro)

    if orden == 'nombre': deudores = deudores.order_by('nombre_completo')
    elif orden == '-nombre': deudores = deudores.order_by('-nombre_completo')
    elif orden == 'agencia': deudores = deudores.order_by('agencia')
    elif orden == '-agencia': deudores = deudores.order_by('-agencia')
    elif orden == 'mora': deudores = deudores.order_by('rango_dias_mora')
    elif orden == '-mora': deudores = deudores.order_by('-rango_dias_mora')
    elif orden == 'deuda_total': deudores = deudores.order_by('saldo_deuda')
    elif orden == '-deuda_total': deudores = deudores.order_by('-saldo_deuda')
    
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
    
    lista_deudores = []
    for d in deudores:
        if not d.ultima_llamada: 
            color = "rojo"
        else:
            dias = (timezone.now() - d.ultima_llamada).days
            color = "rojo" if dias >= 3 else ("amarillo" if dias >= 1 else "verde")
        
        alerta_promesa = d.tiene_promesa_vencida is not None
        proxima_promesa = d.ultima_promesa_fecha
        
        lista_deudores.append({
            'deudor': d,
            'color': color,
            'alerta_promesa': alerta_promesa,
            'proxima_promesa': proxima_promesa
        })
    
    if not orden:
        def prioridad(item):
            if item['alerta_promesa']:
                return 0
            orden_color = {"rojo": 1, "amarillo": 2, "verde": 3}
            return orden_color.get(item['color'], 4)
        lista_deudores.sort(key=prioridad)
        
    deudores_ordenados = [item['deudor'] for item in lista_deudores]
    
    paginator = Paginator(deudores_ordenados, 20)
    page_number = request.GET.get('page')
    deudores_paginados = paginator.get_page(page_number)
    
    deudores_con_info = []
    for d in deudores_paginados:
        info = next((item for item in lista_deudores if item['deudor'].id == d.id), None)
        if info:
            d.color = info['color']
            d.alerta_promesa = info['alerta_promesa']
            d.proxima_promesa = info['proxima_promesa']
        else:
            if not d.ultima_llamada: 
                d.color = "rojo"
            else:
                dias = (timezone.now() - d.ultima_llamada).days
                d.color = "rojo" if dias >= 3 else ("amarillo" if dias >= 1 else "verde")
            d.alerta_promesa = False
            d.proxima_promesa = None
        deudores_con_info.append(d)
    
    lista_ids_filtrados = obtener_lista_deudores_filtrados(request, request.user)
    request.session['lista_ids_navegacion'] = lista_ids_filtrados
    
    request.session['filtros_bandeja'] = {
        'q': q,
        'cartera': cartera_filtro,
        'agencia': agencia_filtro,
        'mora': mora_filtro,
        'page': page_number,
        'orden': orden
    }
    
    return render(request, 'cobranza/bandeja.html', {
        'deudores': deudores_con_info,
        'lista_carteras': lista_carteras,
        'lista_agencias': lista_agencias,
        'lista_moras': lista_moras,
        'q': q,
        'cartera_filtro': cartera_filtro,
        'agencia_filtro': agencia_filtro,
        'mora_filtro': mora_filtro,
        'orden_actual': orden,
        'es_gerente': es_gerente_flag,
    })

# --- RECIBIR LLAMADA DESDE KUBO Y REDIRIGIR A FICHA DEL CLIENTE ---
@login_required
def datos_cliente_kubo(request, telefono, campana, cod_cliente, cod_telefono):
    """
    Endpoint que recibe la URL de Kubo y redirige a la ficha del cliente
    URL: /datos-cliente/<telefono>/<campana>/<cod_cliente>/<cod_telefono>/
    
    Ejemplo: https://micrm.com/datos-cliente/967050203/85200/U7Hlpt2u/0w=/N6mIwgDkYQa=/
    """
    # Buscar cliente por teléfono
    try:
        deudor = Deudor.objects.get(telefono_principal=telefono)
    except Deudor.DoesNotExist:
        # Buscar en teléfonos adicionales
        try:
            telefono_extra = TelefonoExtra.objects.get(numero=telefono)
            deudor = telefono_extra.deudor
        except TelefonoExtra.DoesNotExist:
            return HttpResponse("Cliente no encontrado", status=404)
    
    # Redirigir a la ficha de gestión del cliente
    return redirect('registrar_gestion', deudor_id=deudor.id)

# --- GENERAR CAMPAÑA ASTERISK CON FILTROS (GERENTES) ---
@login_required
def generar_campana_asterisk(request):
    if not es_gerente(request.user):
        return HttpResponse("Acceso Denegado. Solo la Gerencia puede generar campañas.", status=403)
    
    CAMPANA_ID = '85200'
    
    if request.method == 'POST':
        # Obtener filtros del formulario
        cartera_filtro = request.POST.get('cartera', '')
        agencia_filtro = request.POST.get('agencia', '')
        mora_desde = request.POST.get('mora_desde', '')
        monto_minimo = request.POST.get('monto_minimo', '')
        dias_sin_gestion = request.POST.get('dias_sin_gestion', '')
        
        # Construir consulta
        deudores = Deudor.objects.filter(saldo_deuda__gt=0)
        
        if cartera_filtro:
            deudores = deudores.filter(cartera=cartera_filtro)
        
        if agencia_filtro:
            deudores = deudores.filter(agencia=agencia_filtro)
        
        if mora_desde and mora_desde.isdigit():
            mora_num = int(mora_desde)
            deudores = deudores.filter(rango_dias_mora__gte=mora_num)
        
        if monto_minimo and monto_minimo.replace('.', '').isdigit():
            deudores = deudores.filter(saldo_deuda__gte=Decimal(monto_minimo))
        
        if dias_sin_gestion and dias_sin_gestion.isdigit():
            fecha_limite = timezone.now() - timedelta(days=int(dias_sin_gestion))
            deudores = deudores.annotate(ultima_gestion=Max('gestion__fecha'))
            deudores = deudores.filter(Q(ultima_gestion__isnull=True) | Q(ultima_gestion__lte=fecha_limite))
        
        # Excluir clientes sin teléfono válido
        deudores = deudores.exclude(telefono_principal='').exclude(telefono_principal='Sin número')
        
        if not deudores.exists():
            return HttpResponse("No hay clientes que cumplan con los filtros seleccionados.", status=400)
        
        # Generar CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="campana_asterisk.csv"'
        writer = csv.writer(response)
        writer.writerow(['TELEFONO', 'CAMPANA', 'COD_CLIENTE', 'COD_TELEFONO'])
        
        for d in deudores:
            telefono = d.telefono_principal
            if telefono and len(telefono) >= 9:
                cod_cliente = encode_md5_base64(d.documento)
                cod_telefono = encode_md5_base64(f"{d.id}{telefono}")
                writer.writerow([telefono, CAMPANA_ID, cod_cliente, cod_telefono])
        
        return response
    
    else:
        # GET: mostrar formulario con listas de carteras y agencias
        lista_carteras = Deudor.objects.values_list('cartera', flat=True).distinct()
        lista_carteras = sorted([c for c in lista_carteras if c and str(c).strip() != ''])
        
        lista_agencias = Deudor.objects.values_list('agencia', flat=True).distinct()
        lista_agencias = sorted([a for a in lista_agencias if a and str(a).strip() != ''])
        
        return render(request, 'cobranza/campana_asterisk_gerente.html', {
            'lista_carteras': lista_carteras,
            'lista_agencias': lista_agencias,
        })

# --- EXPORTAR TODOS LOS CLIENTES ---
@login_required
def exportar_todos_asterisk(request):
    if not es_gerente(request.user):
        return HttpResponse("Acceso Denegado.", status=403)
    
    CAMPANA_ID = '85200'
    
    deudores = Deudor.objects.filter(saldo_deuda__gt=0).exclude(telefono_principal='').exclude(telefono_principal='Sin número')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="todos_clientes.csv"'
    writer = csv.writer(response)
    writer.writerow(['TELEFONO', 'CAMPANA', 'COD_CLIENTE', 'COD_TELEFONO'])
    
    for d in deudores:
        telefono = d.telefono_principal
        if telefono and len(telefono) >= 9:
            cod_cliente = encode_md5_base64(d.documento)
            cod_telefono = encode_md5_base64(f"{d.id}{telefono}")
            writer.writerow([telefono, CAMPANA_ID, cod_cliente, cod_telefono])
    
    return response

# --- EXPORTAR MOROSOS 30+ DÍAS ---
@login_required
def exportar_morosos_30(request):
    if not es_gerente(request.user):
        return HttpResponse("Acceso Denegado.", status=403)
    
    CAMPANA_ID = '85200'
    
    deudores = Deudor.objects.filter(
        saldo_deuda__gt=0,
        rango_dias_mora__gte=30
    ).exclude(telefono_principal='').exclude(telefono_principal='Sin número')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="morosos_30_dias.csv"'
    writer = csv.writer(response)
    writer.writerow(['TELEFONO', 'CAMPANA', 'COD_CLIENTE', 'COD_TELEFONO'])
    
    for d in deudores:
        telefono = d.telefono_principal
        if telefono and len(telefono) >= 9:
            cod_cliente = encode_md5_base64(d.documento)
            cod_telefono = encode_md5_base64(f"{d.id}{telefono}")
            writer.writerow([telefono, CAMPANA_ID, cod_cliente, cod_telefono])
    
    return response

# --- EXPORTAR MOROSOS 90+ DÍAS ---
@login_required
def exportar_morosos_90(request):
    if not es_gerente(request.user):
        return HttpResponse("Acceso Denegado.", status=403)
    
    CAMPANA_ID = '85200'
    
    deudores = Deudor.objects.filter(
        saldo_deuda__gt=0,
        rango_dias_mora__gte=90
    ).exclude(telefono_principal='').exclude(telefono_principal='Sin número')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="morosos_90_dias.csv"'
    writer = csv.writer(response)
    writer.writerow(['TELEFONO', 'CAMPANA', 'COD_CLIENTE', 'COD_TELEFONO'])
    
    for d in deudores:
        telefono = d.telefono_principal
        if telefono and len(telefono) >= 9:
            cod_cliente = encode_md5_base64(d.documento)
            cod_telefono = encode_md5_base64(f"{d.id}{telefono}")
            writer.writerow([telefono, CAMPANA_ID, cod_cliente, cod_telefono])
    
    return response

# --- EXPORTAR PROMESAS VENCIDAS ---
@login_required
def exportar_promesas_vencidas(request):
    if not es_gerente(request.user):
        return HttpResponse("Acceso Denegado.", status=403)
    
    CAMPANA_ID = '85200'
    hoy = timezone.now().date()
    
    # Buscar clientes con promesas vencidas sin pago posterior
    deudores_ids = Gestion.objects.filter(
        resultado__icontains='PROMESA',
        fecha_promesa__lt=hoy
    ).exclude(
        deudor__gestion__resultado__icontains='PAGO',
        deudor__gestion__fecha__gt=models.F('fecha')
    ).values_list('deudor_id', flat=True).distinct()
    
    deudores = Deudor.objects.filter(id__in=deudores_ids).exclude(telefono_principal='').exclude(telefono_principal='Sin número')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="promesas_vencidas.csv"'
    writer = csv.writer(response)
    writer.writerow(['TELEFONO', 'CAMPANA', 'COD_CLIENTE', 'COD_TELEFONO'])
    
    for d in deudores:
        telefono = d.telefono_principal
        if telefono and len(telefono) >= 9:
            cod_cliente = encode_md5_base64(d.documento)
            cod_telefono = encode_md5_base64(f"{d.id}{telefono}")
            writer.writerow([telefono, CAMPANA_ID, cod_cliente, cod_telefono])
    
    return response

# --- SUBIR LISTA DE LLAMADAS ---
@login_required
def subir_lista_llamadas(request):
    if not es_gerente(request.user):
        return HttpResponse("Acceso Denegado. Solo la Gerencia puede generar campañas.", status=403)
    
    CAMPANA_ID = '85200'
    resultados = []
    
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        try:
            archivo = request.FILES['archivo_excel']
            df = pd.read_excel(archivo, dtype=str).fillna('')
            
            if 'DNI' not in df.columns or 'TELEFONO' not in df.columns:
                return render(request, 'cobranza/subir_lista_llamadas.html', {
                    'error': "El archivo debe tener las columnas 'DNI' y 'TELEFONO'",
                    'resultados': []
                })
            
            for index, row in df.iterrows():
                dni = str(row.get('DNI', '')).strip()
                telefono = str(row.get('TELEFONO', '')).strip()
                
                telefono_limpio = ''.join(filter(str.isdigit, telefono))
                
                if len(telefono_limpio) != 9:
                    resultados.append({
                        'dni': dni,
                        'nombre': '',
                        'telefono': telefono,
                        'cod_cliente': '',
                        'cod_telefono': '',
                        'estado': '❌ ERROR',
                        'motivo': 'Teléfono no tiene 9 dígitos'
                    })
                    continue
                
                try:
                    deudor = Deudor.objects.get(documento=dni)
                except Deudor.DoesNotExist:
                    resultados.append({
                        'dni': dni,
                        'nombre': '',
                        'telefono': telefono_limpio,
                        'cod_cliente': '',
                        'cod_telefono': '',
                        'estado': '❌ ERROR',
                        'motivo': 'DNI no encontrado en la base'
                    })
                    continue
                
                cod_cliente = encode_md5_base64(deudor.documento)
                cod_telefono = encode_md5_base64(f"{deudor.id}{telefono_limpio}")
                
                resultados.append({
                    'dni': dni,
                    'nombre': deudor.nombre_completo,
                    'telefono': telefono_limpio,
                    'cod_cliente': cod_cliente,
                    'cod_telefono': cod_telefono,
                    'estado': '✅ OK',
                    'motivo': ''
                })
            
            request.session['campana_resultados'] = resultados
            
            exitosos = len([r for r in resultados if r['estado'] == '✅ OK'])
            fallidos = len([r for r in resultados if r['estado'] == '❌ ERROR'])
            
            return render(request, 'cobranza/subir_lista_llamadas.html', {
                'resultados': resultados,
                'exitosos': exitosos,
                'fallidos': fallidos,
                'total': len(resultados),
                'campana_id': CAMPANA_ID,
                'mensaje_exito': f"Procesado: {exitosos} exitosos, {fallidos} fallidos"
            })
            
        except Exception as e:
            return render(request, 'cobranza/subir_lista_llamadas.html', {
                'error': f"Error al procesar el archivo: {e}",
                'resultados': []
            })
    
    return render(request, 'cobranza/subir_lista_llamadas.html', {
        'resultados': []
    })

# --- EXPORTAR CSV DESDE LISTA SUBIDA ---
@login_required
def exportar_csv_desde_lista(request):
    if not es_gerente(request.user):
        return HttpResponse("Acceso Denegado.", status=403)
    
    CAMPANA_ID = '85200'
    resultados = request.session.get('campana_resultados', [])
    
    if not resultados:
        return HttpResponse("No hay datos para exportar", status=400)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="campana_asterisk.csv"'
    writer = csv.writer(response)
    writer.writerow(['TELEFONO', 'CAMPANA', 'COD_CLIENTE', 'COD_TELEFONO'])
    
    for r in resultados:
        if r['estado'] == '✅ OK':
            writer.writerow([
                r['telefono'],
                CAMPANA_ID,
                r['cod_cliente'],
                r['cod_telefono']
            ])
    
    return response

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
    if filtros.get('mora'): params.append(f"rango_dias_mora={filtros['mora']}")
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

# --- DASHBOARD ---
@login_required
def dashboard_gerente(request):
    hoy = timezone.now().date()
    es_gerente_flag = es_gerente(request.user)
    
    periodo = request.GET.get('periodo', 'hoy')
    
    if periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=7)
        periodo_texto = "Últimos 7 días"
    elif periodo == 'mes':
        fecha_inicio = hoy - timedelta(days=30)
        periodo_texto = "Últimos 30 días"
    else:
        fecha_inicio = hoy
        periodo_texto = "Hoy"
    
    total_deudores = Deudor.objects.count()
    total_cartera = Deudor.objects.aggregate(Sum('saldo_deuda'))['saldo_deuda__sum'] or 0
    total_recuperado = Gestion.objects.aggregate(Sum('monto_pago'))['monto_pago__sum'] or 0
    
    stats_pago = Gestion.objects.filter(
        resultado__icontains='PAGO',
        fecha__date__gte=fecha_inicio
    ).count()
    
    stats_promesa = Gestion.objects.filter(
        resultado__icontains='PROMESA',
        fecha__date__gte=fecha_inicio
    ).count()
    
    productividad = User.objects.annotate(
        total_gestiones=Count('gestion', filter=Q(gestion__fecha__date__gte=fecha_inicio)),
        total_pagos=Count('gestion', filter=Q(gestion__fecha__date__gte=fecha_inicio, gestion__resultado__icontains='PAGO')),
        total_promesas=Count('gestion', filter=Q(gestion__fecha__date__gte=fecha_inicio, gestion__resultado__icontains='PROMESA')),
        monto_recuperado=Sum('gestion__monto_pago', filter=Q(gestion__fecha__date__gte=fecha_inicio))
    ).filter(total_gestiones__gt=0).order_by('-total_gestiones')
    
    gestores_nombres = [g.username.upper() for g in productividad]
    gestores_gestiones = [g.total_gestiones for g in productividad]
    gestores_montos = [float(g.monto_recuperado or 0) for g in productividad]
    
    return render(request, 'cobranza/dashboard.html', {
        'es_gerente': es_gerente_flag,
        'total_cartera': total_cartera,
        'total_recuperado': total_recuperado,
        'total_deudores': total_deudores,
        'productividad': productividad,
        'grafico_labels': ['Pagos', 'Promesas'],
        'grafico_data': [stats_pago, stats_promesa],
        'periodo': periodo,
        'periodo_texto': periodo_texto,
        'gestores_nombres': gestores_nombres,
        'gestores_gestiones': gestores_gestiones,
        'gestores_montos': gestores_montos,
    })

# --- EXPORTAR CSV ASTERISK (TODOS LOS CLIENTES - MANTENIDO) ---
@login_required
def exportar_csv_asterisk(request):
    if not es_gerente(request.user): 
        return HttpResponse("No", status=403)
    
    CAMPANA_ID = '85200'
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Asterisk_PP.csv"'
    writer = csv.writer(response)
    writer.writerow(['TELEFONO', 'CAMPANA', 'COD_CLIENTE', 'COD_TELEFONO'])
    
    for d in Deudor.objects.filter(saldo_deuda__gt=0):
        telefono = d.telefono_principal
        if telefono and telefono != 'Sin número' and len(telefono) >= 9:
            cod_cliente = encode_md5_base64(d.documento)
            cod_telefono = encode_md5_base64(f"{d.id}{telefono}")
            writer.writerow([telefono, CAMPANA_ID, cod_cliente, cod_telefono])
    
    return response

# --- BUSCAR POR DNI ---
@login_required
def buscar_por_dni(request, dni):
    deudor = get_object_or_404(Deudor, documento=dni)
    return redirect('registrar_gestion', deudor_id=deudor.id)

# --- EXPORTAR GESTIONES A EXCEL ---
@login_required
def exportar_gestiones_excel(request):
    gestiones = Gestion.objects.all().order_by('-fecha')
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['FECHA', 'GESTOR', 'DNI', 'CLIENTE', 'RESULTADO', 'MONTO'])
    for g in gestiones:
        ws.append([g.fecha.strftime('%d/%m/%Y'), g.gestor.username, g.deudor.documento, g.deudor.nombre_completo, g.resultado, g.monto_pago])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Reporte_PP.xlsx'
    wb.save(response)
    return response

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

    # --- API: RECIBIR GESTIÓN DESDE APP JUDICIAL DE CAMPO ---
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
    
    # --- MÓDULO: PANEL DE CAMPAÑAS ASTERISK Y CARGA DE EXCEL ---
@login_required
def panel_campanas_asterisk(request):
    if not es_gerente(request.user):
        return HttpResponse("Acceso Denegado. Solo Gerencia.", status=403)

    mensajes = ""
    errores = []
    exitosos = 0
    fallidos = 0

    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        nombre_campana = request.POST.get('nombre_campana')
        proveedor = request.POST.get('proveedor')
        archivo = request.FILES['archivo_excel']

        try:
            # 1. Creamos la "Campaña Maestra" en la base de datos
            nueva_campana = CampanaAsterisk.objects.create(
                nombre=nombre_campana,
                proveedor=proveedor,
                usuario_creador=request.user
            )

            # 2. Leemos el Excel
            df = pd.read_excel(archivo, dtype=str).fillna('')

            # Validamos que el Excel tenga las columnas correctas
            if 'NRO_DOCUMENTO' not in df.columns or 'NRO_TELEFONO' not in df.columns:
                nueva_campana.delete() # Cancelamos la creación
                errores.append("El archivo debe tener exactamente las columnas 'NRO_DOCUMENTO' y 'NRO_TELEFONO'.")
            else:
                # 3. Cruzamos los datos fila por fila
                detalles_a_crear = []
                for index, row in df.iterrows():
                    dni = str(row.get('NRO_DOCUMENTO', '')).strip()
                    telefono = str(row.get('NRO_TELEFONO', '')).strip()
                    telefono_limpio = ''.join(filter(str.isdigit, telefono))

                    # Regla 1: Que tenga 9 dígitos
                    if len(telefono_limpio) != 9:
                        fallidos += 1
                        errores.append(f"Fila {index+2} (DNI {dni}): El teléfono no tiene 9 dígitos.")
                        continue

                    # Regla 2: Que el DNI exista en nuestra bóveda
                    deudor = Deudor.objects.filter(documento=dni).first()
                    if not deudor:
                        fallidos += 1
                        errores.append(f"Fila {index+2}: El DNI {dni} no existe en el CRM.")
                        continue

                    # Regla 3: ¿El teléfono le pertenece a ese DNI?
                    es_suyo = False
                    if deudor.telefono_principal == telefono_limpio or deudor.tlf_celular_aval == telefono_limpio:
                        es_suyo = True
                    elif TelefonoExtra.objects.filter(deudor=deudor, numero=telefono_limpio).exists():
                        es_suyo = True

                    if not es_suyo:
                        fallidos += 1
                        errores.append(f"Fila {index+2}: El Tel {telefono_limpio} no está registrado para el DNI {dni}.")
                        continue

                    # Si pasó todas las reglas: Generamos el código KUBO
                    cod_cliente = encode_md5_base64(dni)
                    cod_telefono = encode_md5_base64(f"{deudor.id}{telefono_limpio}")

                    # Lo preparamos para guardarlo en el anexo
                    detalles_a_crear.append(
                        DetalleCampanaAsterisk(
                            campana=nueva_campana,
                            dni=dni,
                            telefono=telefono_limpio,
                            cod_cliente=cod_cliente,
                            cod_telefono=cod_telefono
                        )
                    )
                    exitosos += 1

                # 4. Guardamos todos los números válidos
                if detalles_a_crear:
                    DetalleCampanaAsterisk.objects.bulk_create(detalles_a_crear)
                    mensajes = f"¡Campaña creada con éxito! {exitosos} números validados y encriptados."
                else:
                    nueva_campana.delete() # Si ningún número valió, no guardamos la campaña
                    mensajes = "Operación cancelada: Ningún número del Excel pasó las validaciones de seguridad."

        except Exception as e:
            errores.append(f"Error grave al leer el archivo: {str(e)}")

    # 5. Listamos las campañas para mostrarlas en la tabla
    lista_campanas = CampanaAsterisk.objects.all()

    return render(request, 'cobranza/panel_campanas.html', {
        'lista_campanas': lista_campanas,
        'mensajes': mensajes,
        'errores': errores[:15], # Mostramos máximo 15 errores para no saturar la pantalla
        'exitosos': exitosos,
        'fallidos': fallidos
    })

# --- MÓDULO: DESCARGAR CSV DE LA CAMPAÑA ---
@login_required
def descargar_csv_campana(request, campana_id):
    if not es_gerente(request.user):
        return HttpResponse("Acceso Denegado.", status=403)

    # 1. Buscamos la campaña exacta que el Gerente seleccionó
    campana = get_object_or_404(CampanaAsterisk, id=campana_id)
    detalles = campana.detalles.all() # Traemos todos sus números validados

    # 2. Preparamos el archivo descargable
    response = HttpResponse(content_type='text/csv')
    # El nombre del archivo se verá profesional: Ej. "Asterisk_Camp_1_PROEMPRESA.csv"
    nombre_archivo = f"Asterisk_Camp_{campana.id}_{campana.nombre.replace(' ', '_')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'

    writer = csv.writer(response)
    
    # 3. Las Cabeceras Exactas que exige el proveedor
    writer.writerow(['TELEFONO', 'CAMPANA', 'COD_CLIENTE', 'COD_TELEFONO'])

    # 4. Llenamos el Excel (¡Adiós al 85200 fijo!)
    for d in detalles:
        writer.writerow([
            d.telefono,
            str(campana.id),  # ¡LA MAGIA! Inserta automáticamente el ID 1, 2, 3...
            d.cod_cliente,
            d.cod_telefono
        ])

    return response

# --- RUTA SECRETA: ELIMINAR GESTIÓN (SOLO GERENTES) ---
@login_required
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

@login_required
def api_zadarma_webrtc_key(request):
    """Genera la llave dinámica para el teléfono verde flotante"""
    api_url = "/v1/webrtc/get_key/"
    params = {'sip': settings.ZADARMA_SIP}

    # 1. Ordenar y codificar parámetros
    sorted_params = dict(sorted(params.items()))
    query_string = urlencode(sorted_params)

    # 2. Firma Zadarma: método + query + md5(query)
    md5_hash = hashlib.md5(query_string.encode('utf-8')).hexdigest()
    data_to_sign = f"{api_url}{query_string}{md5_hash}"

    # 3. HMAC-SHA1 en HEXADECIMAL
    signature = hmac.new(
        settings.ZADARMA_SECRET.encode('utf-8'),
        data_to_sign.encode('utf-8'),
        hashlib.sha1
    ).hexdigest()

    headers = {'Authorization': f"{settings.ZADARMA_KEY}:{signature}"}

    try:
        response = requests.get(f"https://api.zadarma.com{api_url}", params=params, headers=headers)
        return JsonResponse(response.json())
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def iniciar_callback(request, numero_cliente):
    """Inicia la llamada para el botón azul"""
    num = str(numero_cliente).strip()
    if len(num) == 9 and num.startswith('9'):
        num = f"51{num}"

    api_method = '/v1/request/callback/'
    params = {'from': settings.ZADARMA_SIP, 'to': num}

    # 1. Firma idéntica al método anterior
    sorted_params = dict(sorted(params.items()))
    query_string = urlencode(sorted_params)
    md5_hash = hashlib.md5(query_string.encode('utf-8')).hexdigest()
    data_to_sign = f"{api_method}{query_string}{md5_hash}"

    signature = hmac.new(
        settings.ZADARMA_SECRET.encode('utf-8'),
        data_to_sign.encode('utf-8'),
        hashlib.sha1
    ).hexdigest()

    headers = {'Authorization': f"{settings.ZADARMA_KEY}:{signature}"}
    response = requests.get(f"https://api.zadarma.com{api_method}", params=params, headers=headers)

    print(f"--- [CHISMOSO] LLAMADA A {num} | RESPUESTA: {response.json()}")
    return JsonResponse(response.json())