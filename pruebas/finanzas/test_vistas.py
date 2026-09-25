"""Pruebas de vistas, permisos y seguridad del módulo 6: honorarios, catálogos y cuentas de cobro."""

from decimal import Decimal

import pytest
from django.urls import reverse

from aplicaciones.finanzas.models import ConceptoFacturable, CuentaCobro, Honorario, MetodoPago
from aplicaciones.seguridad.models import PermisoRolModulo

pytestmark = pytest.mark.django_db

URLS_PROTEGIDAS = ["finanzas:historico", "finanzas:generar", "finanzas:catalogos"]


def _datos_cuenta(cliente, *lineas, valor_total="1000000"):
    datos = {
        "cliente": cliente.pk,
        "periodo_facturado": CuentaCobro.MENSUAL,
        "fecha_inicio_periodo": "2026-09-01",
        "valor_total": valor_total,
        "fecha_vencimiento_pago": "2026-10-10",
        "lineas-TOTAL_FORMS": str(len(lineas)),
        "lineas-INITIAL_FORMS": "0",
    }
    for indice, (descripcion, valor) in enumerate(lineas):
        datos[f"lineas-{indice}-descripcion_linea"] = descripcion
        datos[f"lineas-{indice}-valor_linea"] = valor
    return datos


# ---------------------------------------------------------------------------
# Acceso sin sesión / módulo inhabilitado / permisos por rol
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("nombre_url", URLS_PROTEGIDAS)
def test_urls_requieren_sesion(client, nombre_url):
    respuesta = client.get(reverse(nombre_url))
    assert respuesta.status_code == 302
    assert reverse("seguridad:iniciar_sesion") in respuesta.url


def test_historico_requiere_modulo_habilitado(client, usuario_administrador, modulo_finanzas):
    PermisoRolModulo.objects.create(rol=usuario_administrador.rol, modulo=modulo_finanzas, habilitado=False)
    client.force_login(usuario_administrador)
    assert client.get(reverse("finanzas:historico")).status_code == 403


@pytest.mark.parametrize("usuario_fixture", ["usuario_senior", "usuario_junior"])
@pytest.mark.parametrize("nombre_url", ["finanzas:generar", "finanzas:catalogos"])
def test_solo_administrador_genera_y_gestiona_catalogos(client, request, usuario_fixture, nombre_url):
    client.force_login(request.getfixturevalue(usuario_fixture))
    assert client.get(reverse(nombre_url)).status_code == 403


@pytest.mark.parametrize("usuario_fixture", ["usuario_senior", "usuario_junior"])
def test_solo_administrador_configura_honorario(client, request, usuario_fixture, cliente):
    client.force_login(request.getfixturevalue(usuario_fixture))
    respuesta = client.post(
        reverse("finanzas:honorario", args=[cliente.pk]), {"tipo": Honorario.FIJO_MENSUAL, "monto": "1"}
    )
    assert respuesta.status_code == 403
    assert not Honorario.objects.exists()


def test_senior_consulta_historico_sin_botones_de_administrador(client, usuario_senior):
    client.force_login(usuario_senior)
    respuesta = client.get(reverse("finanzas:historico"))
    assert respuesta.status_code == 200
    assert reverse("finanzas:generar") not in respuesta.content.decode()


def test_junior_no_elimina_cuenta_de_su_cliente(client, usuario_junior, cuenta_cliente_junior):
    client.force_login(usuario_junior)
    respuesta = client.post(reverse("finanzas:eliminar", args=[cuenta_cliente_junior.pk]))
    assert respuesta.status_code == 403
    assert CuentaCobro.objects.filter(pk=cuenta_cliente_junior.pk).exists()


# ---------------------------------------------------------------------------
# IDOR: cuentas de clientes no asignados
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("nombre_url", ["finanzas:detalle", "finanzas:descargar"])
def test_junior_no_accede_a_cuenta_de_cliente_ajeno(client, usuario_junior, cuenta_cliente, nombre_url):
    client.force_login(usuario_junior)
    assert client.get(reverse(nombre_url, args=[cuenta_cliente.pk])).status_code == 404


