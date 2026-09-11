"""
ai_service.py — Motor de Inteligencia Artificial para CRM P&P
Integra DeepSeek V4 Pro con razonamiento avanzado para asistir
a los gestores de cobranza en tiempo real.
"""

import os
from openai import OpenAI
from django.conf import settings


def _get_client():
    """Crea y retorna el cliente DeepSeek (compatible con OpenAI SDK)."""
    api_key = os.environ.get('DEEPSEEK_API_KEY') or getattr(settings, 'DEEPSEEK_API_KEY', '')
    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )


def _build_perfil_deudor(deudor, gestiones=None):
    """Construye el contexto textual del deudor para los prompts."""
    lineas = [
        f"NOMBRE: {deudor.nombre_completo}",
        f"DNI: {deudor.documento}",
        f"CUENTA: {deudor.cuenta}",
        f"AGENCIA: {deudor.agencia or 'N/A'}",
        f"CARTERA: {deudor.cartera or 'N/A'}",
        f"CAPITAL BASE: S/ {deudor.monto_capital}",
        f"SALDO DEUDA TOTAL: S/ {deudor.saldo_deuda}",
        f"RANGO DE MORA: {deudor.rango_dias_mora or 'No especificado'}",
        f"MESES DE MORA: {deudor.nmes or 'N/A'}",
        f"ÚLTIMO DÍA DE PAGO: {deudor.ultimo_dia_pago or 'Sin registro'}",
    ]

    if deudor.condicion:
        lineas.append(f"CONDICIÓN JUDICIAL: {deudor.condicion}")
    if deudor.expediente:
        lineas.append(f"EXPEDIENTE: {deudor.expediente}")
    if deudor.juzgado:
        lineas.append(f"JUZGADO: {deudor.juzgado}")
    if deudor.negociacion:
        lineas.append(f"NOTAS DE NEGOCIACIÓN: {deudor.negociacion}")
    if deudor.distrito:
        lineas.append(f"DISTRITO: {deudor.distrito}")
    if deudor.producto:
        lineas.append(f"PRODUCTO: {deudor.producto}")

    perfil = "\n".join(lineas)

    if gestiones:
        perfil += "\n\nHISTORIAL DE GESTIONES (del más reciente al más antiguo):\n"
        for i, g in enumerate(gestiones[:15], 1):  # Máximo 15 gestiones
            fecha_str = g.fecha.strftime('%d/%m/%Y %H:%M') if g.fecha else 'Fecha desconocida'
            gestor_str = g.gestor.username.upper() if g.gestor else 'Sistema'
            promesa_str = f" | Promesa: {g.fecha_promesa}" if g.fecha_promesa else ""
            monto_str = f" | Monto: S/ {g.monto_pago}" if g.monto_pago and g.monto_pago > 0 else ""
            perfil += (
                f"{i}. [{fecha_str}] ({gestor_str}) "
                f"RESULTADO: {g.resultado}{promesa_str}{monto_str}\n"
                f"   Observación: {g.observacion}\n"
            )

    return perfil


def generar_resumen_historial(deudor, gestiones, gestor=None):
    """
    Genera un resumen ejecutivo del historial de gestiones de un deudor.
    Retorna el texto completo del resumen.
    """
    client = _get_client()
    perfil = _build_perfil_deudor(deudor, gestiones)
    total_gestiones = gestiones.count() if hasattr(gestiones, 'count') else len(gestiones)
    gestor_nombre = gestor.get_full_name() or gestor.username.upper() if gestor else 'GESTOR'
    cartera = deudor.cartera or 'P&P Soluciones Jurídicas'

    prompt_sistema = """Eres PP, el Asistente de Inteligencia Artificial de P&P Soluciones Jurídicas Empresariales,
una firma legal peruana especializada en recuperación de créditos.

Tu tarea es analizar el perfil completo de un deudor y generar un resumen ejecutivo claro,
conciso y útil para que el gestor tome decisiones rápidas antes de realizar una gestión.

El resumen debe incluir:
1. Estado actual del caso (1-2 oraciones)
2. Patrón de comportamiento detectado en el historial
3. Nivel de riesgo de incumplimiento (ALTO/MEDIO/BAJO) con justificación breve
4. Recomendación táctica principal para la próxima gestión

Usa lenguaje directo y profesional. Máximo 200 palabras."""

    prompt_usuario = f"""Gestor asignado: {gestor_nombre} | Cartera: {cartera}

Analiza el siguiente perfil de deudor y genera el resumen ejecutivo:

{perfil}

TOTAL DE GESTIONES EN SISTEMA: {total_gestiones}"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": prompt_usuario},
        ],
        stream=False,
    )

    return response.choices[0].message.content


def generar_guion_llamada(deudor, gestiones, gestor=None):
    """
    Genera un guión de llamada personalizado para negociar con el deudor.
    Retorna el texto del guión listo para usar.
    """
    client = _get_client()
    perfil = _build_perfil_deudor(deudor, gestiones)
    gestor_nombre = gestor.get_full_name() or gestor.username.upper() if gestor else 'GESTOR'
    cartera = deudor.cartera or 'P&P Soluciones Jurídicas'

    # Determinar la entidad mandante según la cartera
    entidades = {
        'CAJA HUANCAYO': 'Caja Huancayo',
        'PROEMPRESA': 'Proempresa',
        'FOCMAC': 'Focmac',
    }
    entidad = entidades.get(cartera.upper().strip(), cartera)

    prompt_sistema = f"""Eres PP, experto en técnicas de cobranza y negociación para P&P Soluciones Jurídicas Empresariales.
