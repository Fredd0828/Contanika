from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("seguridad", "0006_modulo_secciones_asistente"),
    ]

    operations = [
        migrations.AddField(
            model_name="configuraciondespacho",
            name="dias_aviso_vencimientos",
            field=models.PositiveSmallIntegerField(
                default=5,
                help_text="La campana avisa los vencimientos pendientes con esta anticipación. 0 = solo alertas configuradas.",
                verbose_name="días de aviso de vencimientos",
            ),
        ),
    ]
