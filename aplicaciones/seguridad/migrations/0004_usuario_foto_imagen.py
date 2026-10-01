# Módulo 8: la foto de perfil pasa de una URL sin mecanismo de subida a una
# imagen cargada desde «Mi perfil» (mismo cambio que el membrete en el M4).

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("seguridad", "0003_membrete_despacho_imagen"),
    ]

    operations = [
        migrations.RenameField(
            model_name="usuario",
            old_name="foto_url",
            new_name="foto",
        ),
        migrations.AlterField(
            model_name="usuario",
            name="foto",
            field=models.ImageField(blank=True, max_length=255, upload_to="fotos/"),
        ),
    ]
