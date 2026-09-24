"""Pruebas de vistas, permisos y seguridad del módulo 3: tablero de tareas Kanban."""

import pytest
from django.urls import reverse

from aplicaciones.seguridad.models import PermisoRolModulo
from aplicaciones.tareas.models import HistorialTarea, ObservacionTarea, Tarea

pytestmark = pytest.mark.django_db

URLS_PROTEGIDAS = [
    "tareas:tablero",
    "tareas:crear",
    "tareas:notificaciones",
]


@pytest.fixture
def tarea_admin(cliente, usuario_administrador):
    return Tarea.objects.create(
        cliente=cliente,
        titulo="Preparar retención en la fuente",
        responsable=usuario_administrador,
        prioridad=Tarea.ALTA,
    )


@pytest.fixture
def tarea_junior(cliente_junior, usuario_junior):
    return Tarea.objects.create(
        cliente=cliente_junior,
        titulo="Reunir soportes de renta",
        responsable=usuario_junior,
        prioridad=Tarea.MEDIA,
    )


# ---------------------------------------------------------------------------
# Acceso sin sesión
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("nombre_url", URLS_PROTEGIDAS)
def test_urls_requieren_sesion(client, nombre_url):
    """Sin sesión, todas las URLs del módulo redirigen al inicio de sesión."""
    respuesta = client.get(reverse(nombre_url))
    assert respuesta.status_code == 302
    assert reverse("seguridad:iniciar_sesion") in respuesta.url


def test_tablero_requiere_modulo_habilitado(client, usuario_administrador, modulo_tareas):
    """Si el módulo se inhabilita para el rol, la URL bloquea el acceso (RQF031)."""
    PermisoRolModulo.objects.create(rol=usuario_administrador.rol, modulo=modulo_tareas, habilitado=False)
    client.force_login(usuario_administrador)
    assert client.get(reverse("tareas:tablero")).status_code == 403


# ---------------------------------------------------------------------------
# Tablero
# ---------------------------------------------------------------------------


def test_tablero_carga_y_agrupa_por_estado(client, usuario_administrador, tarea_admin):
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("tareas:tablero"))
    assert respuesta.status_code == 200
    tablero = dict((estado, tareas) for estado, _, tareas in respuesta.context["tablero"])
    assert tarea_admin in tablero[Tarea.POR_HACER]


def test_tablero_junior_no_ve_tareas_ajenas(client, usuario_junior, tarea_admin, tarea_junior):
    client.force_login(usuario_junior)
    contenido = client.get(reverse("tareas:tablero")).content.decode()
    assert "Reunir soportes de renta" in contenido
    assert "Preparar retención en la fuente" not in contenido


# ---------------------------------------------------------------------------
# Crear / editar / eliminar (Administrador y Contador Senior)
# ---------------------------------------------------------------------------


def test_junior_no_puede_crear_tarea(client, usuario_junior):
    client.force_login(usuario_junior)
    assert client.get(reverse("tareas:crear")).status_code == 403


def test_senior_crea_tarea(client, usuario_senior, cliente):
    client.force_login(usuario_senior)
    respuesta = client.post(
        reverse("tareas:crear"),
        {
            "cliente": cliente.pk,
            "titulo": "Presentar IVA bimestral",
            "tipo_tarea": "Declaración",
            "prioridad": Tarea.ALTA,
        },
    )
    assert respuesta.status_code == 302
    creada = Tarea.objects.get(titulo="Presentar IVA bimestral")
    assert creada.estado == Tarea.POR_HACER


def test_senior_edita_tarea(client, usuario_senior, tarea_admin):
    client.force_login(usuario_senior)
    respuesta = client.post(
        reverse("tareas:editar", args=[tarea_admin.pk]),
        {
            "cliente": tarea_admin.cliente_id,
            "titulo": "Preparar retención (actualizada)",
            "prioridad": Tarea.MEDIA,
        },
    )
    assert respuesta.status_code == 302
    tarea_admin.refresh_from_db()
    assert tarea_admin.titulo == "Preparar retención (actualizada)"


def test_junior_no_puede_editar_tarea(client, usuario_junior, tarea_junior):
    client.force_login(usuario_junior)
    assert client.get(reverse("tareas:editar", args=[tarea_junior.pk])).status_code == 403


def test_admin_elimina_tarea(client, usuario_administrador, tarea_admin):
    client.force_login(usuario_administrador)
    respuesta = client.post(reverse("tareas:eliminar", args=[tarea_admin.pk]))
    assert respuesta.status_code == 302
    assert not Tarea.objects.filter(pk=tarea_admin.pk).exists()


