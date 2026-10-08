"""Fixtures del módulo 7: comunicaciones integradas."""

from datetime import datetime

import pytest
from django.utils import timezone

from aplicaciones.comunicaciones.models import Comunicacion


def momento(anio, mes, dia, hora=10):
    return timezone.make_aware(datetime(anio, mes, dia, hora, 0))


@pytest.fixture
def comunicacion_automatica(cliente, usuario_administrador):
    """Correo enviado por el sistema desde Honorarios."""
    return Comunicacion.objects.create(
        cliente=cliente,
        canal=Comunicacion.CORREO,
        tipo=Comunicacion.AUTOMATICA,
        contenido_resumen="Cuenta de cobro No. 1 por $ 1.100.000",
        usuario=usuario_administrador,
        modulo_origen="Honorarios",
        fecha_hora=momento(2026, 9, 15),
    )


@pytest.fixture
def comunicacion_manual_junior(cliente_junior, usuario_senior):
    """Llamada registrada a mano con un cliente del Contador Junior."""
    return Comunicacion.objects.create(
        cliente=cliente_junior,
        canal=Comunicacion.LLAMADA,
        tipo=Comunicacion.MANUAL,
        contenido_resumen="Se acordó enviar los extractos el viernes.",
        usuario=usuario_senior,
        modulo_origen=Comunicacion.ORIGEN_MANUAL,
        fecha_hora=momento(2026, 9, 20),
    )
