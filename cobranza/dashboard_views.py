from .models import *
from .views import es_gerente
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
import csv
import openpyxl

@login_required
def dashboard_gerente(request):
    hoy = timezone.now().date()
    es_gerente_flag = es_gerente(request.user)
    
    periodo = request.GET.get('periodo', 'hoy')
    
    if periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=7)
        periodo_texto = "Últimos 7 días"
    elif periodo == 'mes':
        fecha_inicio = hoy - timedelta(days=30)
        periodo_texto = "Últimos 30 días"
    else:
        fecha_inicio = hoy
        periodo_texto = "Hoy"
    
    total_deudores = Deudor.objects.count()
    total_cartera = Deudor.objects.aggregate(Sum('saldo_deuda'))['saldo_deuda__sum'] or 0
    total_recuperado = Gestion.objects.aggregate(Sum('monto_pago'))['monto_pago__sum'] or 0
    
    stats_pago = Gestion.objects.filter(
        resultado__icontains='PAGO',
        fecha__date__gte=fecha_inicio
    ).count()
    
    stats_promesa = Gestion.objects.filter(
        resultado__icontains='PROMESA',
        fecha__date__gte=fecha_inicio
    ).count()
    
    productividad = User.objects.annotate(
        total_gestiones=Count('gestion', filter=Q(gestion__fecha__date__gte=fecha_inicio)),
        total_pagos=Count('gestion', filter=Q(gestion__fecha__date__gte=fecha_inicio, gestion__resultado__icontains='PAGO')),
        total_promesas=Count('gestion', filter=Q(gestion__fecha__date__gte=fecha_inicio, gestion__resultado__icontains='PROMESA')),
        monto_recuperado=Sum('gestion__monto_pago', filter=Q(gestion__fecha__date__gte=fecha_inicio))
    ).filter(total_gestiones__gt=0).order_by('-total_gestiones')
    
    gestores_nombres = [g.username.upper() for g in productividad]
    gestores_gestiones = [g.total_gestiones for g in productividad]
    gestores_montos = [float(g.monto_recuperado or 0) for g in productividad]
    
    return render(request, 'cobranza/dashboard.html', {
        'es_gerente': es_gerente_flag,
        'total_cartera': total_cartera,
        'total_recuperado': total_recuperado,
        'total_deudores': total_deudores,
        'productividad': productividad,
        'grafico_labels': ['Pagos', 'Promesas'],
        'grafico_data': [stats_pago, stats_promesa],
        'periodo': periodo,
        'periodo_texto': periodo_texto,
        'gestores_nombres': gestores_nombres,
        'gestores_gestiones': gestores_gestiones,
        'gestores_montos': gestores_montos,
    })

@login_required
def exportar_gestiones_excel(request):
    if not es_gerente(request.user):
        return HttpResponse("Acceso Denegado.", status=403)
    gestiones = Gestion.objects.all().order_by('-fecha')
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['FECHA', 'GESTOR', 'DNI', 'CLIENTE', 'RESULTADO', 'MONTO'])
    for g in gestiones:
        ws.append([g.fecha.strftime('%d/%m/%Y'), g.gestor.username, g.deudor.documento, g.deudor.nombre_completo, g.resultado, g.monto_pago])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Reporte_PP.xlsx'
    wb.save(response)
    return response

