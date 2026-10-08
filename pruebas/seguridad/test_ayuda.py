"""Pruebas de las guías paso a paso de la sección de ayuda (HU053)."""

import pytest
from django.urls import NoReverseMatch, reverse

from aplicaciones.seguridad import guias
from aplicaciones.seguridad.models import Modulo, PermisoRolModulo, Rol

pytestmark = pytest.mark.django_db


def _url(slug):
    return reverse("seguridad:guia", kwargs={"slug": slug})


# ---------------------------------------------------------------------------
# Catálogo
# ---------------------------------------------------------------------------


def test_los_slugs_no_se_repiten():
    assert len(guias.POR_SLUG) == len(guias.GUIAS)


@pytest.mark.parametrize("guia", guias.GUIAS, ids=lambda guia: guia.slug)
def test_cada_guia_esta_completa_y_bien_enlazada(guia):
    assert guia.titulo and guia.resumen and guia.icono.startswith("bi-")
    assert len(guia.pasos) >= 2 and all(paso.titulo for paso in guia.pasos)
    assert guia.modulo is None or guia.modulo in guias.NOMBRES_MODULO
    assert set(guia.roles) <= {Rol.ADMINISTRADOR, Rol.CONTADOR_SENIOR, Rol.CONTADOR_JUNIOR}
    assert all(slug in guias.POR_SLUG and slug != guia.slug for slug in guia.relacionadas)
    if guia.ruta:
        assert guia.etiqueta_ruta
        try:
            reverse(guia.ruta)
        except NoReverseMatch:
            pytest.fail(f"La guía «{guia.slug}» apunta a una ruta que no existe: {guia.ruta}")


def test_todos_los_modulos_tienen_al_menos_una_guia():
    assert {guia.modulo for guia in guias.GUIAS} >= set(guias.NOMBRES_MODULO)


# ---------------------------------------------------------------------------
# Visibilidad por rol y por módulo
# ---------------------------------------------------------------------------


def test_el_administrador_ve_todas_las_guias(usuario_administrador):
    assert len(guias.guias_visibles(usuario_administrador)) == len(guias.GUIAS)


def test_el_junior_no_ve_los_procesos_que_no_puede_hacer(usuario_junior):
    slugs = {guia.slug for guia in guias.guias_visibles(usuario_junior)}
    assert {"crear-cliente", "anotar-expediente", "mi-perfil"} <= slugs
    assert not slugs & {"importar-clientes", "registrar-abono", "crear-usuario", "crear-tarea"}


def test_el_senior_no_ve_los_procesos_del_administrador(usuario_senior):
    slugs = {guia.slug for guia in guias.guias_visibles(usuario_senior)}
    assert {"importar-clientes", "crear-tarea", "registrar-comunicacion"} <= slugs
    assert not slugs & {"generar-cuenta-cobro", "crear-usuario", "modulos-por-rol"}


def test_modulo_inhabilitado_oculta_sus_guias(usuario_junior):
    modulo = Modulo.objects.create(codigo_modulo=Modulo.MOD01_CLIENTES, nombre_modulo="Clientes")
    PermisoRolModulo.objects.create(rol=usuario_junior.rol, modulo=modulo, habilitado=False)
    grupos = [grupo["nombre"] for grupo in guias.guias_por_grupo(usuario_junior)]
    assert "Clientes" not in grupos
    assert guias.GRUPO_GENERAL in grupos


def test_las_guias_se_agrupan_por_modulo(usuario_administrador):
    grupos = guias.guias_por_grupo(usuario_administrador)
    assert grupos[0]["nombre"] == "Clientes"
    assert sum(len(grupo["guias"]) for grupo in grupos) == len(guias.GUIAS)


# ---------------------------------------------------------------------------
# Vistas
# ---------------------------------------------------------------------------


def test_la_guia_requiere_sesion(client):
    respuesta = client.get(_url("crear-cliente"))
    assert respuesta.status_code == 302
    assert reverse("seguridad:iniciar_sesion") in respuesta.url


def test_la_ayuda_lista_las_guias_del_rol(client, usuario_junior):
    client.force_login(usuario_junior)
    contenido = client.get(reverse("seguridad:ayuda")).content.decode()
    assert "Guías paso a paso" in contenido
    assert _url("crear-cliente") in contenido
    assert _url("crear-usuario") not in contenido


def test_la_guia_muestra_pasos_notas_y_enlace_a_la_pantalla(client, usuario_administrador):
    client.force_login(usuario_administrador)
    respuesta = client.get(_url("crear-cliente"))
    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    guia = guias.POR_SLUG["crear-cliente"]
    assert guia.titulo in contenido and "Antes de empezar" in contenido
    assert contenido.count('class="ay-paso"') == len(guia.pasos)
    assert reverse("clientes:crear") in contenido
    assert _url("importar-clientes") in contenido


def test_las_relacionadas_respetan_el_rol(client, usuario_junior):
    client.force_login(usuario_junior)
    respuesta = client.get(_url("crear-cliente"))
    assert [guia.slug for guia in respuesta.context["relacionadas"]] == []


def test_guia_de_otro_rol_responde_403(client, usuario_junior):
    client.force_login(usuario_junior)
    assert client.get(_url("crear-usuario")).status_code == 403


def test_guia_de_modulo_inhabilitado_responde_403(client, usuario_senior):
    modulo = Modulo.objects.create(codigo_modulo=Modulo.MOD03_TAREAS, nombre_modulo="Tareas")
    PermisoRolModulo.objects.create(rol=usuario_senior.rol, modulo=modulo, habilitado=False)
    client.force_login(usuario_senior)
    assert client.get(_url("crear-tarea")).status_code == 403


def test_guia_inexistente_responde_404(client, usuario_administrador):
    client.force_login(usuario_administrador)
    assert client.get(_url("no-existe")).status_code == 404


def test_el_buscador_de_la_barra_lleva_al_listado_de_clientes(client, usuario_junior, cliente):
    client.force_login(usuario_junior)
    contenido = client.get(reverse("seguridad:ayuda")).content.decode()
    assert f'action="{reverse("clientes:lista")}"' in contenido and 'name="busqueda"' in contenido
    respuesta = client.get(reverse("clientes:lista"), {"busqueda": cliente.nombre_razon_social[:5]})
    assert cliente in respuesta.context["clientes"]


def test_el_buscador_no_aparece_sin_el_modulo_de_clientes(client, usuario_junior):
    modulo = Modulo.objects.create(codigo_modulo=Modulo.MOD01_CLIENTES, nombre_modulo="Clientes")
    PermisoRolModulo.objects.create(rol=usuario_junior.rol, modulo=modulo, habilitado=False)
    client.force_login(usuario_junior)
    assert 'name="busqueda"' not in client.get(reverse("seguridad:ayuda")).content.decode()


def test_el_texto_de_las_guias_se_escapa(client, usuario_administrador, monkeypatch):
    peligrosa = guias.Guia(
        slug="prueba",
        titulo="<script>alert(1)</script>",
        resumen="Resumen",
        icono="bi-bug",
        pasos=(guias.Paso("Uno"), guias.Paso("Dos")),
    )
    monkeypatch.setitem(guias.POR_SLUG, "prueba", peligrosa)
    client.force_login(usuario_administrador)
    contenido = client.get(_url("prueba")).content.decode()
    assert "<script>alert(1)</script>" not in contenido
    assert "&lt;script&gt;" in contenido
