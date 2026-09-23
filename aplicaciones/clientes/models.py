"""
Modelos del módulo 1: gestión de clientes.

Incluye la ficha central del cliente, sus municipios adicionales, el catálogo
de tipos de servicio, la relación entre clientes y servicios y las
credenciales de acceso a portales que se guardan en el perfil del cliente.
"""

from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models
from django.utils import timezone

DIAS_AVISO_CREDENCIAL = 90


def _get_fernet():
    """Retorna una instancia de Fernet con la clave configurada."""
    clave = getattr(settings, "CREDENCIAL_CLAVE_CIFRADO", None)
    if not clave:
        raise ValueError("CREDENCIAL_CLAVE_CIFRADO no está configurada en settings")
    return Fernet(clave.encode() if isinstance(clave, str) else clave)


class Cliente(models.Model):
    """Ficha central de cada cliente del despacho."""

    NATURAL = "Natural"
    JURIDICA = "Jurídica"
    OPCIONES_TIPO_PERSONA = [(NATURAL, NATURAL), (JURIDICA, JURIDICA)]

    NIT = "NIT"
    CC = "CC"
    CE = "CE"
    TI = "TI"
    PASAPORTE = "Pasaporte"
    RUT = "RUT"
    OPCIONES_TIPO_DOCUMENTO = [
        (NIT, "NIT"),
        (CC, "Cédula de Ciudadanía"),
        (CE, "Cédula de Extranjería"),
        (TI, "Tarjeta de Identidad"),
        (PASAPORTE, "Pasaporte"),
        (RUT, "RUT"),
    ]

    ACTIVO = "Activo"
    INACTIVO = "Inactivo"
    OPCIONES_ESTADO = [(ACTIVO, ACTIVO), (INACTIVO, INACTIVO)]

    id_cliente = models.AutoField(primary_key=True)
    nombre_razon_social = models.CharField(max_length=200)
    nit_cedula = models.CharField(max_length=10)
    tipo_documento = models.CharField(
        max_length=15,
        choices=OPCIONES_TIPO_DOCUMENTO,
        default=NIT,
    )
    tipo_persona = models.CharField(max_length=10, choices=OPCIONES_TIPO_PERSONA)
    regimen_tributario = models.CharField(max_length=40, blank=True)
    responsable_iva = models.BooleanField(default=False)
    ciudad = models.CharField(max_length=60, blank=True)
    municipio_principal = models.CharField(max_length=60, blank=True)
    informacion_contacto = models.CharField(max_length=200, blank=True)
    correo_cliente = models.EmailField(max_length=200, blank=True)
    responsable = models.ForeignKey(
        "seguridad.Usuario",
        on_delete=models.PROTECT,
        db_column="id_usuario_responsable",
        related_name="clientes_asignados",
        null=True,
        blank=True,
    )
    estado = models.CharField(max_length=15, choices=OPCIONES_ESTADO, default=ACTIVO)
    fecha_registro = models.DateField(default=timezone.localdate)

    class Meta:
        db_table = "cliente"
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["nombre_razon_social"]
        indexes = [
            models.Index(fields=["nit_cedula"], name="idx_cliente_nit"),
            models.Index(fields=["estado"], name="idx_cliente_estado"),
        ]

    def __str__(self):
        return f"{self.nombre_razon_social} ({self.nit_cedula})"

    def inactivar(self):
        """
        Inactiva al cliente conservando todo su historial.

        No se elimina el registro: los módulos de calendario, documentos,
        finanzas y expediente siguen mostrando la trazabilidad del cliente.
        """
        self.estado = self.INACTIVO
        self.save(update_fields=["estado"])


class ClienteMunicipio(models.Model):
    """Municipio o distrito adicional donde el cliente presenta impuestos (multi-ICA)."""

    id_cliente_municipio = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        db_column="id_cliente",
        related_name="municipios_adicionales",
    )
    municipio = models.CharField(max_length=60)

    class Meta:
        db_table = "cliente_municipio"
        verbose_name = "municipio adicional del cliente"
        verbose_name_plural = "municipios adicionales del cliente"
        ordering = ["municipio"]

    def __str__(self):
        return f"{self.municipio} ({self.cliente.nombre_razon_social})"


class TipoServicio(models.Model):
    """Catálogo de tipos de servicio contable prestado."""

    id_tipo_servicio = models.AutoField(primary_key=True)
    nombre_servicio = models.CharField(max_length=80, unique=True)

    class Meta:
        db_table = "tipo_servicio"
        verbose_name = "tipo de servicio"
        verbose_name_plural = "tipos de servicio"
        ordering = ["nombre_servicio"]

    def __str__(self):
        return self.nombre_servicio


class ClienteServicio(models.Model):
    """Relación entre un cliente y los tipos de servicio contable que recibe."""

    id_cliente_servicio = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        db_column="id_cliente",
        related_name="servicios",
    )
    tipo_servicio = models.ForeignKey(
        TipoServicio,
        on_delete=models.PROTECT,
        db_column="id_tipo_servicio",
        related_name="clientes",
    )

    class Meta:
        db_table = "cliente_servicio"
        verbose_name = "servicio del cliente"
        verbose_name_plural = "servicios del cliente"
        constraints = [
            models.UniqueConstraint(fields=["cliente", "tipo_servicio"], name="unico_cliente_servicio"),
        ]

    def __str__(self):
        return f"{self.cliente.nombre_razon_social} - {self.tipo_servicio.nombre_servicio}"


class Credencial(models.Model):
    """
    Credencial de acceso a un portal del cliente (DIAN, Hacienda, etc.).

    La clave se guarda cifrada en `clave_cifrada` y se muestra enmascarada en
    pantalla. Las fechas de creación y actualización son automáticas.
    """

    id_credencial = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        db_column="id_cliente",
        related_name="credenciales",
    )
    concepto = models.CharField(max_length=60)
    usuario_acceso = models.CharField(max_length=100)
    clave_cifrada = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "credencial"
        verbose_name = "credencial de acceso"
        verbose_name_plural = "credenciales de acceso"
        ordering = ["concepto"]

    def __str__(self):
        return f"{self.concepto} - {self.cliente.nombre_razon_social}"

    @property
    def dias_sin_actualizacion(self):
        """Días transcurridos desde la última actualización de la credencial."""
        return (timezone.now() - self.fecha_ultima_actualizacion).days

    @property
    def requiere_actualizacion(self):
        """Indica si la credencial lleva más de 90 días sin actualizarse."""
        return self.dias_sin_actualizacion > DIAS_AVISO_CREDENCIAL

    def establecer_clave(self, clave_plana: str) -> None:
        """
        Cifra y guarda la clave plana en `clave_cifrada`.

        Args:
            clave_plana: Contraseña en texto plano a cifrar.
        """
        fernet = _get_fernet()
        self.clave_cifrada = fernet.encrypt(clave_plana.encode()).decode()

    def obtener_clave(self) -> str:
        """
        Descifra y retorna la clave en texto plano.

        Returns:
            Contraseña descifrada.

        Raises:
            ValueError: Si la clave no se puede descifrar.
        """
        fernet = _get_fernet()
        return fernet.decrypt(self.clave_cifrada.encode()).decode()

    @property
    def clave_plana(self) -> str:
        """
        Propiedad de solo lectura para acceder a la clave descifrada.

        Útil en templates y serializadores donde se necesita la clave
        temporalmente (ej. mostrar/ocultar en UI).

        Returns:
            Contraseña en texto plano.
        """
        return self.obtener_clave()
