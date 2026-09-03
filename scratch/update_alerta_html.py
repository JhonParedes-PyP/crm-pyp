import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\judicial\detalle.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """                    {% for alerta in alertas %}
                    <div style="background: #f8f9fa; border: 1px solid #eee; padding: 12px; border-radius: 6px; margin-bottom: 10px;">
                        <h5 style="margin: 0 0 5px 0; color: #333;">{{ alerta.tipo_alerta }}</h5>
                        <p style="margin: 0; font-size: 12px; color: #dc3545; font-weight: bold;">Vence: {{ alerta.fecha_vencimiento|date:"d M Y" }}</p>
                    </div>
                    {% empty %}"""

new_block = """                    {% for alerta in alertas %}
                    <div style="background: #f8f9fa; border: 1px solid #eee; padding: 12px; border-radius: 6px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h5 style="margin: 0 0 5px 0; color: #333;">{{ alerta.tipo_alerta }}</h5>
                            <p style="margin: 0; font-size: 12px; color: #dc3545; font-weight: bold;">Vence: {{ alerta.fecha_vencimiento|date:"d M Y" }}</p>
                        </div>
                        <form method="POST" onsubmit="return confirm('¿Estás seguro que ya cumpliste con esta alerta? Desaparecerá de tu lista de pendientes.');">
                            {% csrf_token %}
                            <input type="hidden" name="action" value="complete_alerta">
                            <input type="hidden" name="alerta_id" value="{{ alerta.id }}">
                            <button type="submit" style="background: #28a745; color: white; border: none; border-radius: 4px; padding: 5px 10px; font-size: 11px; font-weight: bold; cursor: pointer;" title="Marcar como Completado">✔ Cumplido</button>
                        </form>
                    </div>
                    {% empty %}"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("detalle.html updated successfully.")
else:
    print("Could not find the block to replace!")
