"""
Siembra el catálogo de obligaciones tributarias y asigna a cada cliente
existente las obligaciones que le correspondían con la lógica automática
anterior (régimen tributario + responsable de IVA), para que ningún cliente
quede sin obligaciones al pasar al modelo de selección explícita.
"""

from django.db import migrations

NACIONAL = "Nacional"
DISTRITAL = "Distrital"

CATALOGO_INICIAL = [
    ("Renta personas naturales", NACIONAL),
    ("Renta personas jurídicas", NACIONAL),
    ("Renta grandes contribuyentes", NACIONAL),
    ("Retención en la fuente", NACIONAL),
    ("IVA bimestral", NACIONAL),
    ("IVA cuatrimestral", NACIONAL),
    ("RST anticipo bimestral", NACIONAL),
    ("RST consolidada anual", NACIONAL),
    ("Exógena nacional", NACIONAL),
    ("Exógena distrital", DISTRITAL),
]


def _obligaciones_por_cliente_legado(cliente):
    """Reproduce la lógica automática que existía antes de la selección explícita."""
    regimen = (cliente.regimen_tributario or "").strip().lower()

    if "simple" in regimen or "simplif" in regimen:
        return ["RST anticipo bimestral", "RST consolidada anual"]
    if cliente.tipo_persona == "Jurídica":
        obligaciones = ["Renta personas jurídicas", "Retención en la fuente"]
        if cliente.responsable_iva:
            obligaciones.append("IVA bimestral")
        return obligaciones

    obligaciones = ["Renta personas naturales"]
    if cliente.responsable_iva:
        obligaciones += ["IVA bimestral", "Retención en la fuente"]
    return obligaciones


def sembrar_y_migrar(apps, schema_editor):
    ObligacionTributaria = apps.get_model("clientes", "ObligacionTributaria")
    ClienteObligacion = apps.get_model("clientes", "ClienteObligacion")
    Cliente = apps.get_model("clientes", "Cliente")

    catalogo = {}
    for nombre, ambito in CATALOGO_INICIAL:
        obligacion, _ = ObligacionTributaria.objects.get_or_create(
            nombre=nombre, defaults={"ambito": ambito}
        )
        catalogo[nombre] = obligacion

    for cliente in Cliente.objects.all():
        for nombre in _obligaciones_por_cliente_legado(cliente):
            obligacion = catalogo.get(nombre)
            if obligacion is not None:
                ClienteObligacion.objects.get_or_create(cliente=cliente, obligacion_tributaria=obligacion)


def revertir(apps, schema_editor):
    ClienteObligacion = apps.get_model("clientes", "ClienteObligacion")
    ObligacionTributaria = apps.get_model("clientes", "ObligacionTributaria")
    ClienteObligacion.objects.all().delete()
    ObligacionTributaria.objects.filter(nombre__in=[nombre for nombre, _ in CATALOGO_INICIAL]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0005_obligaciontributaria_clienteobligacion"),
    ]

    operations = [
        migrations.RunPython(sembrar_y_migrar, revertir),
    ]
