import pandas as pd
import openpyxl
import urllib.parse
import csv
from decimal import Decimal
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from .models import Deudor, Gestion, TelefonoExtra, AsignacionCartera
from django.db import models
from django.db.models import Q, Sum, Count, Max, OuterRef, Subquery
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.urls import reverse

# --- FUNCIÓN PARA VERIFICAR SI ES GERENTE ---
def es_gerente(user):
    return user.groups.filter(name='GERENTE').exists() or user.is_superuser

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
def obtener_lista_deudores_filtrados(request, usuario=None):
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
    
    return [item['id'] for item in lista_deudores]

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
    
    paginator = Paginator(deudores_ordenados, 10)
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

# --- NUEVA VISTA: ASIGNACIÓN DE CARTERAS Y AGENCIAS (SOLO GERENTES) ---
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

# --- NUEVA VISTA: CARGA MASIVA DE TELÉFONOS (SOLO GERENTES) ---
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

@login_required
def exportar_csv_asterisk(request):
    if not es_gerente(request.user): 
        return HttpResponse("No", status=403)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Asterisk_PP.csv"'
    writer = csv.writer(response)
    writer.writerow(['TELEFONO', 'CAMPANA', 'COD_CLIENTE', 'COD_TELEFONO'])
    for d in Deudor.objects.filter(saldo_deuda__gt=0):
        writer.writerow([d.telefono_principal, '85182', d.documento, d.id])
    return response

@login_required
def buscar_por_dni(request, dni):
    deudor = get_object_or_404(Deudor, documento=dni)
    return redirect('registrar_gestion', deudor_id=deudor.id)

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