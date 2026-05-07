# CRM PyP - Sistema de Gestión de Cobranzas

## 📌 Descripción General
Este es el repositorio del sistema CRM de PyP Soluciones Jurídicas Empresariales, desarrollado en **Django (Python)**. El sistema gestiona deudores, carteras de cobranza, seguimiento de llamadas, integraciones con SIP/WebRTC (Zadarma/Asterisk), asignaciones dinámicas a agentes y ahora cuenta con un **Asistente de Inteligencia Artificial** integrado.

---

## 🚀 Últimos Avances y Mejoras Implementadas

---

### 🤖 [06/05/2026] — Integración de IA DeepSeek (Asistente PP)

Se integró la API de **DeepSeek V3 (deepseek-chat)** directamente en la ficha de cada deudor mediante un asistente llamado **PP** (P&P Soluciones Jurídicas). Esta integración es completamente contextual: la IA conoce el perfil completo del deudor, su historial de gestiones, el gestor logueado y la entidad mandante (cartera).

#### 📁 Archivos creados/modificados:

| Archivo | Cambio |
|---------|--------|
| `cobranza/ai_service.py` | **NUEVO** — Motor central de IA con 3 funciones |
| `cobranza/api_views.py` | 3 endpoints REST de IA agregados |
| `cobranza/templates/cobranza/gestionar.html` | Panel visual ARIA/PP con chat en tiempo real |
| `crm_pyp_config/urls.py` | 3 rutas nuevas registradas |
| `.env` | Variable `DEEPSEEK_API_KEY` agregada |
| `deploy.py` | Actualizado para subir `ai_service.py` e instalar `openai` en el venv del servidor |

#### 🧠 Funcionalidades de la IA:

**1. 📋 Resumen Ejecutivo del Caso** — `GET /api/ai/resumen/<deudor_id>/`
- Analiza todo el historial de gestiones del deudor (hasta 15 registros)
- Detecta patrones de comportamiento (promesas incumplidas, pagos tardíos, etc.)
- Asigna nivel de riesgo: **ALTO / MEDIO / BAJO**
- Recomienda la táctica para la próxima gestión

**2. 📞 Guión de Llamada Personalizado** — `GET /api/ai/guion/<deudor_id>/`
- Genera un script de cobranza listo para usar
- Identifica al gestor por su nombre (ej: `JPAREDES`) y la entidad mandante (ej: `Caja Huancayo`, `Proempresa`, `Focmac`)
- Incluye apertura, verificación, propósito, negociación, manejo de objeciones y cierre
- Adapta el tono según el historial: más firme con promesas incumplidas, más amigable en primer contacto

**3. 💬 Chat en Tiempo Real con PP** — `POST /api/ai/chat/<deudor_id>/`
- Chat conversacional con **streaming SSE** (el texto aparece en tiempo real)
- Mantiene contexto del historial de la conversación (hasta 10 mensajes)
- El asistente conoce el caso completo antes de responder
- Soporta `Ctrl+Enter` para enviar rápido

#### 🎨 Panel visual "PP" en la ficha del deudor:
- Diseño premium con fondo oscuro degradado (`#0f0c29 → #302b63 → #24243e`)
- Botones con gradientes de color diferenciados por función
- Burbujas de chat estilo WhatsApp
- Cursor parpadeante durante el streaming
- Colapsable con botón "Minimizar / Expandir"

#### ⚙️ Detalles técnicos:
- **Modelo:** `deepseek-chat` (DeepSeek V3) — respuesta en 3-5 segundos
- **SDK:** `openai` (compatible con la API de DeepSeek via `base_url`)
- **Streaming:** Server-Sent Events (SSE) con `StreamingHttpResponse` de Django
- **Seguridad:** Todos los endpoints protegidos con `@login_required`
- **Personalización:** Cada prompt incluye el nombre del gestor (`request.user`) y la entidad según la cartera del deudor

#### 🗺️ Mapa de entidades por cartera:
```python
entidades = {
    'CAJA HUANCAYO': 'Caja Huancayo',
    'PROEMPRESA':    'Proempresa',
    'FOCMAC':        'Focmac',
}
```

