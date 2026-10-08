"""
Modelos del módulo 9: expediente y bitácora por cliente.

La bitácora es cronológica e inmutable: las anotaciones no se editan ni se
eliminan, solo se marcan como archivadas por el Administrador, de modo que el
historial de gestión de cada cliente quede completo desde su ingreso al
despacho.
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
        Impide eliminar anotaciones de la bitácora.

        Si algo intenta borrar una anotación, el sistema la archiva en su
        lugar para no perder la trazabilidad del expediente.
        """
        self.archivar()
