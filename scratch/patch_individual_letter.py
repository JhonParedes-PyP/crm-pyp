import re

file_path = r'c:\CRM PYP\cobranza\views.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Modify GET
content = content.replace(
    "cartera = request.GET.get('cartera')",
    "cliente_dni = request.GET.get('cliente_dni')\n        cartera = request.GET.get('cartera')"
)

# 2. Modify qs
old_qs = """        # Filtrar clientes
        qs = Deudor.objects.filter(activo=True)
        if cartera:
            qs = qs.filter(cartera=cartera)"""
new_qs = """        # Filtrar clientes
        qs = Deudor.objects.filter(activo=True)
        if cliente_dni:
            qs = qs.filter(documento=cliente_dni)
        else:
            if cartera:
                qs = qs.filter(cartera=cartera)"""
content = content.replace(old_qs, new_qs)

# 3. Modify Hoja de Ruta
pattern = re.compile(r"(p_titulo = doc_final\.add_paragraph\(\).*?doc_final\.add_page_break\(\))", re.DOTALL)
match = pattern.search(content)

if match:
    block = match.group(1)
    indented_block = "\n".join("    " + line if line.strip() else line for line in block.split("\n"))
    new_block = f"""if cliente_dni:
                distrito_filename = f"Cliente_{{cliente_dni}}"
            else:
{indented_block}"""
    content = content.replace(block, new_block)
else:
    print("WARNING: Could not find hoja de ruta block")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("PATCH VIEWS SUCCESS")