---

### 1. Sistema de Alertas de Pagos por Vencer (Ventana Bloqueante)
Se ha implementado una lógica estricta para asegurar el seguimiento de los pagos de los clientes:
- **Cálculo Automático**: El sistema calcula la **próxima fecha de pago** automáticamente sumando 30 días al campo `ultimo_dia_pago`.
- **Ventana Flotante Obligatoria**: Si un cliente tiene su próxima fecha de pago entre "hoy" y "dentro de 2 días", al gestor le aparecerá una **ventana oscura bloqueante** cubriendo toda la pantalla tanto en la **Bandeja** como en la **Agenda**.
- **Forzado de Gestión**: La ventana no permite hacer clics fuera de ella. Obliga al agente a dar clic en **"Gestionar"** para registrar una acción sobre el deudor. Una vez gestionado en el día actual, desaparece del listado de bloqueo.

### 2. Privilegios de Superusuario (Bypass del Bloqueo)
- Se incorporó un botón especial **"Cerrar (JPAREDES)"** dentro del modal bloqueante.
- **Acceso Exclusivo**: Solo el administrador/supervisor principal (`JPAREDES`) puede visualizar este botón, lo cual le permite cerrar la alerta obligatoria, restaurar el scroll de la página y continuar explorando o buscando deudores libremente por la plataforma sin ser forzado a gestionar inmediatamente.

### 3. Badge Global de Notificación
- Se agregó un **Badge Naranja Notificador** en el menú de navegación general (sidebar izquierdo) para las opciones de **Bandeja** / **Bandeja General**.
- Muestra el conteo exacto de los clientes cuyos pagos están próximos a vencer.
- Se actualiza en tiempo real de acuerdo a la visibilidad del usuario (los gestores normales solo ven la cuenta de sus propias carteras asignadas, mientras que los gerentes ven el panorama completo).

### 4. Flujo de Despliegue (Deploy) Optimizado
- Se perfeccionó el archivo `deploy.py` para asegurar integraciones CI/CD locales exitosas.
- Se implementó un reajuste forzado (`git fetch origin && git reset --hard origin/main`) en el servidor Ubuntu durante el pase a producción, previniendo posibles conflictos ("merge conflicts") ocasionados por la modificación en vivo de archivos .py directamente en producción.

---

## 🛠 Entorno y Tecnologías
- **Backend:** Django 6.x / Python 3.x
- **Base de Datos:** PostgreSQL (producción) / SQLite (desarrollo local).
- **Servidor Web:** Gunicorn + Nginx (Producción en Linux Ubuntu).
- **Frontend:** HTML5, CSS3, Vanilla JS, Django Templating.
- **VoIP / SIP:** Janus WebRTC, Zadarma, Dialers con Asterisk.
- **Inteligencia Artificial:** DeepSeek V3 API (`deepseek-chat`) vía OpenAI SDK compatible.

---

## ⚙️ Flujo de Deployment
Para enviar los últimos cambios locales al servidor de producción:

```powershell
# 1. Guardar cambios en Git
git add .
git commit -m "descripción del cambio"
git push origin main

# 2. Deploy al servidor (SSH + git pull + install + migrate + restart)
py deploy.py
```

> El script `deploy.py` conecta por SSH al servidor `134.209.76.91`, jala los cambios desde GitHub, sube el `.env` actualizado, instala dependencias nuevas en el `venv`, aplica migraciones y reinicia Gunicorn automáticamente.

---

## 🔑 Variables de Entorno requeridas (`.env`)

```env
DJANGO_SECRET_KEY=...
DJANGO_DEBUG=True
DB_NAME=pyp_db
DB_USER=postgres
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=5432
ZADARMA_KEY=...
ZADARMA_SECRET=...
ZADARMA_SIP=...
ZADARMA_API_TOKEN=...
DEEPSEEK_API_KEY=sk-...   ← Clave de la IA DeepSeek
```

> ⚠️ El archivo `.env` está en `.gitignore` y **nunca se sube a GitHub**. El `deploy.py` lo sube directamente al servidor vía SFTP.
