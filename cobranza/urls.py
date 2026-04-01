from django.urls import path
from . import views

urlpatterns = [
    # Navegación y Gestión
    path('dashboard/', views.dashboard_gerente, name='dashboard_gerente'),
    path('bandeja-trabajo/', views.bandeja_gestor, name='bandeja_gestor'),
    path('subir-excel/', views.subir_excel, name='subir_excel'),
    path('gestionar/<int:deudor_id>/', views.registrar_gestion, name='registrar_gestion'),
    
    # Campañas y Pop-ups
    path('exportar/', views.exportar_gestiones_excel, name='exportar_gestiones_excel'),
    path('descargar-campana/', views.exportar_csv_asterisk, name='descargar_asterisk'),
    path('pop/<str:dni>/', views.buscar_por_dni, name='pop_dni'),
    
    # Salida segura
    path('logout/', views.salir_sistema, name='logout'),
    
    # Asignación de Carteras (solo gerentes)
    path('asignar-carteras/', views.asignar_carteras, name='asignar_carteras'),
    
    # Carga masiva de teléfonos (solo gerentes)
    path('cargar-telefonos/', views.cargar_telefonos, name='cargar_telefonos'),
]