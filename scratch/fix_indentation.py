import re

file_path = r'c:\CRM PYP\cobranza\views.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

bad_block = """            # --- 1. HOJA DE RUTA ---
            if cliente_dni:
                distrito_filename = f"Cliente_{cliente_dni}"
            else:
p_titulo = doc_final.add_paragraph()
                run_titulo = p_titulo.add_run('HOJA DE RUTA - NOTIFICACIONES')"""

good_block = """            # --- 1. HOJA DE RUTA ---
            if cliente_dni:
                distrito_filename = f"Cliente_{cliente_dni}"
            else:
                p_titulo = doc_final.add_paragraph()
                run_titulo = p_titulo.add_run('HOJA DE RUTA - NOTIFICACIONES')"""

content = content.replace(bad_block, good_block)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("FIX SUCCESS")
