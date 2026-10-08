"""Pruebas de los formularios del módulo 2: validaciones de entrada."""

from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from aplicaciones.calendario.formularios import (
    AnotacionCalendarioForm,
    ConfiguracionAlertaForm,
    ImportarDianForm,
    TablaReferenciaDianForm,
    VencimientoManualForm,
)
from aplicaciones.calendario.models import (
    AnotacionCalendario,
    TablaReferenciaDian,
    Vencimiento,
)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# TablaReferenciaDianForm
# ---------------------------------------------------------------------------


def test_referencia_dian_rechaza_duplicados():
    """No se puede repetir obligación + grupo + período."""
    TablaReferenciaDian.objects.create(
        tipo_obligacion="IVA bimestral",
        grupo_nit="1",
        fecha_vencimiento=date(2026, 3, 10),
        periodo_gravable="2026-01",
    )
    formulario = TablaReferenciaDianForm(
        data={
            "tipo_obligacion": "IVA bimestral",
            "grupo_nit": "1",
            "fecha_vencimiento": "2026-03-11",
            "periodo_gravable": "2026-01",
        }
    )
    assert not formulario.is_valid()
    assert "Ya existe una referencia" in str(formulario.errors)


def test_referencia_dian_acepta_misma_obligacion_otro_grupo():
    """La misma obligación con otro grupo sí es válida."""
    TablaReferenciaDian.objects.create(
        tipo_obligacion="IVA bimestral",
        grupo_nit="1",
        fecha_vencimiento=date(2026, 3, 10),
        periodo_gravable="2026-01",
    )
    formulario = TablaReferenciaDianForm(
        data={
            "tipo_obligacion": "IVA bimestral",
            "grupo_nit": "2",
            "fecha_vencimiento": "2026-03-11",
            "periodo_gravable": "2026-01",
        }
    )
    assert formulario.is_valid(), formulario.errors


# ---------------------------------------------------------------------------
# VencimientoManualForm
# ---------------------------------------------------------------------------


def test_vencimiento_distrital_exige_municipio(cliente, usuario_administrador):
    """Un vencimiento distrital o municipal sin municipio no es válido."""
    formulario = VencimientoManualForm(
        data={
            "cliente": cliente.pk,
            "tipo_obligacion": "ICA",
            "ambito": Vencimiento.MUNICIPAL,
            "municipio": "",
            "fecha_vencimiento": "2026-05-15",
            "estado_presentacion": Vencimiento.PENDIENTE,
        },
        usuario=usuario_administrador,
    )
    assert not formulario.is_valid()
    assert "municipio" in formulario.errors


def test_vencimiento_nacional_no_exige_municipio(cliente, usuario_administrador):
    """Un vencimiento nacional no necesita municipio."""
    formulario = VencimientoManualForm(
        data={
            "cliente": cliente.pk,
            "tipo_obligacion": "IVA bimestral",
            "ambito": Vencimiento.NACIONAL,
            "municipio": "",
            "fecha_vencimiento": "2026-05-15",
            "estado_presentacion": Vencimiento.PENDIENTE,
        },
        usuario=usuario_administrador,
    )
    assert formulario.is_valid(), formulario.errors


def test_formulario_junior_solo_lista_sus_clientes(cliente, cliente_junior, usuario_junior):
    """El select de clientes del Junior solo muestra sus clientes asignados."""
    formulario = VencimientoManualForm(usuario=usuario_junior)
    clientes = formulario.fields["cliente"].queryset
    assert cliente_junior in clientes
    assert cliente not in clientes


# ---------------------------------------------------------------------------
# ConfiguracionAlertaForm
# ---------------------------------------------------------------------------


def test_alerta_rechaza_anticipacion_mayor_a_60():
    """La anticipación de una alerta no puede superar 60 días."""
    formulario = ConfiguracionAlertaForm(data={"dias_anticipacion": 61, "canal": "Correo"})
    assert not formulario.is_valid()
    assert "dias_anticipacion" in formulario.errors


# ---------------------------------------------------------------------------
# AnotacionCalendarioForm
# ---------------------------------------------------------------------------


def test_anotacion_por_etiqueta_exige_destinatarios():
    """La visibilidad por etiqueta necesita al menos un destinatario."""
    formulario = AnotacionCalendarioForm(
        data={
            "fecha": "2026-10-05",
            "contenido": "Reunión",
            "visibilidad": AnotacionCalendario.POR_ETIQUETA,
            "destinatarios": [],
        }
    )
    assert not formulario.is_valid()
    assert "destinatarios" in formulario.errors


def test_anotacion_equipo_no_exige_destinatarios():
    """La visibilidad de equipo completo no necesita destinatarios."""
    formulario = AnotacionCalendarioForm(
        data={
            "fecha": "2026-10-05",
            "contenido": "Reunión general",
            "visibilidad": AnotacionCalendario.EQUIPO,
            "destinatarios": [],
        }
    )
    assert formulario.is_valid(), formulario.errors


# ---------------------------------------------------------------------------
# ImportarDianForm
# ---------------------------------------------------------------------------


def test_importar_dian_rechaza_extension_invalida():
    """Solo se aceptan archivos .xlsx."""
    archivo = SimpleUploadedFile("calendario.csv", b"contenido", content_type="text/csv")
    formulario = ImportarDianForm(files={"archivo": archivo})
    assert not formulario.is_valid()
    assert "archivo" in formulario.errors


def test_importar_dian_rechaza_archivo_grande():
    """El archivo no puede superar 5 MB."""
    archivo = SimpleUploadedFile(
        "calendario.xlsx", b"0" * (5 * 1024 * 1024 + 1), content_type="application/vnd.ms-excel"
    )
    formulario = ImportarDianForm(files={"archivo": archivo})
    assert not formulario.is_valid()
    assert "archivo" in formulario.errors
