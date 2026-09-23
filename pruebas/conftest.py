"""Fixtures compartidas por todas las pruebas del sistema Contanika."""

import pytest
from django.contrib.auth import get_user_model

from aplicaciones.clientes.models import Cliente
from aplicaciones.seguridad.models import Modulo, Rol

Usuario = get_user_model()

CLAVE_PRUEBAS = "ClaveSegura123"
CLAVE_CIFRADO_PRUEBAS = "tl0BjzeE61CqzeDjKd8FH6Qs8ayUmd4AumYKFngCh8o="


@pytest.fixture(autouse=True)
def configurar_clave_cifrado(settings):
    """Fija la clave de cifrado de credenciales para que las pruebas no dependan del .env."""
    settings.CREDENCIAL_CLAVE_CIFRADO = CLAVE_CIFRADO_PRUEBAS


@pytest.fixture
def rol_administrador(db):
    return Rol.objects.create(nombre_rol=Rol.ADMINISTRADOR)


@pytest.fixture
def rol_senior(db):
    return Rol.objects.create(nombre_rol=Rol.CONTADOR_SENIOR)


@pytest.fixture
def rol_junior(db):
    return Rol.objects.create(nombre_rol=Rol.CONTADOR_JUNIOR)


@pytest.fixture
def usuario_administrador(rol_administrador):
    return Usuario.objects.create_user(
        correo="paula@befrec.co",
        nombre="Paula Andrea Blanco",
        password=CLAVE_PRUEBAS,
        rol=rol_administrador,
    )


@pytest.fixture
def usuario_senior(rol_senior):
    return Usuario.objects.create_user(
        correo="senior@befrec.co",
        nombre="Contador Senior",
        password=CLAVE_PRUEBAS,
        rol=rol_senior,
    )


@pytest.fixture
def usuario_junior(rol_junior):
    return Usuario.objects.create_user(
        correo="junior@befrec.co",
        nombre="Contador Junior",
        password=CLAVE_PRUEBAS,
        rol=rol_junior,
    )


@pytest.fixture
def modulo_clientes(db):
    return Modulo.objects.create(
        codigo_modulo=Modulo.MOD01_CLIENTES,
        nombre_modulo="Gestión de clientes",
    )


@pytest.fixture
def modulo_tareas(db):
    return Modulo.objects.create(
        codigo_modulo=Modulo.MOD03_TAREAS,
        nombre_modulo="Tablero de tareas Kanban",
    )


@pytest.fixture
def cliente(usuario_administrador):
    return Cliente.objects.create(
        nombre_razon_social="Comercializadora La Rebaja SAS",
        nit_cedula="900123456",
        tipo_documento=Cliente.NIT,
        tipo_persona=Cliente.JURIDICA,
        regimen_tributario="Régimen ordinario",
        ciudad="Bogotá D.C.",
        municipio_principal="Bogotá D.C.",
        informacion_contacto="3101234567",
        correo_cliente="gerencia@larebaja.co",
        responsable=usuario_administrador,
    )
