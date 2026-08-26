import os

html_path = r"c:\CRM PYP\cobranza\templates\cobranza\base.html"
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# I will find the exact block from `<div class="menu">` to `</div>\n        {% if user.is_authenticated %}`
start_tag = '<div class="menu">'
end_tag = '        </div>\n        {% if user.is_authenticated %}'

if start_tag in content and end_tag in content:
    idx_start = content.find(start_tag)
    idx_end = content.find(end_tag)
    
    new_menu = """<style>
            .menu-group {
                display: flex;
                align-items: center;
                gap: 15px;
                padding-right: 15px;
                border-right: 1px solid rgba(255,255,255,0.2);
            }
            .menu-group:last-child {
                border-right: none;
            }
            .group-title {
                font-size: 10px;
                text-transform: uppercase;
                color: #88c0d0;
                font-weight: 800;
                letter-spacing: 1px;
                margin-right: 5px;
                opacity: 0.8;
            }
            @media (max-width: 768px) {
                .menu-group {
                    border-right: none;
                    border-bottom: 1px solid rgba(255,255,255,0.2);
                    padding-bottom: 10px;
                    width: 100%;
                    justify-content: center;
                }
            }
        </style>
        <div class="menu">
            
            <!-- GESTIÓN -->
            <div class="menu-group">
                <span class="group-title">Gestión</span>
                <a href="{% url 'dashboard_gerente' %}">📊 Dashboard</a>
                
                {% if not es_gerente %}
                <a id="agenda-link" href="{% url 'agenda_diaria' %}" style="position:relative;">
                    📅 Agenda Diaria
                    {% if agenda_alertas_count > 0 %}
                    <span style="position:absolute; top:-8px; right:-10px; background:#dc3545; color:white; border-radius:50%; width:18px; height:18px; font-size:10px; font-weight:bold; display:flex; align-items:center; justify-content:center; line-height:1;">{{ agenda_alertas_count }}</span>
                    {% endif %}
                </a>
                <a href="{% url 'rutas_cobranza' %}">🗺️ Rutas de Cobranza</a>
                <a href="{% url 'bandeja_gestor' %}" style="position:relative;">
                    📞 Bandeja
                    {% if pagos_proximos_count > 0 %}
                    <span class="badge-pagos-proximos" style="position:absolute; top:-8px; right:-10px; background:#ff8c00; color:white; border-radius:50%; width:18px; height:18px; font-size:10px; font-weight:bold; display:flex; align-items:center; justify-content:center; line-height:1; box-shadow:0 0 5px rgba(0,0,0,0.3);" title="Pagos por vencer">{{ pagos_proximos_count }}</span>
                    {% endif %}
                </a>
                {% endif %}

                {% if es_gerente %}
                <a href="{% url 'vouchers_pendientes' %}">📑 Vouchers</a>
                {% if puede_modo_agente %}
                <a href="{% url 'bandeja_gestor' %}?modo=agente" style="position:relative;">
                    📞 Mi Bandeja
                    {% if pagos_proximos_count > 0 %}
                    <span class="badge-pagos-proximos" style="position:absolute; top:-8px; right:-10px; background:#ff8c00; color:white; border-radius:50%; width:18px; height:18px; font-size:10px; font-weight:bold; display:flex; align-items:center; justify-content:center; line-height:1; box-shadow:0 0 5px rgba(0,0,0,0.3);" title="Pagos por vencer">{{ pagos_proximos_count }}</span>
                    {% endif %}
                </a>
                <a href="{% url 'agenda_diaria' %}?modo=agente">📅 Mi Agenda</a>
                {% endif %}
                <a href="{% url 'rutas_cobranza' %}">🗺️ Rutas de Cobranza</a>
                {% endif %}
            </div>

            <!-- OPERACIONES (Gerencia) -->
            {% if es_gerente %}
            <div class="menu-group">
                <span class="group-title">Operaciones</span>
                <a href="{% url 'asignar_carteras' %}">👥 Asignar Carteras</a>
                <a href="{% url 'asignaciones_diarias' %}">📅 Asignación Diaria</a>
            </div>
            {% endif %}

            <!-- CARGAS Y PROCESOS -->
            <div class="menu-group">
                <span class="group-title">Procesos</span>
                <a href="{% url 'subir_excel' %}">📁 Cargar Cartera</a>
                <a href="{% url 'generar_cartas' %}">📩 Generar Cartas</a>
                {% if es_gerente %}
                <a href="{% url 'cargar_telefonos' %}">📱 Cargar Teléfonos</a>
                {% endif %}
                {% if user.username == 'JPAREDES' %}
                <a href="{% url 'subir_gestiones_masivas' %}">📤 Subir Gestiones</a>
                {% endif %}
            </div>

            <!-- HERRAMIENTAS -->
            {% if es_gerente %}
            <div class="menu-group">
                <span class="group-title">Herramientas</span>
                <a href="{% url 'panel_campanas' %}">🎧 Asterisk</a>
                <a href="{% url 'panel_estrategia_ia' %}" style="color: #00d2ff;">🤖 Estrategia IA</a>
            </div>
            {% endif %}

            <!-- SISTEMA -->
            <div class="menu-group">
                <span class="group-title">Sistema</span>
                {% if user.is_staff %}
                <a href="/admin/">⚙️ Configuración</a>
                {% endif %}
                <a href="#" onclick="window.open('{% url 'webphone_popup' %}', 'WebPhone', 'width=260,height=460,resizable=no'); return false;" style="background: #e83e8c; padding: 5px 12px; border-radius: 4px; color: white; border: 1px solid white;">📞 Iniciar Teléfono</a>
            </div>
"""

    # Do replacement
    content = content[:idx_start] + new_menu + content[idx_end:]

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Menu replaced successfully.")
else:
    print("Tags not found.")
