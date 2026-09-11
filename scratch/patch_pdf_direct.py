import os
import re

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\estrategia_ia.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r"                        var opt = \{.*?\n        \}\);"

new_code = """        var opt = {
            margin:       [15, 10, 15, 10],
            filename:     filename,
            image:        { type: 'jpeg', quality: 1.0 },
            html2canvas:  { scale: 2, useCORS: true, scrollY: 0 },
            jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' },
            pagebreak:    { mode: ['css', 'legacy'] }
        };

        var headerHTML = `
            <div id="temp-pdf-header" style="text-align: center; border-bottom: 2px solid #003366; padding-bottom: 10px; margin-bottom: 15px;">
                <h1 style="margin:0; color: #003366; font-size: 20px;">Reporte Estratégico de Cobranza</h1>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #333;"><strong>Cartera:</strong> ${carteraStr} | <strong>Agencias:</strong> ${agenciasStr.replace(/_/g, ', ')} | <strong>Fecha:</strong> ${fechaStr}</p>
            </div>
        `;
        resultado.insertAdjacentHTML('afterbegin', headerHTML);

        // Agregamos una clase temporal si es necesario para evitar cortes de tabla en PDF
        var tables = resultado.querySelectorAll('table');
        tables.forEach(t => t.style.pageBreakInside = 'avoid');

        html2pdf().set(opt).from(resultado).save().then(function() {
            var tempHeader = document.getElementById('temp-pdf-header');
            if (tempHeader) tempHeader.remove();
            
            tables.forEach(t => t.style.pageBreakInside = '');
        });"""

content = re.sub(pattern, new_code, content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("PATCH PDF SUCCESS")
