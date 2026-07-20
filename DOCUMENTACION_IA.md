# Documentación Técnica de P&P Cobranza (App Cliente)

Este documento describe la arquitectura, la estructura de datos y las integraciones de la aplicación de escritorio P&P Cobranza. **Su propósito es servir como contexto técnico integral para cualquier Inteligencia Artificial (IA) o desarrollador que necesite comprender cómo funciona la app, cómo está estructurada la información y cómo interconectarse con ella.**

---

## 1. Descripción General
- **Plataforma:** Aplicación de escritorio/móvil basada en Python.
- **Framework de UI:** [Flet](https://flet.dev/) (basado en Flutter).
- **Propósito:** Gestión de cobranza (judicial y extrajudicial) para agentes en campo y en oficina.
- **Flujo Principal:** 
  1. El agente inicia sesión.
  2. La app descarga la "cartera" asignada a ese agente desde el CRM principal (vía REST API).
  3. El agente busca clientes, visualiza sus datos y registra acciones: guardar ubicaciones GPS, evidencias fotográficas, o "gestiones" (notas de seguimiento).
  4. La app envía estos registros al CRM en tiempo real y actualiza su caché local en memoria.

---

## 2. Estructura del Proyecto
El código base se encuentra organizado principalmente en el directorio raíz y en la carpeta `app/`:

- `main.py`: Punto de entrada de la aplicación. Maneja el estado global, el enrutamiento visual (ocultar/mostrar columnas) y los eventos principales de UI.
- `app/columnas.py`: Define la clase estática `Columnas` que mapea cada campo de la base de datos a un índice numérico entero. **Es el núcleo para entender cómo se lee la lista de datos local**.
- `app/services/gestor_cobranza.py`: Clase `GestorCobranza` (Singleton). Se encarga de descargar la cartera (`GET`), mantener el caché en memoria para búsquedas ultra rápidas, y hacer peticiones `PATCH` al CRM para actualizar campos específicos.
- `app/services/crm_api.py`: Contiene funciones que interactúan con endpoints independientes (no atados a una fila de la cartera). Por ejemplo: `verificar_login` y `enviar_gestion_campo` (`POST`).
- `app/ui/`: Carpeta con los componentes visuales modulares de la aplicación (Login, Menú, Búsqueda, Vista Judicial, Vista Extrajudicial).

---

## 3. Modelo de Datos (Caché en Memoria)

Para optimizar el rendimiento, la aplicación lee los diccionarios JSON provenientes del CRM y los convierte en **Listas Posicionales** de longitud fija (37 elementos: índices 0 al 36).

### A. Columnas Principales del CRM (0 a 32)
Estas provienen directamente de la base de datos central de cobranzas.
* `0`: CARTERA_TIPO
* `1`: CUENTA / COD_CREDITO
* `2`: NOMBRE / NOM_CLI
* `3`: PRODUCTO
* `4`: NMES
* `5`: INGRESO_JUDICIAL
* `6`: AGENCIA
* `7`: DNI / DOC_DNI_RUC
* `8`: DIRECCION
* `9`: DEPARTAMENTO
* `10`: PROVINCIA
* `11`: DISTRITO
* `12`: DIR_NEGOCIO
* `13`: TELEFONO
* `14`: CAPITAL
* `15`: TOTAL (Deuda)
* `16 a 32`: Otros campos legales y de seguimiento (Proceso, Juzgado, Condición, Zona, Último pago, etc.)

### B. Columnas Extra / Gestionadas por la App (33 a 36)
Son variables que la App actualiza vía API para enriquecer la base de datos:
* `33`: LINK_GPS
* `34`: LINK_GPS_AVAL
* `35`: GESTION_EXTRA (Histórico concatenado de gestiones del agente)
* `36`: FOTO_EVIDENCIA

---

## 4. Endpoints y Conexión (Para Interconexión)

Las variables de entorno y URLs base están definidas en `app.config`. La aplicación se conecta con un CRM remoto protegido con un Bearer Token.

Si otra IA o sistema requiere enviar o proveer datos a esta App (o replicar su comportamiento), debe respetar los siguientes Endpoints:

### A. Autenticación / Login
- **URL:** `API_LOGIN_URL`
- **Método:** `POST`
- **Payload:** `{"username": "<usuario>", "password": "<clave>"}`
- **Descripción:** Valida credenciales. Devuelve HTTP 200 si es exitoso.

### B. Obtención de Cartera (Paginada)
- **URL:** `API_CARTERA_URL`
- **Método:** `GET`
- **Query Params:** `?agente=<USERNAME>&page=<N>&page_size=500`
- **Respuesta Esperada:** 
  ```json
  {
    "data": [
      {
        "fila_id": 1234,
        "nombre": "JUAN PEREZ",
        "dni": "12345678",
        ...
      }
    ],
    "has_more": true
  }
  ```
- **Nota:** La app mapea las llaves del JSON a las posiciones de la lista descritas en la sección 3.

### C. Actualización de Campos Específicos
- **URL:** `API_CARTERA_URL{fila_id}/` (Ej: `.../cartera/1234/`)
- **Método:** `PATCH`
- **Headers:** `Authorization: Bearer <TOKEN_CRM>`
- **Payload:** Modificaciones parciales, ej. `{"link_gps": "https://maps.google.com/..."}`

### D. Registro de Gestiones de Campo
- **URL:** `API_CRM_URL`
- **Método:** `POST`
- **Headers:** `Authorization: Bearer <TOKEN_CRM>`
- **Payload Esperado:**
  ```json
  {
      "dni": "12345678",
      "resultado": "GESTIÓN DE CAMPO",
      "observacion": "El cliente indicó que pagará mañana...",
      "gestor_username": "JUAN_AGENTE"
  }
  ```

---

## 5. Notas Importantes para Interacción Futura

1. **Gestión de Sesión:** Si la App detecta 5 minutos de inactividad de red o UI, cierra la sesión automáticamente por seguridad.
2. **Offline Mode Parcial:** Actualmente actualiza la memoria caché `GestorCobranza._cache_datos` sin importar si la red falla, pero los envíos al CRM fallarán si no hay internet (Excepto en intentos de 3 retries para las gestiones).
3. **Nuevos Funcionalidades Planificadas:** 
   - *Carga Masiva de Gestiones:* Se habilitará la lectura de archivos CSV/Excel localmente, los cuales iterarán sobre el Endpoint **D** de arriba para envíos en lote.
