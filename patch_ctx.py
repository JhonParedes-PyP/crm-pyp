import os

path = r"c:\CRM PYP\crm_pyp_config\context_processors.py"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the first return
old_ret_1 = """        return {
            'agenda_alertas_count': total,
            'pagos_proximos_count': pagos_proximos_count,
            'puede_modo_agente': request.user.username.upper() == 'JPAREDES',
        }"""
new_ret_1 = """        return {
            'agenda_alertas_count': total,
            'pagos_proximos_count': pagos_proximos_count,
            'puede_modo_agente': request.user.username.upper() == 'JPAREDES',
            'es_gerente_global': es_gerente_flag,
        }"""

# Replace the second return
old_ret_2 = """        return {
            'agenda_alertas_count': 0,
            'pagos_proximos_count': 0,
            'puede_modo_agente': request.user.username.upper() == 'JPAREDES',
        }"""
new_ret_2 = """        return {
            'agenda_alertas_count': 0,
            'pagos_proximos_count': 0,
            'puede_modo_agente': request.user.username.upper() == 'JPAREDES',
            'es_gerente_global': request.user.groups.filter(name='GERENTE').exists() or request.user.is_superuser,
        }"""

# Replace unauthenticated return
old_ret_3 = "return {'agenda_alertas_count': 0, 'pagos_proximos_count': 0, 'puede_modo_agente': False}"
new_ret_3 = "return {'agenda_alertas_count': 0, 'pagos_proximos_count': 0, 'puede_modo_agente': False, 'es_gerente_global': False}"


if old_ret_1 in content:
    content = content.replace(old_ret_1, new_ret_1)
if old_ret_2 in content:
    content = content.replace(old_ret_2, new_ret_2)
if old_ret_3 in content:
    content = content.replace(old_ret_3, new_ret_3)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("context_processors updated")
