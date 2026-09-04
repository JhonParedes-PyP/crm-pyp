import os

file_path = r'c:\CRM PYP\cobranza\judicial_views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add import
if "from .asignaciones import aplicar_visibilidad_por_asignaciones" not in content:
    content = content.replace("from django.db.models import Q", "from django.db.models import Q\nfrom .asignaciones import aplicar_visibilidad_por_asignaciones")

# 2. Update dashboard_judicial
old_dash = """def dashboard_judicial(request):
    if not request.user.is_superuser and not request.user.groups.filter(name='Gerencia').exists():
        pass # Depending on auth, might allow legal assistants too

    hoy = date.today()
    fin_semana = hoy + timedelta(days=7)

    alertas_hoy = AlertaJudicial.objects.filter(estado='PENDIENTE', fecha_vencimiento__lte=hoy).count()
    alertas_semana = AlertaJudicial.objects.filter(estado='PENDIENTE', fecha_vencimiento__gt=hoy, fecha_vencimiento__lte=fin_semana).count()
    total_activos = ExpedienteJudicial.objects.filter(estado_proceso='ACTIVO').count()

    # List pending alerts
    alertas_pendientes = AlertaJudicial.objects.filter(estado='PENDIENTE').select_related('expediente__deudor').order_by('fecha_vencimiento')"""

new_dash = """def dashboard_judicial(request):
    hoy = date.today()
    fin_semana = hoy + timedelta(days=7)

    qs_alertas = aplicar_visibilidad_por_asignaciones(AlertaJudicial.objects.all(), request.user, related_prefix='expediente__deudor__')
    qs_exp = aplicar_visibilidad_por_asignaciones(ExpedienteJudicial.objects.all(), request.user, related_prefix='deudor__')

    alertas_hoy = qs_alertas.filter(estado='PENDIENTE', fecha_vencimiento__lte=hoy).count()
    alertas_semana = qs_alertas.filter(estado='PENDIENTE', fecha_vencimiento__gt=hoy, fecha_vencimiento__lte=fin_semana).count()
    total_activos = qs_exp.filter(estado_proceso='ACTIVO').count()

    # List pending alerts
    alertas_pendientes = qs_alertas.filter(estado='PENDIENTE').select_related('expediente__deudor').order_by('fecha_vencimiento')"""
content = content.replace(old_dash, new_dash)

# 3. Update buscar_expediente
old_buscar = """    # We only show results if a search or filter was applied
    if query or cartera_q or agencia_q:
        qs = ExpedienteJudicial.objects.all()"""

new_buscar = """    # We only show results if a search or filter was applied
    if query or cartera_q or agencia_q:
        qs = aplicar_visibilidad_por_asignaciones(ExpedienteJudicial.objects.all(), request.user, related_prefix='deudor__')"""
content = content.replace(old_buscar, new_buscar)

# 4. Update detalle_expediente
old_detalle = """def detalle_expediente(request, expediente_id):
    expediente = get_object_or_404(ExpedienteJudicial, id=expediente_id)"""

new_detalle = """def detalle_expediente(request, expediente_id):
    qs_exp = aplicar_visibilidad_por_asignaciones(ExpedienteJudicial.objects.all(), request.user, related_prefix='deudor__')
    expediente = get_object_or_404(qs_exp, id=expediente_id)"""
content = content.replace(old_detalle, new_detalle)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("judicial_views.py updated successfully.")
