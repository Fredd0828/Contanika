"""Pruebas del endurecimiento de seguridad pr01 (cabeceras, cookies, archivos, robots y secretos)."""

import importlib
import io
import logging
import subprocess
from pathlib import Path

import pytest
from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import RequestFactory
from django.urls import reverse
from PIL import Image

from aplicaciones.comunes import formularios as comunes
from aplicaciones.comunes.middleware import MonitorConsultasMiddleware
from aplicaciones.comunes.vistas import direccion_ip
from aplicaciones.seguridad.models import ConfiguracionDespacho
from pruebas.conftest import CLAVE_PRUEBAS

pytestmark = pytest.mark.django_db

RAIZ = Path(settings.RUTA_BASE)


def _png(nombre="foto.png"):
    contenido = io.BytesIO()
    Image.new("RGB", (4, 4), "white").save(contenido, "PNG")
    return SimpleUploadedFile(nombre, contenido.getvalue(), content_type="image/png")


# ---------------------------------------------------------------------------
# 18. Cabeceras de seguridad · 15. Contenido · 19. HTTPS
# ---------------------------------------------------------------------------


def test_toda_respuesta_lleva_las_cabeceras_de_seguridad(client):
    cabeceras = client.get(reverse("seguridad:iniciar_sesion")).headers
    csp = cabeceras["Content-Security-Policy"]
    assert "default-src 'self'" in csp and "frame-ancestors 'none'" in csp and "object-src 'none'" in csp
    assert "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net" in csp
    assert cabeceras["X-Frame-Options"] == "DENY"
    assert cabeceras["X-Content-Type-Options"] == "nosniff"
    assert cabeceras["Referrer-Policy"] == "same-origin"
    assert cabeceras["Cross-Origin-Opener-Policy"] == "same-origin"
    assert "camera=()" in cabeceras["Permissions-Policy"]
    assert cabeceras["X-Robots-Tag"] == "noindex, nofollow"


def test_lo_que_viene_del_cdn_lleva_huella_de_integridad():
    for plantilla in ("base.html", "seguridad/panel.html", "reportes/reporte.html"):
        html = (RAIZ / "plantillas" / plantilla).read_text(encoding="utf-8")
        for linea in html.splitlines():
            if "cdn.jsdelivr.net" in linea:
                assert 'integrity="sha384-' in linea and 'crossorigin="anonymous"' in linea, linea.strip()


def test_la_csp_permite_los_origenes_que_usan_las_plantillas():
    csp = settings.CSP_DIRECTIVAS
    assert "https://cdn.jsdelivr.net" in csp["script-src"] and "https://cdn.jsdelivr.net" in csp["style-src"]
    assert (
        "https://fonts.googleapis.com" in csp["style-src"] and "https://fonts.gstatic.com" in csp["font-src"]
    )
    assert "https://wa.me" in csp["form-action"]


# ---------------------------------------------------------------------------
# 9. Cookies de sesión
# ---------------------------------------------------------------------------


def test_cookie_de_sesion_protegida_y_con_vencimiento(client, usuario_junior):
    respuesta = client.post(
        reverse("seguridad:iniciar_sesion"), {"username": usuario_junior.correo, "password": CLAVE_PRUEBAS}
    )
    galleta = respuesta.cookies[settings.SESSION_COOKIE_NAME]
    assert galleta["httponly"] and galleta["samesite"] == "Lax"
    assert not galleta["max-age"]  # se borra al cerrar el navegador
    assert client.session.get_expiry_age() == 8 * 60 * 60


# ---------------------------------------------------------------------------
# 12. Protección contra robots
# ---------------------------------------------------------------------------


def test_campo_senuelo_rechaza_a_los_robots_aunque_la_clave_sea_correcta(client, usuario_junior):
    url = reverse("seguridad:iniciar_sesion")
    assert 'name="sitio_web"' in client.get(url).content.decode()

    respuesta = client.post(
        url,
        {"username": usuario_junior.correo, "password": CLAVE_PRUEBAS, "sitio_web": "http://spam.example"},
    )

    assert respuesta.status_code == 200
    assert "_auth_user_id" not in client.session
    assert "Las credenciales no son correctas" in respuesta.content.decode()


