import os

file_path = r"c:\CRM PYP\cobranza\templates\cobranza\dashboard.html"

with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

start1 = text.find('{% if es_gerente and pagos_no_reflejados_caja_huancayo %}')
end1 = text.find('{% endif %}', start1) + 11

start2 = text.find('{% if es_gerente and pagos_no_reflejados_proempresa %}')
end2 = text.find('{% endif %}', start2) + 11

blocks = text[start1:end1] + '\n\n' + text[start2:end2]

# manual replace for mojibake inside these two blocks
replacements = {
    'ÃƒÂ°Ã‚ÂŸÃ‚Â”Ã‚Â ': '🔍',
    'ÃƒÂƒÃ‚Âº': 'ú',
    'aÃƒÂƒÃ‚Âºn': 'aún',
    'gestiÃƒÂƒÃ‚Â³n': 'gestión',
    'AcciÃƒÂƒÃ‚Â³n': 'Acción',
    'ÃƒÂƒÃ‚Âš': 'Ú',
    'âš ï¸ ': '⚠️',
    'aÃºn': 'aún',
    'gestiÃ³n': 'gestión',
    'PAGÃ“': 'PAGO',
    'ǽs?': '⚠️',
    'aǟn': 'aún',
    'gestiǟn': 'gestión',
    'PAGǟ"': 'PAGO',
    'Acciǟn': 'Acción',
}
for k, v in replacements.items():
    blocks = blocks.replace(k, v)

with open(r"c:\CRM PYP\scratch\blocks_fixed.txt", "w", encoding="utf-8") as f:
    f.write(blocks)
