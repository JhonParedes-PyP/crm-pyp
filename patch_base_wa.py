import os
import re

html_path = r"c:\CRM PYP\cobranza\templates\cobranza\base.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add link to WhatsApp Masivo
target = """<a href="{% url 'panel_campanas' %}">🎧 Asterisk</a>"""
replacement = """<a href="{% url 'panel_campanas' %}">🎧 Asterisk</a>
                <a href="{% url 'panel_whatsapp_masivo' %}" style="color: #25D366;">📲 WhatsApp Masivo</a>"""

content = content.replace(target, replacement)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("base.html patched.")
