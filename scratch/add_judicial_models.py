import os

file_path = r'c:\CRM PYP\cobranza\models.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_models = '''
# ==========================================
# MÓDULO JUDICIAL (AISLADO DE EXTRAJUDICIAL)
# ==========================================

class ExpedienteJudicial(models.Model):
    ESTADOS_PROCESO = (
        ('ACTIVO', 'Activo'),
        ('ARCHIVO', 'Archivo Provisional'),
        ('CONCLUIDO', 'Concluido'),
    )
    deudor = models.ForeignKey(Deudor, on_delete=models.CASCADE, related_name='expedientes_judiciales')
    numero_expediente = models.CharField(max_length=100, verbose_name="N° de Expediente Principal")
    numero_cautelar = models.CharField(max_length=100, null=True, blank=True, verbose_name="N° de Expediente Cautelar")
    materia = models.CharField(max_length=150, verbose_name="Materia del Proceso")
    juzgado = models.CharField(max_length=200, verbose_name="Juzgado")
    especialista_legal = models.CharField(max_length=200, null=True, blank=True, verbose_name="Especialista Legal")
    estado_proceso = models.CharField(max_length=50, choices=ESTADOS_PROCESO, default='ACTIVO')
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name="Fecha de Inicio del Proceso")
    
    class Meta:
        verbose_name = "Expediente Judicial"
        verbose_name_plural = "Expedientes Judiciales"
        ordering = ['-id']

    def __str__(self):
        return f"{self.numero_expediente} - {self.deudor.nombre_completo}"


class ActoProcesal(models.Model):
    expediente = models.ForeignKey(ExpedienteJudicial, on_delete=models.CASCADE, related_name='actos_procesales')
    numero_resolucion = models.CharField(max_length=50, null=True, blank=True, verbose_name="N° de Resolución")
    fecha_resolucion = models.DateField(verbose_name="Fecha de Resolución")
    fecha_notificacion = models.DateField(null=True, blank=True, verbose_name="Fecha de Notificación")
    descripcion = models.TextField(verbose_name="Descripción / Resumen")
    fojas = models.IntegerField(null=True, blank=True, verbose_name="Fojas")
    sumilla = models.CharField(max_length=255, null=True, blank=True, verbose_name="Sumilla")
    
    fecha_registro = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Acto Procesal"
        verbose_name_plural = "Actos Procesales"
        ordering = ['-fecha_resolucion', '-id']

    def __str__(self):
        return f"Resolución {self.numero_resolucion} - {self.expediente.numero_expediente}"


class AlertaJudicial(models.Model):
    ESTADOS_ALERTA = (
        ('PENDIENTE', 'Pendiente'),
        ('COMPLETADO', 'Completado'),
        ('VENCIDO', 'Vencido'),
    )
    acto_procesal = models.ForeignKey(ActoProcesal, on_delete=models.CASCADE, related_name='alertas', null=True, blank=True)
    expediente = models.ForeignKey(ExpedienteJudicial, on_delete=models.CASCADE, related_name='alertas')
    tipo_alerta = models.CharField(max_length=150, verbose_name="Tipo de Alerta / Tarea")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento")
    estado = models.CharField(max_length=50, choices=ESTADOS_ALERTA, default='PENDIENTE')
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Alerta Judicial"
        verbose_name_plural = "Alertas Judiciales"
        ordering = ['fecha_vencimiento']

    def __str__(self):
        return f"Alerta {self.fecha_vencimiento} - {self.tipo_alerta}"
'''

if 'class ExpedienteJudicial' not in content:
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(new_models)
    print('Models added.')
else:
    print('Models already exist.')
