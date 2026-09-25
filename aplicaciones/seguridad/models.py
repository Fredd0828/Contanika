"""
Modelos del módulo 8: equipo de trabajo, roles y configuración del despacho.

Aquí viven las tablas rol, usuario, modulo, permiso_rol_modulo y
configuracion_despacho, que son la base de la autenticación y de la
visibilidad configurable de módulos por rol (RQF031).
"""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class Rol(models.Model):
    """Rol del sistema: Administrador, Contador Senior o Contador Junior."""

    ADMINISTRADOR = "Administrador"
    CONTADOR_SENIOR = "Contador Senior"
    CONTADOR_JUNIOR = "Contador Junior"

    OPCIONES_ROL = [
        (ADMINISTRADOR, ADMINISTRADOR),
        (CONTADOR_SENIOR, CONTADOR_SENIOR),
        (CONTADOR_JUNIOR, CONTADOR_JUNIOR),
    ]

    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=30, unique=True, choices=OPCIONES_ROL)

    class Meta:
        db_table = "rol"
        verbose_name = "rol"
        verbose_name_plural = "roles"
        ordering = ["id_rol"]

    def __str__(self):
        return self.nombre_rol


class Modulo(models.Model):
    """
    Catálogo de los diez módulos funcionales del sistema.

    El código MOD01…MOD10 se usa en el menú, en los mixins de acceso y en la
    tabla permiso_rol_modulo para habilitar o inhabilitar módulos por rol.
    """

    MOD01_CLIENTES = "MOD01"
    MOD02_CALENDARIO = "MOD02"
    MOD03_TAREAS = "MOD03"
    MOD04_DOCUMENTOS = "MOD04"
    MOD05_HALLAZGOS = "MOD05"
    MOD06_FINANZAS = "MOD06"
    MOD07_COMUNICACIONES = "MOD07"
    MOD08_EQUIPO = "MOD08"
    MOD09_EXPEDIENTE = "MOD09"
    MOD10_REPORTES = "MOD10"

    OPCIONES_CODIGO = [
        (MOD01_CLIENTES, "Gestión de clientes"),
        (MOD02_CALENDARIO, "Calendario"),
        (MOD03_TAREAS, "Tablero de tareas Kanban"),
        (MOD04_DOCUMENTOS, "Expedición de documentos y certificados"),
        (MOD05_HALLAZGOS, "Hallazgos y revisiones"),
        (MOD06_FINANZAS, "Honorarios, cartera y cuentas de cobro"),
        (MOD07_COMUNICACIONES, "Comunicaciones integradas"),
        (MOD08_EQUIPO, "Gestión de equipo y roles"),
        (MOD09_EXPEDIENTE, "Expediente y bitácora por cliente"),
        (MOD10_REPORTES, "Reportes y análisis"),
    ]

    id_modulo = models.AutoField(primary_key=True)
    nombre_modulo = models.CharField(max_length=60)
    codigo_modulo = models.CharField(max_length=20, unique=True, choices=OPCIONES_CODIGO)

    class Meta:
        db_table = "modulo"
        verbose_name = "módulo"
        verbose_name_plural = "módulos"
        ordering = ["id_modulo"]

    def __str__(self):
        return f"{self.codigo_modulo} - {self.nombre_modulo}"


class UsuarioManager(BaseUserManager):
    """Administrador del modelo de usuario basado en correo electrónico."""

    use_in_migrations = True

    def create_user(self, correo, nombre, password=None, **extra):
        """Crea un usuario normal con la contraseña cifrada."""
        if not correo:
            raise ValueError("El correo electrónico es obligatorio.")
        correo = self.normalize_email(correo)
        usuario = self.model(correo=correo, nombre=nombre, **extra)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, correo, nombre, password=None, **extra):
        """Crea un superusuario y le asigna el rol Administrador por defecto."""
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("estado", Usuario.ACTIVO)
        if extra.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")
        if "rol" not in extra:
            extra["rol"], _ = Rol.objects.get_or_create(nombre_rol=Rol.ADMINISTRADOR)
        return self.create_user(correo, nombre, password, **extra)


