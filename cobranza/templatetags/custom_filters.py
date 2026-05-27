from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Obtiene un valor de un diccionario por su clave"""
    return dictionary.get(key, [])

import re
from django.utils.html import escape
from django.utils.safestring import mark_safe

@register.filter
def format_obs(value):
    """Resalta el número de teléfono en las observaciones"""
    if not value:
        return ""
    safe_value = escape(value)
    pattern = r'^\[Tel:\s([^\]]+)\]'
    replacement = r'<strong style="font-size: 15px; font-weight: 900; color: #003366; background: #e8f0fe; padding: 3px 6px; border-radius: 4px; border: 1px solid #b6d4fe; margin-right: 5px; display: inline-block;">📞 \1</strong>'
    formatted_value = re.sub(pattern, replacement, safe_value)
    return mark_safe(formatted_value)