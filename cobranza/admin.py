from django.contrib import admin
from .models import Deudor, Gestion, TelefonoExtra, AsignacionCartera

admin.site.register(Deudor)
admin.site.register(Gestion)
admin.site.register(TelefonoExtra)
admin.site.register(AsignacionCartera)