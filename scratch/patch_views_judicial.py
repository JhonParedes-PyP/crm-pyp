import re

file_path = r'c:\CRM PYP\cobranza\views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# We need to insert the code for both Caja Huancayo and Proempresa where update_or_create happens.
# There are two places: one for Caja_Huancayo/Estandar and one for Proempresa.
# Actually, wait, let's see how many `update_or_create` there are.

insert_code = """
                            # --- CREACIÓN AUTOMÁTICA DE EXPEDIENTE JUDICIAL ---
                            if deudor.expediente and deudor.expediente.strip() not in ('', 'nan', 'None', '-'):
                                from cobranza.models import ExpedienteJudicial
                                juzgado_val = deudor.juzgado.strip() if deudor.juzgado else 'NO ESPECIFICADO'
                                materia_val = deudor.proceso.strip() if deudor.proceso else 'NO ESPECIFICADO'
                                ExpedienteJudicial.objects.get_or_create(
                                    deudor=deudor,
                                    numero_expediente=deudor.expediente.strip(),
                                    defaults={
                                        'juzgado': juzgado_val,
                                        'materia': materia_val,
                                        'fecha_inicio': deudor.fec_demanda
                                    }
                                )
                            # --------------------------------------------------
"""

content = content.replace(
    "neg_str_conv = defaults.get('negociacion', '')",
    insert_code.lstrip('\n') + "                            neg_str_conv = defaults.get('negociacion', '')"
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("views.py patched.")
