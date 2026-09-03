import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\judicial\detalle.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """            <!-- Resoluciones / Actos Procesales -->
            <div style="background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); overflow: hidden;">
                <div style="padding: 20px; background: #f8f9fa; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; color: #333;">Actos Procesales (Resoluciones)</h3>
                    <button onclick="document.getElementById('modalActo').style.display='flex'" style="background: #28a745; color: white; padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">+ Nuevo Acto</button>
                </div>
                <div style="padding: 20px;">
                    {% for a in actos %}
                    <div style="border-left: 4px solid {% if a.cuaderno == 'CAUTELAR' %}#ffc107{% else %}#0056b3{% endif %}; padding-left: 15px; margin-bottom: 20px; background: {% if a.cuaderno == 'CAUTELAR' %}#fffdf5{% else %}#f8fbfd{% endif %}; padding: 10px 15px; border-radius: 0 8px 8px 0;">
                        <div style="display: flex; justify-content: space-between;">
                            <h4 style="margin: 0 0 5px 0; color: #333;">
                                <span class="badge {% if a.cuaderno == 'CAUTELAR' %}bg-warning text-dark{% else %}bg-primary{% endif %}">{{ a.cuaderno }}</span>
                                Resolución N° {{ a.numero_resolucion|default:"-" }}
                            </h4>
                            <span style="color: #666; font-size: 12px;">Res: {{ a.fecha_resolucion|date:"d M Y"|default:"Importado" }}</span>
                        </div>
                        {% if a.sumilla %}<p style="margin: 5px 0; font-weight: bold; color: #444;">Sumilla: {{ a.sumilla }}</p>{% endif %}
                        <p style="margin: 0; font-size: 14px; color: #555; line-height: 1.5;">{{ a.descripcion|linebreaksbr }}</p>
                    </div>
                    {% empty %}
                    <p style="color: #777; text-align: center; margin: 20px 0;">Aún no se han registrado actos procesales.</p>
                    {% endfor %}
                </div>
            </div>"""

new_block = """            <!-- Resoluciones / Actos Procesales -->
            <div style="background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); overflow: hidden;">
                <div style="padding: 20px; background: #f8f9fa; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; color: #333;">Actos Procesales (Resoluciones)</h3>
                    <button onclick="document.getElementById('modalActo').style.display='flex'" style="background: #28a745; color: white; padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">+ Nuevo Acto</button>
                </div>
                
                <div style="padding: 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <!-- CUADERNO PRINCIPAL -->
                    <div>
                        <h4 style="color: #0056b3; border-bottom: 2px solid #0056b3; padding-bottom: 5px; margin-top: 0;">Cuaderno Principal</h4>
                        {% for a in actos %}
                            {% if a.cuaderno == 'PRINCIPAL' %}
                            <div style="border-left: 4px solid #0056b3; padding-left: 15px; margin-bottom: 20px; background: #f8fbfd; padding: 10px 15px; border-radius: 0 8px 8px 0;">
                                <div style="display: flex; justify-content: space-between;">
                                    <h5 style="margin: 0 0 5px 0; color: #333;">
                                        Resolución N° {{ a.numero_resolucion|default:"-" }}
                                    </h5>
                                    <div style="text-align: right;">
                                        <span style="color: #666; font-size: 12px; display: block;">Res: {{ a.fecha_resolucion|date:"d M Y"|default:"Importado" }}</span>
                                        <span style="color: #17a2b8; font-size: 11px; font-weight: bold; display: block;">Reg: {{ a.registrado_por.username|default:"Sistema" }}</span>
                                    </div>
                                </div>
                                {% if a.sumilla %}<p style="margin: 5px 0; font-weight: bold; color: #444; font-size: 13px;">Sumilla: {{ a.sumilla }}</p>{% endif %}
                                <p style="margin: 5px 0 0 0; font-size: 13px; color: #555; line-height: 1.4;">{{ a.descripcion|linebreaksbr }}</p>
                                {% if es_gerencia %}
                                <form method="POST" style="margin-top: 10px; text-align: right;" onsubmit="return confirm('¿Seguro que deseas borrar este acto procesal?');">
                                    {% csrf_token %}
                                    <input type="hidden" name="action" value="delete_acto">
                                    <input type="hidden" name="acto_id" value="{{ a.id }}">
                                    <button type="submit" style="background: transparent; color: #dc3545; border: none; font-size: 12px; cursor: pointer; text-decoration: underline;">Borrar</button>
                                </form>
                                {% endif %}
                            </div>
                            {% endif %}
                        {% endfor %}
                    </div>

                    <!-- CUADERNO CAUTELAR -->
                    <div>
                        <h4 style="color: #d39e00; border-bottom: 2px solid #ffc107; padding-bottom: 5px; margin-top: 0;">Cuaderno Cautelar</h4>
                        {% for a in actos %}
                            {% if a.cuaderno == 'CAUTELAR' %}
                            <div style="border-left: 4px solid #ffc107; padding-left: 15px; margin-bottom: 20px; background: #fffdf5; padding: 10px 15px; border-radius: 0 8px 8px 0;">
                                <div style="display: flex; justify-content: space-between;">
                                    <h5 style="margin: 0 0 5px 0; color: #333;">
                                        Resolución N° {{ a.numero_resolucion|default:"-" }}
                                    </h5>
                                    <div style="text-align: right;">
                                        <span style="color: #666; font-size: 12px; display: block;">Res: {{ a.fecha_resolucion|date:"d M Y"|default:"Importado" }}</span>
                                        <span style="color: #17a2b8; font-size: 11px; font-weight: bold; display: block;">Reg: {{ a.registrado_por.username|default:"Sistema" }}</span>
                                    </div>
                                </div>
                                {% if a.sumilla %}<p style="margin: 5px 0; font-weight: bold; color: #444; font-size: 13px;">Sumilla: {{ a.sumilla }}</p>{% endif %}
                                <p style="margin: 5px 0 0 0; font-size: 13px; color: #555; line-height: 1.4;">{{ a.descripcion|linebreaksbr }}</p>
                                {% if es_gerencia %}
                                <form method="POST" style="margin-top: 10px; text-align: right;" onsubmit="return confirm('¿Seguro que deseas borrar este acto procesal?');">
                                    {% csrf_token %}
                                    <input type="hidden" name="action" value="delete_acto">
                                    <input type="hidden" name="acto_id" value="{{ a.id }}">
                                    <button type="submit" style="background: transparent; color: #dc3545; border: none; font-size: 12px; cursor: pointer; text-decoration: underline;">Borrar</button>
                                </form>
                                {% endif %}
                            </div>
                            {% endif %}
                        {% endfor %}
                    </div>
                </div>
            </div>"""

if "<!-- Resoluciones / Actos Procesales -->" in content:
    content = content.replace(old_block, new_block)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("detalle.html updated successfully.")
else:
    print("Could not find the block to replace!")
