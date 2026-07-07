import sys

path = 'c:/CRM PYP/cobranza/views.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update puede_eliminar logic
content = content.replace(
    "'puede_eliminar': puede_depurar_telefonos(request.user) and numero_repetido_en_cliente(conteo_numeros_cliente, deudor.telefono_principal),",
    "'puede_eliminar': True,"
)

content = content.replace(
    "'puede_eliminar': puede_depurar_telefonos(request.user) and numero_repetido_en_cliente(conteo_numeros_cliente, deudor.tlf_celular_aval),",
    "'puede_eliminar': True,"
)

content = content.replace(
    "'puede_eliminar': puede_depurar_telefonos(request.user) and numero_repetido_en_cliente(conteo_numeros_cliente, tel.numero),",
    "'puede_eliminar': True,"
)

# 2. Remove access checks
check_str = """    if not puede_depurar_telefonos(request.user):
        return HttpResponse("Acceso Denegado. Accion exclusiva para JPAREDES.", status=403)"""

content = content.replace(check_str, "")

# 3. Update observation
old_obs1 = 'observacion=f"JPAREDES eliminó el {etiqueta}: {numero}.",\n'
new_obs1 = 'observacion=f"El gestor {request.user.username.upper()} eliminó el {etiqueta}: {numero}.",\n'
content = content.replace(old_obs1, new_obs1)

old_obs2 = 'observacion=f"JPAREDES eliminó el teléfono manual {numero} ({descripcion}).",\n'
new_obs2 = 'observacion=f"El gestor {request.user.username.upper()} eliminó el teléfono manual {numero} ({descripcion}).",\n'
content = content.replace(old_obs2, new_obs2)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Modifications applied successfully.")
