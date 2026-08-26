import os

html_path = r"c:\CRM PYP\cobranza\templates\cobranza\dashboard.html"
with open(html_path, 'r', encoding='latin-1') as f:
    lines = f.readlines()

proempresa_table = """
    {% if es_gerente and pagos_no_reflejados_proempresa %}
    <div style="background: white; border-radius: 8px; padding: 20px; margin-top: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-left: 4px solid #dc3545;">
        <h3 style="color: #dc3545; margin-bottom: 15px; margin-top: 0; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 20px;">⚠️</span> Pagos No Reflejados Proempresa (Mes Actual)
        </h3>
        <p style="font-size: 13px; color: #666; margin-top: -10px; margin-bottom: 15px;">Clientes cuya base indica que realizaron un pago este mes (IMP RECUP > 0), pero que aún no cuentan con una gestión de PAGÓ registrada en el sistema.</p>
        
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <thead style="background-color: #f8f9fa;">
                    <tr>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Cliente</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Documento</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Gestor Asignado</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">IMP RECUP</th>
                        <th style="padding: 10px; text-align: center; border-bottom: 2px solid #dee2e6;">Acción</th>
                    </tr>
                </thead>
                <tbody>
                    {% for p in pagos_no_reflejados_proempresa %}
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px;">{{ p.nombre_completo }}</td>
                        <td style="padding: 10px;">{{ p.documento }}</td>
                        <td style="padding: 10px;">
                            {% if p.gestores_actuales.all %}
                                {% for ag in p.gestores_actuales.all %}
                                    <span style="display: inline-block; background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-size: 11px;">{{ ag.gestor.username }}</span>
                                {% endfor %}
                            {% else %}
                                <span style="color: #999; font-style: italic;">Sin asignar</span>
                            {% endif %}
                        </td>
                        <td style="padding: 10px; font-weight: bold; color: #28a745;">
                            S/ {{ p.imp_recup|default:"0.00" }}
                        </td>
                        <td style="padding: 10px; text-align: center;">
                            <a href="{% url 'historial_gestiones' deudor_id=p.id %}" target="_blank" style="background: #003366; color: white; padding: 4px 10px; text-decoration: none; border-radius: 4px; font-size: 12px;">Revisar</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}
"""

# Find the end of huancayo block and insert the table
# We look for "</div>\n<script>\n" backwards or similar, but the safest is just find the end of pagos_no_reflejados_huancayo.
# Let's find the closing `    {% endif %}\n\n</div>\n\n<script>\n`

new_lines = []
inserted_table = False
for line in lines:
    new_lines.append(line)
    if "dataCarteras =" in line and not inserted_table:
        # Insert BEFORE script block? Let's just insert it before `<script>` tag.
        pass

# Let's do it cleanly by finding `<script>` tag that starts the JS.
new_lines = []
for i, line in enumerate(lines):
    if "<script>" in line and "DOMContentLoaded" in lines[i+1]:
        new_lines.append(proempresa_table + "\n")
    new_lines.append(line)

with open(html_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Updated dashboard.html with Proempresa table")
