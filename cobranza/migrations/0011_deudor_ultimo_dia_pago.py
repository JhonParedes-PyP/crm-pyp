from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cobranza', '0010_detallecampanaasterisk'),
    ]

    operations = [
        migrations.AddField(
            model_name='deudor',
            name='ultimo_dia_pago',
            field=models.DateField(blank=True, null=True),
        ),
    ]
