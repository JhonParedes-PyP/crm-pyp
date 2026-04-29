# Integración WebRTC Janus (CRM P&P)

Este documento guarda la memoria técnica y arquitectónica de cómo se resolvió la integración nativa de telefonía IPBusiness (Asterisk/Janus) dentro del CRM en Django. Cualquier futuro agente (IA) o desarrollador debe leer esto antes de modificar la lógica de telefonía.

## 1. Arquitectura de Conexión (Sin VPN)
El sistema utiliza **WebRTC** a través del motor `Janus`. 
- **WebSocket Gateway:** `wss://wrtc2.ipb.com.pe:8989/janus`
- **SIP Proxy Interno (Asterisk):** `192.168.199.129:5060`

**Punto Clave:** Como el navegador del agente se conecta directamente al servidor Janus (que es público), **NO ES NECESARIO** que el agente esté conectado a una VPN. Janus recibe la petición pública y la enruta internamente hacia Asterisk.

## 2. Filtro CORS y Pruebas Locales
El servidor `wrtc2.ipb.com.pe` tiene configurado un filtro de **Allowed Origins (CORS)**.
- Solo acepta conexiones WebSocket desde `https://pyp.ipb.pe` y `https://crm.pypsolucionesjuridicas.com`.
- **Error 403 Forbidden en el navegador (Localhost):** Si se prueba en `http://localhost:8000`, la conexión WebSocket será rechazada inmediatamente con un error `403 Forbidden` porque `localhost` no está en la lista blanca. 
- **Solución para Desarrollo Local:** Para probar localmente, se debe usar una extensión de navegador (ej. *ModHeader*) para falsificar la cabecera HTTP `Origin` y enviarla como `https://pyp.ipb.pe`.

## 3. Algoritmo de Cifrado de Claves SIP (El Problema Resuelto)
El mayor obstáculo de la integración fue un error `403 Forbidden` devuelto directamente por el Asterisk (SIP) indicando contraseña incorrecta, a pesar de usar la contraseña del archivo Excel original (`ANEXOS Y CLAVES.xlsx`).

### ¿Por qué fallaba?
IPBusiness no entregó contraseñas crudas en su Excel, sino que entregó cadenas **ya ofuscadas**. La estructura de las cadenas en el Excel era:
`[Prefijo "0b"] + [Contraseña Real] + [20 Caracteres Aleatorios]`

Ejemplo (JPAREDES): `0baZ7@Kp#3mLx9wT2[QvBfEoYdN8rJcMu.sHa276527b4b69e8f95aa73`
- Prefijo: `0b`
- Contraseña Real: `aZ7@Kp#3mLx9wT2[QvBfEoYdN8rJcMu.sHa`
- Basura IPB: `276527b4b69e8f95aa73`

### La Solución en `api_views.py`
Para que el archivo `sip.js` local (o remoto de IPB) funcione correctamente, en `cobranza/api_views.py` se implementó la siguiente lógica al vuelo:
1. Extrae la clave ofuscada de la Base de Datos (`AgenteSIP`).
2. Verifica si empieza con `0b`. Si es así, **recorta los 2 primeros caracteres y los últimos 20 caracteres** mediante `clave_db[2:-20]`. Esto aísla la contraseña real y cruda.
3. Se aplica un nuevo bloque de ofuscación (`basura = "ABCDEFGHIJKLMNOPQRSTUV"` -> 22 caracteres) requerido por la lógica frontend que se copió de IPBusiness.
4. El frontend (`base.html`) toma los primeros 20 caracteres como `service_account_email` y el `sip.js` recorta 22 caracteres en total, revelando la contraseña real limpia para enviarla a Asterisk.

Con esto, el sistema es agnóstico: permite a cualquier agente loguearse y automáticamente descifra y re-empaca su contraseña de anexo sin intervención manual.

## 4. Próximos Pasos: Llamadas Progresivas y Screen Pop (CTI)
Está planificado para el futuro implementar el **Screen Pop** para el motor de campañas progresivas de Asterisk. El flujo acordado será:
1. Al subir el CSV de campaña, Asterisk guardará el `TELEFONO` y `COD_CLIENTE`.
2. Cuando el cliente conteste y Asterisk asigne la llamada al Webphone del agente, IPBusiness inyectará el `COD_CLIENTE` o Caller ID en los **Headers SIP** de la llamada.
3. El archivo `sip.js` local deberá ser modificado en la sección de "incoming call" para extraer ese Header SIP.
4. Una vez extraído el código, Javascript hará un redireccionamiento automático (ej. `window.location.href = ...` o abrirá un modal) a la vista de gestión correspondiente para que el agente vea los datos del cliente al instante.
