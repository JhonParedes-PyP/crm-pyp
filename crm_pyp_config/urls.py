from django.contrib import admin
from django.urls import path
from cobranza import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Panel de Administración de Django
    path('admin/', admin.site.urls),
    
    # --- API: RECIBIR GESTIÓN DESDE APP JUDICIAL ---
    path('api/v1/gestiones-campo/', views.api_recibir_gestion_campo, name='api_recibir_gestion_campo'),

    # --- API: APP MÓVIL P&P COBRANZA ---
    path('api/v1/auth/app-login/', views.api_app_login, name='api_app_login'),
    path('api/v1/app-credentials/', views.api_app_credentials, name='api_app_credentials'),

    # Autenticación y Seguridad
    path('login/', auth_views.LoginView.as_view(template_name='cobranza/login.html'), name='login'),
    path('salir/', views.salir_sistema, name='salir_sistema'),

    # Rutas Principales del CRM
    path('', views.dashboard_gerente, name='inicio'),
    path('dashboard/', views.dashboard_gerente, name='dashboard_gerente'),
    path('subir-excel/', views.subir_excel, name='subir_excel'),
    path('bandeja-gestor/', views.bandeja_gestor, name='bandeja_gestor'),
    
    # Ficha del Cliente y Acciones
    path('gestionar/<int:deudor_id>/', views.registrar_gestion, name='registrar_gestion'),
    path('buscar-dni/<str:dni>/', views.buscar_por_dni, name='buscar_por_dni'),
    
    # RUTA SECRETA: Eliminar Cliente (Solo Gerentes)
    path('eliminar-cliente/<int:deudor_id>/', views.eliminar_cliente, name='eliminar_cliente'),
    # --- NUEVA RUTA SECRETA: ELIMINAR GESTIÓN ---
    path('eliminar-gestion/<int:gestion_id>/', views.eliminar_gestion, name='eliminar_gestion'),

    # Exportaciones y Reportes
    path('exportar-asterisk/', views.exportar_csv_asterisk, name='descargar_asterisk'),
    path('exportar-gestiones/', views.exportar_gestiones_excel, name='exportar_gestiones_excel'),
    
    # Asignación de Carteras (solo gerentes)
    path('asignar-carteras/', views.asignar_carteras, name='asignar_carteras'),
    
    # Carga masiva de teléfonos (solo gerentes)
    path('cargar-telefonos/', views.cargar_telefonos, name='cargar_telefonos'),
    
    # Campañas Asterisk Antiguas (solo gerentes)
    path('subir-lista-llamadas/', views.subir_lista_llamadas, name='subir_lista_llamadas'),
    path('exportar-csv-campana/', views.exportar_csv_desde_lista, name='exportar_csv_campana'),
    path('campana-asterisk/', views.generar_campana_asterisk, name='generar_campana_asterisk'),
    path('exportar-todos-asterisk/', views.exportar_todos_asterisk, name='exportar_todos_asterisk'),
    path('exportar-morosos-30/', views.exportar_morosos_30, name='exportar_morosos_30'),
    path('exportar-morosos-90/', views.exportar_morosos_90, name='exportar_morosos_90'),
    path('exportar-promesas-vencidas/', views.exportar_promesas_vencidas, name='exportar_promesas_vencidas'),
    
    # --- NUEVO MÓDULO ASTERISK P&P (EL QUE CREAMOS HOY) ---
    path('campanas-asterisk/', views.panel_campanas_asterisk, name='panel_campanas'),
    path('campanas-asterisk/descargar/<int:campana_id>/', views.descargar_csv_campana, name='descargar_csv_campana'),

    # Ruta para callback de Kubo (con 4 parámetros)
    path('datos-cliente/<str:telefono>/<str:campana>/<str:cod_cliente>/<str:cod_telefono>/', views.datos_cliente_kubo, name='datos_cliente_kubo'),
    # --- RUTA DE SEGURIDAD WEBRTC ZADARMA ---
    path('api/webrtc-key/', views.api_zadarma_webrtc_key, name='api_zadarma_webrtc_key'),
    # crm_pyp_config/urls.py
    path('iniciar-llamada/<str:numero_cliente>/', views.iniciar_callback, name='iniciar_callback'),
]