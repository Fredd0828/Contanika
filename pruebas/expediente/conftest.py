"""Fixtures del módulo 9: expediente y bitácora por cliente."""

from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from aplicaciones.expediente.models import Anotacion


@pytest.fixture(autouse=True)
def media_root_temporal(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


def archivo_prueba(nombre="soporte.pdf", contenido=b"%PDF-contenido-de-prueba"):
    return SimpleUploadedFile(nombre, contenido, content_type="application/pdf")


@pytest.fixture
def anotacion_cliente(cliente, usuario_administrador):
    return Anotacion.objects.create(
        cliente=cliente,
        usuario=usuario_administrador,
        tipo_anotacion="Retención en la fuente",
        fecha=date(2026, 3, 10),
        contenido="Se presentó la retención en la fuente de febrero.",
    )


@pytest.fixture
def anotacion_cliente_junior(cliente_junior, usuario_administrador):
    return Anotacion.objects.create(
        cliente=cliente_junior,
        usuario=usuario_administrador,
        tipo_anotacion="Reunión",
        fecha=date(2026, 9, 1),
        contenido="Reunión de inicio con el cliente.",
    )
