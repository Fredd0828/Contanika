"""Pruebas de los formularios del módulo 5: hallazgos y revisiones contables."""

from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from aplicaciones.hallazgos.formularios import AdjuntoHallazgoForm, CambiarEstadoHallazgoForm, HallazgoForm
from aplicaciones.hallazgos.models import Hallazgo

pytestmark = pytest.mark.django_db


def test_hallazgo_form_restringe_cliente_para_junior(usuario_junior, cliente, cliente_junior):
    formulario = HallazgoForm(usuario=usuario_junior)
    assert list(formulario.fields["cliente"].queryset) == [cliente_junior]


def test_hallazgo_form_admin_ve_todos_los_clientes(usuario_administrador, cliente, cliente_junior):
    clientes = set(HallazgoForm(usuario=usuario_administrador).fields["cliente"].queryset)
    assert {cliente, cliente_junior} <= clientes


def test_hallazgo_form_muestra_las_fechas_del_periodo_al_editar(usuario_administrador):
    """Un campo `type="date"` solo acepta año-mes-día; con otro formato el navegador lo deja vacío."""
    formulario = HallazgoForm(
        usuario=usuario_administrador,
        initial={"fecha_inicio_periodo": date(2026, 8, 1), "fecha_fin_periodo": date(2026, 8, 31)},
    )
    assert 'value="2026-08-01"' in str(formulario["fecha_inicio_periodo"])
    assert 'value="2026-08-31"' in str(formulario["fecha_fin_periodo"])


def test_cambiar_estado_form_exige_observacion_para_cerrar():
    formulario = CambiarEstadoHallazgoForm(data={"estado": Hallazgo.CERRADO, "observacion_cierre": ""})
    assert not formulario.is_valid()


def test_cambiar_estado_form_permite_cerrar_con_observacion():
    formulario = CambiarEstadoHallazgoForm(
        data={"estado": Hallazgo.CERRADO, "observacion_cierre": "Todo aclarado."}
    )
    assert formulario.is_valid(), formulario.errors


def test_cambiar_estado_form_no_exige_observacion_para_otros_estados():
    formulario = CambiarEstadoHallazgoForm(data={"estado": Hallazgo.EN_PROCESO, "observacion_cierre": ""})
    assert formulario.is_valid(), formulario.errors


def test_adjunto_form_rechaza_extension_no_permitida():
    archivo = SimpleUploadedFile("virus.exe", b"contenido", content_type="application/octet-stream")
    formulario = AdjuntoHallazgoForm(files={"archivo": archivo})
    assert not formulario.is_valid()
    assert "archivo" in formulario.errors


def test_adjunto_form_rechaza_archivo_mayor_a_10mb():
    archivo = SimpleUploadedFile("soporte.pdf", b"0" * (11 * 1024 * 1024), content_type="application/pdf")
    formulario = AdjuntoHallazgoForm(files={"archivo": archivo})
    assert not formulario.is_valid()
    assert "archivo" in formulario.errors


def test_adjunto_form_acepta_pdf_valido():
    archivo = SimpleUploadedFile("soporte.pdf", b"%PDF-contenido", content_type="application/pdf")
    formulario = AdjuntoHallazgoForm(files={"archivo": archivo})
    assert formulario.is_valid(), formulario.errors
