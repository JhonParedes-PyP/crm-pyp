import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\bandeja.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """    <div style="overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">"""

new_content = """    {% if deudores %}
    <div style="margin-bottom: 15px; display: flex; justify-content: flex-end;">
        <a href="{% url 'registrar_gestion' deudores.0.id %}?auto_dialer=1{% if request.GET.urlencode %}&{{ request.GET.urlencode }}{% endif %}" 
           style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 14px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; align-items: center; gap: 8px; animation: pulse 2s infinite;">
            🚀 Iniciar Auto-Marcador
        </a>
    </div>
    <style>
        @keyframes pulse {
            0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7); }
            70% { transform: scale(1.02); box-shadow: 0 0 0 10px rgba(40, 167, 69, 0); }
            100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(40, 167, 69, 0); }
        }
    </style>
    {% endif %}

    <div style="overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">"""

content = content.replace(target, new_content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("PATCH BANDEJA SUCCESS")
