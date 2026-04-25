from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cobranza', '0014_seguimientoprogramado'),
    ]

    operations = [
        migrations.AddField(
            model_name='deudor',
            name='producto',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='deudor',
            name='nmes',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='deudor',
            name='departamento',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='deudor',
            name='provincia',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='deudor',
            name='dir_negocio',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deudor',
            name='imp_recup',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='deudor',
            name='imp_capital_rec',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='deudor',
            name='num_doc_conyuge',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='deudor',
            name='num_doc_aval',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='deudor',
            name='zona',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
