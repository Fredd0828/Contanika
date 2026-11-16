"""La IP del visitante detrás del proxy del servidor (nginx)."""

from axes.helpers import get_client_ip_address
from django.test import RequestFactory, override_settings

from aplicaciones.comunes.vistas import direccion_ip


def _peticion(**meta):
    return RequestFactory().get("/", REMOTE_ADDR="127.0.0.1", **meta)


@override_settings(CONFIAR_EN_PROXY=True)
def test_axes_usa_la_ip_real_detras_del_proxy():
    """Sin esto, todos llegarían como 127.0.0.1 y un bloqueo afectaría a todos."""
    peticion = _peticion(HTTP_X_FORWARDED_FOR="203.0.113.7")
    assert get_client_ip_address(peticion) == "203.0.113.7"
    assert get_client_ip_address(peticion) == direccion_ip(peticion)


@override_settings(CONFIAR_EN_PROXY=True)
def test_dos_visitantes_detras_del_proxy_tienen_ip_distinta():
    uno = _peticion(HTTP_X_FORWARDED_FOR="203.0.113.7")
    otro = _peticion(HTTP_X_FORWARDED_FOR="198.51.100.20")
    assert get_client_ip_address(uno) != get_client_ip_address(otro)


@override_settings(CONFIAR_EN_PROXY=False)
def test_sin_proxy_se_ignora_la_cabecera():
    """En local nadie puede hacerse pasar por otra IP escribiendo la cabecera."""
    peticion = _peticion(HTTP_X_FORWARDED_FOR="203.0.113.7")
    assert get_client_ip_address(peticion) == "127.0.0.1"
