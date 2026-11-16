"""
Operaciones de escritura del módulo 8: equipo de trabajo, roles y permisos.

Reglas de los administradores (HU022-5):
- Siempre debe quedar al menos un Administrador activo.
- Tener más de un Administrador activo a la vez exige una confirmación
  explícita de quien hace el cambio.
"""

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

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


def dias_vigencia_enlace():
    """Días que dura un enlace de acceso antes de vencer (`PASSWORD_RESET_TIMEOUT`)."""
    return max(1, settings.PASSWORD_RESET_TIMEOUT // (60 * 60 * 24))


def enlace_acceso(usuario):
    """
    Enlace de un solo uso para que el usuario cree su contraseña.

    Usa el generador de Django: el enlace deja de servir en cuanto la
    contraseña cambia, y vence a los `PASSWORD_RESET_TIMEOUT` segundos.
    """
    ruta = reverse(
        "seguridad:crear_contrasena",
        kwargs={
            "uidb64": urlsafe_base64_encode(force_bytes(usuario.pk)),
            "token": default_token_generator.make_token(usuario),
        },
    )
    return f"{settings.URL_SITIO.rstrip('/')}{ruta}"


def enviar_enlace_acceso(usuario, nuevo=True):
    """
    Envía al usuario el enlace para crear su contraseña (HU022-3).

    La contraseña nunca viaja en el correo. Devuelve `(enviado, enlace)`: si
    el servidor de correo falla, el Administrador recibe el enlace en
    pantalla para entregarlo por otro medio.
    """
    enlace = enlace_acceso(usuario)
    contexto = {"usuario": usuario, "enlace": enlace, "nuevo": nuevo, "dias": dias_vigencia_enlace()}
    asunto = "Bienvenido a Contanika" if nuevo else "Contanika: enlace para crear su contraseña"
    cuerpo = render_to_string("seguridad/correos/acceso.txt", contexto)
    try:
        send_mail(asunto, cuerpo, None, [usuario.correo])
    except OSError:  # smtplib.SMTPException y los errores de conexión heredan de OSError
        return False, enlace
    return True, enlace


def crear_usuario(formulario, confirmado=False):
    """
    Crea el usuario sin contraseña utilizable y le envía el enlace para que la
    cree él mismo. Devuelve el usuario, si el correo salió y el enlace.
    """
    usuario = formulario.save(commit=False)
    validar_administradores(usuario, usuario.rol, Usuario.ACTIVO, confirmado)
    usuario.estado = Usuario.ACTIVO
    usuario.set_unusable_password()
    usuario.save()
    enviado, enlace = enviar_enlace_acceso(usuario, nuevo=True)
    return usuario, enviado, enlace


def actualizar_usuario(formulario, confirmado=False):
    """Guarda los datos, el correo y el rol del usuario. La contraseña no se toca aquí."""
    usuario = formulario.save(commit=False)
    validar_administradores(usuario, usuario.rol, usuario.estado, confirmado)
    usuario.save()
    return usuario


def reenviar_acceso(usuario):
    """
    Vuelve a enviar el enlace de acceso: sirve si el usuario perdió el correo,
    si el enlace venció o si olvidó su contraseña. La contraseña actual sigue
    sirviendo hasta que el usuario cree una nueva.
    """
    if usuario.estado != Usuario.ACTIVO:
        raise ErrorEquipo("El usuario está inactivo: actívelo antes de enviarle un enlace de acceso.")
    return enviar_enlace_acceso(usuario, nuevo=False)


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
