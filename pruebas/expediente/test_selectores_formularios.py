"""Pruebas de selectores y formularios del módulo 9: expediente y bitácora."""

from datetime import date

import pytest

from aplicaciones.comunes.models import Adjunto
from aplicaciones.expediente import selectores
from aplicaciones.expediente.formularios import AnotacionForm
from aplicaciones.expediente.models import Anotacion

from .conftest import archivo_prueba

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Selectores
# ---------------------------------------------------------------------------


def test_junior_solo_ve_anotaciones_de_sus_clientes(
    usuario_junior, anotacion_cliente, anotacion_cliente_junior
):
    assert list(selectores.anotaciones_visibles(usuario_junior)) == [anotacion_cliente_junior]


def test_junior_ve_anotaciones_de_otros_usuarios_en_sus_clientes(usuario_junior, anotacion_cliente_junior):
    # HU027-5: ve todas las anotaciones del expediente, no solo las propias.
    assert anotacion_cliente_junior.usuario != usuario_junior
    assert anotacion_cliente_junior in selectores.anotaciones_visibles(usuario_junior)


def test_senior_ve_todas(usuario_senior, anotacion_cliente, anotacion_cliente_junior):
    assert selectores.anotaciones_visibles(usuario_senior).count() == 2


def test_filtro_por_tipo_ignora_mayusculas(
    usuario_administrador, anotacion_cliente, anotacion_cliente_junior
):
    resultado = selectores.filtrar_anotaciones(usuario_administrador, tipo="retención EN LA FUENTE")
    assert list(resultado) == [anotacion_cliente]


def test_filtro_por_rango_usa_fecha_del_evento(
    usuario_administrador, anotacion_cliente, anotacion_cliente_junior
):
    resultado = selectores.filtrar_anotaciones(
        usuario_administrador, desde=date(2026, 3, 1), hasta=date(2026, 3, 31)
    )
    assert list(resultado) == [anotacion_cliente]


def test_archivadas_se_ocultan_salvo_que_se_pidan(usuario_administrador, anotacion_cliente):
    anotacion_cliente.archivar()
    assert not selectores.filtrar_anotaciones(usuario_administrador).exists()
    assert selectores.filtrar_anotaciones(usuario_administrador, incluir_archivadas=True).exists()


def test_tipos_incluye_sugeridos_y_usados_sin_repetir(usuario_administrador, anotacion_cliente, cliente):
    Anotacion.objects.create(
        cliente=cliente, usuario=usuario_administrador, tipo_anotacion="reunión", contenido="x"
    )
    tipos = selectores.tipos_de_anotacion(usuario_administrador)
    assert tipos[: len(Anotacion.TIPOS_SUGERIDOS)] == Anotacion.TIPOS_SUGERIDOS
    assert "Retención en la fuente" in tipos
    assert "reunión" not in tipos  # ya está como "Reunión"


def test_con_adjuntos_asigna_lista_por_anotacion(anotacion_cliente, anotacion_cliente_junior):
    Adjunto.objects.create(
        tabla_origen=Adjunto.ANOTACION,
        id_origen=anotacion_cliente.pk,
        archivo=archivo_prueba(),
        nombre_archivo="soporte.pdf",
    )
    # Un adjunto de hallazgo con el mismo id no debe mezclarse.
    Adjunto.objects.create(
        tabla_origen=Adjunto.HALLAZGO,
        id_origen=anotacion_cliente_junior.pk,
        archivo=archivo_prueba(),
        nombre_archivo="hallazgo.pdf",
    )
    anotaciones = {a.pk: a for a in selectores.con_adjuntos(Anotacion.objects.all())}
    assert [a.nombre_archivo for a in anotaciones[anotacion_cliente.pk].lista_adjuntos] == ["soporte.pdf"]
    assert anotaciones[anotacion_cliente_junior.pk].lista_adjuntos == []


# ---------------------------------------------------------------------------
# Formulario de anotación
# ---------------------------------------------------------------------------


def _datos(cliente_pk):
    return {
        "cliente": cliente_pk,
        "tipo_anotacion": "  Llamada  ",
        "fecha": "2026-09-30",
        "contenido": "Llamada para pedir soportes.",
    }


def test_formulario_valido_sin_archivos(usuario_administrador, cliente):
    formulario = AnotacionForm(_datos(cliente.pk), usuario=usuario_administrador)
    assert formulario.is_valid(), formulario.errors
    assert formulario.cleaned_data["tipo_anotacion"] == "Llamada"
    assert formulario.cleaned_data["archivos"] == []


def _con_archivos(cantidad, nombre="soporte.pdf"):
    from django.utils.datastructures import MultiValueDict

    return MultiValueDict({"archivos": [archivo_prueba(f"{i}-{nombre}") for i in range(cantidad)]})


def test_administrador_adjunta_hasta_5(usuario_administrador, cliente):
    assert AnotacionForm(_datos(cliente.pk), _con_archivos(5), usuario=usuario_administrador).is_valid()
    formulario = AnotacionForm(_datos(cliente.pk), _con_archivos(6), usuario=usuario_administrador)
    assert not formulario.is_valid()
    assert "máximo 5" in str(formulario.errors["archivos"])


def test_junior_adjunta_hasta_3(usuario_junior, cliente_junior):
    assert AnotacionForm(_datos(cliente_junior.pk), _con_archivos(3), usuario=usuario_junior).is_valid()
    formulario = AnotacionForm(_datos(cliente_junior.pk), _con_archivos(4), usuario=usuario_junior)
    assert not formulario.is_valid()
    assert "máximo 3" in str(formulario.errors["archivos"])


def test_rechaza_extension_no_permitida(usuario_administrador, cliente):
    formulario = AnotacionForm(
        _datos(cliente.pk), _con_archivos(1, "virus.exe"), usuario=usuario_administrador
    )
    assert not formulario.is_valid()
    assert "formato no permitido" in str(formulario.errors["archivos"])


def test_rechaza_archivo_de_mas_de_10_mb(usuario_administrador, cliente, settings):
    from django.utils.datastructures import MultiValueDict

    grande = archivo_prueba("grande.pdf", b"0" * (10 * 1024 * 1024 + 1))
    formulario = AnotacionForm(
        _datos(cliente.pk), MultiValueDict({"archivos": [grande]}), usuario=usuario_administrador
    )
    assert not formulario.is_valid()
    assert "10 MB" in str(formulario.errors["archivos"])


def test_junior_no_puede_elegir_cliente_ajeno(usuario_junior, cliente):
    formulario = AnotacionForm(_datos(cliente.pk), usuario=usuario_junior)
    assert not formulario.is_valid()
    assert "cliente" in formulario.errors
