import os
import re

html_path = r"c:\CRM PYP\cobranza\templates\cobranza\base.html"
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix CSS
content = content.replace(
    ".menu { \n            display: flex; \n            align-items: center; \n            gap: 25px;\n            flex-wrap: wrap;\n        }",
    ".menu { \n            display: flex; \n            align-items: flex-start; \n            gap: 25px;\n            flex-wrap: wrap;\n        }"
)

# Add CSS for <details> and <summary>
css_to_add = """
        details.menu-group {
            cursor: pointer;
        }
        details.menu-group summary {
            list-style: none; /* Hide default arrow */
            user-select: none;
            outline: none;
            margin-bottom: 8px;
        }
        details.menu-group summary::-webkit-details-marker {
            display: none;
        }
        .group-title {
            font-size: 11px;
            text-transform: uppercase;
            color: #88c0d0;
            font-weight: 800;
            letter-spacing: 1px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .group-title::after {
            content: '▼';
            font-size: 8px;
            margin-left: 6px;
            opacity: 0.7;
        }
        details[open].menu-group .group-title::after {
            content: '▲';
        }
        details.menu-group a {
            margin-bottom: 5px; /* Add space between links */
        }
"""
if "details.menu-group" not in content:
    content = content.replace(".group-title {", css_to_add + "\n        .group-title_old {")

# Find the menu block and replace <div class="menu-group"> with <details class="menu-group"> and <span class="group-title"> with <summary class="group-title">
# Also change the first group to <details class="menu-group" open>
menu_start_idx = content.find('<div class="menu">')
if menu_start_idx != -1:
    menu_end_idx = content.find('</div>\n        {% if user.is_authenticated %}', menu_start_idx)
    menu_block = content[menu_start_idx:menu_end_idx]
    
    # Replace the blocks
    menu_block = menu_block.replace('<div class="menu-group">', '<details class="menu-group">')
    menu_block = menu_block.replace('</div>\n            {% endif %}', '</details>\n            {% endif %}')
    # For groups not wrapped in endif
    menu_block = re.sub(r'</details>\n(\s*<!--)', r'</details>\n\1', menu_block)
    menu_block = menu_block.replace('</details>\n            </div>', '</details>\n            </details>') # Whoops
    # Better to just use regex to match each group block
    pass

# A cleaner way is to just do a string replacement on the exact menu block:
new_menu_block = """<div class="menu">
            
            <!-- GESTIÓN -->
            <details class="menu-group" open>
                <summary class="group-title">Gestión</summary>
                <a href="{% url 'dashboard_gerente' %}">📊 Dashboard</a>
                
                {% if not es_gerente_global %}
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

                {% if es_gerente_global %}
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
            </details>

            <!-- OPERACIONES (Gerencia) -->
            {% if es_gerente_global %}
            <details class="menu-group">
                <summary class="group-title">Operaciones</summary>
                <a href="{% url 'agenda_diaria' %}">📆 Agenda de Supervisión</a>
                <a href="{% url 'asignar_carteras' %}">👥 Asignar Carteras</a>
                <a href="{% url 'asignaciones_diarias' %}">📅 Asignación Diaria</a>
            </details>
            {% endif %}

            <!-- CARGAS Y PROCESOS -->
            <details class="menu-group">
                <summary class="group-title">Procesos</summary>
                <a href="{% url 'subir_excel' %}">📁 Cargar Cartera</a>
                <a href="{% url 'generar_cartas' %}">📩 Generar Cartas</a>
                {% if es_gerente_global %}
                <a href="{% url 'cargar_telefonos' %}">📱 Cargar Teléfonos</a>
                {% endif %}
                {% if user.username == 'JPAREDES' %}
                <a href="{% url 'subir_gestiones_masivas' %}">📤 Subir Gestiones</a>
                {% endif %}
            </details>

            <!-- HERRAMIENTAS -->
            {% if es_gerente_global %}
            <details class="menu-group">
                <summary class="group-title">Herramientas</summary>
                <a href="{% url 'panel_campanas' %}">🎧 Asterisk</a>
                <a href="{% url 'panel_estrategia_ia' %}" style="color: #00d2ff;">🤖 Estrategia IA</a>
            </details>
            {% endif %}

            <!-- SISTEMA -->
            <details class="menu-group">
                <summary class="group-title">Sistema</summary>
                {% if user.is_staff %}
                <a href="/admin/">⚙️ Configuración</a>
                {% endif %}
                <a href="#" onclick="window.open('{% url 'webphone_popup' %}', 'WebPhone', 'width=260,height=460,resizable=no'); return false;" style="background: #e83e8c; padding: 5px 12px; border-radius: 4px; color: white; border: 1px solid white;">📞 Iniciar Teléfono</a>
            </details>
"""
if menu_start_idx != -1:
    content = content[:menu_start_idx] + new_menu_block + content[menu_end_idx:]

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Menu details applied.")
