import os

file_path = r'c:\CRM PYP\cobranza\judicial_views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "def buscar_expediente(request):" in line:
        new_lines.append(line)
        new_lines.append("""
    from django.contrib import messages
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'crear_expediente':
            doc_or_cuenta = request.POST.get('doc_or_cuenta', '').strip()
            num_exp = request.POST.get('numero_expediente', '').strip()
            materia = request.POST.get('materia', '').strip()
            juzgado = request.POST.get('juzgado', '').strip()
            
            deudor = Deudor.objects.filter(Q(documento=doc_or_cuenta) | Q(cuenta=doc_or_cuenta)).first()
            if deudor:
                exp = ExpedienteJudicial.objects.create(
                    deudor=deudor,
                    numero_expediente=num_exp,
                    materia=materia,
                    juzgado=juzgado,
                    estado_proceso='ACTIVO'
                )
                messages.success(request, 'Expediente creado correctamente.')
                return redirect('detalle_expediente', expediente_id=exp.id)
            else:
                messages.error(request, 'No se encontr&oacute; un cliente con ese DNI o Cuenta.')
                return redirect('buscar_expediente')
""")
    else:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("PATCH VIEWS 2 SUCCESS")
