"""
Amplía el catálogo de obligaciones con todo lo que trae el calendario
tributario de la DIAN (página 2 del calendario 2026) y la exógena nacional de
grandes contribuyentes, que va por último dígito y no por los dos últimos.

Solo agrega filas: no toca las obligaciones ya marcadas en los clientes.
"""

from django.db import migrations

NACIONAL = "Nacional"

OBLIGACIONES_NUEVAS = [
    "Impuesto al consumo",
    "Gasolina y ACPM",
    "Impuesto al carbono",
    "IVA servicios desde el exterior",
    "Bebidas ultraprocesadas",
    "Plásticos de un solo uso",
    "Presencia económica significativa",
    "Impuesto al patrimonio",
    "Precios transferencia - informativa",
    "Precios transferencia - documentación",
    "Informe país por país",
    "Beneficiarios finales (RUB)",
    "Activos exterior grandes contribuyentes",
    "Activos exterior personas jurídicas",
    "Activos exterior personas naturales",
    "Activos exterior RST",
    "Exógena nacional grandes contribuyentes",
]


def agregar(apps, schema_editor):
    ObligacionTributaria = apps.get_model("clientes", "ObligacionTributaria")
    for nombre in OBLIGACIONES_NUEVAS:
        ObligacionTributaria.objects.get_or_create(nombre=nombre, defaults={"ambito": NACIONAL})


def quitar(apps, schema_editor):
    ObligacionTributaria = apps.get_model("clientes", "ObligacionTributaria")
    ObligacionTributaria.objects.filter(nombre__in=OBLIGACIONES_NUEVAS, clientes__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0007_unico_cliente_nit"),
    ]

    operations = [
        migrations.RunPython(agregar, quitar),
    ]
