from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count
from .models import Deudor, Gestion, TelefonoExtra, AsignacionCartera, CampanaAsterisk, DetalleCampanaAsterisk

# ─── Títulos del panel administrativo ───────────────────────────────────────
admin.site.site_header  = "P&P Soluciones Jurídicas — Administración"
admin.site.site_title   = "CRM P&P"
admin.site.index_title  = "Panel de Control"


# ─── DEUDOR ─────────────────────────────────────────────────────────────────
@admin.register(Deudor)
class DeudorAdmin(admin.ModelAdmin):
    list_display        = ('documento', 'nombre_completo', 'telefono_principal',
                           'cartera', 'agencia', 'saldo_deuda_fmt', 'rango_dias_mora')
    list_filter         = ('cartera', 'agencia', 'rango_dias_mora')
    search_fields       = ('documento', 'nombre_completo', 'telefono_principal', 'cuenta')
    ordering            = ('nombre_completo',)
    list_per_page       = 30
    fieldsets = (
        ('Identificación', {
            'fields': ('documento', 'nombre_completo', 'cuenta')
        }),
        ('Contacto', {
            'fields': ('telefono_principal', 'dir_casa', 'distrito')
        }),
        ('Cartera', {
            'fields': ('cartera', 'agencia', 'rango_dias_mora', 'monto_capital', 'saldo_deuda')
        }),
        ('Aval / Cónyuge', {
            'classes': ('collapse',),
            'fields': ('nom_conyuge', 'nom_aval', 'tlf_celular_aval', 'nom_conyuge_aval')
        }),
    )

    @admin.display(description='Saldo Deuda', ordering='saldo_deuda')
    def saldo_deuda_fmt(self, obj):
        if obj.saldo_deuda is not None:
            valor_formateado = f"{obj.saldo_deuda:,.2f}"
            return format_html('<span style="color:#8a3a00;font-weight:600;">S/ {}</span>', valor_formateado)
        return '—'


# ─── GESTIÓN ────────────────────────────────────────────────────────────────
@admin.register(Gestion)
class GestionAdmin(admin.ModelAdmin):
    list_display        = ('fecha', 'gestor', 'deudor', 'resultado', 'monto_pago_fmt', 'fecha_promesa')
    list_filter         = ('resultado', 'gestor', 'fecha')
    search_fields       = ('deudor__documento', 'deudor__nombre_completo',
                           'gestor__username', 'observacion')
    date_hierarchy      = 'fecha'
    ordering            = ('-fecha',)
    list_per_page       = 40
    readonly_fields     = ('fecha',)
    fieldsets = (
        ('Datos de la gestión', {
            'fields': ('deudor', 'gestor', 'resultado', 'observacion')
        }),
        ('Pago / Promesa', {
            'fields': ('monto_pago', 'fecha_promesa')
        }),
        ('Registro automático', {
            'classes': ('collapse',),
            'fields': ('fecha',)
        }),
    )

    @admin.display(description='Monto Pago', ordering='monto_pago')
    def monto_pago_fmt(self, obj):
        if obj.monto_pago and obj.monto_pago > 0:
            valor_formateado = f"{obj.monto_pago:,.2f}"
            return format_html('<span style="color:#1a6e2e;font-weight:700;">S/ {}</span>', valor_formateado)
        return '—'


# ─── TELÉFONO EXTRA ─────────────────────────────────────────────────────────
@admin.register(TelefonoExtra)
class TelefonoExtraAdmin(admin.ModelAdmin):
    list_display        = ('deudor', 'numero', 'descripcion')
    list_filter         = ('descripcion',)
    search_fields       = ('deudor__documento', 'deudor__nombre_completo', 'numero')
    ordering            = ('deudor__nombre_completo',)
    list_per_page       = 40


# ─── ASIGNACIÓN DE CARTERA ──────────────────────────────────────────────────
@admin.register(AsignacionCartera)
class AsignacionCarteraAdmin(admin.ModelAdmin):
    list_display        = ('gestor', 'tipo_badge', 'valor', 'fecha_asignacion')
    list_filter         = ('tipo', 'gestor')
    search_fields       = ('gestor__username', 'valor')
    ordering            = ('gestor__username', 'tipo', 'valor')
    list_per_page       = 50

    @admin.display(description='Tipo', ordering='tipo')
    def tipo_badge(self, obj):
        color = '#003366' if obj.tipo == 'cartera' else '#8a5a00'
        return format_html('<span style="background:{};color:white;padding:2px 8px;'
                           'border-radius:10px;font-size:11px;">{}</span>',
                           color, obj.tipo.upper())


# ─── CAMPAÑA ASTERISK ───────────────────────────────────────────────────────
@admin.register(CampanaAsterisk)
class CampanaAsteriskAdmin(admin.ModelAdmin):
    list_display        = ('id', 'nombre', 'proveedor', 'activa_badge',
                           'usuario_creador', 'fecha_creacion', 'total_numeros')
    list_filter         = ('proveedor', 'activa')
    search_fields       = ('nombre', 'usuario_creador__username')
    ordering            = ('-id',)
    list_per_page       = 20
    readonly_fields     = ('fecha_creacion',)

    @admin.display(description='Estado', ordering='activa', boolean=False)
    def activa_badge(self, obj):
        if obj.activa:
            return mark_safe('<span style="background:#1a6e2e;color:white;padding:2px 10px;'
                             'border-radius:10px;font-size:11px;">● ACTIVA</span>')
        return mark_safe('<span style="background:#888;color:white;padding:2px 10px;'
                         'border-radius:10px;font-size:11px;">○ Inactiva</span>')

    @admin.display(description='Nº Teléfonos')
    def total_numeros(self, obj):
        # Usa la anotación de get_queryset en vez de una query extra por fila
        return getattr(obj, '_total_numeros', obj.detalles.count())

    def get_queryset(self, request):
        # Resolver conteo de teléfonos en 1 sola query (evita N+1)
        qs = super().get_queryset(request)
        return qs.annotate(_total_numeros=Count('detalles'))


# ─── DETALLE CAMPAÑA ASTERISK ───────────────────────────────────────────────
@admin.register(DetalleCampanaAsterisk)
class DetalleCampanaAsteriskAdmin(admin.ModelAdmin):
    list_display        = ('campana', 'dni', 'telefono', 'cod_cliente', 'cod_telefono')
    list_filter         = ('campana',)
    search_fields       = ('dni', 'telefono')
    ordering            = ('campana', 'dni')
    list_per_page       = 50