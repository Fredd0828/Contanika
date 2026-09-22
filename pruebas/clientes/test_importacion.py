"""Pruebas de la importación masiva de clientes desde Excel (RQF013)."""

from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from openpyxl import Workbook

from aplicaciones.clientes.importacion import COLUMNAS
from aplicaciones.clientes.models import Cliente

pytestmark = pytest.mark.django_db

ENCABEZADOS = [columna[1] for columna in COLUMNAS]
FILA_VALIDA = [
    "Panadería El Trigal SAS",
    "901222333",
    "Jurídica",
    "Régimen ordinario",
    "Sí",
    "Bogotá D.C.",
    "Bogotá D.C.",
    "contacto@trigal.co",
    "",
    "Declaración de renta; IVA",
    "Soacha",
]


def _archivo_excel(filas):
    """Construye un archivo .xlsx en memoria con la plantilla y las filas dadas."""
    libro = Workbook()
    hoja = libro.active
    hoja.append(ENCABEZADOS)
    for fila in filas:
        hoja.append(fila)
    buffer = BytesIO()
    libro.save(buffer)
    return SimpleUploadedFile(
        "clientes.xlsx",
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def test_descargar_plantilla(client, usuario_administrador):
    """El Administrador descarga la plantilla en formato Excel."""
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("clientes:plantilla"))
    assert respuesta.status_code == 200
    assert "spreadsheetml" in respuesta["Content-Type"]
    assert "attachment" in respuesta["Content-Disposition"]


def test_junior_no_puede_descargar_plantilla(client, usuario_junior):
    """El Contador Junior no puede descargar la plantilla."""
    client.force_login(usuario_junior)
    assert client.get(reverse("clientes:plantilla")).status_code == 403


def test_junior_no_puede_importar(client, usuario_junior):
    """El Contador Junior no puede entrar al formulario de importación."""
    client.force_login(usuario_junior)
    assert client.get(reverse("clientes:importar")).status_code == 403


def test_importar_archivo_valido(client, usuario_senior):
    """Un archivo correcto crea los clientes con servicios y municipios."""
    client.force_login(usuario_senior)
    respuesta = client.post(
        reverse("clientes:importar"),
        {"archivo": _archivo_excel([FILA_VALIDA])},
    )
    assert respuesta.status_code == 200
    creado = Cliente.objects.get(nit_cedula="901222333")
    assert creado.responsable == usuario_senior
    assert creado.servicios.count() == 2
    assert creado.municipios_adicionales.filter(municipio="Soacha").exists()


def test_importacion_informa_filas_con_error(client, usuario_senior):
    """Las filas inválidas no se importan y se informa el motivo."""
    fila_sin_nit = ["Cliente sin NIT", "", "Natural", "", "No", "", "", "", "", "", ""]
    client.force_login(usuario_senior)
    respuesta = client.post(
        reverse("clientes:importar"),
        {"archivo": _archivo_excel([FILA_VALIDA, fila_sin_nit])},
    )
    contenido = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert Cliente.objects.filter(nit_cedula="901222333").exists()
    assert Cliente.objects.count() == 1
    assert "Fila 3" in contenido
    assert "Falta el NIT" in contenido


def test_no_importa_nit_duplicado_del_sistema(client, usuario_senior, cliente):
    """No se importa una fila cuyo NIT ya existe en el sistema."""
    fila = list(FILA_VALIDA)
    fila[1] = cliente.nit_cedula
    client.force_login(usuario_senior)
    respuesta = client.post(
        reverse("clientes:importar"),
        {"archivo": _archivo_excel([fila])},
    )
    assert respuesta.status_code == 200
    assert "Ya existe un cliente" in respuesta.content.decode()
    assert Cliente.objects.count() == 1


def test_rechaza_archivo_con_extension_incorrecta(client, usuario_senior):
    """El formulario rechaza archivos que no sean .xlsx."""
    client.force_login(usuario_senior)
    archivo = SimpleUploadedFile("clientes.csv", b"contenido", content_type="text/csv")
    respuesta = client.post(reverse("clientes:importar"), {"archivo": archivo})
    assert respuesta.status_code == 200
    assert "formato Excel" in respuesta.content.decode()
    assert Cliente.objects.count() == 0