def test_junior_no_puede_eliminar_tarea(client, usuario_junior, tarea_junior):
    client.force_login(usuario_junior)
    respuesta = client.post(reverse("tareas:eliminar", args=[tarea_junior.pk]))
    assert respuesta.status_code == 403
    assert Tarea.objects.filter(pk=tarea_junior.pk).exists()


# ---------------------------------------------------------------------------
# Detalle (IDOR)
# ---------------------------------------------------------------------------


def test_detalle_junior_tarea_ajena_devuelve_404(client, usuario_junior, tarea_admin):
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("tareas:detalle", args=[tarea_admin.pk]))
    assert respuesta.status_code == 404


def test_detalle_junior_su_tarea_carga(client, usuario_junior, tarea_junior):
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("tareas:detalle", args=[tarea_junior.pk]))
    assert respuesta.status_code == 200


# ---------------------------------------------------------------------------
# Cambiar estado
# ---------------------------------------------------------------------------


def test_junior_cambia_estado_de_su_tarea(client, usuario_junior, tarea_junior):
    client.force_login(usuario_junior)
    respuesta = client.post(
        reverse("tareas:cambiar_estado", args=[tarea_junior.pk]), {"estado": Tarea.EN_PROGRESO}
    )
    assert respuesta.status_code == 302
    tarea_junior.refresh_from_db()
    assert tarea_junior.estado == Tarea.EN_PROGRESO
    assert HistorialTarea.objects.filter(tarea=tarea_junior).count() == 1


def test_junior_no_cambia_estado_de_tarea_ajena(client, usuario_junior, tarea_admin):
    """IDOR: el Junior no encuentra (404) una tarea que no tiene asignada."""
    client.force_login(usuario_junior)
    respuesta = client.post(
        reverse("tareas:cambiar_estado", args=[tarea_admin.pk]), {"estado": Tarea.EN_PROGRESO}
    )
    assert respuesta.status_code == 404


def test_cambiar_estado_via_ajax_devuelve_json(client, usuario_administrador, tarea_admin):
    client.force_login(usuario_administrador)
    respuesta = client.post(
        reverse("tareas:cambiar_estado", args=[tarea_admin.pk]),
        {"estado": Tarea.EN_REVISION},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert respuesta.status_code == 200
    assert respuesta.json() == {"ok": True, "estado": Tarea.EN_REVISION}


# ---------------------------------------------------------------------------
# Observaciones
# ---------------------------------------------------------------------------


def test_agregar_observacion_en_tarea_propia(client, usuario_junior, tarea_junior):
    client.force_login(usuario_junior)
    respuesta = client.post(
        reverse("tareas:agregar_observacion", args=[tarea_junior.pk]),
        {"contenido": "Se solicitaron soportes adicionales."},
    )
    assert respuesta.status_code == 302
    assert ObservacionTarea.objects.filter(tarea=tarea_junior).count() == 1


def test_agregar_observacion_en_tarea_ajena_devuelve_404(client, usuario_junior, tarea_admin):
    client.force_login(usuario_junior)
    respuesta = client.post(
        reverse("tareas:agregar_observacion", args=[tarea_admin.pk]),
        {"contenido": "Intento no autorizado."},
    )
    assert respuesta.status_code == 404


# ---------------------------------------------------------------------------
# Notificaciones
# ---------------------------------------------------------------------------


def test_notificaciones_endpoint_lista_cambios_de_otros(
    client, usuario_junior, usuario_administrador, tarea_junior
):
    tarea_junior.cambiar_estado(Tarea.EN_PROGRESO, usuario_administrador)
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("tareas:notificaciones"))
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["total"] == 1
    assert datos["notificaciones"][0]["tarea"] == tarea_junior.pk


# ---------------------------------------------------------------------------
# Seguridad transversal
# ---------------------------------------------------------------------------


def test_post_sin_csrf_es_rechazado(client, usuario_administrador, cliente):
    from django.test import Client as ClienteSinCsrf

    cliente_http = ClienteSinCsrf(enforce_csrf_checks=True)
    cliente_http.force_login(usuario_administrador)
    respuesta = cliente_http.post(
        reverse("tareas:crear"),
        {"cliente": cliente.pk, "titulo": "Sin CSRF", "prioridad": Tarea.MEDIA},
    )
    assert respuesta.status_code == 403


def test_titulo_con_script_se_escapa_en_el_tablero(client, usuario_administrador, cliente):
    Tarea.objects.create(
        cliente=cliente,
        titulo="<script>alert('xss')</script>",
        responsable=usuario_administrador,
    )
    client.force_login(usuario_administrador)
    contenido = client.get(reverse("tareas:tablero")).content.decode()
    assert "<script>alert('xss')</script>" not in contenido
    assert "&lt;script&gt;" in contenido
