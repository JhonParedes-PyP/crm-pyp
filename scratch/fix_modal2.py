import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\judicial\buscar.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

parts = content.split('{% endblock %}')

if len(parts) > 1 and '<div id="addExpedienteModal"' in parts[1]:
    new_content = parts[0] + parts[1] + "\n{% endblock %}"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("FIXED MODAL LOCATION 2")
else:
    print("MODAL NOT FOUND AFTER ENDBLOCK 2")
