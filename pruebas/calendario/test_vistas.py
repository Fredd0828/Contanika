"""Pruebas de vistas, permisos y seguridad del módulo 2: calendario."""

from datetime import date

import pytest
from django.urls import reverse

from aplicaciones.calendario.models import (
    AnotacionCalendario,
    ConfiguracionAlerta,
    TablaReferenciaDian,
    Vencimiento,
)
from aplicaciones.seguridad.models import PermisoRolModulo

pytestmark = pytest.mark.django_db

URLS_PUBLICAS_PROTEGIDAS = [
    "calendario:calendario",
    "calendario:lista",
    "calendario:crear_vencimiento",
    "calendario:generar",
    "calendario:cargar_dian",
    "calendario:crear_anotacion",
]


@pytest.fixture
def vencimiento(cliente):
    return Vencimiento.objects.create(
        cliente=cliente,
        tipo_obligacion="IVA bimestral",
        ambito=Vencimiento.NACIONAL,
        fecha_vencimiento=date(2026, 3, 17),
        estado_validacion=Vencimiento.PENDIENTE_VALIDAR,
    )


@pytest.fixture
def vencimiento_junior(cliente_junior):
    return Vencimiento.objects.create(
        cliente=cliente_junior,
        tipo_obligacion="ICA",
        ambito=Vencimiento.MUNICIPAL,
        municipio="Chía",
        fecha_vencimiento=date(2026, 4, 20),
    )


# ---------------------------------------------------------------------------
# Acceso sin sesión
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("nombre_url", URLS_PUBLICAS_PROTEGIDAS)
def test_urls_requieren_sesion(client, nombre_url):
    """Sin sesión, todas las URLs del módulo redirigen al inicio de sesión."""
    respuesta = client.get(reverse(nombre_url))
    assert respuesta.status_code == 302
    assert reverse("seguridad:iniciar_sesion") in respuesta.url


# ---------------------------------------------------------------------------
# Calendario
# ---------------------------------------------------------------------------


def test_calendario_vista_mes_carga(client, usuario_administrador, vencimiento):
    """La vista mensual carga y muestra los vencimientos del mes."""
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("calendario:calendario"), {"fecha": "2026-03-15"})
    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert "marzo" in contenido
    assert "Comercializadora La Rebaja" in contenido


def test_calendario_vista_semana_y_dia(client, usuario_administrador, vencimiento):
    """Las vistas semanal y diaria también cargan."""
    client.force_login(usuario_administrador)
    for vista in ("semana", "dia"):
        respuesta = client.get(reverse("calendario:calendario"), {"vista": vista, "fecha": "2026-03-17"})
        assert respuesta.status_code == 200
        assert "Comercializadora La Rebaja" in respuesta.content.decode()


def test_calendario_junior_no_ve_clientes_ajenos(client, usuario_junior, vencimiento, vencimiento_junior):
    """El Junior solo ve los vencimientos de sus clientes en el calendario."""
    client.force_login(usuario_junior)
    contenido = client.get(reverse("calendario:calendario"), {"fecha": "2026-03-17"}).content.decode()
    assert "Comercializadora La Rebaja" not in contenido

    contenido = client.get(reverse("calendario:calendario"), {"fecha": "2026-04-20"}).content.decode()
    assert "Papelería El Lápiz" in contenido


# ---------------------------------------------------------------------------
# Listado de vencimientos
# ---------------------------------------------------------------------------


def test_lista_requiere_modulo_habilitado(client, usuario_administrador, modulo_calendario):
    """Si el módulo se inhabilita para el rol, la URL bloquea el acceso (RQF031)."""
    PermisoRolModulo.objects.create(rol=usuario_administrador.rol, modulo=modulo_calendario, habilitado=False)
    client.force_login(usuario_administrador)
    assert client.get(reverse("calendario:lista")).status_code == 403


