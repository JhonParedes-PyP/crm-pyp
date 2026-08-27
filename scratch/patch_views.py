import os

file_path = r"c:\CRM PYP\cobranza\dashboard_views.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the condition in dashboard_views.py for Pagos No Reflejados
old_code = """    # Cruce de Pagos No Registrados (Caja Huancayo) - Para Gerente
    # Clientes cuya base dice que pagaron en el mes actual, pero no tienen gestión de "PAGÓ" en el CRM
    pagos_no_reflejados_huancayo = []
    if es_gerente_flag:
        gestiones_pago_mes = Gestion.objects.filter(
            deudor=OuterRef('pk'),
            resultado__icontains='PAG',
            fecha__gte=inicio_mes_actual
        )
        
        pagos_no_reflejados_huancayo = Deudor.objects.filter(
            cartera__icontains='CAJA HUANCAYO',
            ultimo_dia_pago__gte=inicio_mes_actual
        ).annotate(
            tiene_gestion_pago=Exists(gestiones_pago_mes)
        ).filter(
            tiene_gestion_pago=False
        ).order_by('-ultimo_dia_pago')[:100]

        pagos_no_reflejados_proempresa = Deudor.objects.filter(
            cartera__icontains='PROEMPRESA',
            imp_recup__gt=0
        ).annotate(
            tiene_gestion_pago=Exists(gestiones_pago_mes)
        ).filter(
            tiene_gestion_pago=False
        ).order_by('-imp_recup')[:100]"""

new_code = """    # Cruce de Pagos No Registrados (Caja Huancayo)
    # Clientes cuya base dice que pagaron en el mes actual, pero no tienen gestión de "PAGÓ" en el CRM
    gestiones_pago_mes = Gestion.objects.filter(
        deudor=OuterRef('pk'),
        resultado__icontains='PAG',
        fecha__gte=inicio_mes_actual
    )
    
    pagos_no_reflejados_huancayo = Deudor.objects.filter(
        cartera__icontains='CAJA HUANCAYO',
        ultimo_dia_pago__gte=inicio_mes_actual
    ).annotate(
        tiene_gestion_pago=Exists(gestiones_pago_mes)
    ).filter(
        tiene_gestion_pago=False
    ).order_by('-ultimo_dia_pago')[:100]

    pagos_no_reflejados_proempresa = Deudor.objects.filter(
        cartera__icontains='PROEMPRESA',
        imp_recup__gt=0
    ).annotate(
        tiene_gestion_pago=Exists(gestiones_pago_mes)
    ).filter(
        tiene_gestion_pago=False
    ).order_by('-imp_recup')[:100]"""

content = content.replace(old_code, new_code)

# Replace the dictionary mapping 
content = content.replace("'pagos_no_reflejados_proempresa': pagos_no_reflejados_proempresa if es_gerente_flag else [],", "'pagos_no_reflejados_proempresa': pagos_no_reflejados_proempresa,")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("dashboard_views.py patched.")
