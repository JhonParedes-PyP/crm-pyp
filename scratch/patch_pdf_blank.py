import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\estrategia_ia.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target_opt = """            html2canvas:  { 
                scale: 2,
                useCORS: true,
                windowWidth: 800 // Forzar el ancho del canvas para que no corte el contenido
            },"""
new_opt = """            html2canvas:  { 
                scale: 2,
                useCORS: true,
                windowWidth: 800, // Forzar el ancho del canvas para que no corte el contenido
                scrollY: 0,
                scrollX: 0
            },"""
content = content.replace(target_opt, new_opt)

target_style = """        element.style.background = 'white';"""
new_style = """        element.style.background = 'white';
        element.style.zIndex = '-9999';"""
content = content.replace(target_style, new_style)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("PATCH HTML SUCCESS")
