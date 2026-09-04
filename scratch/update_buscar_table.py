import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\judicial\buscar.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_thead = """            <thead>
                <tr style="background: #f1f3f5; text-align: left;">
                    <th style="padding: 12px 20px; border-bottom: 2px solid #ddd;">N° Expediente</th>"""

new_thead = """            <thead>
                <tr style="background: #f1f3f5; text-align: left;">
                    <th style="padding: 12px 10px; border-bottom: 2px solid #ddd; width: 40px; text-align: center;">#</th>
                    <th style="padding: 12px 20px; border-bottom: 2px solid #ddd;">N° Expediente</th>"""

old_tbody = """            <tbody>
                {% for e in expedientes %}
                <tr style="border-bottom: 1px solid #eee; transition: background 0.2s;">
                    <td style="padding: 12px 20px; font-weight: bold; color: #0056b3;">{{ e.numero_expediente }}</td>"""

new_tbody = """            <tbody>
                {% for e in expedientes %}
                <tr style="border-bottom: 1px solid #eee; transition: background 0.2s;">
                    <td style="padding: 12px 10px; font-weight: bold; color: #666; text-align: center;">{{ forloop.counter }}</td>
                    <td style="padding: 12px 20px; font-weight: bold; color: #0056b3;">{{ e.numero_expediente }}</td>"""


if old_thead in content and old_tbody in content:
    content = content.replace(old_thead, new_thead)
    content = content.replace(old_tbody, new_tbody)
    
    # Check for empty state colspan
    old_empty = """                    <td colspan="6" style="padding: 30px; text-align: center; color: #777;">
                        No se encontraron expedientes con los filtros aplicados.
                    </td>"""
    new_empty = """                    <td colspan="7" style="padding: 30px; text-align: center; color: #777;">
                        No se encontraron expedientes con los filtros aplicados.
                    </td>"""
    content = content.replace(old_empty, new_empty)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("buscar.html updated successfully.")
else:
    print("Could not find the block to replace!")
