import os
import django
from django.template import Context, Template
from django.conf import settings

settings.configure(TEMPLATES=[{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': False,
    'OPTIONS': {},
}])
django.setup()

tpl = Template("{% if 'SIN NEGOCIACI' in var.upper %}YES{% else %}NO{% endif %}")
print(tpl.render(Context({'var': 'Sin Negociación'})))
