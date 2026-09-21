"""
Modelos del módulo 3: tablero de tareas Kanban.

Cada tarjeta del tablero es una tarea asignada a un cliente y a un
responsable; los cambios de estado y las observaciones de avance quedan
registrados para conservar la trazabilidad del trabajo del despacho.
"""

from django.db import models


class Tarea(models.Model):
    """
    Tarjeta del tablero Kanban.

    El campo `mostrar_en_calendario` permite que la fecha de vencimiento de la
    tarea aparezca también en el módulo de calendario con las mismas alertas.
    """

    POR_HACER = "Por hacer"
    EN_PROGRESO = "En progreso"
    EN_REVISION = "En revisión"
    TERMINADO = "Terminado"
    OPCIONES_ESTADO = [
        (POR_HACER, POR_HACER),
        (EN_PROGRESO, EN_PROGRESO),
        (EN_REVISION, EN_REVISION),
        (TERMINADO, TERMINADO),
    ]

    ALTA = "Alta"
    MEDIA = "Media"
    BAJA = "Baja"
    OPCIONES_PRIORIDAD = [(ALTA, ALTA), (MEDIA, MEDIA), (BAJA, BAJA)]

    id_tarea = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        db_column="id_cliente",
        related_name="tareas",
    )
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    tipo_tarea = models.CharField(max_length=40, blank=True)
    responsable = models.ForeignKey(
        "seguridad.Usuario",
        on_delete=models.PROTECT,
        db_column="id_usuario_responsable",
        related_name="tareas_asignadas",
        null=True,
        blank=True,
    )
    prioridad = models.CharField(max_length=10, choices=OPCIONES_PRIORIDAD, default=MEDIA)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=OPCIONES_ESTADO, default=POR_HACER)
    mostrar_en_calendario = models.BooleanField(default=False)

    class Meta:
        db_table = "tarea"
        verbose_name = "tarea"
        verbose_name_plural = "tareas"
        ordering = ["-fecha_vencimiento", "prioridad"]
        indexes = [
            models.Index(fields=["estado"], name="idx_tarea_estado"),
            models.Index(fields=["cliente", "estado"], name="idx_tarea_cliente"),
        ]

    def __str__(self):
        return f"{self.titulo} ({self.estado})"

    def cambiar_estado(self, nuevo_estado, usuario):
        """
        Cambia el estado de la tarea y guarda el rastro del cambio.

        Devuelve el registro de historial creado. Si el estado no cambia,
        no se genera historial y devuelve None.
        """
        if nuevo_estado == self.estado:
            return None
        estado_anterior = self.estado
        self.estado = nuevo_estado
        self.save(update_fields=["estado"])
        return HistorialTarea.objects.create(
            tarea=self,
            usuario=usuario,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
        )


class HistorialTarea(models.Model):
    """Registro de cada cambio de estado de una tarea, con usuario y fecha."""

    id_historial = models.AutoField(primary_key=True)
    tarea = models.ForeignKey(
        Tarea,
        on_delete=models.CASCADE,
        db_column="id_tarea",
        related_name="historial",
    )
    usuario = models.ForeignKey(
        "seguridad.Usuario",
        on_delete=models.PROTECT,
        db_column="id_usuario",
        related_name="cambios_tarea",
    )
    estado_anterior = models.CharField(max_length=20, choices=Tarea.OPCIONES_ESTADO)
    estado_nuevo = models.CharField(max_length=20, choices=Tarea.OPCIONES_ESTADO)
    fecha_cambio = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "historial_tarea"
        verbose_name = "historial de tarea"
        verbose_name_plural = "historiales de tareas"
        ordering = ["-fecha_cambio"]

    def __str__(self):
        return f"{self.tarea.titulo}: {self.estado_anterior} → {self.estado_nuevo}"


class ObservacionTarea(models.Model):
    """Observación de avance registrada por un usuario sobre una tarea."""

    id_observacion = models.AutoField(primary_key=True)
    tarea = models.ForeignKey(
        Tarea,
        on_delete=models.CASCADE,
        db_column="id_tarea",
        related_name="observaciones",
    )
    usuario = models.ForeignKey(
        "seguridad.Usuario",
        on_delete=models.PROTECT,
        db_column="id_usuario",
        related_name="observaciones_tarea",
    )
    contenido = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "observacion_tarea"
        verbose_name = "observación de tarea"
        verbose_name_plural = "observaciones de tareas"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Observación de {self.usuario.nombre} en {self.tarea.titulo}"