def test_el_inicio_de_sesion_normal_sigue_funcionando(client, usuario_junior):
    respuesta = client.post(
        reverse("seguridad:iniciar_sesion"),
        {"username": usuario_junior.correo, "password": CLAVE_PRUEBAS, "sitio_web": ""},
    )
    assert respuesta.status_code == 302 and "_auth_user_id" in client.session


def test_robots_txt_pide_no_recorrer_el_sistema(client):
    """Los buscadores solo pueden leer la página web de inicio; el resto del sistema, no."""
    respuesta = client.get("/robots.txt")
    assert respuesta.status_code == 200
    assert respuesta.content.decode().splitlines() == ["User-agent: *", "Allow: /$", "Disallow: /"]


def test_solo_la_pagina_web_de_inicio_se_deja_indexar(client):
    assert client.get(reverse("seguridad:inicio")).headers["X-Robots-Tag"] == "index, follow"
    assert client.get(reverse("seguridad:iniciar_sesion")).headers["X-Robots-Tag"] == "noindex, nofollow"


# ---------------------------------------------------------------------------
# 6. Autenticación del servidor: archivos subidos
# ---------------------------------------------------------------------------


def _url_media(nombre):
    return reverse("media", kwargs={"ruta": nombre})


def test_los_archivos_subidos_exigen_sesion(client, usuario_junior, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    usuario_junior.foto = _png()
    usuario_junior.save()
    respuesta = client.get(_url_media(usuario_junior.foto.name))
    assert respuesta.status_code == 302 and reverse("seguridad:iniciar_sesion") in respuesta.url


def test_la_foto_la_ve_su_dueno_y_el_administrador_pero_no_otro_usuario(
    client, usuario_junior, usuario_senior, usuario_administrador, settings, tmp_path
):
    settings.MEDIA_ROOT = tmp_path
    usuario_junior.foto = _png()
    usuario_junior.save()
    url = _url_media(usuario_junior.foto.name)
    for usuario, esperado in ((usuario_junior, 200), (usuario_administrador, 200), (usuario_senior, 404)):
        client.force_login(usuario)
        respuesta = client.get(url)
        assert respuesta.status_code == esperado, usuario
    client.force_login(usuario_junior)
    assert client.get(url).headers["Cache-Control"] == "private, max-age=300"


def test_el_membrete_lo_ve_cualquier_usuario_con_sesion(client, usuario_junior, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    despacho = ConfiguracionDespacho.objects.create(nombre_despacho="Befrec", membrete=_png("membrete.png"))
    client.force_login(usuario_junior)
    assert client.get(_url_media(despacho.membrete.name)).status_code == 200


@pytest.mark.parametrize(
    "ruta",
    [
        "documentos/2026/10/certificado.pdf",
        "cuentas_cobro/2026/10/cuenta.pdf",
        "adjuntos/hallazgos/2026/10/soporte.pdf",
        "fotos/../../.env",
        "despacho/../../.env",
    ],
)
def test_lo_demas_no_se_entrega_por_direccion_ni_al_administrador(
    client, usuario_administrador, settings, tmp_path, ruta
):
    settings.MEDIA_ROOT = tmp_path
    destino = tmp_path / ruta
    if ".." not in ruta:
        destino.parent.mkdir(parents=True)
        destino.write_bytes(b"%PDF-privado")
    client.force_login(usuario_administrador)
    assert client.get(f"/{settings.MEDIA_URL.lstrip('/')}{ruta}").status_code == 404


# ---------------------------------------------------------------------------
# 16. Subida de archivos
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("nombre", "contenido"),
    [
        ("soporte.pdf", b"%PDF-1.7 contenido"),
        ("soporte.PDF", b"%PDF-1.7 contenido"),
        ("libro.xlsx", b"PK\x03\x04 contenido"),
        ("carta.docx", b"PK\x03\x04 contenido"),
        ("viejo.xls", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1 contenido"),
        ("foto.jpg", b"\xff\xd8\xff\xe0 contenido"),
        ("foto.png", b"\x89PNG\r\n\x1a\n contenido"),
    ],
)
def test_adjunto_con_contenido_real_se_acepta(nombre, contenido):
    archivo = SimpleUploadedFile(nombre, contenido)
    assert comunes.validar_archivo_adjunto(archivo) is archivo
    assert archivo.tell() == 0  # queda listo para guardarse


@pytest.mark.parametrize(
    ("nombre", "contenido"),
    [
        ("programa.pdf", b"MZ\x90\x00 ejecutable de Windows"),
        ("pagina.png", b"<html><script>alert(1)</script></html>"),
        ("macro.xlsx", b"\xd0\xcf\x11\xe0 no es un xlsx"),
        ("guion.jpg", b"#!/bin/bash\nrm -rf /"),
        ("vacio.pdf", b""),
    ],
)
def test_adjunto_disfrazado_con_otra_extension_se_rechaza(nombre, contenido):
    with pytest.raises(forms.ValidationError, match="no corresponde"):
        comunes.validar_archivo_adjunto(SimpleUploadedFile(nombre, contenido))


@pytest.mark.parametrize("nombre", ["virus.exe", "pagina.html", "imagen.svg", "guion.php", "sin_extension"])
def test_adjunto_con_extension_no_permitida_se_rechaza(nombre):
    with pytest.raises(forms.ValidationError, match="formato no permitido"):
        comunes.validar_archivo_adjunto(SimpleUploadedFile(nombre, b"%PDF-contenido"))


def test_excel_de_importacion_valida_extension_contenido_y_tamano():
    assert comunes.validar_excel_subido(SimpleUploadedFile("clientes.xlsx", b"PK\x03\x04 libro"))
    for nombre, contenido, mensaje in (
        ("clientes.csv", b"a,b", "formato Excel"),
        ("clientes.xlsx", b"no es un libro", "no corresponde"),
        ("clientes.xlsx", b"PK\x03\x04" + b"0" * (5 * 1024 * 1024), "no debe superar"),
    ):
        with pytest.raises(forms.ValidationError, match=mensaje):
            comunes.validar_excel_subido(SimpleUploadedFile(nombre, contenido))


def test_imagen_subida_solo_jpg_o_png_y_con_tope_de_tamano():
    assert comunes.validar_imagen_subida(_png(), "perfil", 2 * 1024 * 1024)
    gif = SimpleUploadedFile("foto.gif", b"GIF89a", content_type="image/gif")
    with pytest.raises(forms.ValidationError, match="JPG o PNG"):
        comunes.validar_imagen_subida(gif, "perfil", 2 * 1024 * 1024)
    grande = SimpleUploadedFile("foto.png", b"0" * (3 * 1024 * 1024), content_type="image/png")
    with pytest.raises(forms.ValidationError, match="no debe superar los 2 MB"):
        comunes.validar_imagen_subida(grande, "perfil", 2 * 1024 * 1024)
    assert comunes.validar_imagen_subida(None, "perfil", 1) is None


def test_limites_de_subida_configurados():
    assert settings.DATA_UPLOAD_MAX_MEMORY_SIZE == 5 * 1024 * 1024
    assert settings.DATA_UPLOAD_MAX_NUMBER_FILES == 10
    assert settings.FILE_UPLOAD_PERMISSIONS == 0o640  # sin permiso de ejecución


# ---------------------------------------------------------------------------
# 17. Límite de respuestas y de peticiones
# ---------------------------------------------------------------------------


def test_el_enlace_publico_del_pdf_limita_las_peticiones_por_ip(client):
    cache.clear()
    url = reverse("finanzas:pdf_publico", kwargs={"token": "token-inventado"})
    codigos = [client.get(url).status_code for _ in range(21)]
    assert codigos[:20] == [404] * 20  # enlace inválido, pero dentro del tope
    assert codigos[20] == 429
    assert client.get(url).headers["Retry-After"] == "60"
    # Otra dirección IP tiene su propio tope.
    assert client.get(url, REMOTE_ADDR="10.0.0.9").status_code == 404
    cache.clear()


def test_la_ip_solo_se_toma_del_proxy_si_se_confia_en_el(settings):
    peticion = RequestFactory().get("/", REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="203.0.113.7, 10.0.0.1")
    settings.CONFIAR_EN_PROXY = False
    assert direccion_ip(peticion) == "10.0.0.1"
    settings.CONFIAR_EN_PROXY = True
    assert direccion_ip(peticion) == "203.0.113.7"


def test_la_api_tiene_paginacion_y_limite_de_peticiones():
    api = settings.REST_FRAMEWORK
    assert api["PAGE_SIZE"] == 25
    assert set(api["DEFAULT_THROTTLE_RATES"]) == {"anon", "user"}
    assert api["DEFAULT_PERMISSION_CLASSES"] == ["rest_framework.permissions.IsAuthenticated"]


# ---------------------------------------------------------------------------
# 13. Monitoreo de consultas
# ---------------------------------------------------------------------------


def _peticion_con_consultas(cantidad):
    def vista(_peticion):
        with connection.cursor() as cursor:
            for _ in range(cantidad):
                cursor.execute("SELECT 1")
        return "respuesta"

    return MonitorConsultasMiddleware(vista)(RequestFactory().get("/clientes/"))


def test_registra_las_consultas_lentas_sin_guardar_parametros(settings, caplog):
    settings.BD_CONSULTA_LENTA_MS = 0  # toda consulta cuenta como lenta
    with caplog.at_level(logging.WARNING, logger="contanika.consultas"):
        logging.getLogger("contanika.consultas").propagate = True
        try:
            assert _peticion_con_consultas(1) == "respuesta"
        finally:
            logging.getLogger("contanika.consultas").propagate = False
    assert any("Consulta lenta" in r.message and "GET /clientes/" in r.message for r in caplog.records)


def test_registra_las_peticiones_con_demasiadas_consultas(settings, caplog):
    settings.BD_MAXIMO_CONSULTAS = 3
    registro = logging.getLogger("contanika.consultas")
    registro.propagate = True
    try:
        with caplog.at_level(logging.WARNING, logger="contanika.consultas"):
            _peticion_con_consultas(5)
            assert any("Petición con 5 consultas" in r.message for r in caplog.records)
            caplog.clear()
            _peticion_con_consultas(2)
            assert not caplog.records
    finally:
        registro.propagate = False


def test_los_eventos_de_seguridad_van_a_su_registro():
    registros = settings.LOGGING["loggers"]
    assert {"django.security", "django.request", "axes", "contanika.consultas"} <= set(registros)
    assert "seguridad" in registros["axes"]["handlers"]


# ---------------------------------------------------------------------------
# 1, 2 y 3. Secretos, repositorio y usuario de la base de datos
# ---------------------------------------------------------------------------


def _git(*argumentos):
    try:
        proceso = subprocess.run(  # noqa: S603
            ["git", *argumentos], cwd=RAIZ, capture_output=True, text=True, timeout=30, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        pytest.skip("git no está disponible")
    return proceso


@pytest.mark.parametrize(
    "archivo", [".env", "CREDENCIALES_PRUEBA.md", "registros/seguridad.log", "media/x.pdf"]
)
def test_los_archivos_con_secretos_estan_fuera_del_repositorio(archivo):
    assert _git("check-ignore", "-q", archivo).returncode == 0, f"{archivo} no está en .gitignore"
    assert _git("ls-files", "--error-unmatch", archivo).returncode != 0, f"{archivo} está versionado"


def test_ningun_archivo_versionado_trae_contrasenas_escritas():
    patron = (
        r"Contanika2026|(SECRET_KEY|BD_CLAVE|CORREO_CLAVE|SUPABASE_CLAVE_SERVICIO)\s*=\s*[A-Za-z0-9+/_-]{12,}"
    )
    proceso = _git("grep", "-n", "-I", "-E", patron, "--", ".", ":!pruebas/seguridad/test_pr01.py")
    hallazgos = [linea for linea in proceso.stdout.splitlines() if "clave-secreta-de-desarrollo" not in linea]
    assert not hallazgos, "Secretos en el repositorio:\n" + "\n".join(hallazgos)


VARIABLES_PRODUCCION = {
    "SECRET_KEY": "k" + "aB3$xY9!" * 8,
    "CREDENCIAL_CLAVE_CIFRADO": "tl0BjzeE61CqzeDjKd8FH6Qs8ayUmd4AumYKFngCh8o=",
    "ALLOWED_HOSTS": "contanika.example",
    "BD_USUARIO": "contanika_app",
    "BD_CLAVE": "una-clave",
    "BD_HOST": "bd.example",
}


def _cargar_produccion(monkeypatch, **cambios):
    for nombre, valor in {**VARIABLES_PRODUCCION, **cambios}.items():
        monkeypatch.setenv(nombre, valor)
    import config.settings.produccion as produccion

    return importlib.reload(produccion)


def test_produccion_arranca_con_secretos_validos_y_https_obligatorio(monkeypatch):
    produccion = _cargar_produccion(monkeypatch)
    # Cargar producción no debe tocar la configuración en uso (comparten base.py).
    assert settings.DATABASES["default"]["HOST"] != "bd.example"
    assert "DEFAULT_RENDERER_CLASSES" not in settings.REST_FRAMEWORK
    assert produccion.DEBUG is False and produccion.SECURE_SSL_REDIRECT is True
    assert produccion.SECURE_HSTS_SECONDS >= 31536000
    assert produccion.SESSION_COOKIE_SECURE and produccion.CSRF_COOKIE_SECURE
    assert produccion.SESSION_COOKIE_NAME.startswith("__Host-")
    assert produccion.DATABASES["default"]["OPTIONS"]["sslmode"] == "require"
    assert produccion.DATABASES["default"]["USER"] == "contanika_app"


@pytest.mark.parametrize(
    ("variable", "valor", "mensaje"),
    [
        ("SECRET_KEY", "clave-secreta-de-desarrollo-solo-local", "SECRET_KEY"),
        ("SECRET_KEY", "corta", "SECRET_KEY"),
        ("CREDENCIAL_CLAVE_CIFRADO", "", "CREDENCIAL_CLAVE_CIFRADO"),
        ("ALLOWED_HOSTS", "", "ALLOWED_HOSTS"),
        ("BD_USUARIO", "postgres", "postgres"),
        ("BD_USUARIO", "postgres.abcdefghijklmnop", "postgres"),
    ],
)
def test_produccion_no_arranca_con_secretos_de_desarrollo(monkeypatch, variable, valor, mensaje):
    with pytest.raises(ImproperlyConfigured, match=mensaje):
        _cargar_produccion(monkeypatch, **{variable: valor})


# ---------------------------------------------------------------------------
# 3 y 4. Scripts de la base de datos · 20. Dependencias
# ---------------------------------------------------------------------------


def test_script_de_roles_no_da_privilegios_de_mas():
    sql = (RAIZ / "scripts/bd/03_rol_aplicacion.sql").read_text(encoding="utf-8")
    assert sql.count("NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS") == 2
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO contanika_app" in sql
    assert "GRANT ALL" not in sql and "CAMBIE_ESTA_CLAVE" in sql
    # Sin esto, en Supabase (`postgres` no es superusuario) fallan este script y el de RLS.
    assert "GRANT contanika_dueno TO CURRENT_USER" in sql


def test_script_de_rls_cubre_todas_las_tablas_y_cierra_la_api_publica():
    sql = (RAIZ / "scripts/bd/04_activar_rls.sql").read_text(encoding="utf-8")
    assert "ENABLE ROW LEVEL SECURITY" in sql and "FROM pg_tables WHERE schemaname = 'public'" in sql
    assert "CREATE POLICY acceso_aplicacion" in sql and "ARRAY['anon', 'authenticated']" in sql


def test_el_escaneo_de_dependencias_esta_automatizado():
    assert "pip-audit" in (RAIZ / "scripts/calidad.sh").read_text(encoding="utf-8")
    dependabot = (RAIZ / ".github/dependabot.yml").read_text(encoding="utf-8")
    assert "package-ecosystem: pip" in dependabot and "interval: weekly" in dependabot
    flujo = (RAIZ / ".github/workflows/seguridad.yml").read_text(encoding="utf-8")
    assert "pip-audit" in flujo and "bandit" in flujo
