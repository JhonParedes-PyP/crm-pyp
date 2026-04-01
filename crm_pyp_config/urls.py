from django.contrib import admin
from django.urls import path
from cobranza import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Panel de Administración de Django
    path('admin/', admin.site.urls),

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

    # Exportaciones y Reportes
    path('exportar-asterisk/', views.exportar_csv_asterisk, name='descargar_asterisk'),
    path('exportar-gestiones/', views.exportar_gestiones_excel, name='exportar_gestiones_excel'),
    
    # Asignación de Carteras (solo gerentes)
    path('asignar-carteras/', views.asignar_carteras, name='asignar_carteras'),
    
    # Carga masiva de teléfonos (solo gerentes)
    path('cargar-telefonos/', views.cargar_telefonos, name='cargar_telefonos'),
    
    # Campañas Asterisk (solo gerentes)
    path('subir-lista-llamadas/', views.subir_lista_llamadas, name='subir_lista_llamadas'),
    path('exportar-csv-campana/', views.exportar_csv_desde_lista, name='exportar_csv_campana'),
    
    # Campañas Asterisk con filtros (solo gerentes)
    path('campana-asterisk/', views.generar_campana_asterisk, name='generar_campana_asterisk'),
    path('exportar-todos-asterisk/', views.exportar_todos_asterisk, name='exportar_todos_asterisk'),
    path('exportar-morosos-30/', views.exportar_morosos_30, name='exportar_morosos_30'),
    path('exportar-morosos-90/', views.exportar_morosos_90, name='exportar_morosos_90'),
    path('exportar-promesas-vencidas/', views.exportar_promesas_vencidas, name='exportar_promesas_vencidas'),
    
    # NUEVA RUTA: Callback de Kubo (recibir llamada y abrir ficha del cliente)
    path('datos-cliente/<str:telefono>/<str:campana>/<str:cod_cliente>/', views.datos_cliente_kubo, name='datos_cliente_kubo'),
]