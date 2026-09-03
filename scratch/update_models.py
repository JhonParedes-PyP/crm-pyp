import os
import re

file_path = r'c:\CRM PYP\cobranza\models.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacement1 = """class ExpedienteJudicial(models.Model):
    ESTADOS_PROCESO = (
        ('ACTIVO', 'Activo'),
        ('ARCHIVO', 'Archivo Provisional'),
        ('CONCLUIDO', 'Concluido'),
    )
    deudor = models.ForeignKey(Deudor, on_delete=models.CASCADE, related_name='expedientes_judiciales')
    numero_expediente = models.CharField(max_length=100, verbose_name="N° de Expediente Principal")
    numero_cautelar = models.CharField(max_length=100, null=True, blank=True, verbose_name="N° de Expediente Cautelar")
    materia = models.CharField(max_length=150, verbose_name="Materia del Proceso")
    
    # Nuevos campos
    distrito_judicial = models.CharField(max_length=150, null=True, blank=True, verbose_name="Distrito Judicial")
    sede_judicial = models.CharField(max_length=150, null=True, blank=True, verbose_name="Sede Judicial")
    condicion_recuperabilidad = models.CharField(max_length=50, null=True, blank=True, verbose_name="Condición")
    probabilidad_recuperacion = models.CharField(max_length=50, null=True, blank=True, verbose_name="Probabilidad de Recuperación")
    detalle_bien = models.TextField(null=True, blank=True, verbose_name="Detalle del Bien / Garantía")
    
    # Campos Cautelar
    codigo_cautelar = models.CharField(max_length=100, null=True, blank=True, verbose_name="Código Cautelar")
    tipo_medida_cautelar = models.CharField(max_length=150, null=True, blank=True, verbose_name="Tipo Medida Cautelar")
    estado_cautelar = models.CharField(max_length=100, null=True, blank=True, verbose_name="Estado Medida Cautelar")
    fecha_cautelar = models.DateField(null=True, blank=True, verbose_name="Fecha Presentación Cautelar")
    monto_demandado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Monto Demandado")

    juzgado = models.CharField(max_length=200, verbose_name="Juzgado")
    especialista_legal = models.CharField(max_length=200, null=True, blank=True, verbose_name="Especialista Legal")
    estado_proceso = models.CharField(max_length=50, choices=ESTADOS_PROCESO, default='ACTIVO')
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name="Fecha de Inicio del Proceso")"""

replacement2 = """class ActoProcesal(models.Model):
    CUADERNO_CHOICES = (
        ('PRINCIPAL', 'Principal'),
        ('CAUTELAR', 'Cautelar'),
    )
    expediente = models.ForeignKey(ExpedienteJudicial, on_delete=models.CASCADE, related_name='actos_procesales')
    cuaderno = models.CharField(max_length=20, choices=CUADERNO_CHOICES, default='PRINCIPAL')"""


content = re.sub(r'class ExpedienteJudicial\(models\.Model\):.*?fecha_inicio = models\.DateField\(null=True, blank=True, verbose_name="Fecha de Inicio del Proceso"\)', replacement1, content, flags=re.DOTALL)
content = re.sub(r'class ActoProcesal\(models\.Model\):.*?expediente = models\.ForeignKey\(ExpedienteJudicial, on_delete=models\.CASCADE, related_name=\'actos_procesales\'\)', replacement2, content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('models.py modified')