def test_junior_consulta_y_descarga_cuenta_de_su_cliente(client, usuario_junior, cuenta_cliente_junior):
    client.force_login(usuario_junior)
    assert client.get(reverse("finanzas:detalle", args=[cuenta_cliente_junior.pk])).status_code == 200
    respuesta = client.get(reverse("finanzas:descargar", args=[cuenta_cliente_junior.pk]))
    assert respuesta.status_code == 200
    assert respuesta["Content-Type"] == "application/pdf"
    assert "attachment" in respuesta["Content-Disposition"]


# ---------------------------------------------------------------------------
# Generar cuenta de cobro
# ---------------------------------------------------------------------------


def test_generar_get_con_cliente_sugiere_valor_y_lineas(
    client, usuario_administrador, cliente_con_servicios, servicio_contabilidad
):
    Honorario.objects.create(cliente=cliente_con_servicios, monto=Decimal("900000"))
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("finanzas:generar"), {"cliente": cliente_con_servicios.pk})
    assert respuesta.status_code == 200
    assert respuesta.context["formulario"].initial["valor_total"] == Decimal("900000")
    assert len(respuesta.context["formset"].forms) == 2


def test_generar_cuenta_de_cobro_completa(client, usuario_administrador, cliente, despacho):
    client.force_login(usuario_administrador)
    respuesta = client.post(
        reverse("finanzas:generar"),
        _datos_cuenta(cliente, ("Contabilidad mensual", "700000"), ("<script>alert(1)</script>", "300000")),
    )
    cuenta = CuentaCobro.objects.get(cliente=cliente)
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("finanzas:detalle", args=[cuenta.pk])
    assert cuenta.detalles.count() == 2
    assert cuenta.archivo

    detalle = client.get(respuesta.url).content.decode()
    assert "<script>alert(1)</script>" not in detalle
    assert "&lt;script&gt;" in detalle


def test_generar_rechaza_lineas_que_no_suman_el_total(client, usuario_administrador, cliente):
    client.force_login(usuario_administrador)
    respuesta = client.post(reverse("finanzas:generar"), _datos_cuenta(cliente, ("Contabilidad", "500000")))
    assert respuesta.status_code == 200
    assert not CuentaCobro.objects.exists()
    assert "debe ser igual al valor total" in respuesta.content.decode()


def test_generar_sin_token_csrf_es_rechazado(usuario_administrador, cliente):
    from django.test import Client

    cliente_http = Client(enforce_csrf_checks=True)
    cliente_http.force_login(usuario_administrador)
    respuesta = cliente_http.post(reverse("finanzas:generar"), _datos_cuenta(cliente, ("Contabilidad", "")))
    assert respuesta.status_code == 403
    assert not CuentaCobro.objects.exists()


# ---------------------------------------------------------------------------
# Detalle, eliminación e histórico
# ---------------------------------------------------------------------------


def test_administrador_elimina_cuenta_sin_abonos(client, usuario_administrador, cuenta_cliente):
    client.force_login(usuario_administrador)
    respuesta = client.post(reverse("finanzas:eliminar", args=[cuenta_cliente.pk]))
    assert respuesta.status_code == 302
    assert not CuentaCobro.objects.filter(pk=cuenta_cliente.pk).exists()


def test_eliminar_cuenta_con_abonos_muestra_error(client, usuario_administrador, cuenta_cliente):
    cuenta_cliente.abonos.create(
        monto=Decimal("1"),
        responsable=usuario_administrador,
        saldo_anterior=Decimal("1000000"),
        saldo_resultante=Decimal("999999"),
    )
    client.force_login(usuario_administrador)
    respuesta = client.post(reverse("finanzas:eliminar", args=[cuenta_cliente.pk]), follow=True)
    assert CuentaCobro.objects.filter(pk=cuenta_cliente.pk).exists()
    assert "ya tiene abonos registrados" in respuesta.content.decode()


def test_historico_filtra_por_cliente(
    client, usuario_administrador, cliente, cuenta_cliente, cuenta_cliente_junior
):
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("finanzas:historico"), {"cliente": cliente.pk})
    assert list(respuesta.context["cuentas"]) == [cuenta_cliente]


