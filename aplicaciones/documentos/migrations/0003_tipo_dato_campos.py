"""
Tipo de dato de cada campo de plantilla (23-nov-2026): los valores en pesos,
las identificaciones y los porcentajes solo aceptan números al generar el
documento. Los campos que ya existen toman el tipo que les corresponde por su
nombre (la misma regla de `CampoPlantilla.tipo_dato_sugerido`, copiada aquí
para que la migración no dependa del código actual).
"""

from django.db import migrations, models

PREFIJOS_PESOS = (
    "valor",
    "total",
    "monto",
    "ingreso",
    "patrimonio",
    "consignaciones",
    "activo",
    "pasivo",
    "saldo",
    "salario",
)


def _sugerido(nombre_campo):
    nombre = nombre_campo.strip().lower()
    if "porcentaje" in nombre:
        return "Porcentaje"
    if nombre.startswith(("identificación", "identificacion", "cédula", "cedula", "número de identificación")):
        return "Número"
    if nombre.startswith(PREFIJOS_PESOS):
        return "Valor en pesos"
    return "Texto"


def asignar_tipos(apps, schema_editor):
    CampoPlantilla = apps.get_model("documentos", "CampoPlantilla")
    for campo in CampoPlantilla.objects.all():
        tipo = _sugerido(campo.nombre_campo)
        if tipo != "Texto":
            CampoPlantilla.objects.filter(pk=campo.pk).update(tipo_dato=tipo)


class Migration(migrations.Migration):
    dependencies = [
        ("documentos", "0002_remove_documento_archivo_url_documento_archivo_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="campoplantilla",
            name="tipo_dato",
            field=models.CharField(
                choices=[
                    ("Texto", "Texto"),
                    ("Valor en pesos", "Valor en pesos"),
                    ("Número", "Número (sin puntos)"),
                    ("Porcentaje", "Porcentaje"),
                ],
                default="Texto",
                max_length=20,
                verbose_name="tipo de dato",
            ),
        ),
        migrations.RunPython(asignar_tipos, migrations.RunPython.noop),
    ]
