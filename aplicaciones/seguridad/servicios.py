"""
Operaciones de escritura del módulo 8: equipo de trabajo, roles y permisos.

Reglas de los administradores (HU022-5):
- Siempre debe quedar al menos un Administrador activo.
- Tener más de un Administrador activo a la vez exige una confirmación
  explícita de quien hace el cambio.
"""

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string

from .models import Modulo, PermisoRolModulo, Rol, Usuario


class ErrorEquipo(Exception):
    """Operación sobre el equipo que viola una regla de negocio."""


class ConfirmacionRequerida(ErrorEquipo):
    """El cambio es válido, pero deja más de un Administrador activo y debe confirmarse."""


def administradores_activos(excluir=None):
    consulta = Usuario.objects.filter(rol__nombre_rol=Rol.ADMINISTRADOR, estado=Usuario.ACTIVO)
    if excluir is not None and excluir.pk:
        consulta = consulta.exclude(pk=excluir.pk)
    return consulta


def validar_administradores(usuario, rol, estado, confirmado=False):
    """
    Revisa cómo queda el grupo de administradores activos si `usuario`
    pasa a tener `rol` y `estado`.
    """
    otros = administradores_activos(excluir=usuario)
    sera_admin_activo = rol.nombre_rol == Rol.ADMINISTRADOR and estado == Usuario.ACTIVO
    if not sera_admin_activo and not otros.exists():
        raise ErrorEquipo("Debe quedar al menos un Administrador activo en el sistema.")
    if sera_admin_activo and otros.exists() and not confirmado:
        nombres = ", ".join(otros.values_list("nombre", flat=True))
        raise ConfirmacionRequerida(
            f"Ya hay un Administrador activo ({nombres}). Confirme que desea tener más de un Administrador."
        )


def enviar_correo_acceso(usuario, clave, nuevo=True):
    """
    Envía al usuario su correo de acceso y la contraseña temporal (HU022-3).

    Devuelve False si el servidor de correo rechaza el envío: el usuario ya
    quedó guardado y el Administrador puede entregarle los datos de otra forma.
    """
    contexto = {
        "usuario": usuario,
        "clave": clave,
        "nuevo": nuevo,
        "url_sitio": getattr(settings, "URL_SITIO", ""),
    }
    asunto = "Bienvenido a Contanika" if nuevo else "Contanika: nueva contraseña temporal"
    cuerpo = render_to_string("seguridad/correos/acceso.txt", contexto)
    try:
        send_mail(asunto, cuerpo, None, [usuario.correo])
    except OSError:  # smtplib.SMTPException y los errores de conexión heredan de OSError
        return False
    return True


def crear_usuario(formulario, confirmado=False):
    """
    Crea el usuario con su contraseña temporal y le envía sus datos de acceso.
    Devuelve el usuario y si el correo se pudo enviar.
    """
    usuario = formulario.save(commit=False)
    validar_administradores(usuario, usuario.rol, Usuario.ACTIVO, confirmado)
    clave = formulario.cleaned_data["clave_temporal"]
    usuario.estado = Usuario.ACTIVO
    usuario.set_password(clave)
    usuario.save()
    return usuario, enviar_correo_acceso(usuario, clave, nuevo=True)


def actualizar_usuario(formulario, confirmado=False):
    """
    Guarda los datos del usuario. Si se indicó una contraseña temporal nueva,
    la asigna y se la envía. Devuelve el usuario y si el correo se envió
    (None cuando no hubo cambio de contraseña).
    """
    usuario = formulario.save(commit=False)
    validar_administradores(usuario, usuario.rol, usuario.estado, confirmado)
    clave = formulario.cleaned_data.get("clave_temporal")
    if clave:
        usuario.set_password(clave)
    usuario.save()
    correo_enviado = enviar_correo_acceso(usuario, clave, nuevo=False) if clave else None
    return usuario, correo_enviado


def cambiar_estado_usuario(usuario, estado, actor, confirmado=False):
    """Activa o inactiva un usuario; un usuario inactivo no puede iniciar sesión."""
    if usuario.pk == actor.pk and estado == Usuario.INACTIVO:
        raise ErrorEquipo("No puede inactivar su propio usuario.")
    validar_administradores(usuario, usuario.rol, estado, confirmado)
    usuario.estado = estado
    usuario.save(update_fields=["estado"])
    return usuario


def tiene_historial(usuario):
    """
    Indica si el usuario aparece en algún registro del sistema (tareas,
    anotaciones, abonos, comunicaciones, clientes asignados, etc.).
    """
    for relacion in Usuario._meta.related_objects:
        if not (relacion.one_to_many or relacion.one_to_one):
            continue
        filtro = {relacion.field.name: usuario}
        if relacion.related_model._default_manager.filter(**filtro).exists():
            return True
    return False


@transaction.atomic
def eliminar_usuario(usuario, actor):
    """
    Elimina un usuario sin historial (p. ej. creado por error). Si ya tiene
    registros asociados se debe inactivar, para conservar la trazabilidad.
    """
    if usuario.pk == actor.pk:
        raise ErrorEquipo("No puede eliminar su propio usuario.")
    if tiene_historial(usuario):
        raise ErrorEquipo(
            f"{usuario.nombre} tiene registros en el sistema y no se puede eliminar sin perder la "
            "trazabilidad. Inactívelo: no podrá iniciar sesión y se conserva su historial."
        )
    validar_administradores(usuario, usuario.rol, Usuario.INACTIVO)
    if usuario.firma:
        usuario.firma.delete(save=False)
    if usuario.foto:
        usuario.foto.delete(save=False)
    usuario.delete()


# El Administrador siempre conserva el módulo de equipo: si lo inhabilitara
# para su propio rol no podría volver a habilitar nada.
PERMISOS_FIJOS = {(Rol.ADMINISTRADOR, Modulo.MOD08_EQUIPO)}


def es_permiso_fijo(rol, modulo):
    return (rol.nombre_rol, modulo.codigo_modulo) in PERMISOS_FIJOS


@transaction.atomic
def guardar_permisos_modulos(habilitados):
    """
    Guarda la matriz módulo × rol (HU050). `habilitados` es el conjunto de
    pares (id_rol, id_modulo) marcados; los demás quedan inhabilitados. Los
    datos de un módulo inhabilitado se conservan, solo se oculta el acceso.
    """
    for rol in Rol.objects.all():
        for modulo in Modulo.objects.all():
            habilitado = es_permiso_fijo(rol, modulo) or (rol.pk, modulo.pk) in habilitados
            PermisoRolModulo.objects.update_or_create(
                rol=rol, modulo=modulo, defaults={"habilitado": habilitado}
            )


def actualizar_perfil(formulario):
    """Guarda los datos del perfil propio (HU024)."""
    return formulario.save()
