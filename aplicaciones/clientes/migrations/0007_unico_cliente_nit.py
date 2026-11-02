from django.db import migrations, models


class Migration(migrations.Migration):
    """El NIT o cédula de un cliente es único también en la base de datos."""

    dependencies = [
        ("clientes", "0006_sembrar_obligaciones_tributarias"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="cliente",
            constraint=models.UniqueConstraint(fields=("nit_cedula",), name="unico_cliente_nit"),
        ),
    ]
