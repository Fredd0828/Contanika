"""
Rellena `periodo_gravable` en los vencimientos nacionales automáticos que ya
existían antes de agregar ese campo, para que la próxima vez que alguien
recalcule (después de corregir una fecha en la tabla DIAN) el sistema pueda
identificar el mismo período y actualizarlo en vez de crear un duplicado.
"""

from django.db import migrations


def calcular_grupo_nit(cliente):
    """Reproduce aplicaciones.calendario.servicios.calcular_grupo_nit sin importar el módulo."""
    numero = (cliente.nit_cedula or "").strip()
    if not numero.isdigit():
        return None
    if cliente.tipo_documento == "NIT":
        return numero[-1]
    if cliente.tipo_documento == "CC":
        return numero[-2:].zfill(2)
    return None


def backfill(apps, schema_editor):
    Vencimiento = apps.get_model("calendario", "Vencimiento")
    TablaReferenciaDian = apps.get_model("calendario", "TablaReferenciaDian")

    pendientes = Vencimiento.objects.filter(
        ambito="Nacional", tarea__isnull=True, periodo_gravable=""
    ).select_related("cliente")

    for vencimiento in pendientes:
        grupo = calcular_grupo_nit(vencimiento.cliente)
        if grupo is None:
            continue
        coincidencias = list(
            TablaReferenciaDian.objects.filter(
                tipo_obligacion=vencimiento.tipo_obligacion,
                grupo_nit=grupo,
                fecha_vencimiento=vencimiento.fecha_vencimiento,
            )
        )
        if len(coincidencias) == 1:
            vencimiento.periodo_gravable = coincidencias[0].periodo_gravable
            vencimiento.save(update_fields=["periodo_gravable"])


def revertir(apps, schema_editor):
    Vencimiento = apps.get_model("calendario", "Vencimiento")
    Vencimiento.objects.filter(ambito="Nacional", tarea__isnull=True).update(periodo_gravable="")


class Migration(migrations.Migration):

    dependencies = [
        ("calendario", "0002_vencimiento_periodo_gravable"),
    ]

    operations = [
        migrations.RunPython(backfill, revertir),
    ]
