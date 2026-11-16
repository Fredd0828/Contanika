"""
Revisiones propias de `python gestionar.py check --deploy`.

Avisan de lo que impide que el sistema funcione bien en un servidor aunque
arranque: sin correo saliente no llegan los enlaces de acceso, las alertas
ni las cuentas de cobro, y con la dirección local los enlaces de los correos
no abren fuera del equipo. La guía es `documentacion/CONFIGURAR_CORREO.md`.
"""

from django.conf import settings
from django.core.checks import Tags, Warning, register

DIRECCIONES_LOCALES = ("127.0.0.1", "localhost")


@register(Tags.security, deploy=True)
def revisar_correo_y_direccion(app_configs, **kwargs):
    avisos = []
    if settings.EMAIL_BACKEND.endswith("smtp.EmailBackend") and not settings.EMAIL_HOST:
        avisos.append(
            Warning(
                "No hay servidor de correo configurado (CORREO_HOST vacío): no saldrán los enlaces "
                "de acceso, las alertas ni las cuentas de cobro.",
                hint="Siga documentacion/CONFIGURAR_CORREO.md y complete CORREO_* en el .env del servidor.",
                id="contanika.W001",
            )
        )
    if any(local in settings.URL_SITIO for local in DIRECCIONES_LOCALES):
        avisos.append(
            Warning(
                f"URL_SITIO es «{settings.URL_SITIO}»: los enlaces de los correos no abrirán fuera "
                "de este equipo.",
                hint="Escriba en el .env del servidor la dirección pública, por ejemplo https://contanika.midespacho.co.",
                id="contanika.W002",
            )
        )
    return avisos
