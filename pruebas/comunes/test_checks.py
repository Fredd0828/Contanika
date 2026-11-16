"""Pruebas de las revisiones de `check --deploy` sobre el correo y la dirección pública."""

from aplicaciones.comunes.checks import revisar_correo_y_direccion

SMTP = "django.core.mail.backends.smtp.EmailBackend"


def _ids(avisos):
    return {aviso.id for aviso in avisos}


def test_avisa_si_no_hay_servidor_de_correo(settings):
    settings.EMAIL_BACKEND = SMTP
    settings.EMAIL_HOST = ""
    settings.URL_SITIO = "https://contanika.midespacho.co"
    assert _ids(revisar_correo_y_direccion(None)) == {"contanika.W001"}


def test_avisa_si_la_direccion_es_la_del_equipo(settings):
    settings.EMAIL_BACKEND = SMTP
    settings.EMAIL_HOST = "smtp.gmail.com"
    settings.URL_SITIO = "http://127.0.0.1:8000"
    assert _ids(revisar_correo_y_direccion(None)) == {"contanika.W002"}


def test_sin_avisos_cuando_todo_esta_configurado(settings):
    settings.EMAIL_BACKEND = SMTP
    settings.EMAIL_HOST = "smtp.gmail.com"
    settings.URL_SITIO = "https://contanika.midespacho.co"
    assert revisar_correo_y_direccion(None) == []


def test_el_correo_por_consola_no_se_considera_un_error(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    settings.EMAIL_HOST = ""
    settings.URL_SITIO = "https://contanika.midespacho.co"
    assert revisar_correo_y_direccion(None) == []
