"""Fixtures compartidas por todas las pruebas del sistema Contanika."""

import pytest
from django.contrib.auth import get_user_model

from aplicaciones.clientes.models import Cliente, ClienteObligacion, ObligacionTributaria
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
def modulo_documentos(db):
    return Modulo.objects.create(
        codigo_modulo=Modulo.MOD04_DOCUMENTOS,
        nombre_modulo="Expedición de documentos y certificados",
    )


@pytest.fixture
def modulo_hallazgos(db):
    return Modulo.objects.create(
        codigo_modulo=Modulo.MOD05_HALLAZGOS,
        nombre_modulo="Hallazgos y revisiones",
    )


@pytest.fixture
def modulo_finanzas(db):
    return Modulo.objects.create(
        codigo_modulo=Modulo.MOD06_FINANZAS,
        nombre_modulo="Honorarios, cartera y cuentas de cobro",
    )


def _asignar_obligaciones(cliente, *nombres):
    """Marca en el cliente las obligaciones tributarias indicadas por nombre."""
    for nombre in nombres:
        obligacion, _ = ObligacionTributaria.objects.get_or_create(nombre=nombre)
        ClienteObligacion.objects.get_or_create(cliente=cliente, obligacion_tributaria=obligacion)
    return cliente


@pytest.fixture
def cliente(usuario_administrador):
    cliente = Cliente.objects.create(
        nombre_razon_social="Comercializadora La Rebaja SAS",
        nit_cedula="900123456",
        tipo_documento=Cliente.NIT,
        tipo_persona=Cliente.JURIDICA,
        regimen_tributario="Régimen ordinario",
        responsable_iva=True,
        ciudad="Bogotá D.C.",
        municipio_principal="Bogotá D.C.",
        informacion_contacto="3101234567",
        correo_cliente="gerencia@larebaja.co",
        responsable=usuario_administrador,
    )
    return _asignar_obligaciones(
        cliente, "Renta personas jurídicas", "Retención en la fuente", "IVA bimestral"
    )


@pytest.fixture
def cliente_natural(usuario_administrador):
    """Persona natural con cédula: el grupo DIAN usa los dos últimos dígitos."""
    cliente = Cliente.objects.create(
        nombre_razon_social="Juan Pablo Méndez",
        nit_cedula="1032456789",
        tipo_documento=Cliente.CC,
        tipo_persona=Cliente.NATURAL,
        regimen_tributario="Régimen ordinario",
        responsable_iva=False,
        responsable=usuario_administrador,
    )
    return _asignar_obligaciones(cliente, "Renta personas naturales")


@pytest.fixture
def cliente_extranjero(usuario_administrador):
    """Cliente con documento extranjero: no tiene grupo DIAN calculable."""
    return Cliente.objects.create(
        nombre_razon_social="Global Trading LLC",
        nit_cedula="E987654",
        tipo_documento=Cliente.PASAPORTE,
        tipo_persona=Cliente.JURIDICA,
        regimen_tributario="Régimen ordinario",
        responsable=usuario_administrador,
    )


@pytest.fixture
def cliente_junior(usuario_junior):
    """Cliente asignado al Contador Junior (el único que puede consultar)."""
    return Cliente.objects.create(
        nombre_razon_social="Papelería El Lápiz",
        nit_cedula="901555777",
        tipo_documento=Cliente.NIT,
        tipo_persona=Cliente.JURIDICA,
        regimen_tributario="Régimen ordinario",
        responsable=usuario_junior,
    )


@pytest.fixture
def modulo_calendario(db):
    return Modulo.objects.create(
        codigo_modulo=Modulo.MOD02_CALENDARIO,
        nombre_modulo="Calendario",
    )


@pytest.fixture
def referencia_dian(db):
    """Fila de la tabla DIAN para probar el cálculo de vencimientos."""
    from datetime import date

    from aplicaciones.calendario.models import TablaReferenciaDian

    return TablaReferenciaDian.objects.create(
        tipo_obligacion="IVA bimestral",
        grupo_nit="6",
        fecha_vencimiento=date(2026, 3, 17),
        periodo_gravable="2026-01",
    )
