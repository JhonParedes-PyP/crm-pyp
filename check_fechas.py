from cobranza.models import Deudor

# All CAJA HUANCAYO clients
qs = Deudor.objects.filter(cartera='CAJA HUANCAYO', activo=True)
total = qs.count()

# With Convenio
# From previous logic: qs.exclude(negociacion__isnull=True).exclude(negociacion__exact='').exclude(negociacion__iexact='nan').exclude(negociacion__iexact='none').exclude(negociacion__iexact='null')
qs_convenio = qs.exclude(negociacion__isnull=True).exclude(negociacion__exact='').exclude(negociacion__iexact='nan').exclude(negociacion__iexact='none').exclude(negociacion__iexact='null')

convenio_total = qs_convenio.count()
convenio_with_date = qs_convenio.exclude(ultimo_dia_pago__isnull=True).count()
convenio_without_date = qs_convenio.filter(ultimo_dia_pago__isnull=True).count()

print(f"Total Caja Huancayo: {total}")
print(f"Total con Convenio: {convenio_total}")
print(f"Con Convenio y Fecha de Pago: {convenio_with_date}")
print(f"Con Convenio SIN Fecha de Pago: {convenio_without_date}")
