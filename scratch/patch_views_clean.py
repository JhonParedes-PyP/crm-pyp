import re

file_path = r'c:\CRM PYP\cobranza\views.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure we only touch generar_cartas
# Split the file by "def generar_cartas(request):"
parts = content.split("def generar_cartas(request):")
if len(parts) == 2:
    top_part = parts[0]
    func_part = "def generar_cartas(request):" + parts[1]
    
    # In func_part, do the replacements
    func_part = func_part.replace(
        "cartera = request.GET.get('cartera')",
        "cliente_dni = request.GET.get('cliente_dni')\n        cartera = request.GET.get('cartera')",
        1 # ONLY THE FIRST MATCH!
    )
    
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
    func_part = func_part.replace(old_qs, new_qs, 1)
    
    # 3. Modify Hoja de Ruta
    pattern = re.compile(r"(p_titulo = doc_final\.add_paragraph\(\).*?doc_final\.add_page_break\(\))", re.DOTALL)
    match = pattern.search(func_part)
    if match:
        block = match.group(1)
        indented_block = "\n".join("    " + line if line.strip() else line for line in block.split("\n"))
        new_block = f"""if cliente_dni:
                distrito_filename = f"Cliente_{{cliente_dni}}"
            else:
{indented_block}"""
        func_part = func_part.replace(block, new_block, 1)
    
    # save back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(top_part + func_part)
        
    print("PATCH VIEWS EXCELLENT")
else:
    print("Could not split file!")
