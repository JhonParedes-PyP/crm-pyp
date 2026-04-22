from .models import *
from .views import es_gerente, encode_md5_base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
import csv
import pandas as pd

@login_required
def datos_cliente_kubo(request, telefono, campana, cod_cliente, cod_telefono):
    """
    Endpoint que recibe la URL de Kubo y redirige a la ficha del cliente
    URL: /datos-cliente/<telefono>/<campana>/<cod_cliente>/<cod_telefono>/
    
    Ejemplo: https://micrm.com/datos-cliente/967050203/85200/U7Hlpt2u/0w=/N6mIwgDkYQa=/
    """
    # Buscar cliente por teléfono (usando filter para evitar MultipleObjectsReturned)
    deudor = Deudor.objects.filter(telefono_principal=telefono).first()
    if not deudor:
        # Buscar en teléfonos adicionales
        telefono_extra = TelefonoExtra.objects.filter(numero=telefono).first()
        if telefono_extra:
            deudor = telefono_extra.deudor
        else:
            return HttpResponse("Cliente no encontrado", status=404)

    # Redirigir a la ficha de gestión del cliente
    return redirect('registrar_gestion', deudor_id=deudor.id)

@login_required
def panel_campanas_asterisk(request):
    if not es_gerente(request.user):
        return HttpResponse("Acceso Denegado. Solo Gerencia.", status=403)

    mensajes = ""
    errores = []
    exitosos = 0
    fallidos = 0

    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        nombre_campana = request.POST.get('nombre_campana')
        proveedor = request.POST.get('proveedor')
        archivo = request.FILES['archivo_excel']

        try:
            # 1. Creamos la "Campaña Maestra" en la base de datos
            nueva_campana = CampanaAsterisk.objects.create(
                nombre=nombre_campana,
                proveedor=proveedor,
                usuario_creador=request.user
            )

            # 2. Leemos el Excel
            df = pd.read_excel(archivo, dtype=str).fillna('')

            # Validamos que el Excel tenga las columnas correctas
            if 'NRO_DOCUMENTO' not in df.columns or 'NRO_TELEFONO' not in df.columns:
                nueva_campana.delete() # Cancelamos la creación
                errores.append("El archivo debe tener exactamente las columnas 'NRO_DOCUMENTO' y 'NRO_TELEFONO'.")
            else:
                # 3. Cruzamos los datos fila por fila
                detalles_a_crear = []
                for index, row in df.iterrows():
                    dni = str(row.get('NRO_DOCUMENTO', '')).strip()
                    telefono = str(row.get('NRO_TELEFONO', '')).strip()
                    telefono_limpio = ''.join(filter(str.isdigit, telefono))

                    # Regla 1: Que tenga 9 dígitos
                    if len(telefono_limpio) != 9:
                        fallidos += 1
                        errores.append(f"Fila {index+2} (DNI {dni}): El teléfono no tiene 9 dígitos.")
                        continue

                    # Regla 2: Que el DNI exista en nuestra bóveda
                    deudor = Deudor.objects.filter(documento=dni).first()
                    if not deudor:
                        fallidos += 1
                        errores.append(f"Fila {index+2}: El DNI {dni} no existe en el CRM.")
                        continue

                    # Regla 3: ¿El teléfono le pertenece a ese DNI?
                    es_suyo = False
                    if deudor.telefono_principal == telefono_limpio or deudor.tlf_celular_aval == telefono_limpio:
                        es_suyo = True
                    elif TelefonoExtra.objects.filter(deudor=deudor, numero=telefono_limpio).exists():
                        es_suyo = True

                    if not es_suyo:
                        fallidos += 1
                        errores.append(f"Fila {index+2}: El Tel {telefono_limpio} no está registrado para el DNI {dni}.")
                        continue

                    # Si pasó todas las reglas: Generamos el código KUBO
                    cod_cliente = encode_md5_base64(dni)
                    cod_telefono = encode_md5_base64(f"{deudor.id}{telefono_limpio}")

                    # Lo preparamos para guardarlo en el anexo
                    detalles_a_crear.append(
                        DetalleCampanaAsterisk(
                            campana=nueva_campana,
                            dni=dni,
                            telefono=telefono_limpio,
                            cod_cliente=cod_cliente,
                            cod_telefono=cod_telefono
                        )
                    )
                    exitosos += 1

                # 4. Guardamos todos los números válidos
                if detalles_a_crear:
                    DetalleCampanaAsterisk.objects.bulk_create(detalles_a_crear)
                    mensajes = f"¡Campaña creada con éxito! {exitosos} números validados y encriptados."
                else:
                    nueva_campana.delete() # Si ningún número valió, no guardamos la campaña
                    mensajes = "Operación cancelada: Ningún número del Excel pasó las validaciones de seguridad."

        except Exception as e:
            errores.append(f"Error grave al leer el archivo: {str(e)}")

    # 5. Listamos las campañas para mostrarlas en la tabla
    lista_campanas = CampanaAsterisk.objects.all()

    return render(request, 'cobranza/panel_campanas.html', {
        'lista_campanas': lista_campanas,
        'mensajes': mensajes,
        'errores': errores[:15], # Mostramos máximo 15 errores para no saturar la pantalla
        'exitosos': exitosos,
        'fallidos': fallidos
    })

@login_required
def descargar_csv_campana(request, campana_id):
    if not es_gerente(request.user):
        return HttpResponse("Acceso Denegado.", status=403)

    # 1. Buscamos la campaña exacta que el Gerente seleccionó
    campana = get_object_or_404(CampanaAsterisk, id=campana_id)
    detalles = campana.detalles.all() # Traemos todos sus números validados

    # 2. Preparamos el archivo descargable
    response = HttpResponse(content_type='text/csv')
    # El nombre del archivo se verá profesional: Ej. "Asterisk_Camp_1_PROEMPRESA.csv"
    nombre_archivo = f"Asterisk_Camp_{campana.id}_{campana.nombre.replace(' ', '_')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'

    writer = csv.writer(response)
    
    # 3. Las Cabeceras Exactas que exige el proveedor
    writer.writerow(['TELEFONO', 'CAMPANA', 'COD_CLIENTE', 'COD_TELEFONO'])

    # 4. Llenamos el Excel (¡Adiós al 85200 fijo!)
    for d in detalles:
        writer.writerow([
            d.telefono,
            str(campana.id),  # ¡LA MAGIA! Inserta automáticamente el ID 1, 2, 3...
            d.cod_cliente,
            d.cod_telefono
        ])

    return response

