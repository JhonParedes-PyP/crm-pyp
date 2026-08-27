import os

file_path = r"c:\CRM PYP\cobranza\templates\cobranza\dashboard.html"

# Checkout da75cacd (which is the fully clean base)
os.system(f'git checkout da75cacd -- "{file_path}"')

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add Revisar button that was in da75cacd? Wait, da75cacd ALREADY has registrar_gestion! Let's check!
# Actually, I want to keep all the fixes (registrar_gestion, etc) from main!
# So checkout main!
os.system(f'git checkout main -- "{file_path}"')

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

tables_code = """
    {% if es_gerente and pagos_no_reflejados_caja_huancayo %}
    <div style="background: white; border-radius: 8px; padding: 20px; margin-top: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-left: 4px solid #ffc107;">
        <h3 style="color: #ffc107; margin-bottom: 15px; margin-top: 0; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 20px;">🔍</span> Pagos No Reflejados Caja Huancayo (Mes Actual)
        </h3>
        <p style="font-size: 13px; color: #666; margin-top: -10px; margin-bottom: 15px;">Clientes cuya base indica que realizaron un pago este mes, pero que aún no cuentan con una gestión de PAGO registrada en el sistema.</p>
        
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <thead style="background-color: #f8f9fa;">
                    <tr>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Cliente</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Documento</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Gestor Asignado</th>
                        <th style="padding: 10px;">Última Fecha Pago (Base)</th>
                        <th style="padding: 10px; text-align: center; border-bottom: 2px solid #dee2e6;">Acción</th>
                    </tr>
                </thead>
                <tbody>
                    {% for p in pagos_no_reflejados_caja_huancayo %}
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
                        <td style="padding: 10px;">{{ p.ultimo_dia_pago|date:"d/m/Y"|default:"-" }}</td>
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
    content = content.replace("</div>\n</div>\n\n<script>", "</div>\n</div>\n" + tables_code + "\n<script>")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Added missing tables to main dashboard!")
