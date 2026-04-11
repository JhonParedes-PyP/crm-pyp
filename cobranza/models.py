from django.db import models
from django.contrib.auth.models import User

class Deudor(models.Model):
    # DATOS PRINCIPALES (Los que ya teníamos)
    documento = models.CharField(max_length=20, unique=True) # DOC_DNI_RUC
    nombre_completo = models.CharField(max_length=200)       # NOM_CLI
    telefono_principal = models.CharField(max_length=50)     # TLF_CELULAR_CLIENTE
    cuenta = models.CharField(max_length=50, default='N/A')  # COD_CREDITO
    agencia = models.CharField(max_length=100, default='N/A')# NOM_AGENCIA
    cartera = models.CharField(max_length=50, default='GENERAL')
    
    # DATOS DE DINERO
    monto_capital = models.DecimalField(max_digits=12, decimal_places=2, default=0) # DEUDA_CAP
    saldo_deuda = models.DecimalField(max_digits=12, decimal_places=2, default=0)   # DEUDA_TOTAL
    
    # NUEVOS DATOS (Hoja 2) - Se permite que estén vacíos (null=True, blank=True)
    dir_casa = models.TextField(null=True, blank=True)
    distrito = models.CharField(max_length=100, null=True, blank=True)
    nom_conyuge = models.CharField(max_length=200, null=True, blank=True)
    nom_aval = models.CharField(max_length=200, null=True, blank=True)
    tlf_celular_aval = models.CharField(max_length=50, null=True, blank=True)
    nom_conyuge_aval = models.CharField(max_length=200, null=True, blank=True)
    rango_dias_mora = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.nombre_completo

class TelefonoExtra(models.Model):
    deudor = models.ForeignKey(Deudor, on_delete=models.CASCADE)
    numero = models.CharField(max_length=20)
    descripcion = models.CharField(max_length=50)

class Gestion(models.Model):
    deudor = models.ForeignKey(Deudor, on_delete=models.CASCADE)
    gestor = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    resultado = models.CharField(max_length=100)
    observacion = models.TextField()
    fecha_promesa = models.DateField(null=True, blank=True)
    monto_pago = models.DecimalField(max_digits=10, decimal_places=2, default=0)

# --- MODELO ACTUALIZADO: ASIGNACIÓN DE CARTERA Y AGENCIA POR GESTOR ---
class AsignacionCartera(models.Model):
    TIPO_CHOICES = [
        ('cartera', 'Cartera'),
        ('agencia', 'Agencia'),
    ]
    
    gestor = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='asignaciones')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='cartera')
    valor = models.CharField(max_length=100)  # Nombre de la cartera o agencia asignada
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['gestor', 'tipo', 'valor']  # Evita duplicados
        
    def __str__(self):
        return f"{self.gestor.username} - {self.get_tipo_display()}: {self.valor}"


# --- NUEVO MÓDULO: CAMPAÑAS ASTERISK ---
class CampanaAsterisk(models.Model):
    PROVEEDORES_CHOICES = [
        ('CAJA HUANCAYO', 'Caja Huancayo'),
        ('PROEMPRESA', 'Proempresa'),
        ('FOCMAC', 'Focmac'),
    ]

    # El campo ID se crea de forma automática e invisible (1, 2, 3...)
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Campaña")
    proveedor = models.CharField(max_length=50, choices=PROVEEDORES_CHOICES, verbose_name="Proveedor")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    activa = models.BooleanField(default=True, verbose_name="¿Campaña Activa?")
    usuario_creador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Creado por")

    class Meta:
        verbose_name = "Campaña Asterisk"
        verbose_name_plural = "Campañas Asterisk"
        ordering = ['-id'] # Ordena para que la última campaña creada aparezca primero

    def __str__(self):
        return f"Campaña {self.id} - {self.nombre}"

class DetalleCampanaAsterisk(models.Model):
    # Esto vincula cada teléfono con su campaña maestra (la 1, la 2, etc.)
    campana = models.ForeignKey(CampanaAsterisk, on_delete=models.CASCADE, related_name='detalles')
    
    # Los datos que irán directo al Excel final
    dni = models.CharField(max_length=20, verbose_name="DNI")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    cod_cliente = models.CharField(max_length=100, verbose_name="Código Cliente (Kubo)")
    cod_telefono = models.CharField(max_length=100, verbose_name="Código Teléfono (Kubo)")

    class Meta:
        verbose_name = "Detalle de Campaña"
        verbose_name_plural = "Detalles de Campaña"

    def __str__(self):
        return f"Campaña {self.campana.id} - Tel: {self.telefono}"