from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cobranza', '0013_foto_evidencia_imagefield'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SeguimientoProgramado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_programada', models.DateField()),
                ('motivo', models.CharField(max_length=200)),
                ('completado', models.BooleanField(default=False)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('deudor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seguimientos', to='cobranza.deudor')),
                ('gestor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seguimientos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Seguimiento Programado',
                'verbose_name_plural': 'Seguimientos Programados',
                'ordering': ['fecha_programada'],
            },
        ),
    ]