def test_lista_con_filtros(client, usuario_administrador, vencimiento, vencimiento_junior):
    """El filtro por ámbito deja solo los vencimientos de ese ámbito."""
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("calendario:lista"), {"ambito": Vencimiento.MUNICIPAL})
    resultados = list(respuesta.context["vencimientos"])
    assert resultados == [vencimiento_junior]


# ---------------------------------------------------------------------------
# Detalle y acciones del vencimiento
# ---------------------------------------------------------------------------


def test_detalle_junior_cliente_ajeno_devuelve_404(client, usuario_junior, vencimiento):
    """IDOR: el Junior no puede ver el detalle de un vencimiento ajeno."""
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("calendario:detalle", args=[vencimiento.pk]))
    assert respuesta.status_code == 404


def test_detalle_junior_su_cliente_si_carga(client, usuario_junior, vencimiento_junior):
    """El Junior sí consulta el detalle de vencimientos de sus clientes."""
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("calendario:detalle", args=[vencimiento_junior.pk]))
    assert respuesta.status_code == 200


def test_junior_no_puede_crear_vencimiento(client, usuario_junior):
    """El Junior no tiene permiso para registrar vencimientos."""
    client.force_login(usuario_junior)
    assert client.get(reverse("calendario:crear_vencimiento")).status_code == 403


def test_senior_crea_vencimiento_manual(client, usuario_senior, cliente):
    """El Contador Senior registra un vencimiento municipal con su municipio."""
    client.force_login(usuario_senior)
    respuesta = client.post(
        reverse("calendario:crear_vencimiento"),
        {
            "cliente": cliente.pk,
            "tipo_obligacion": "ICA municipal",
            "ambito": Vencimiento.MUNICIPAL,
            "municipio": "Bogotá D.C.",
            "fecha_vencimiento": "2026-05-15",
            "estado_presentacion": Vencimiento.PENDIENTE,
        },
    )
    assert respuesta.status_code == 302
    creado = Vencimiento.objects.get(tipo_obligacion="ICA municipal")
    assert creado.responsable == usuario_senior
    assert creado.es_automatico_dian is False


def test_cambiar_estado_presentacion(client, usuario_senior, vencimiento):
    """El cambio de estado actualiza el vencimiento."""
    client.force_login(usuario_senior)
    respuesta = client.post(
        reverse("calendario:cambiar_estado", args=[vencimiento.pk]),
        {"estado_presentacion": Vencimiento.PRESENTADA},
    )
    assert respuesta.status_code == 302
    vencimiento.refresh_from_db()
    assert vencimiento.estado_presentacion == Vencimiento.PRESENTADA


def test_validar_vencimiento(client, usuario_senior, vencimiento):
    """La validación marca el vencimiento automático como validado."""
    client.force_login(usuario_senior)
    respuesta = client.post(reverse("calendario:validar", args=[vencimiento.pk]), {"accion": "validar"})
    assert respuesta.status_code == 302
    vencimiento.refresh_from_db()
    assert vencimiento.estado_validacion == Vencimiento.VALIDADO


def test_junior_no_puede_cambiar_estado(client, usuario_junior, vencimiento_junior):
    """El Junior no puede cambiar estados de presentación."""
    client.force_login(usuario_junior)
    respuesta = client.post(
        reverse("calendario:cambiar_estado", args=[vencimiento_junior.pk]),
        {"estado_presentacion": Vencimiento.PRESENTADA},
    )
    assert respuesta.status_code == 403


# ---------------------------------------------------------------------------
# Vencimientos desde el perfil del cliente (Módulo 1)
# ---------------------------------------------------------------------------


def test_detalle_cliente_muestra_sus_vencimientos(client, usuario_administrador, cliente, vencimiento):
    """El perfil del cliente lista sus vencimientos."""
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("clientes:detalle", args=[cliente.pk]))
    assert respuesta.status_code == 200
    assert vencimiento in list(respuesta.context["vencimientos"])
    assert "Vencimientos del cliente" in respuesta.content.decode()


