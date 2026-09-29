import re

file_path = r'c:\CRM PYP\cobranza\views.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Modify template selection
old_template = """            try:
                # Crear documento final a partir de la plantilla para conservar estilos y márgenes
                template_path = os.path.join(settings.BASE_DIR, 'plantilla_caja_huancayo_v2.docx')
                doc_final = Document(template_path)"""

new_template = """            try:
                # Crear documento final a partir de la plantilla para conservar estilos y márgenes
                if clientes and clientes[0].cartera and 'PROEMPRESA' in clientes[0].cartera.upper():
                    template_path = os.path.join(settings.BASE_DIR, 'plantilla_proempresa.docx')
                else:
                    template_path = os.path.join(settings.BASE_DIR, 'plantilla_caja_huancayo_v2.docx')
                doc_final = Document(template_path)"""

content = content.replace(old_template, new_template)

# 2. Remove redundant template_path before loop
old_redundant = """            # --- 2. GENERAR CARTAS ---
            template_path = os.path.join(settings.BASE_DIR, 'plantilla_caja_huancayo_v2.docx')
            
            for i, c in enumerate(clientes):"""

new_redundant = """            # --- 2. GENERAR CARTAS ---
            for i, c in enumerate(clientes):"""

content = content.replace(old_redundant, new_redundant)


# 3. Update mapping dictionary
old_mapping = """                    mapping = {
                        '[FECHA_ACTUAL]': datetime.date.today().strftime('%d/%m/%Y'),
                        '[NOMBRE_CLIENTE]': c.nombre_completo,
                        '[NUM_CUENTA]': c.cuenta or '',
                        '[DIRECCION_CLIENTE]': f"{c.dir_casa} - {c.distrito} - {c.provincia} - {c.departamento}",
                        '[NOMBRE_AVAL]': c.nom_aval or 'SIN AVAL',
                        '[AGENCIA]': c.agencia or 'S/A',
                        '[MONTO_DEUDA]': f"{c.saldo_deuda:.2f}" if c.saldo_deuda else '0.00',
                        '[DISTRITO_O_PROVINCIA]': c.distrito or c.provincia or "",
                        '[NRO_CARTA]': c.correlativo or c.expediente or f"{i+1:04d}-2026-COD",
                        '[FECHA_ULT_PAGO]': c.ultimo_dia_pago.strftime('%d/%m/%Y') if c.ultimo_dia_pago else '--/--/----'
                    }"""

new_mapping = """                    mapping = {
                        '[FECHA_ACTUAL]': datetime.date.today().strftime('%d/%m/%Y'),
                        '[NOMBRE_CLIENTE]': c.nombre_completo,
                        '[NUM_CUENTA]': c.cuenta or '',
                        '[DIRECCION_CLIENTE]': f"{c.dir_casa} - {c.distrito} - {c.provincia} - {c.departamento}",
                        '[NOMBRE_AVAL]': c.nom_aval or 'SIN AVAL',
                        '[AGENCIA]': c.agencia or 'S/A',
                        '[MONTO_DEUDA]': f"{c.saldo_deuda:.2f}" if c.saldo_deuda else '0.00',
                        '[DISTRITO_O_PROVINCIA]': c.distrito or c.provincia or "",
                        '[NRO_CARTA]': c.correlativo or c.expediente or f"{i+1:04d}-2026-COD",
                        '[FECHA_ULT_PAGO]': c.ultimo_dia_pago.strftime('%d/%m/%Y') if c.ultimo_dia_pago else '--/--/----',
                        '[CONYUGE_CLIENTE]': c.nom_conyuge or '',
                        '[DOMICILIO_AVAL]': f"{c.aval_direccion or ''} {c.aval_distrito or ''}".strip() or '--',
                        '[DIR_NEGOCIO]': c.dir_negocio or '--',
                        '[TIPO_PROCESO]': c.proceso or '--',
                        '[TELEFONO_CLIENTE]': c.telefono_principal or '--'
                    }"""

content = content.replace(old_mapping, new_mapping)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("PATCH PROEMPRESA CARTAS SUCCESS")