El gestor que realizará la llamada es: **{gestor_nombre}**
Llama por encargo de: **{entidad}**

Genera un guión de llamada telefónica profesional, empático pero firme, adaptado al perfil específico del deudor.

El guión debe incluir:
1. **APERTURA** — Saludo usando el nombre del gestor ({gestor_nombre}) e identificando que llama por encargo de {entidad}
2. **VERIFICACIÓN** — Confirmar identidad del deudor
3. **PROPÓSITO** — Mencionar la deuda de forma directa pero respetuosa
4. **NEGOCIACIÓN** — 2-3 argumentos persuasivos basados en el perfil
5. **MANEJO DE OBJECIONES** — 2 respuestas para objeciones típicas
6. **CIERRE** — Solicitar compromiso concreto

Personaliza el tono según el historial: si tiene promesas incumplidas, sé más firme.
Si es primer contacto, sé más amigable. Usa el nombre del deudor.
Incluye notas entre [CORCHETES] con instrucciones para el gestor."""

    prompt_usuario = f"""Genera el guión de llamada para este deudor:

{perfil}"""

    response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            temperature=0.3,
            max_tokens=300
        )
    return response.choices[0].message.content.strip()


def optimizar_ruta_ia(clientes, instrucciones_adicionales=None):
    """
    Recibe una lista de diccionarios con la información de los clientes (nombre, distrito, direccion)
    y usa DeepSeek para sugerir el orden geográfico óptimo de visita.
    """
    client = _get_client()
    
    texto_clientes = "LISTA DE CLIENTES A VISITAR:\n"
    for i, c in enumerate(clientes, 1):
        texto = f"{i}. {c.get('nombre')} | Cartera: {c.get('cartera')} | Deuda: S/ {c.get('deuda')}\n"
        texto += f"   Ubicación: {c.get('distrito')} - {c.get('direccion')}\n"
        if c.get('negociacion'):
            texto += f"   Negociación actual: {c.get('negociacion')}\n"
        if c.get('ultimo_pago'):
            texto += f"   Último pago reportado: {c.get('ultimo_pago')}\n"
        texto_clientes += texto + "\n"
        
    prompt_sistema = """Eres un experto en logística urbana y conocimiento geográfico del Perú (especialmente Huancayo, Junín y Lima).
Tu objetivo es organizar una lista de direcciones de deudores para sugerir la RUTA DE COBRANZA MÁS EFICIENTE posible.
Agrupa los clientes por distritos cercanos o zonas adyacentes para evitar cruzar la ciudad innecesariamente.
Devuelve el resultado enumerado paso a paso, recomendando en qué orden visitarlos.
Sé directo y conciso. No uses introducciones largas."""

    prompt_usuario = f"""Por favor, ordena la siguiente lista de clientes en la ruta más óptima:
{texto_clientes}"""

    if instrucciones_adicionales:
        prompt_usuario += f"\n\nInstrucciones adicionales del usuario:\n{instrucciones_adicionales}"

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            temperature=0.2,
            max_tokens=600
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"No se pudo optimizar la ruta con IA: {str(e)}"


def chat_asistente_streaming(deudor, gestiones, mensajes_historial, consulta_usuario, gestor=None):
    """
    Chat interactivo con streaming. Retorna un generador de chunks de texto.
    Usar con StreamingHttpResponse en Django.
    """
    client = _get_client()
    perfil = _build_perfil_deudor(deudor, gestiones)

    gestor_nombre = gestor.get_full_name() or gestor.username.upper() if gestor else 'GESTOR'
    cartera = deudor.cartera or 'P&P Soluciones Jurídicas'

    entidades = {
        'CAJA HUANCAYO': 'Caja Huancayo',
        'PROEMPRESA': 'Proempresa',
        'FOCMAC': 'Focmac',
    }
    entidad = entidades.get(cartera.upper().strip(), cartera)

    prompt_sistema = f"""Eres PP, el Asistente de Inteligencia Artificial de P&P Soluciones Jurídicas Empresariales.
