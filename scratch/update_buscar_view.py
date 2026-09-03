import re
import os

file_path = r'c:\CRM PYP\cobranza\judicial_views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_func = """def buscar_expediente(request):
    query = request.GET.get('q', '')
    expedientes = []
    if query:
        expedientes = ExpedienteJudicial.objects.filter(
            Q(numero_expediente__icontains=query) |
            Q(deudor__nombre_completo__icontains=query) |
            Q(deudor__documento__icontains=query)
        )
    return render(request, 'cobranza/judicial/buscar.html', {'expedientes': expedientes, 'query': query})"""

new_func = """def buscar_expediente(request):
    query = request.GET.get('q', '')
    cartera_q = request.GET.get('cartera', '')
    agencia_q = request.GET.get('agencia', '')
    
    expedientes = []
    
    # We only show results if a search or filter was applied
    if query or cartera_q or agencia_q:
        qs = ExpedienteJudicial.objects.all()
        if query:
            qs = qs.filter(
                Q(numero_expediente__icontains=query) |
                Q(deudor__nombre_completo__icontains=query) |
                Q(deudor__documento__icontains=query)
            )
        if cartera_q:
            qs = qs.filter(deudor__cartera=cartera_q)
        if agencia_q:
            qs = qs.filter(deudor__agencia=agencia_q)
        expedientes = qs
        
    carteras = Deudor.objects.filter(expedientes_judiciales__isnull=False).values_list('cartera', flat=True).distinct()
    agencias = Deudor.objects.filter(expedientes_judiciales__isnull=False).values_list('agencia', flat=True).distinct()
    
    return render(request, 'cobranza/judicial/buscar.html', {
        'expedientes': expedientes,
        'query': query,
        'cartera_q': cartera_q,
        'agencia_q': agencia_q,
        'carteras': carteras,
        'agencias': agencias,
    })"""

content = content.replace(old_func, new_func)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('judicial_views updated')
