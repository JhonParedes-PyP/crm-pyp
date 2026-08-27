from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Deudor
from .views import es_gerente
import pandas as pd
from datetime import timedelta
from django.utils import timezone
import random

@login_required
def panel_whatsapp_masivo(request):
    if not es_gerente(request.user):
        return HttpResponse("Acceso Denegado. Solo Gerencia.", status=403)
        
    carteras = Deudor.objects.filter(activo=True).values_list('cartera', flat=True).distinct().order_by('cartera')
    carteras_limpias = [c for c in carteras if c and c.strip()]
    
    # Extraer mapa de agencias por cartera para el desplegable dinámico
    import json
    mapa_agencias = {}
    for c in carteras_limpias:
        ags = Deudor.objects.filter(cartera=c, activo=True).values_list('agencia', flat=True).distinct()
        mapa_agencias[c] = sorted([a for a in ags if a and a.strip()])
        
    return render(request, 'cobranza/whatsapp_masivo.html', {
        'carteras': carteras_limpias,
        'mapa_agencias': json.dumps(mapa_agencias)
    })

@login_required
def exportar_whatsapp_excel(request):
    if not es_gerente(request.user):
        return HttpResponse("Acceso Denegado.", status=403)
        
    if request.method == 'POST':
        cartera = request.POST.get('cartera')
        agencias = request.POST.getlist('agencias')
        filtro_audiencia = request.POST.get('filtro_audiencia')
        
        if not cartera:
            return HttpResponse("Debe seleccionar una cartera.", status=400)
            
        qs = Deudor.objects.filter(cartera=cartera, activo=True)
        if agencias:
            qs = qs.filter(agencia__in=agencias)
            
        hoy = timezone.now().date()
        
        datos_exportar = []
        
        # Variaciones de texto (Spintax simple)
        saludos = ["Hola", "Buenos días", "Estimado(a)", "Saludos"]
        # El intro se generará dinámicamente según la cartera
        
        for c in qs:
            tiene_negociacion = False
            neg_str = str(c.negociacion).upper() if c.negociacion else ''
            if neg_str and neg_str not in ('NAN', 'NONE', 'NULL', 'SIN NEGOCIACIÓN', 'SIN NEGOCIACION'):
                tiene_negociacion = True
                
            # Filtro de audiencia
            if filtro_audiencia == 'sin_negociacion' and tiene_negociacion: continue
            if filtro_audiencia == 'con_negociacion' and not tiene_negociacion: continue
            
            numero = c.telefono_principal
            # Limpiar número
            if not numero:
                continue
            numero_limpio = ''.join(filter(str.isdigit, numero))
            if len(numero_limpio) != 9:
                continue
                
            nombre_corto = c.nombre_completo.split(',')[0] if ',' in c.nombre_completo else c.nombre_completo.split(' ')[0]
            
            # Usar nombre completo si parece ser una empresa
            palabras_empresa = ["CORPORACION", "EMPRESA", "INVERSIONES", "CONSORCIO", "ASOCIACION", "GRUPO", "COMERCIAL", "SERVICIOS", "S.A.C", "S.R.L", "E.I.R.L"]
            if any(palabra in c.nombre_completo.upper() for palabra in palabras_empresa):
                nombre_corto = c.nombre_completo.strip()
                
            saldo = float(c.saldo_deuda) if c.saldo_deuda else 0.0
            
            saludo = random.choice(saludos)
            intro = random.choice([f"nos comunicamos por encargo de {cartera}.", f"le escribimos por encargo de {cartera}."])
            
            mensaje = ""
            
            if tiene_negociacion:
                # Logica de 30 días
                if c.ultimo_dia_pago:
                    dias_desde_pago = (hoy - c.ultimo_dia_pago).days
                    if 25 <= dias_desde_pago <= 35:
                        mensaje = f"{saludo} {nombre_corto}, {intro} Le recordamos que su cuota de convenio con {cartera} está próxima a vencer o acaba de vencer. Por favor, regularice su pago a la brevedad para mantener los beneficios de su negociación."
                    else:
                        # No está en la ventana de 30 días, lo saltamos
                        continue
                else:
                    # Tiene negociación pero no tiene último día de pago, lo saltamos o mandamos generico?
                    continue
            else:
                # Cobranza normal (sin negociación)
                mensaje = f"{saludo} {nombre_corto}, {intro} Su crédito en {cartera} registra una deuda pendiente de S/ {saldo:.2f}. Le instamos a regularizar su situación de forma inmediata para evitar que su expediente pase a instancias mayores o procesos de embargo. Comuníquese urgente con nosotros."
            
            # Formato WA: Agregar código país
            numero_final = f"51{numero_limpio}"
            
            datos_exportar.append({
                'Numero': numero_final,
                'Mensaje': mensaje,
                'Cliente': c.nombre_completo, # Solo para referencia interna del gerente, algunas extensiones lo ignoran
                'Agencia': c.agencia
            })
            
        if not datos_exportar:
            return HttpResponse("No se encontraron clientes que cumplan con los filtros seleccionados (Recuerda que los clientes con convenio solo salen si están a 30 días de su último pago).", status=404)
            
        df = pd.DataFrame(datos_exportar)
        
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='WhatsApp')
        
        output.seek(0)
        
        response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        nombre_archivo = f"WA_Masivo_{cartera}_{hoy.strftime('%Y%m%d')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        
        return response
        
    return HttpResponse("Método no permitido.", status=405)
