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


def optimizar_ruta_ia(clientes):
    """
    Recibe una lista de diccionarios con la información de los clientes (nombre, distrito, direccion)
    y usa DeepSeek para sugerir el orden geográfico óptimo de visita.
    """
    client = _get_client()
    
    texto_clientes = "LISTA DE CLIENTES A VISITAR:\n"
    for i, c in enumerate(clientes, 1):
        texto_clientes += f"{i}. {c.get('nombre')} | Distrito: {c.get('distrito')} | Dirección: {c.get('direccion')}\n"
        
    prompt_sistema = """Eres un experto en logística urbana y conocimiento geográfico del Perú (especialmente Huancayo, Junín y Lima).
Tu objetivo es organizar una lista de direcciones de deudores para sugerir la RUTA DE COBRANZA MÁS EFICIENTE posible.
Agrupa los clientes por distritos cercanos o zonas adyacentes para evitar cruzar la ciudad innecesariamente.
Devuelve el resultado enumerado paso a paso, recomendando en qué orden visitarlos.
Sé directo y conciso. No uses introducciones largas."""

    prompt_usuario = f"""Por favor, ordena la siguiente lista de clientes en la ruta más óptima:
{texto_clientes}"""

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
