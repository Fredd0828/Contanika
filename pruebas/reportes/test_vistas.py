"""Pruebas de vistas, permisos y seguridad del módulo 10 y de la sección de ayuda."""

import pytest
from django.urls import reverse
from django.utils import timezone

from aplicaciones.reportes.models import DescargaReporte, PermisoReporteRol, Reporte
from aplicaciones.seguridad.models import Modulo, PermisoRolModulo

pytestmark = pytest.mark.django_db


def _url(slug):
    return reverse("reportes:reporte", kwargs={"slug": slug})


# ---------------------------------------------------------------------------
# Acceso
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("url", ["/reportes/", "/reportes/clientes/", "/ayuda/"])
def test_requieren_sesion(client, url):
    respuesta = client.get(url)
    assert respuesta.status_code == 302
    assert reverse("seguridad:iniciar_sesion") in respuesta.url


def test_modulo_inhabilitado_bloquea(client, usuario_senior):
    modulo = Modulo.objects.create(codigo_modulo=Modulo.MOD10_REPORTES, nombre_modulo="Reportes")
    PermisoRolModulo.objects.create(rol=usuario_senior.rol, modulo=modulo, habilitado=False)
    client.force_login(usuario_senior)
    assert client.get(reverse("reportes:inicio")).status_code == 403


def test_reporte_oculto_no_aparece_ni_abre(client, usuario_junior):
    reporte = Reporte.objects.create(nombre_reporte=Reporte.INGRESOS, modulo_origen="Honorarios")
    PermisoReporteRol.objects.create(reporte=reporte, rol=usuario_junior.rol, habilitado=False)
    client.force_login(usuario_junior)
    nombres = [d.nombre for d in client.get(reverse("reportes:inicio")).context["reportes"]]
    assert Reporte.INGRESOS not in nombres and len(nombres) == 5
    assert client.get(_url("ingresos")).status_code == 403


def test_reporte_inexistente_es_404(client, usuario_administrador):
    client.force_login(usuario_administrador)
    assert client.get(_url("no-existe")).status_code == 404


@pytest.mark.parametrize("nombre_url", ["reportes:visibilidad", "reportes:descargas"])
def test_configuracion_solo_administrador(client, usuario_senior, nombre_url):
    client.force_login(usuario_senior)
    assert client.get(reverse(nombre_url)).status_code == 403


# ---------------------------------------------------------------------------
# Vista previa y descargas
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "slug", ["clientes", "vencimientos", "cartera", "cuentas-cobro", "tareas", "ingresos"]
)
def test_vista_previa_de_cada_reporte(client, usuario_administrador, datos_reportes, slug):
    client.force_login(usuario_administrador)
    respuesta = client.get(_url(slug))
    assert respuesta.status_code == 200
    assert respuesta.context["resultado"] is not None


def test_grafico_se_entrega_escapado(client, usuario_administrador, datos_reportes, cliente):
    cliente.nombre_razon_social = "</script><script>alert(1)</script>"
    cliente.save()
    client.force_login(usuario_administrador)
    contenido = client.get(_url("cartera")).content.decode()
    assert "</script><script>alert(1)" not in contenido
    assert 'id="datos-grafico"' in contenido


def test_descarga_excel_registra_quien_y_filtros(client, usuario_administrador, datos_reportes):
    client.force_login(usuario_administrador)
    respuesta = client.get(_url("vencimientos"), {"ambito": "Nacional", "formato": "Excel"})
    assert respuesta.status_code == 200
    assert respuesta["Content-Type"].startswith("application/vnd.openxmlformats")
    assert "reporte_vencimientos_" in respuesta["Content-Disposition"]
    descarga = DescargaReporte.objects.get()
    assert descarga.usuario == usuario_administrador
    assert descarga.formato == DescargaReporte.EXCEL
    assert descarga.reporte.nombre_reporte == Reporte.VENCIMIENTOS
    assert descarga.filtros == "Ámbito: Nacional"


def test_descarga_pdf(client, usuario_administrador, datos_reportes):
    client.force_login(usuario_administrador)
    respuesta = client.get(_url("ingresos"), {"formato": "PDF"})
    assert respuesta["Content-Type"] == "application/pdf"
    assert respuesta.content.startswith(b"%PDF")
    assert DescargaReporte.objects.get().filtros == ""


