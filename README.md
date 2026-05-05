# CRM PyP - Sistema de Gestión de Cobranzas

## 📌 Descripción General
Este es el repositorio del sistema CRM de PyP Soluciones Jurídicas Empresariales, desarrollado en **Django (Python)**. El sistema gestiona deudores, carteras de cobranza, seguimiento de llamadas, integraciones con SIP/WebRTC (Zadarma/Asterisk) y asignaciones dinámicas a agentes de cobranza y supervisores.

---

## 🚀 Últimos Avances y Mejoras Implementadas

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
- **Backend:** Django 5.x / Python 3.x
- **Base de Datos:** SQLite / PostgreSQL (según entorno).
- **Servidor Web:** Gunicorn + Nginx (Producción en Linux).
- **Frontend:** HTML5, CSS3, Vanilla JS, Jinja Templating.
- **VoIP / SIP:** Janus WebRTC, Zadarma, Dialers con Asterisk.

## ⚙️ Uso Básico del Deployment
Para enviar los últimos cambios locales al servidor de producción, se ejecuta desde la raíz del proyecto Windows:

```powershell
py deploy.py
```
*(Este script entra por SSH al servidor, jala los cambios desde Git, actualiza dependencias y reinicia Gunicorn).*
