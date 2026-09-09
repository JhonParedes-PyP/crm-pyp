import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\judicial\detalle.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

parts = content.split('{% endblock %}')

if len(parts) > 1 and '<!-- Modal Editar Expediente -->' in parts[1]:
    # The modal is in the second part
    new_content = parts[0] + parts[1] + "\n{% endblock %}"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("FIXED MODAL LOCATION")
else:
    print("MODAL NOT FOUND AFTER ENDBLOCK")
