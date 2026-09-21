"""
Modelos del módulo 10: reportes y análisis.

Catálogo de los seis reportes del sistema y la habilitación de cada uno
por rol, que el Administrador configura de forma individual.
"""

from django.db import models


class Reporte(models.Model):
    """Catálogo de los reportes disponibles en el módulo de análisis."""

    CLIENTES = "Clientes"
    VENCIMIENTOS = "Vencimientos tributarios"
    CARTERA = "Cartera"
    CUENTAS_COBRO = "Cuentas de cobro"
    TAREAS = "Tareas del Kanban"
    INGRESOS = "Ingresos mensuales del despacho"

    OPCIONES_REPORTE = [
        (CLIENTES, CLIENTES),
        (VENCIMIENTOS, VENCIMIENTOS),
        (CARTERA, CARTERA),
        (CUENTAS_COBRO, CUENTAS_COBRO),
        (TAREAS, TAREAS),
        (INGRESOS, INGRESOS),
    ]

    id_reporte = models.AutoField(primary_key=True)
    nombre_reporte = models.CharField(max_length=60, unique=True, choices=OPCIONES_REPORTE)
    modulo_origen = models.CharField(max_length=40)

    class Meta:
        db_table = "reporte"
        verbose_name = "reporte"
        verbose_name_plural = "reportes"
        ordering = ["id_reporte"]

    def __str__(self):
        return self.nombre_reporte


class PermisoReporteRol(models.Model):
    """Habilitación de cada reporte individual por rol."""

    id_permiso_reporte = models.AutoField(primary_key=True)
    reporte = models.ForeignKey(
        Reporte,
        on_delete=models.CASCADE,
        db_column="id_reporte",
        related_name="permisos_rol",
    )
    rol = models.ForeignKey(
        "seguridad.Rol",
        on_delete=models.CASCADE,
        db_column="id_rol",
        related_name="permisos_reporte",
    )
    habilitado = models.BooleanField(default=True)

    class Meta:
        db_table = "permiso_reporte_rol"
        verbose_name = "permiso de reporte por rol"
        verbose_name_plural = "permisos de reportes por rol"
        constraints = [
            models.UniqueConstraint(fields=["reporte", "rol"], name="unico_reporte_rol"),
        ]

    def __str__(self):
        return f"{self.rol.nombre_rol} - {self.reporte.nombre_reporte}: {self.habilitado}"
