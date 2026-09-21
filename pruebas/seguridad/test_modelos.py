"""Pruebas de los modelos de seguridad: usuario, roles y permisos."""

import pytest
from django.contrib.auth import get_user_model

from aplicaciones.seguridad.models import Modulo, PermisoRolModulo, Rol

from ..conftest import CLAVE_PRUEBAS

Usuario = get_user_model()

pytestmark = pytest.mark.django_db


def test_contrasena_se_guarda_cifrada(usuario_administrador):
    """La contraseña nunca se almacena en texto plano (RQNF004)."""
    assert usuario_administrador.password != CLAVE_PRUEBAS
    assert usuario_administrador.check_password(CLAVE_PRUEBAS)


def test_is_active_refleja_el_estado_colombiano(usuario_administrador):
    """El estado Activo/Inactivo del diccionario se refleja en is_active."""
    assert usuario_administrador.is_active is True
    usuario_administrador.estado = Usuario.INACTIVO
    usuario_administrador.save(update_fields=["estado"])
    assert usuario_administrador.is_active is False


def test_superusuario_recibe_rol_administrador(rol_administrador):
    """create_superuser asigna el rol Administrador automáticamente."""
    superusuario = Usuario.objects.create_superuser(
        correo="jefe@contanika.co",
        nombre="Jefe del despacho",
        password=CLAVE_PRUEBAS,
    )
    assert superusuario.rol.nombre_rol == Rol.ADMINISTRADOR
    assert superusuario.is_staff is True
    assert superusuario.is_superuser is True


def test_modulo_habilitado_por_defecto(usuario_junior, modulo_clientes):
    """Sin fila de configuración, el módulo se considera habilitado."""
    assert usuario_junior.tiene_modulo_habilitado(Modulo.MOD01_CLIENTES) is True


def test_modulo_inhabilitado_bloquea_al_rol(usuario_junior, modulo_clientes):
    """El Administrador puede inhabilitar un módulo para un rol (RQF031)."""
    PermisoRolModulo.objects.create(rol=usuario_junior.rol, modulo=modulo_clientes, habilitado=False)
    assert usuario_junior.tiene_modulo_habilitado(Modulo.MOD01_CLIENTES) is False


def test_superusuario_siempre_tiene_acceso(rol_junior, modulo_clientes):
    """El superusuario conserva acceso aunque el módulo esté inhabilitado."""
    superusuario = Usuario.objects.create_superuser(
        correo="root@contanika.co",
        nombre="Superusuario",
        password=CLAVE_PRUEBAS,
        rol=rol_junior,
    )
    PermisoRolModulo.objects.create(rol=rol_junior, modulo=modulo_clientes, habilitado=False)
    assert superusuario.tiene_modulo_habilitado(Modulo.MOD01_CLIENTES) is True
