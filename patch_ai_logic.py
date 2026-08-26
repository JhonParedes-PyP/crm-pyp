import os
import re

path_views = r"c:\CRM PYP\cobranza\estrategia_ia_views.py"
with open(path_views, 'r', encoding='utf-8') as f:
    views_content = f.read()

# Add the calculation block
new_logic = """        # 3. Pagos recientes
        hace_30_dias = timezone.now().date() - timedelta(days=30)
        pagos_recientes = qs.filter(ultimo_dia_pago__gte=hace_30_dias).order_by('-ultimo_dia_pago')[:20]
        
        # --- NUEVA LOGICA: CONVENIOS ---
        qs_convenios = qs.exclude(negociacion__isnull=True).exclude(negociacion__exact='')\\
                         .exclude(negociacion__iexact='nan').exclude(negociacion__iexact='none')\\
                         .exclude(negociacion__iexact='null')\\
                         .exclude(negociacion__iexact='SIN NEGOCIACIÓN')\\
                         .exclude(negociacion__iexact='SIN NEGOCIACION')
                         
        hoy = timezone.now().date()
        mes_actual = hoy.month
        anio_actual = hoy.year
        
        lista_convenios = []
        for c in qs_convenios:
            al_dia = False
            dias_atraso = 0
            fecha_pago_str = 'NO REGISTRA'
            if c.ultimo_dia_pago:
                fecha_pago_str = c.ultimo_dia_pago.strftime('%d/%m/%Y')
                if c.ultimo_dia_pago.year > anio_actual or (c.ultimo_dia_pago.year == anio_actual and c.ultimo_dia_pago.month >= mes_actual):
                    al_dia = True
                else:
                    dias_atraso = (hoy - c.ultimo_dia_pago).days
                    if dias_atraso <= 0:
                        al_dia = True
                        dias_atraso = 0
            else:
                dias_atraso = 9999
                
            lista_convenios.append({
                'nombre_completo': c.nombre_completo,
                'saldo_deuda': float(c.saldo_deuda) if c.saldo_deuda else 0.0,
                'ultimo_dia_pago': fecha_pago_str,
                'dias_atraso': 'CLIENTE AL DIA' if al_dia else f"{dias_atraso} días",
                '_es_al_dia': al_dia,
                '_dias_atraso_num': dias_atraso
            })
            
        lista_convenios.sort(key=lambda x: (x['_es_al_dia'], -x['_dias_atraso_num']))
        
        # Quitar las llaves internas para no ensuciar el JSON de la IA
        for item in lista_convenios:
            del item['_es_al_dia']
            del item['_dias_atraso_num']
            
        # --- NUEVA LOGICA: PRODUCTOS (NORMAL VS OTROS) ---
        agrupacion_productos = list(qs.values('agencia', 'producto').annotate(
            total_clientes=Count('id'),
            suma_deuda=Sum('saldo_deuda')
        ).order_by('agencia', 'producto'))
        
        for item in agrupacion_productos:
            item['suma_deuda'] = float(item['suma_deuda']) if item['suma_deuda'] else 0.0

        # 4. Construir Diccionario con todo para la IA
        datos_agrupados = {
            'cartera': cartera,
            'agencias': agencias if agencias else 'Todas',
            'total_clientes': total_deudores,
            'total_deuda_acumulada_soles': float(total_deuda),
            'top_deudas': list(top_deudas.values('nombre_completo', 'saldo_deuda', 'distrito', 'telefono_principal')),
            'casos_embargo_judicial': list(embargos.values('nombre_completo', 'saldo_deuda', 'proceso', 'condicion')),
            'pagos_recientes': list(pagos_recientes.values('nombre_completo', 'ultimo_dia_pago', 'saldo_deuda')),
            'clientes_con_convenio': lista_convenios,
            'distribucion_por_producto': agrupacion_productos
        }"""

views_content = re.sub(
    r"# 3\. Pagos recientes.*?datos_agrupados = {.*?}",
    new_logic,
    views_content,
    flags=re.DOTALL
)

with open(path_views, 'w', encoding='utf-8') as f:
    f.write(views_content)

# AI Service
path_ai = r"c:\CRM PYP\cobranza\ai_service.py"
with open(path_ai, 'r', encoding='utf-8') as f:
    ai_content = f.read()

old_instruction = "3. (PRIORIDAD ALTA) Dale MUCHA IMPORTANCIA a los clientes que tienen CONVENIOS DE PAGO o NEGOCIACIÓN. Fíjate en sus fechas de pago y evalúa si, dada la fecha actual, ya deberían haber pagado y han incumplido. Diseña un plan de choque específico para estos convenios caídos o próximos a vencer."

new_instruction = """3. (PRIORIDAD ALTA) Analiza TODOS los clientes que tienen NEGOCIACIÓN o CONVENIOS DE PAGO en la sección de 'clientes_con_convenio'. 
   - Presenta estrictamente una tabla Markdown con las columnas: Cliente, Deuda, Último Pago, Días de Atraso, Acción Inmediata.
   - IMPORTANTE: Los clientes con Días de Atraso = 'CLIENTE AL DIA' SIEMPRE deben figurar AL ÚLTIMO de la tabla. Los clientes más vencidos deben estar AL FRENTE (arriba de la tabla).
   - Genera una acción inmediata o recomendación estratégica para este grupo de convenios.
3.5 (PRIORIDAD MEDIA) Haz un análisis profundo de la 'distribucion_por_producto'. Identifica los clientes cuyo producto es 'NORMAL'. Estos créditos (especialmente en Caja Huancayo) pagan mayor comisión. Compara estos con otros productos (como REACTIVA, FAE, etc. que pagan comisiones muy bajas como 5%).
   - Analiza qué créditos pagan más DENTRO DE CADA AGENCIA.
   - Recomienda estrategias extrajudiciales dando altísima prioridad a los créditos 'NORMAL' para maximizar la comisión obtenida."""

ai_content = ai_content.replace(old_instruction, new_instruction)

with open(path_ai, 'w', encoding='utf-8') as f:
    f.write(ai_content)

print("Patch applied to AI logic")
