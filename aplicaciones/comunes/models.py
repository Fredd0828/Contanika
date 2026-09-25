"""Modelos compartidos por varios módulos del sistema Contanika."""

from django.db import models


class Adjunto(models.Model):
    """
    Archivo de soporte adjunto a un hallazgo o a una anotación del expediente.

    Es una tabla genérica: `tabla_origen` indica a qué entidad pertenece el
    archivo ('hallazgo' o 'anotacion') y `id_origen` guarda el identificador
    de esa entidad, evitando duplicar la relación en cada módulo.
    """

    HALLAZGO = "hallazgo"
    ANOTACION = "anotacion"
    OPCIONES_TABLA_ORIGEN = [
        (HALLAZGO, "Hallazgo"),
        (ANOTACION, "Anotación"),
    ]

    id_adjunto = models.AutoField(primary_key=True)
    tabla_origen = models.CharField(max_length=30, choices=OPCIONES_TABLA_ORIGEN)
    id_origen = models.PositiveIntegerField()
    archivo = models.FileField(upload_to="adjuntos/hallazgos/%Y/%m/", max_length=255)
    nombre_archivo = models.CharField(max_length=150)
    fecha_carga = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "adjunto"
        verbose_name = "adjunto"
        verbose_name_plural = "adjuntos"
        ordering = ["-fecha_carga"]
        indexes = [
            models.Index(fields=["tabla_origen", "id_origen"], name="idx_adjunto_origen"),
        ]

    def __str__(self):
        return self.nombre_archivo
