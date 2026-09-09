import os

file_path = r'c:\CRM PYP\cobranza\judicial_views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_detalle = False

for line in lines:
    if "elif action == 'complete_alerta':" in line:
        new_lines.append("""        elif action == 'edit_expediente':
            # Principal
            expediente.numero_expediente = request.POST.get('numero_expediente', expediente.numero_expediente)
            expediente.materia = request.POST.get('materia', expediente.materia)
            expediente.juzgado = request.POST.get('juzgado', expediente.juzgado)
            expediente.sede_judicial = request.POST.get('sede_judicial', expediente.sede_judicial)
            expediente.distrito_judicial = request.POST.get('distrito_judicial', expediente.distrito_judicial)
            expediente.condicion_recuperabilidad = request.POST.get('condicion_recuperabilidad', expediente.condicion_recuperabilidad)
            expediente.probabilidad_recuperacion = request.POST.get('probabilidad_recuperacion', expediente.probabilidad_recuperacion)
            expediente.detalle_bien = request.POST.get('detalle_bien', expediente.detalle_bien)
            expediente.estado_proceso = request.POST.get('estado_proceso', expediente.estado_proceso)
            
            monto_str = request.POST.get('monto_demandado')
            if monto_str:
                try:
                    expediente.monto_demandado = Decimal(monto_str.replace(',', ''))
                except:
                    pass
            
            # Cautelar
            expediente.numero_cautelar = request.POST.get('numero_cautelar', expediente.numero_cautelar)
            expediente.codigo_cautelar = request.POST.get('codigo_cautelar', expediente.codigo_cautelar)
            expediente.tipo_medida_cautelar = request.POST.get('tipo_medida_cautelar', expediente.tipo_medida_cautelar)
            expediente.estado_cautelar = request.POST.get('estado_cautelar', expediente.estado_cautelar)
            
            f_cau = request.POST.get('fecha_cautelar')
            if f_cau: expediente.fecha_cautelar = f_cau
            
            expediente.save()
""")
        new_lines.append(line)
    else:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("PATCH VIEWS 1 SUCCESS")