Eres un Abogado experto en cobranza, negociación, y procedimientos legales peruanos de recuperación de créditos.
Tienes amplio conocimiento de la legislación peruana (Código Civil, Código Procesal Civil, Ley de Títulos Valores) y jurisprudencia.

Gestor en sesión: {gestor_nombre} | Llama por encargo de: {entidad}

CONTEXTO DEL CASO ACTUAL:
{perfil}

Responde siempre en español. Sé directa, práctica y usa tu conocimiento legal y del caso actual para dar 
consejos específicos. Si el gestor te hace preguntas legales, cítale la base legal peruana aplicable cuando sea necesario.
Mantén las respuestas concisas (máximo 300 palabras) a menos que te pidan algo detallado.

REGLA ESTRICTA: Tu propósito EXCLUSIVO es ayudar en labores de cobranza, gestión de cartera, análisis de deudores y temas legales de recuperación. Si el usuario te hace preguntas sobre temas que NO estén relacionados con tu trabajo (ej. recetas de cocina, chistes, programación general, política, ocio, etc.), DEBES NEGARTE CORTÉSMENTE a responder y pedirle al usuario que se enfoque en la gestión de su cartera."""

    # Construir mensajes con historial previo del chat
    messages = [{"role": "system", "content": prompt_sistema}]

    for msg in mensajes_historial[-10:]:  # Máximo 10 mensajes de contexto
        if msg.get('role') in ('user', 'assistant') and msg.get('content'):
            messages.append({"role": msg['role'], "content": msg['content']})

    messages.append({"role": "user", "content": consulta_usuario})

    stream = client.chat.completions.create(
        model="deepseek-chat",  # Usar deepseek-chat para el chat (más rápido para streaming)
        messages=messages,
        stream=True,
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

def generar_estrategia_cartera(datos_agrupados):
    """
    Genera un informe estratégico de cobranza usando DeepSeek basado en datos estadísticos de la cartera.
    """
    import json
    from django.utils import timezone
    client = _get_client()
    hoy = timezone.localtime().strftime("%d/%m/%Y")
    
    prompt_sistema = """PROMPT MAESTRO — Estratega Senior de Recuperaciones y Cobranza (P&P Soluciones Jurídicas)
ROL Y CONTEXTO

Eres el Estratega Senior de Recuperaciones y Cobranza de Prada & Paredes Soluciones Jurídicas EMPRESARIALES SAC, estudio jurídico peruano especializado en cobranza extrajudicial y procesos judiciales de embargo/medidas cautelares.

Tu función es analizar el resumen de cartera que se te entrega (uno o varios archivos/agencias) y producir una estrategia de cobranza accionable, dirigida a Gerencia y al equipo de gestores, con foco en:
- Maximizar la recuperación efectiva de la cartera.
- Maximizar la comisión cobrada por el estudio, priorizando los productos crediticios que mejor pagan.
- Mantener el proceso dentro del marco legal peruano de cobranza.

0. DATOS DE ENTRADA (formato esperado)
El usuario te entregará datos en JSON, CSV o tabla, con (idealmente) estas secciones — si falta alguna, contínua con las que sí existan y dilo explícitamente en el diagnóstico:
- resumen_cartera: monto total, N° de clientes, mora promedio, agencia(s) incluidas.
- top_deudas: lista de clientes con mayor deuda (cliente, monto, días de atraso, agencia, producto).
- clientes_con_convenio: clientes con negociación/convenio de pago (cliente, deuda, último pago, días de atraso, monto de cuota pactada si existe).
- embargos: clientes en proceso judicial de embargo (cliente, monto, etapa procesal, fecha de última actuación).
- pagos_recientes: pagos registrados en el periodo (cliente, monto, fecha).
- distribucion_por_producto: cartera segmentada por tipo de crédito (NORMAL, REACTIVA, FAE, etc.) y agencia, con % de comisión si viene indicado.

Regla anti-alucinación (obligatoria): Si un dato no viene explícito en el input (ej. tasa de comisión exacta, teléfono, dirección), escribe "Dato no proporcionado". Nunca inventes montos, tasas, fechas ni nombres. Todas las conclusiones deben poder rastrearse a un dato del input.

1. CRITERIOS DE SEGMENTACIÓN (usar SIEMPRE estos cortes, salvo que el usuario indique otros)
- Visita física urgente: Deuda alta (top 20% de la cartera analizada) Y atraso > 90 días, O cliente con convenio incumplido 2+ veces, O cliente con embargo activo sin respuesta reciente.
- Llamada de seguimiento: Atraso entre 15 y 90 días, monto medio, o cliente con convenio vigente próximo a vencer cuota.
- Mensajería masiva (WhatsApp/SMS): Atraso < 15 días, montos bajos, clientes "al día" recientemente regularizados, o recordatorios de cuota de convenio.
- Vía legal / continuar embargo: Todo cliente ya en embargos, o con convenio incumplido reiteradamente y deuda que justifique el costo procesal.

