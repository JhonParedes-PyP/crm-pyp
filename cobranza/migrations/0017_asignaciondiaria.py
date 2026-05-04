from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cobranza', '0016_agentesip'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AsignacionDiaria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_asignada', models.DateField()),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('deudor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asignaciones_diarias', to='cobranza.deudor')),
                ('gestor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asignaciones_diarias', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Asignacion Diaria',
                'verbose_name_plural': 'Asignaciones Diarias',
                'ordering': ['-fecha_asignada', 'gestor__username', 'deudor__nombre_completo'],
                'unique_together': {('gestor', 'deudor', 'fecha_asignada')},
            },
        ),
    ]
