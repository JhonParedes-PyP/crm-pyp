import os

html_path = r"c:\CRM PYP\cobranza\templates\cobranza\estrategia_ia.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_pdf_code = """        var opt = {
            margin:       10,
            filename:     filename,
            image:        { type: 'jpeg', quality: 0.98 },
            html2canvas:  { scale: 2 },
            jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
        };

        // Clonamos el resultado para aplicarle estilos especficos de impresin si es necesario
        var element = document.createElement('div');
        element.innerHTML = `
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h1 style="color: #003366; text-align: center; border-bottom: 2px solid #003366; padding-bottom: 10px;">Reporte Estratgico de Cobranza</h1>
                <p><strong>Cartera:</strong> ${carteraStr}</p>
                <p><strong>Agencias:</strong> ${agenciasStr.replace(/_/g, ', ')}</p>
                <p><strong>Fecha:</strong> ${fechaStr}</p>
                <hr>
                ${resultado.innerHTML}
            </div>
        `;

        html2pdf().set(opt).from(element).save();"""

# I'll use regex to replace it because of the exact spacing and encoding
import re

new_pdf_code = """        var opt = {
            margin:       [15, 10, 15, 10], // top, left, bottom, right
            filename:     filename,
            image:        { type: 'jpeg', quality: 1.0 },
            html2canvas:  { 
                scale: 2,
                scrollY: 0, // FIX para el error de que sale cortado o empieza a la mitad si la pgina est scrolleada
                windowWidth: document.documentElement.offsetWidth
            },
            jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' },
            pagebreak:    { mode: ['css', 'legacy'] }
        };

        // Clonamos el resultado para aplicarle estilos especficos de impresin si es necesario
        var element = document.createElement('div');
        element.innerHTML = `
            <style>
                .pdf-container { font-family: Arial, sans-serif; font-size: 11px; padding: 0; color: #333; }
                .pdf-container h1, .pdf-container h2, .pdf-container h3 { color: #003366; page-break-after: avoid; margin-top: 15px; margin-bottom: 8px; }
                .pdf-container p { margin-bottom: 8px; line-height: 1.4; }
                .pdf-container table { width: 100% !important; table-layout: fixed; border-collapse: collapse; margin-bottom: 15px; font-size: 9px; }
                .pdf-container th { background-color: #003366; color: white; padding: 6px; text-align: left; border: 1px solid #003366; }
                .pdf-container td { border: 1px solid #ddd; padding: 6px; word-wrap: break-word; }
                .pdf-container tr { page-break-inside: avoid; }
                .pdf-container ul, .pdf-container ol { margin-bottom: 15px; padding-left: 20px; }
                .pdf-container li { margin-bottom: 4px; page-break-inside: avoid; }
                .pdf-header { text-align: center; border-bottom: 2px solid #003366; padding-bottom: 10px; margin-bottom: 15px; }
            </style>
            <div class="pdf-container">
                <div class="pdf-header">
                    <h1 style="margin:0;">Reporte Estratgico de Cobranza</h1>
                    <p style="margin: 5px 0 0 0;"><strong>Cartera:</strong> ${carteraStr} | <strong>Agencias:</strong> ${agenciasStr.replace(/_/g, ', ')} | <strong>Fecha:</strong> ${fechaStr}</p>
                </div>
                ${resultado.innerHTML}
            </div>
        `;

        html2pdf().set(opt).from(element).save();"""

# Read again explicitly handling utf-8
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()
    
# We will just replace the JS block directly by finding boundaries
start_marker = "var opt = {"
end_marker = "html2pdf().set(opt).from(element).save();"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx) + len(end_marker)

if start_idx != -1 and end_idx != -1:
    # Need to handle encoding carefully for '' which is 'é'
    new_pdf_code = new_pdf_code.replace("Reporte Estratgico", "Reporte Estratégico")
    new_pdf_code = new_pdf_code.replace("pgina est", "página está")
    content = content[:start_idx] + new_pdf_code + content[end_idx:]
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("PDF export logic patched successfully.")
else:
    print("Could not find the block to replace.")
