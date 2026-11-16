from django.db import migrations, models

SECCIONES = (
    ("ASISTENTE", "Asistente de consultas"),
)


def crear_secciones_asistente(apps, schema_editor):
    """
    Agrega el asistente de consultas a la matriz de módulos por rol en las
    instalaciones que ya tienen datos. Queda habilitado para todos los roles;
    el Administrador lo apaga por rol desde Equipo y roles. En una base vacía
    no hace nada: los datos los crea `cargar_datos_iniciales`.
    """
    Modulo = apps.get_model("seguridad", "Modulo")
    Rol = apps.get_model("seguridad", "Rol")
    PermisoRolModulo = apps.get_model("seguridad", "PermisoRolModulo")
    if not Modulo.objects.exists():
        return
    for codigo, nombre in SECCIONES:
        modulo, _ = Modulo.objects.get_or_create(codigo_modulo=codigo, defaults={"nombre_modulo": nombre})
        for rol in Rol.objects.all():
            PermisoRolModulo.objects.get_or_create(rol=rol, modulo=modulo, defaults={"habilitado": True})


def quitar_secciones_asistente(apps, schema_editor):
    codigos = [codigo for codigo, _ in SECCIONES]
    apps.get_model("seguridad", "Modulo").objects.filter(codigo_modulo__in=codigos).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("seguridad", "0005_modulo_seccion_panel"),
    ]

    operations = [
        migrations.AlterField(
            model_name="modulo",
            name="codigo_modulo",
            field=models.CharField(
                choices=[
                    ("MOD01", "Gestión de clientes"),
                    ("MOD02", "Calendario"),
                    ("MOD03", "Tablero de tareas Kanban"),
                    ("MOD04", "Expedición de documentos y certificados"),
                    ("MOD05", "Hallazgos y revisiones"),
                    ("MOD06", "Honorarios, cartera y cuentas de cobro"),
                    ("MOD07", "Comunicaciones integradas"),
                    ("MOD08", "Gestión de equipo y roles"),
                    ("MOD09", "Expediente y bitácora por cliente"),
                    ("MOD10", "Reportes y análisis"),
                    ("PANEL", "Panel principal"),
                    ("ASISTENTE", "Asistente de consultas"),
                ],
                max_length=20,
                unique=True,
            ),
        ),
        migrations.RunPython(crear_secciones_asistente, quitar_secciones_asistente),
    ]
