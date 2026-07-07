from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from cobranza import views, api_views, campanas_views, dashboard_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Panel de Administración de Django
    path('admin/', admin.site.urls),

    # --- API: RECIBIR GESTIÓN DESDE APP JUDICIAL ---
    path('api/v1/gestiones-campo/', api_views.api_recibir_gestion_campo, name='api_recibir_gestion_campo'),

    # --- API: APP MÓVIL P&P COBRANZA ---
    path('api/v1/auth/app-login/', api_views.api_app_login, name='api_app_login'),
    path('api/v1/app-credentials/', api_views.api_app_credentials, name='api_app_credentials'),
    path('api/v1/cartera/', api_views.api_cartera_lista, name='api_cartera_lista'),
    path('api/v1/cartera/<int:fila_id>/', api_views.api_cartera_patch, name='api_cartera_patch'),

    # Autenticación y Seguridad
    path('login/', auth_views.LoginView.as_view(template_name='cobranza/login.html'), name='login'),
    path('salir/', views.salir_sistema, name='salir_sistema'),

    # WebPhone Popup
    path('webphone/', views.webphone_popup, name='webphone_popup'),

    # Dashboard y Reportes
    path('', dashboard_views.dashboard_gerente, name='inicio'),
    path('dashboard/', dashboard_views.dashboard_gerente, name='dashboard_gerente'),
    path('dashboard/buscar/', dashboard_views.buscar_cliente_rapido, name='buscar_cliente_rapido'),
    path('exportar-gestiones/', dashboard_views.exportar_gestiones_excel, name='exportar_gestiones_excel'),

    # Agenda Diaria
    path('agenda/', dashboard_views.agenda_diaria, name='agenda_diaria'),
    path('agenda/completar/<int:seguimiento_id>/', dashboard_views.marcar_seguimiento_completado, name='marcar_seguimiento_completado'),
    path('agenda/alertas/', dashboard_views.comprobar_alertas_seguimiento, name='comprobar_alertas_seguimiento'),

    # Rutas Principales del CRM
    path('subir-excel/', views.subir_excel, name='subir_excel'),
    path('subir-gestiones/', views.subir_gestiones_masivas, name='subir_gestiones_masivas'),
    path('bandeja-gestor/', views.bandeja_gestor, name='bandeja_gestor'),

    # Ficha del Cliente y Acciones
    path('gestionar/<int:deudor_id>/', views.registrar_gestion, name='registrar_gestion'),
    path('gestionar/<int:deudor_id>/verificar-telefono/', views.verificar_telefono_duplicado, name='verificar_telefono_duplicado'),
    path('buscar-dni/<str:dni>/', views.buscar_por_dni, name='buscar_por_dni'),

    # RUTA SECRETA: Eliminar Cliente (Solo Gerentes)
    path('eliminar-cliente/<int:deudor_id>/', views.eliminar_cliente, name='eliminar_cliente'),
    # RUTA SECRETA: Eliminar Gestión (Solo Gerentes)
    path('eliminar-gestion/<int:gestion_id>/', views.eliminar_gestion, name='eliminar_gestion'),
    path('eliminar-contacto/<int:deudor_id>/<str:tipo_contacto>/', views.eliminar_contacto_cliente, name='eliminar_contacto_cliente'),
    path('eliminar-telefono-extra/<int:telefono_id>/', views.eliminar_telefono_extra, name='eliminar_telefono_extra'),

    # Asignación de Carteras (solo gerentes)
    path('asignar-carteras/', views.asignar_carteras, name='asignar_carteras'),
    path('asignaciones-diarias/', views.asignaciones_diarias, name='asignaciones_diarias'),

    # Carga masiva de teléfonos (solo gerentes)
    path('cargar-telefonos/', views.cargar_telefonos, name='cargar_telefonos'),

    # --- MÓDULO CAMPAÑAS ASTERISK ---
    path('campanas-asterisk/', campanas_views.panel_campanas_asterisk, name='panel_campanas'),
    path('campanas-asterisk/descargar/<int:campana_id>/', campanas_views.descargar_csv_campana, name='descargar_csv_campana'),

    # Ruta callback de Kubo (captura cualquier dato extra encriptado que tenga barras)
    path('datos-cliente/<str:telefono>/<str:campana>/<path:datos_extra>', campanas_views.datos_cliente_kubo, name='datos_cliente_kubo'),

    # --- ZADARMA WebRTC / Callback ---
    path('api/webrtc-key/', api_views.api_zadarma_webrtc_key, name='api_zadarma_webrtc_key'),
    path('iniciar-llamada/<str:numero_cliente>/', api_views.iniciar_callback, name='iniciar_callback'),

    # --- 🤖 DEEPSEEK AI ASSISTANT ---
    path('api/ai/resumen/<int:deudor_id>/', api_views.api_ai_resumen, name='api_ai_resumen'),
    path('api/ai/guion/<int:deudor_id>/', api_views.api_ai_guion, name='api_ai_guion'),
    path('api/ai/chat/<int:deudor_id>/', api_views.api_ai_chat, name='api_ai_chat'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
