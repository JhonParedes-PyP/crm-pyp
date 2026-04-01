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
    
    # NUEVA RUTA: Asignación de Carteras (solo gerentes)
    path('asignar-carteras/', views.asignar_carteras, name='asignar_carteras'),
    
    # NUEVA RUTA: Carga masiva de teléfonos (solo gerentes)
    path('cargar-telefonos/', views.cargar_telefonos, name='cargar_telefonos'),
]