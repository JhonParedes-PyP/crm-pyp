import sys

path = 'c:/CRM PYP/cobranza/views.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target_block = """    deudores = deudores.annotate(
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
        deudores = deudores.order_by('prioridad', F('ultima_llamada').asc(nulls_first=True))"""


replacement_block = """    hoy_datetime = timezone.now()
    hace_3_dias = hoy_datetime - timedelta(days=3)
    hace_1_dia = hoy_datetime - timedelta(days=1)

    es_vista_gerente = es_gerente(usuario) and not forzar_asignaciones
    
    if not es_vista_gerente:
        deudores = deudores.annotate(
            ultima_promesa_fecha=Subquery(ultima_promesa_subquery),
            ultima_promesa_vencida_fecha=Subquery(ultima_promesa_vencida_fecha_subq),
            pago_tras_promesa=Subquery(pago_tras_promesa_subq),
        )

        prioridad_annotation = Case(
            When(ultima_promesa_vencida_fecha__isnull=False, pago_tras_promesa__isnull=True, then=Value(0)),
            When(ultima_llamada__isnull=True, then=Value(1)),
            When(ultima_llamada__lte=hace_3_dias, then=Value(1)),
            When(ultima_llamada__lte=hace_1_dia, then=Value(2)),
            default=Value(3),
            output_field=IntegerField()
        )
        deudores = deudores.annotate(prioridad=prioridad_annotation)
    else:
        deudores = deudores.annotate(prioridad=Value(3, output_field=IntegerField()))

    if orden == 'nombre': deudores = deudores.order_by('nombre_completo')
    elif orden == '-nombre': deudores = deudores.order_by('-nombre_completo')
    elif orden == 'agencia': deudores = deudores.order_by('agencia')
    elif orden == '-agencia': deudores = deudores.order_by('-agencia')
    elif orden == 'ultimo_dia_pago': deudores = deudores.order_by(F('ultimo_dia_pago').asc(nulls_last=True))
    elif orden == '-ultimo_dia_pago': deudores = deudores.order_by(F('ultimo_dia_pago').desc(nulls_last=True))
    elif orden == 'deuda_total': deudores = deudores.order_by(F('saldo_deuda').asc(nulls_last=True))
    elif orden == '-deuda_total': deudores = deudores.order_by(F('saldo_deuda').desc(nulls_last=True))
    else:
        if es_vista_gerente:
            deudores = deudores.order_by(F('ultima_llamada').desc(nulls_last=True))
        else:
            deudores = deudores.order_by('prioridad', F('ultima_llamada').asc(nulls_first=True))"""

if target_block in content:
    content = content.replace(target_block, replacement_block)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Optimization applied successfully.")
else:
    print("Could not find the target block.")
