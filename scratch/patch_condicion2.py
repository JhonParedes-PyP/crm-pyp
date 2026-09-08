import os
import re

file_path = r'c:\CRM PYP\cobranza\views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r"'condicion': str\(row\.get\('CONDICION', row\.get\('SITUACION', ''\)\)\)\.strip\(\),")
new_line = "'condicion': str(row.get('Condición', row.get('CONDICION', row.get('Condicion', row.get('SITUACION', ''))))).strip(),"

if pattern.search(content):
    content = pattern.sub(new_line, content)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("PATCH 2 SUCCESS")
else:
    print("PATCH 2 FAILED")
