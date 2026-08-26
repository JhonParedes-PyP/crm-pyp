import os
import re

html_path = r"c:\CRM PYP\cobranza\templates\cobranza\estrategia_ia.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# We need to replace the entire PDF logic again
# Let's find where the PDF logic starts and ends
start_marker = "var opt = {"
end_marker = "html2pdf().set(opt).from(element).save();"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx) + len(end_marker)

new_pdf_code = """        var opt = {
            margin:       [15, 10, 15, 10], // top, left, bottom, right
            filename:     filename,
            image:        { type: 'jpeg', quality: 1.0 },
            html2canvas:  { 
                scale: 2,
                useCORS: true,
                windowWidth: 800 // Forzar el ancho del canvas para que no corte el contenido
            },
            jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' },
            pagebreak:    { mode: ['css', 'legacy'] } // avoid-all a veces buggea
        };

        // En lugar de un elemento al aire, lo atamos al DOM temporalmente arriba del todo
        var element = document.createElement('div');
        element.style.position = 'absolute';
        element.style.top = '0';
        element.style.left = '0';
        element.style.width = '790px'; // Ancho ptimo para A4 (210mm)
        element.style.background = 'white';
        element.style.zIndex = '-9999';
        element.style.padding = '20px';
        element.style.boxSizing = 'border-box';
        
        element.innerHTML = `
            <style>
                .pdf-container { font-family: Arial, sans-serif; font-size: 11px; padding: 0; color: #333; }
                .pdf-container h1, .pdf-container h2, .pdf-container h3 { color: #003366; page-break-after: avoid; margin-top: 15px; margin-bottom: 8px; }
                .pdf-container p { margin-bottom: 8px; line-height: 1.4; }
                /* TABLAS FIJAS PARA EVITAR CORTES */
                .pdf-container table { width: 100% !important; table-layout: fixed !important; border-collapse: collapse; margin-bottom: 15px; font-size: 9px; word-wrap: break-word; }
                .pdf-container th { background-color: #003366; color: white; padding: 6px; text-align: left; border: 1px solid #003366; }
                .pdf-container td { border: 1px solid #ddd; padding: 6px; word-wrap: break-word; overflow-wrap: break-word; white-space: normal; }
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

        document.body.appendChild(element); // Lo agregamos al top 0

        html2pdf().set(opt).from(element).save().then(function() {
            // Lo removemos del DOM despus de descargar
            document.body.removeChild(element);
        });"""

new_pdf_code = new_pdf_code.replace("Estratgico", "Estratégico")
new_pdf_code = new_pdf_code.replace("despus", "después")
new_pdf_code = new_pdf_code.replace("ptimo", "óptimo")

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_pdf_code + content[end_idx:]
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("PDF export logic patched successfully.")
else:
    print("Could not find the block to replace.")