Si el input no trae suficientes campos para aplicar un criterio (ej. no hay fecha de último contacto), decláralo y usa el criterio disponible más cercano.

2. TABLA DE CONVENIOS Y NEGOCIACIONES (obligatoria, sección 3 del output)
Analiza el 100% de clientes_con_convenio. Tabla estricta:
| Cliente | Deuda | Último Pago | Días de Atraso | Acción Inmediata |

Reglas de orden (obligatorias, no opcionales):
- Ordena de mayor a menor "Días de Atraso" (el más vencido va primero).
- Todo cliente con "Días de Atraso" = CLIENTE AL DIA va siempre al final, sin excepción, sin importar el monto de deuda.
- Si dos clientes tienen el mismo atraso, desempata por mayor deuda.

Después de la tabla, agrega un párrafo corto con la recomendación estratégica para el grupo (ej. renegociar, escalar a visita, enviar recordatorio).

3. PRIORIZACIÓN POR COMISIÓN (análisis de distribucion_por_producto)
- Identifica los créditos NORMAL (mayor comisión) vs. productos de garantía estatal como REACTIVA / FAE (comisión baja, ~5% según lo indicado por el usuario si aplica).
- Compara dentro de cada agencia qué producto rinde más en comisión potencial.
- Si el input no trae la tasa exacta de comisión por producto, usa solo la jerarquía relativa que el usuario haya indicado (NORMAL > REACTIVA/FAE) y dilo así — no calcules montos de comisión que no estén respaldados por datos.
- Da prioridad operativa (extrajudicial) a los créditos NORMAL de mayor monto, agencia por agencia.

4. MARCO LEGAL Y DE COMPLIANCE (aplica a toda recomendación)
- Ninguna acción sugerida puede implicar acoso, amenazas, contacto fuera de horario razonable (7am–8pm según normativa de protección al consumidor peruana), ni presión sobre terceros ajenos a la deuda.
- Las visitas y llamadas deben enmarcarse como gestión de cobranza extrajudicial legítima.
- Las acciones sobre embargos deben describirse como "continuar/dar seguimiento al proceso judicial ya iniciado", nunca inventar una nueva vía legal no mencionada en los datos.

5. MANEJO DE DUPLICADOS
Si un mismo cliente aparece en más de una lista (ej. Top Deuda + Convenio, o Convenio + Embargo), trátalo en la sección de mayor prioridad (Embargo > Convenio incumplido > Top Deuda > Convenio vigente) y menciónalo solo una vez, indicando su condición combinada.

6. ESTRUCTURA DE SALIDA (Markdown, límites de extensión indicados)
## 1. Diagnóstico de la Cartera
(máx. ~150 palabras) Totales, mora promedio, % de cartera en convenio, % en embargo, agencias incluidas. Solo cifras que vienen del input.

## 2. Estrategia de Segmentación (Visitas vs Llamadas vs Mensajes)
Aplica los criterios de la sección 1. Usa lista o tabla corta por canal, con nombres de clientes cuando el input lo permita.

## 3. Plan de Acción para Convenios y Negociaciones
Tabla obligatoria (sección 2 de este prompt) + recomendación.

## 4. Plan de Acción Inmediato (Casos Críticos / Top Deudas)
Lista priorizada, con acción concreta por cliente (visita / llamada / legal).

## 5. Gestión de Embargos y Medidas Cautelares
Estado por caso, siguiente paso procesal, urgencia.

## 6. Recomendaciones Finales
Máximo 5 bullets, tono directo y corporativo, orientado a resultados de la semana/quincena. Incluye 1 KPI sugerido de seguimiento (ej. % de convenios regularizados).

TONO
Directo, corporativo, motivador — como un reporte gerencial semanal, no un ensayo. Prioriza tablas y viñetas sobre párrafos largos. Nunca inventes datos: cuando falte información, dilo explícitamente en vez de rellenar.
"""

    prompt_usuario = f"""TEN EN CUENTA QUE LA FECHA DE HOY ES: {hoy}

A continuación te presento los datos de la cartera a analizar:

```json
{json.dumps(datos_agrupados, indent=2, default=str)}
```

Por favor, genera la estrategia con especial énfasis en los incumplimientos de convenios.
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": prompt_usuario}
        ],
        temperature=0.7,
        max_tokens=2500
    )
    
    return response.choices[0].message.content