class Usuario(AbstractBaseUser):
    """
    Miembro del equipo del despacho (o el contador independiente).

    Se apoya en django.contrib.auth para el inicio de sesión, el hash de la
    contraseña y las sesiones (RQNF004). El rol del despacho se guarda en la
    tabla rol y los permisos se validan con permiso_rol_modulo.
    """

    ACTIVO = "Activo"
    INACTIVO = "Inactivo"
    OPCIONES_ESTADO = [(ACTIVO, ACTIVO), (INACTIVO, INACTIVO)]

    id_usuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    correo = models.EmailField(max_length=150, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    foto_url = models.URLField(max_length=255, blank=True)
    password = models.CharField(max_length=255, db_column="password_hash")
    firma = models.ImageField(upload_to="firmas/", blank=True)
    identificacion = models.CharField(max_length=20, blank=True)
    numero_tarjeta_profesional = models.CharField(max_length=30, blank=True)
    rol = models.ForeignKey(
        Rol,
        on_delete=models.PROTECT,
        db_column="id_rol",
        related_name="usuarios",
    )
    estado = models.CharField(max_length=15, choices=OPCIONES_ESTADO, default=ACTIVO)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # Campos estándar de Django que no aparecen en el diccionario de datos:
    # habilitan el acceso al panel de administración del framework.
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = "correo"
    REQUIRED_FIELDS = ["nombre"]
    EMAIL_FIELD = "correo"

    class Meta:
        db_table = "usuario"
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.rol.nombre_rol})"

    # -----------------------------------------------------------
    # Compatibilidad con django.contrib.auth
    # -----------------------------------------------------------
    @property
    def is_active(self):
        """Indica si el usuario está activo; Django lo consulta al autenticar."""
        return self.estado == self.ACTIVO

    @is_active.setter
    def is_active(self, valor):
        self.estado = self.ACTIVO if valor else self.INACTIVO

    def has_perm(self, perm, obj=None):
        """Permisos del panel de administración: solo el superusuario."""
        return self.is_superuser

    def has_module_perms(self, app_label):
        """Permisos por aplicación del panel de administración."""
        return self.is_superuser

    # -----------------------------------------------------------
    # Reglas de negocio del despacho
    # -----------------------------------------------------------
    @property
    def es_administrador(self):
        return self.rol.nombre_rol == Rol.ADMINISTRADOR

    @property
    def es_contador_senior(self):
        return self.rol.nombre_rol == Rol.CONTADOR_SENIOR

    @property
    def es_contador_junior(self):
        return self.rol.nombre_rol == Rol.CONTADOR_JUNIOR

    def tiene_modulo_habilitado(self, codigo_modulo):
        """
        Consulta si el rol del usuario tiene habilitado un módulo (RQF031).

        Si no existe una fila de configuración se asume habilitado, de modo
        que un módulo nuevo quede visible hasta que el Administrador decida
        inhabilitarlo para algún rol. El resultado se guarda en caché por
        instancia para no repetir la consulta en cada petición.
        """
        if self.is_superuser:
            return True
        if not hasattr(self, "_cache_modulos_habilitados"):
            self._cache_modulos_habilitados = {
                permiso.modulo.codigo_modulo: permiso.habilitado
                for permiso in PermisoRolModulo.objects.filter(rol=self.rol).select_related("modulo")
            }
        return self._cache_modulos_habilitados.get(codigo_modulo, True)

    def puede_ver_reporte(self, nombre_reporte):
        """Consulta si el rol del usuario tiene habilitado un reporte individual."""
        from aplicaciones.reportes.models import PermisoReporteRol

        if self.is_superuser:
            return True
        if not hasattr(self, "_cache_reportes_habilitados"):
            self._cache_reportes_habilitados = {
                permiso.reporte.nombre_reporte: permiso.habilitado
                for permiso in PermisoReporteRol.objects.filter(rol=self.rol).select_related("reporte")
            }
        return self._cache_reportes_habilitados.get(nombre_reporte, True)


class PermisoRolModulo(models.Model):
    """Habilitación de cada módulo por rol, configurable por el Administrador."""

    id_permiso = models.AutoField(primary_key=True)
    rol = models.ForeignKey(
        Rol,
        on_delete=models.CASCADE,
        db_column="id_rol",
        related_name="permisos_modulo",
    )
    modulo = models.ForeignKey(
        Modulo,
        on_delete=models.CASCADE,
        db_column="id_modulo",
        related_name="permisos_rol",
    )
    habilitado = models.BooleanField(default=True)

    class Meta:
        db_table = "permiso_rol_modulo"
        verbose_name = "permiso de módulo por rol"
        verbose_name_plural = "permisos de módulos por rol"
        constraints = [
            models.UniqueConstraint(fields=["rol", "modulo"], name="unico_rol_modulo"),
        ]

    def __str__(self):
        return f"{self.rol.nombre_rol} - {self.modulo.codigo_modulo}: {self.habilitado}"


class ConfiguracionDespacho(models.Model):
    """Datos fijos del despacho que se imprimen en documentos y cuentas de cobro."""

    id_configuracion = models.AutoField(primary_key=True)
    nombre_despacho = models.CharField(max_length=150, default="Befrec Y Asociados SAS")
    nit_despacho = models.CharField(max_length=20, blank=True)
    membrete_url = models.URLField(max_length=255, blank=True)
    ciudad = models.CharField(max_length=60, blank=True)
    direccion = models.CharField(max_length=150, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    correo = models.EmailField(max_length=100, blank=True)

    class Meta:
        db_table = "configuracion_despacho"
        verbose_name = "configuración del despacho"
        verbose_name_plural = "configuración del despacho"

    def __str__(self):
        return self.nombre_despacho
