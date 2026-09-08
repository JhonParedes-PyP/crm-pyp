import os
import re

file_path = r'c:\CRM PYP\cobranza\views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """                            negociacion_str = str(row.get('Negociacin', '')).strip()
                            condicion_val = str(row.get('Situacin del Proceso', str(row.get('Estado', '')))).strip()
                            if negociacion_str and negociacion_str.lower() != 'nan':
                                condicion_val = f"CONVENIO - {condicion_val}" if condicion_val else "CONVENIO" """
old_block = old_block.replace("", "ó") # In case it was written with ó

# Let's write a smarter patch since exact match might fail due to encoding.
import sys

# Just match the lines using regex
pattern = re.compile(
    r"negociacion_str = str\(row\.get\('Negociaci.n', ''\)\)\.strip\(\)\s+"
    r"condicion_val = str\(row\.get\('Situaci.n del Proceso', str\(row\.get\('Estado', ''\)\)\)\)\.strip\(\)\s+"
    r"if negociacion_str and negociacion_str\.lower\(\) != 'nan':\s+"
    r"condicion_val = f\"CONVENIO - \{condicion_val\}\" if condicion_val else \"CONVENIO\""
)

new_block = """negociacion_str = str(row.get('Negociación', str(row.get('Negociacin', '')))).strip()
                            
                            # Jalar directamente de la columna Condición
                            condicion_val = ''
                            for k in row.keys():
                                k_str = str(k).lower()
                                if 'condici' in k_str or 'condición' in k_str:
                                    condicion_val = str(row.get(k, '')).strip()
                                    break
                            
                            if condicion_val.lower() == 'nan':
                                condicion_val = ''
"""

if pattern.search(content):
    content = pattern.sub(new_block, content)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("PATCH SUCCESS")
else:
    print("PATCH FAILED: Could not find block")
