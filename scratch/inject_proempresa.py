import os

file_path = r"c:\CRM PYP\cobranza\templates\cobranza\dashboard.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix mojibake in Caja Huancayo title
content = content.replace('Y"?', '🔍')
content = content.replace('aǧn', 'aún')
content = content.replace('gestin', 'gestión')
content = content.replace('sltima', 'Última')
content = content.replace('Accin', 'Acción')

proempresa_table = """
    {% if es_gerente and pagos_no_reflejados_proempresa %}
    <div style="background: white; border-radius: 8px; padding: 20px; margin-top: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-left: 4px solid #dc3545;">
        <h3 style="color: #dc3545; margin-bottom: 15px; margin-top: 0; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 20px;">⚠️</span> Pagos No Reflejados Proempresa (Mes Actual)
        </h3>
        <p style="font-size: 13px; color: #666; margin-top: -10px; margin-bottom: 15px;">Clientes cuya base indica que realizaron un pago este mes (IMP RECUP > 0), pero que aún no cuentan con una gestión de PAGO registrada en el sistema.</p>
        
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <thead style="background-color: #f8f9fa;">
                    <tr>
                        <th style="padding: 10px; text-align: center; border-bottom: 2px solid #dee2e6; width: 30px;">#</th>
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
                        <td style="padding: 10px; text-align: center; font-weight: bold; color: #888;">{{ forloop.counter }}</td>
                        <td style="padding: 10px; font-weight: bold;">{{ p.nombre_completo }}</td>
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
                            <a href="{% url 'registrar_gestion' p.id %}" target="_blank" style="background: #17a2b8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 4px; font-size: 12px; font-weight: bold;">Revisar</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}
"""

if "pagos_no_reflejados_proempresa" not in content:
    content = content.replace("</div>\n\n<script>", proempresa_table + "\n</div>\n\n<script>")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Injected successfully!")