def test_filtros_invalidos_no_descargan(client, usuario_administrador):
    client.force_login(usuario_administrador)
    respuesta = client.get(_url("tareas"), {"desde": "2026-12-01", "hasta": "2026-01-01", "formato": "PDF"})
    assert respuesta.status_code == 200
    assert respuesta.context["resultado"] is None
    assert not DescargaReporte.objects.exists()


def test_junior_no_puede_filtrar_por_cliente_ajeno(client, usuario_junior, datos_reportes, cliente):
    client.force_login(usuario_junior)
    respuesta = client.get(_url("tareas"), {"cliente": cliente.pk})
    assert respuesta.context["resultado"] is None  # el cliente no está entre las opciones válidas


def test_historial_de_descargas(client, usuario_administrador, datos_reportes):
    client.force_login(usuario_administrador)
    client.get(_url("clientes"), {"formato": "PDF"})
    respuesta = client.get(reverse("reportes:descargas"))
    assert list(respuesta.context["descargas"]) == list(DescargaReporte.objects.all())


# ---------------------------------------------------------------------------
# Visibilidad por rol
# ---------------------------------------------------------------------------


def test_guardar_visibilidad(client, usuario_administrador, usuario_junior):
    reporte = Reporte.objects.create(nombre_reporte=Reporte.CARTERA, modulo_origen="Honorarios")
    client.force_login(usuario_administrador)
    client.post(reverse("reportes:visibilidad"), {})  # todo desmarcado
    assert not PermisoReporteRol.objects.get(reporte=reporte, rol=usuario_junior.rol).habilitado
    assert PermisoReporteRol.objects.get(reporte=reporte, rol=usuario_administrador.rol).habilitado


def test_visibilidad_sin_csrf_es_rechazada(usuario_administrador):
    from django.test import Client

    cliente_http = Client(enforce_csrf_checks=True)
    cliente_http.force_login(usuario_administrador)
    assert cliente_http.post(reverse("reportes:visibilidad"), {}).status_code == 403


# ---------------------------------------------------------------------------
# Ayuda (HU053)
# ---------------------------------------------------------------------------


def test_ayuda_disponible_para_todos_y_enlazada_en_la_barra(client, usuario_junior):
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("seguridad:ayuda"))
    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert "Preguntas frecuentes" in contenido and "10. Reportes" in contenido
    assert reverse("seguridad:ayuda") in client.get(reverse("seguridad:perfil")).content.decode()


def test_pantalla_de_visibilidad_muestra_la_matriz(client, usuario_administrador, usuario_junior):
    reporte = Reporte.objects.create(nombre_reporte=Reporte.TAREAS, modulo_origen="Tablero Kanban")
    PermisoReporteRol.objects.create(reporte=reporte, rol=usuario_junior.rol, habilitado=False)
    client.force_login(usuario_administrador)
    filas = client.get(reverse("reportes:visibilidad")).context["filas"]
    celdas = {c["rol"].nombre_rol: c for c in filas[0]["celdas"]}
    assert celdas["Contador Junior"]["habilitado"] is False
    assert celdas["Administrador"]["fijo"] is True


def test_historial_de_descargas_filtra_por_reporte_usuario_y_fecha(
    client, usuario_administrador, datos_reportes
):
    client.force_login(usuario_administrador)
    client.get(_url("clientes"), {"formato": "PDF"})
    client.get(_url("tareas"), {"formato": "Excel"})
    tareas = Reporte.objects.get(nombre_reporte=Reporte.TAREAS)
    # El filtro usa la fecha local (Bogotá), no la de UTC: de noche difieren.
    hoy = timezone.localtime(DescargaReporte.objects.first().fecha_hora).date().isoformat()
    filtros = {"reporte": tareas.pk, "usuario": usuario_administrador.pk, "desde": hoy, "hasta": hoy}
    respuesta = client.get(reverse("reportes:descargas"), filtros)
    assert [d.reporte for d in respuesta.context["descargas"]] == [tareas]