def test_calcular_vencimientos_de_un_cliente(client, usuario_senior, cliente, referencia_dian):
    """Desde el perfil se calculan los vencimientos DIAN de ese cliente."""
    client.force_login(usuario_senior)
    respuesta = client.post(reverse("calendario:calcular_cliente", args=[cliente.pk]))
    assert respuesta.status_code == 302
    assert reverse("clientes:detalle", args=[cliente.pk]) in respuesta.url
    assert Vencimiento.objects.filter(cliente=cliente).count() == 1


def test_calcular_cliente_extranjero_no_crea(client, usuario_administrador, cliente_extranjero):
    """Un cliente sin grupo calculable no genera vencimientos desde el perfil."""
    client.force_login(usuario_administrador)
    respuesta = client.post(reverse("calendario:calcular_cliente", args=[cliente_extranjero.pk]))
    assert respuesta.status_code == 302
    assert Vencimiento.objects.filter(cliente=cliente_extranjero).count() == 0


def test_junior_no_puede_calcular_de_cliente(client, usuario_junior, cliente_junior):
    """El Junior no puede calcular vencimientos ni de sus propios clientes."""
    client.force_login(usuario_junior)
    respuesta = client.post(reverse("calendario:calcular_cliente", args=[cliente_junior.pk]))
    assert respuesta.status_code == 403


def test_crear_vencimiento_con_cliente_preseleccionado(client, usuario_senior, cliente):
    """El formulario llega con el cliente preseleccionado desde el perfil."""
    client.force_login(usuario_senior)
    respuesta = client.get(reverse("calendario:crear_vencimiento"), {"cliente": cliente.pk})
    assert respuesta.status_code == 200
    assert respuesta.context["formulario"].initial["cliente"] == str(cliente.pk)


# ---------------------------------------------------------------------------
# Generación masiva
# ---------------------------------------------------------------------------


def test_generar_vencimientos_masivo(client, usuario_administrador, cliente, referencia_dian):
    """El cálculo masivo crea los vencimientos desde la tabla DIAN."""
    client.force_login(usuario_administrador)
    respuesta = client.post(reverse("calendario:generar"))
    assert respuesta.status_code == 302
    assert Vencimiento.objects.filter(cliente=cliente).count() == 1


def test_junior_no_puede_generar_masivo(client, usuario_junior):
    """El Junior no puede disparar el cálculo masivo."""
    client.force_login(usuario_junior)
    assert client.post(reverse("calendario:generar")).status_code == 403


# ---------------------------------------------------------------------------
# Tabla DIAN (solo Administrador)
# ---------------------------------------------------------------------------


def test_cargar_dian_solo_administrador(client, usuario_senior, usuario_administrador):
    """Solo el Administrador accede a la carga de la tabla DIAN."""
    client.force_login(usuario_senior)
    assert client.get(reverse("calendario:cargar_dian")).status_code == 403

    client.force_login(usuario_administrador)
    assert client.get(reverse("calendario:cargar_dian")).status_code == 200


def test_administrador_carga_referencia_manual(client, usuario_administrador):
    """El Administrador registra una fila nueva de la tabla DIAN."""
    client.force_login(usuario_administrador)
    respuesta = client.post(
        reverse("calendario:cargar_dian"),
        {
            "tipo_obligacion": "Anticipo sobretasa",
            "grupo_nit": "3",
            "fecha_vencimiento": "2026-06-15",
            "periodo_gravable": "2026-01",
        },
    )
    assert respuesta.status_code == 302
    assert TablaReferenciaDian.objects.filter(tipo_obligacion="Anticipo sobretasa").exists()


def test_plantilla_dian_descarga_excel(client, usuario_administrador):
    """La plantilla de carga masiva se descarga como Excel."""
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("calendario:plantilla_dian"))
    assert respuesta.status_code == 200
    assert "spreadsheetml" in respuesta["Content-Type"]


# ---------------------------------------------------------------------------
# Alertas
# ---------------------------------------------------------------------------


