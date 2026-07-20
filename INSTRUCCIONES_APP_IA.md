# Instrucciones Clave para la IA Desarrolladora de la App (Flet)

**Contexto para la IA:**
Estás desarrollando la aplicación cliente (escritorio/móvil) "P&P Cobranza" construida en el framework **Flet** (Python). Esta aplicación debe comunicarse con nuestro backend centralizado en Django (el CRM) a través de una API RESTful. 

A continuación, te proporciono la documentación consolidada de cómo está estructurada la memoria de tu app y cómo debes consumir los endpoints del CRM para implementar la funcionalidad de **Geolocalización (GPS) y Gestiones de Campo**.

---

## 1. Estructura de Datos en la App (Caché Local)
Tu aplicación recibe los datos del CRM y los almacena en memoria usando **Listas Posicionales de 37 elementos**. Las columnas relevantes para las funciones de GPS y ubicación son:
- `Índice 2`: NOMBRE DEL CLIENTE
- `Índice 7`: DNI
- `Índice 8`: DIRECCIÓN (Texto)
- `Índice 11`: DISTRITO
- **`Índice 33`: LINK_GPS** (Coordenadas o enlace de Maps del titular)
- **`Índice 34`: LINK_GPS_AVAL** (Coordenadas o enlace de Maps del aval)
- **`Índice 35`: GESTION_EXTRA** (Notas de campo)
- **`Índice 36`: FOTO_EVIDENCIA** (URL de la foto de fachada)

*(Referencia: Archivo `app/columnas.py` en tu estructura Flet).*

---

## 2. Requerimientos de Funcionalidad UI (Lo que debes programar)

### A. Visualización de la Ubicación (Para el Gestor)
En la vista de detalles del cliente (Judicial/Extrajudicial), debes agregar un botón interactivo (ej. un `ft.IconButton` con ícono de mapa). 
- Si el `Índice 33` (LINK_GPS) tiene datos, el botón debe abrir directamente ese enlace en el navegador (`page.launch_url`).
- Si está vacío, puede construir una búsqueda combinando el `Índice 8` y `Índice 11` (Dirección + Distrito, Peru) usando el formato:
  `https://www.google.com/maps/search/?api=1&query={direccion}`

### B. Captura y Envío de Coordenadas (Actualización PATCH)
Debes proveer una interfaz donde el gestor, al estar en la puerta del cliente, pueda guardar las coordenadas actuales. 
- **Endpoint a consumir:** `PATCH /api/v1/cartera/{fila_id}/`
- **Autenticación:** Header `Authorization: Bearer PYP-CAMPO-2026`
- **Formato:** Debes enviar un `multipart/form-data`.
- **Campos a enviar:** 
  - `link_gps`: (String) Las coordenadas capturadas.
  - *(Opcional)* `foto_evidencia`: (File) Archivo adjunto de la cámara.
- **Acción local:** Si el servidor responde `200 OK`, debes actualizar el `Índice 33` y `Índice 36` en tu caché local (`GestorCobranza._cache_datos`) para no tener que recargar toda la cartera.

### C. Registro de la Gestión de Campo (POST)
Cuando el gestor termina la visita, debe registrar qué pasó.
- **Endpoint a consumir:** `POST /api/v1/gestiones-campo/` (O la ruta que tengas en `API_CRM_URL`).
- **Autenticación:** Header `Authorization: Bearer PYP-CAMPO-2026`
- **Formato:** `application/json`
- **Payload:**
  ```json
  {
      "dni": "<Valor del Índice 7>",
      "resultado": "CLIENTE VISITADO",
      "observacion": "<Lo que el gestor escribió en el TextField>",
      "gestor_username": "<Usuario logueado actualmente>"
  }
  ```

---

## 3. Notas Técnicas
- **Offline Mode:** Recuerda la regla del proyecto. Si no hay conexión a internet (excepción `requests.exceptions.ConnectionError`), debes manejar el error con un `SnackBar` avisando al usuario, pero la actualización del caché local (Listas) se debe intentar mantener sincronizada cuando vuelva la red.
- **Seguridad:** Nunca hardcodees el token `PYP-CAMPO-2026` directamente en los componentes de UI, úsalo a nivel de los servicios (`app/services/gestor_cobranza.py`).