def test_ficha_del_cliente_muestra_pestana_honorarios(client, usuario_administrador, cliente, cuenta_cliente):
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("clientes:detalle", args=[cliente.pk]))
    contenido = respuesta.content.decode()
    assert 'id="tab-honorarios"' in contenido
    assert list(respuesta.context["cuentas_cobro"]) == [cuenta_cliente]
    assert reverse("finanzas:honorario", args=[cliente.pk]) in contenido


# ---------------------------------------------------------------------------
# Honorario
# ---------------------------------------------------------------------------


def test_administrador_configura_honorario_por_servicio(
    client, usuario_administrador, cliente_con_servicios, servicio_contabilidad, servicio_nomina
):
    client.force_login(usuario_administrador)
    url = reverse("finanzas:honorario", args=[cliente_con_servicios.pk])
    assert client.get(url).status_code == 200
    respuesta = client.post(
        url,
        {
            "tipo": Honorario.POR_SERVICIO,
            f"servicio_{servicio_contabilidad.pk}": "600000",
            f"servicio_{servicio_nomina.pk}": "250000",
        },
    )
    assert respuesta.status_code == 302
    assert respuesta.url.endswith("#tab-honorarios")
    honorario = Honorario.objects.get(cliente=cliente_con_servicios)
    assert honorario.monto == Decimal("850000")
    assert honorario.usuario_actualizacion == usuario_administrador

    edicion = client.get(url)
    assert edicion.context["formulario"].initial[f"servicio_{servicio_nomina.pk}"] == Decimal("250000")


def test_honorario_invalido_vuelve_a_mostrar_formulario(client, usuario_administrador, cliente):
    client.force_login(usuario_administrador)
    respuesta = client.post(
        reverse("finanzas:honorario", args=[cliente.pk]), {"tipo": Honorario.FIJO_MENSUAL}
    )
    assert respuesta.status_code == 200
    assert not Honorario.objects.exists()


# ---------------------------------------------------------------------------
# Catálogos
# ---------------------------------------------------------------------------


def test_catalogos_crear_editar_y_eliminar(client, usuario_administrador):
    client.force_login(usuario_administrador)
    assert client.get(reverse("finanzas:catalogos")).status_code == 200
    assert client.get(reverse("finanzas:catalogo_crear", args=["metodos-pago"])).status_code == 200

    client.post(reverse("finanzas:catalogo_crear", args=["metodos-pago"]), {"nombre_metodo": "Nequi"})
    metodo = MetodoPago.objects.get(nombre_metodo="Nequi")

    client.post(
        reverse("finanzas:catalogo_editar", args=["metodos-pago", metodo.pk]), {"nombre_metodo": "Daviplata"}
    )
    metodo.refresh_from_db()
    assert metodo.nombre_metodo == "Daviplata"

    client.post(reverse("finanzas:catalogo_eliminar", args=["metodos-pago", metodo.pk]))
    assert not MetodoPago.objects.exists()


def test_catalogo_inexistente_devuelve_404(client, usuario_administrador):
    client.force_login(usuario_administrador)
    assert client.get(reverse("finanzas:catalogo_crear", args=["no-existe"])).status_code == 404


def test_catalogo_duplicado_muestra_error(client, usuario_administrador, concepto_revisoria):
    client.force_login(usuario_administrador)
    respuesta = client.post(
        reverse("finanzas:catalogo_crear", args=["conceptos"]),
        {"nombre_concepto": "Revisoría fiscal", "valor_sugerido": "0"},
    )
    assert respuesta.status_code == 200
    assert ConceptoFacturable.objects.count() == 1


def test_eliminar_elemento_usado_muestra_error(
    client, usuario_administrador, cliente, generar_cuenta, cuenta_bancaria
):
    generar_cuenta(cliente, cuenta_bancaria=cuenta_bancaria)
    client.force_login(usuario_administrador)
    respuesta = client.post(
        reverse("finanzas:catalogo_eliminar", args=["cuentas-bancarias", cuenta_bancaria.pk]), follow=True
    )
    assert "ya está usado" in respuesta.content.decode()