def test_crear_y_eliminar_alerta(client, usuario_senior, vencimiento):
    """El Senior configura y elimina alertas de un vencimiento."""
    client.force_login(usuario_senior)
    respuesta = client.post(
        reverse("calendario:crear_alerta", args=[vencimiento.pk]),
        {"dias_anticipacion": 5, "canal": ConfiguracionAlerta.CORREO},
    )
    assert respuesta.status_code == 302
    alerta = ConfiguracionAlerta.objects.get(vencimiento=vencimiento)
    assert alerta.dias_anticipacion == 5

    respuesta = client.post(reverse("calendario:eliminar_alerta", args=[alerta.pk]))
    assert respuesta.status_code == 302
    assert ConfiguracionAlerta.objects.count() == 0


def test_junior_no_puede_crear_alerta(client, usuario_junior, vencimiento_junior):
    """El Junior no configura alertas."""
    client.force_login(usuario_junior)
    respuesta = client.post(
        reverse("calendario:crear_alerta", args=[vencimiento_junior.pk]),
        {"dias_anticipacion": 5, "canal": ConfiguracionAlerta.CORREO},
    )
    assert respuesta.status_code == 403


# ---------------------------------------------------------------------------
# Anotaciones
# ---------------------------------------------------------------------------


def test_crear_anotacion_cualquier_rol(client, usuario_junior):
    """Cualquier rol autenticado puede crear anotaciones."""
    client.force_login(usuario_junior)
    respuesta = client.post(
        reverse("calendario:crear_anotacion"),
        {
            "fecha": "2026-10-05",
            "contenido": "Revisar cierre de septiembre",
            "visibilidad": AnotacionCalendario.EQUIPO,
            "destinatarios": [],
        },
    )
    assert respuesta.status_code == 302
    assert AnotacionCalendario.objects.filter(contenido__icontains="cierre").exists()


def test_eliminar_anotacion_solo_autor_o_admin(client, usuario_administrador, usuario_senior, usuario_junior):
    """El Senior no puede eliminar la anotación del Junior; el Administrador sí."""
    anotacion = AnotacionCalendario.objects.create(
        fecha=date(2026, 10, 5),
        contenido="Nota del junior",
        autor=usuario_junior,
        visibilidad=AnotacionCalendario.EQUIPO,
    )
    client.force_login(usuario_senior)
    client.post(reverse("calendario:eliminar_anotacion", args=[anotacion.pk]))
    assert AnotacionCalendario.objects.count() == 1

    client.force_login(usuario_administrador)
    client.post(reverse("calendario:eliminar_anotacion", args=[anotacion.pk]))
    assert AnotacionCalendario.objects.count() == 0


# ---------------------------------------------------------------------------
# Seguridad transversal
# ---------------------------------------------------------------------------


def test_post_sin_csrf_es_rechazado(client, usuario_administrador, cliente):
    """Un POST sin token CSRF es rechazado por Django."""
    from django.test import Client as ClienteSinCsrf

    cliente_http = ClienteSinCsrf(enforce_csrf_checks=True)
    cliente_http.force_login(usuario_administrador)
    respuesta = cliente_http.post(
        reverse("calendario:crear_vencimiento"),
        {
            "cliente": cliente.pk,
            "tipo_obligacion": "ICA",
            "ambito": Vencimiento.MUNICIPAL,
            "municipio": "Chía",
            "fecha_vencimiento": "2026-05-15",
            "estado_presentacion": Vencimiento.PENDIENTE,
        },
    )
    assert respuesta.status_code == 403


def test_contenido_anotacion_se_escapa(client, usuario_administrador):
    """Un script en el contenido de la anotación se escapa en la plantilla (XSS)."""
    client.force_login(usuario_administrador)
    AnotacionCalendario.objects.create(
        fecha=date(2026, 10, 5),
        contenido="<script>alert('xss')</script>",
        autor=usuario_administrador,
        visibilidad=AnotacionCalendario.EQUIPO,
    )
    contenido = client.get(reverse("calendario:calendario"), {"fecha": "2026-10-05"}).content.decode()
    assert "<script>alert('xss')</script>" not in contenido
    assert "&lt;script&gt;" in contenido
