import re
import os

file_path = r'c:\CRM PYP\cobranza\views.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the template name in views.py
content = content.replace("'plantilla_proempresa.docx'", "'MODELO DE CARTA DE PROEMPRESA.docx'")

# 2. Update the mapping dict using regex
pattern = r"mapping = \{\s*?\'\[FECHA_ACTUAL\]\':[\s\S]*?\} # Reemplazar en párrafos"

new_mapping = """mapping = {
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
                }
                
                # Reemplazar en párrafos"""

content = re.sub(r"mapping = \{[\s\S]*?\}\s*# Reemplazar en párrafos", new_mapping, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("PATCH SUCCESS!")
