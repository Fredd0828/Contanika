"""
Modelos del módulo 9: expediente y bitácora por cliente.

La bitácora es cronológica: una anotación vigente no se edita ni se elimina.
El Administrador puede archivarla y, ya archivada, corregirla o eliminarla
(decisión del usuario, 23-nov-2026). Cada una de esas acciones queda en el
registro de acciones del expediente (`AccionAnotacion`), que no se borra
aunque la anotación sí.
"""

from django.db import models
from django.utils import timezone


class Anotacion(models.Model):
    """Anotación cronológica del expediente y bitácora de un cliente."""

    # Tipos sugeridos por el spec; el campo es de selección abierta, así que
    # se puede escribir un tipo nuevo (p. ej. "Retención en la fuente").
    TIPOS_SUGERIDOS = [
        "Reunión",
        "Llamada",
        "Entrega de documento",
        "Acuerdo",
        "Observación interna",
        "Nota al cliente",
        "Hito",
        "Alerta",
        "Modificación",
    ]

    id_anotacion = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        db_column="id_cliente",
        related_name="anotaciones",
    )
    tipo_anotacion = models.CharField(max_length=40)
    # Fecha en que ocurrió lo anotado (editable, por defecto hoy); `fecha_hora`
    # es el momento exacto del registro y no se puede alterar (HU025-2).
    fecha = models.DateField(default=timezone.localdate)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        "seguridad.Usuario",
        on_delete=models.PROTECT,
        db_column="id_usuario",
        related_name="anotaciones_expediente",
    )
    contenido = models.TextField()
    archivado = models.BooleanField(default=False)

    class Meta:
        db_table = "anotacion"
        verbose_name = "anotación del expediente"
        verbose_name_plural = "anotaciones del expediente"
        ordering = ["-fecha", "-fecha_hora"]
        indexes = [
            models.Index(fields=["cliente", "-fecha", "-fecha_hora"], name="idx_anotacion_cliente"),
        ]

    def __str__(self):
        return f"{self.tipo_anotacion} - {self.cliente.nombre_razon_social}"

    def archivar(self):
        """Marca la anotación como archivada; el registro se conserva."""
        self.archivado = True
        self.save(update_fields=["archivado"])

    def restaurar(self):
        """Devuelve al expediente una anotación archivada por error."""
        self.archivado = False
        self.save(update_fields=["archivado"])

    def delete(self, *args, **kwargs):
        """
        Impide borrar una anotación por accidente.

        Si algo intenta borrar una anotación, el sistema la archiva en su
        lugar. El borrado real solo lo hace `servicios.eliminar_anotacion`,
        sobre una anotación ya archivada y dejando constancia en el registro.
        """
        self.archivar()


class AccionAnotacion(models.Model):
    """
    Lo que el Administrador hizo con una anotación del expediente: archivarla,
    restaurarla, corregirla o eliminarla. Queda aunque la anotación se borre.
    """

    ARCHIVO = "Archivó"
    RESTAURO = "Restauró"
    EDITO = "Editó"
    ELIMINO = "Eliminó"
    OPCIONES_ACCION = [(ARCHIVO, ARCHIVO), (RESTAURO, RESTAURO), (EDITO, EDITO), (ELIMINO, ELIMINO)]

    id_accion = models.AutoField(primary_key=True)
    anotacion = models.ForeignKey(
        Anotacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="id_anotacion",
        related_name="acciones",
    )
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        db_column="id_cliente",
        related_name="acciones_expediente",
    )
    usuario = models.ForeignKey(
        "seguridad.Usuario",
        on_delete=models.PROTECT,
        db_column="id_usuario",
        related_name="acciones_expediente",
    )
    accion = models.CharField(max_length=20, choices=OPCIONES_ACCION)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    # Qué anotación era (tipo, fecha y contenido) y, al editar, qué cambió.
    detalle = models.TextField(blank=True)

    class Meta:
        db_table = "accion_anotacion"
        verbose_name = "acción sobre una anotación"
        verbose_name_plural = "acciones sobre anotaciones"
        ordering = ["-fecha_hora", "-id_accion"]

    def __str__(self):
        return f"{self.usuario} {self.accion.lower()} una anotación de {self.cliente}"
