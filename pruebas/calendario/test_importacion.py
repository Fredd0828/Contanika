"""Pruebas de la importación masiva de la tabla DIAN y del comando de carga."""

from datetime import date
from io import BytesIO

import pytest
from django.core.management import call_command
from django.urls import reverse
from openpyxl import Workbook, load_workbook

from aplicaciones.calendario.importacion import (
    _expandir_dos_digitos,
    _parse_fecha,
    _parse_mes,
    anio_calendario,
    generar_plantilla_dian,
    importar_dian,
)
from aplicaciones.calendario.models import TablaReferenciaDian, Vencimiento
from aplicaciones.calendario.servicios import generar_vencimientos_cliente
from aplicaciones.clientes.models import ClienteObligacion, ObligacionTributaria

pytestmark = pytest.mark.django_db


def _excel_con_filas(filas):
    """Construye un Excel en memoria con las filas dadas."""
    libro = Workbook()
    hoja = libro.active
    hoja.append(["tipo_obligacion", "grupo_nit", "fecha_vencimiento", "periodo_gravable"])
    for fila in filas:
        hoja.append(fila)
    buffer = BytesIO()
    libro.save(buffer)
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------------------
# Plantilla descargable
# ---------------------------------------------------------------------------


def _filas(hoja):
    """Filas de datos de una hoja de la plantilla (desde la fila 5)."""
    return [fila for fila in hoja.iter_rows(min_row=5, values_only=True) if fila[0]]


def _fila(hoja, tipo, periodo):
    return next(f for f in _filas(hoja) if f[0] == tipo and f[1] == periodo)


def test_plantilla_dian_tiene_la_forma_del_pdf():
    """Hojas por último dígito, por dos dígitos, catálogo e instrucciones."""
    libro = load_workbook(generar_plantilla_dian(2026))
    assert libro.sheetnames == ["Por último dígito", "Por dos dígitos", "Obligaciones", "Instrucciones"]
    encabezado = [c.value for c in libro["Por último dígito"][4]]
    assert encabezado == [
        "Obligación",
        "Período",
        "Detalle",
        "Mes",
        "Año",
        *list("1234567890"),
        "Todos los NIT",
    ]


def test_plantilla_de_un_anio_cargado_sale_llena():
    call_command("cargar_calendario_dian_2026")
    libro = load_workbook(generar_plantilla_dian(2026))
    hoja = libro["Por último dígito"]

    iva = _fila(hoja, "IVA bimestral", "2026-01")
    assert iva[2] == "enero - febrero 2026"
    assert iva[3:6] == ("marzo", 2026, 10)
    assert iva[14] == 24  # dígito 0
    gasolina_diciembre = _fila(hoja, "Gasolina y ACPM", "2026-12")
    assert gasolina_diciembre[3:5] == ("enero", 2027)
    assert gasolina_diciembre[15] == 18  # Todos los NIT

    renta_pn = [f for f in _filas(libro["Por dos dígitos"]) if f[0] == "Renta personas naturales"]
    assert len(renta_pn) == 50
    assert renta_pn[0][3:] == ("01-02", "agosto", 2026, 12)
    assert renta_pn[-1][3:] == ("99-00", "octubre", 2026, 26)


def test_plantilla_de_un_anio_nuevo_sale_en_blanco():
    """El año siguiente copia la estructura, corre los períodos y deja los días vacíos."""
    call_command("cargar_calendario_dian_2026")
    libro = load_workbook(generar_plantilla_dian(2027))
    hoja = libro["Por último dígito"]

    iva = _fila(hoja, "IVA bimestral", "2027-01")
    assert iva[3:5] == ("marzo", 2027)
    assert all(dia is None for dia in iva[5:])
    assert _fila(hoja, "Retención en la fuente", "2027-12")[3:5] == ("enero", 2028)
    assert not [f for f in _filas(hoja) if f[1].startswith("2026-")]


def test_plantilla_sin_nada_cargado_usa_el_calendario_2026():
    libro = load_workbook(generar_plantilla_dian())
    assert _fila(libro["Por último dígito"], "Impuesto al patrimonio", "2026-2C")[15] == 14


def test_plantilla_incluye_filas_en_blanco_para_la_exogena():
    call_command("cargar_calendario_dian_2026")
    libro = load_workbook(generar_plantilla_dian(2026))
    assert _fila(libro["Por último dígito"], "Exógena distrital", "2025")[5:] == (None,) * 11
    assert _fila(libro["Por dos dígitos"], "Exógena nacional", "2025")[6] is None


def test_subir_la_plantilla_sin_tocarla_no_cambia_nada():
    call_command("cargar_calendario_dian_2026")
    resultado = importar_dian(generar_plantilla_dian(2026))
    assert resultado["errores"] == []
    assert resultado["sin_cambios"] == 704
    assert resultado["cargadas"] == resultado["omitidas"] == resultado["eliminadas"] == 0


def _llenar(buffer, cambios):
    """Escribe valores en la plantilla: {(hoja, tipo, periodo, columna): valor}."""
    libro = load_workbook(buffer)
    for (nombre, tipo, periodo, columna), valor in cambios.items():
        hoja = libro[nombre]
        numero = next(
            fila[0].row
            for fila in hoja.iter_rows(min_row=5)
            if fila[0].value == tipo and fila[1].value == periodo
        )
        hoja.cell(row=numero, column=columna).value = valor
    salida = BytesIO()
    libro.save(salida)
    salida.seek(0)
    return salida


def test_cargar_el_anio_nuevo_desde_la_plantilla():
    call_command("cargar_calendario_dian_2026")
    plantilla = generar_plantilla_dian(2027)
    llena = _llenar(
        plantilla,
        {
            ("Por último dígito", "IVA bimestral", "2027-01", 6): 9,  # dígito 1
            ("Por último dígito", "IVA bimestral", "2027-01", 15): 23,  # dígito 0
            ("Por último dígito", "Gasolina y ACPM", "2027-01", 16): 12,  # Todos los NIT
        },
    )
    resultado = importar_dian(llena)

    assert resultado["errores"] == []
    assert resultado["cargadas"] == 3
    assert TablaReferenciaDian.objects.get(
        tipo_obligacion="IVA bimestral", grupo_nit="0", periodo_gravable="2027-01"
    ).fecha_vencimiento == date(2027, 3, 23)
    assert TablaReferenciaDian.objects.get(
        tipo_obligacion="Gasolina y ACPM", grupo_nit="TODOS", periodo_gravable="2027-01"
    ).fecha_vencimiento == date(2027, 2, 12)
    # 2026 sigue intacto.
    assert TablaReferenciaDian.objects.filter(periodo_gravable__startswith="2026").count() > 500


def test_corregir_una_fecha_desde_la_plantilla():
    call_command("cargar_calendario_dian_2026")
    llena = _llenar(generar_plantilla_dian(2026), {("Por último dígito", "IVA bimestral", "2026-01", 6): 11})
    resultado = importar_dian(llena)
    assert resultado["omitidas"] == 1
    assert TablaReferenciaDian.objects.get(
        tipo_obligacion="IVA bimestral", grupo_nit="1", periodo_gravable="2026-01"
    ).fecha_vencimiento == date(2026, 3, 11)


def test_la_plantilla_reporta_cada_error_con_su_lugar():
    call_command("cargar_calendario_dian_2026")
    llena = _llenar(
        generar_plantilla_dian(2027),
        {
            ("Por último dígito", "IVA bimestral", "2027-01", 6): 31,  # 31 de marzo sí existe
            ("Por último dígito", "IVA bimestral", "2027-02", 4): "mayito",  # mes inválido
            ("Por último dígito", "IVA bimestral", "2027-02", 6): 12,
            ("Por último dígito", "Gasolina y ACPM", "2027-01", 16): 30,  # 30 de febrero no existe
            ("Por dos dígitos", "Renta personas naturales", "2027", 4): "07-03",  # rango al revés
        },
    )
    libro = load_workbook(llena)
    libro["Por dos dígitos"].cell(row=5, column=7, value=12)
    libro["Por último dígito"].append(["Impuesto inventado", "2027", "", "marzo", 2027, 5])
    salida = BytesIO()
    libro.save(salida)
    salida.seek(0)

    resultado = importar_dian(salida)
    errores = " ".join(resultado["errores"])
    assert "«mayito» no es válido" in errores
    assert "«30» no existe en febrero de 2027" in errores
    assert "«07-03» no son válidos" in errores
    assert "«Impuesto inventado» no es una obligación del catálogo" in errores
    assert resultado["cargadas"] == 1  # solo IVA 2027-01 dígito 1


def test_no_se_mezclan_grupos_en_el_mismo_periodo():
    call_command("cargar_calendario_dian_2026")
    llena = _llenar(
        generar_plantilla_dian(2027),
        {
            ("Por último dígito", "IVA bimestral", "2027-01", 6): 9,
            ("Por último dígito", "IVA bimestral", "2027-01", 16): 9,
        },
    )
    resultado = importar_dian(llena)
    assert "no mezcle" in resultado["errores"][0]
    assert not TablaReferenciaDian.objects.filter(periodo_gravable="2027-01").exists()


def test_el_archivo_manda_en_cada_periodo():
    """Si un período pasa de fechas por dígito a fecha única, se quitan las anteriores."""
    call_command("cargar_calendario_dian_2026")
    cambios = {("Por último dígito", "Impuesto al patrimonio", "2026-1C", c): None for c in range(6, 16)}
    cambios[("Por último dígito", "Impuesto al patrimonio", "2026-1C", 16)] = 15
    resultado = importar_dian(_llenar(generar_plantilla_dian(2026), cambios))
    assert resultado["eliminadas"] == 10
    assert list(
        TablaReferenciaDian.objects.filter(
            tipo_obligacion="Impuesto al patrimonio", periodo_gravable="2026-1C"
        ).values_list("grupo_nit", flat=True)
    ) == ["TODOS"]


@pytest.mark.parametrize(
    "valor, esperado",
    [
        ("01-02", ["01", "02"]),
        ("99-00", ["99", "00"]),
        (" 05 - 06 ", ["05", "06"]),
        (7, ["07"]),
        ("TODOS", ["TODOS"]),
        ("07-03", None),
        ("1-2-3", None),
        ("abc", None),
        ("", None),
    ],
)
def test_expandir_dos_digitos(valor, esperado):
    assert _expandir_dos_digitos(valor) == esperado


@pytest.mark.parametrize(
    "valor, esperado", [("marzo", 3), ("Mar", 3), ("SETIEMBRE", 9), (12, 12), ("13", None), ("ma", None)]
)
def test_parse_mes(valor, esperado):
    assert _parse_mes(valor) == esperado


@pytest.mark.parametrize(
    "fecha, periodo, esperado",
    [
        (date(2027, 1, 18), "2026-06", 2026),
        (date(2027, 1, 18), "2026-12", 2026),
        (date(2026, 4, 23), "2025", 2026),
        (date(2026, 3, 10), "2026-01", 2026),
    ],
)
def test_anio_calendario(fecha, periodo, esperado):
    assert anio_calendario(fecha, periodo) == esperado


# ---------------------------------------------------------------------------
# Obligaciones con una sola fecha para todos los NIT
# ---------------------------------------------------------------------------


def _marcar(cliente, *nombres):
    for nombre in nombres:
        obligacion = ObligacionTributaria.objects.get(nombre=nombre)
        ClienteObligacion.objects.get_or_create(cliente=cliente, obligacion_tributaria=obligacion)


def test_las_fechas_unicas_aplican_a_cualquier_nit(cliente, usuario_administrador):
    call_command("cargar_calendario_dian_2026")
    _marcar(cliente, "Gasolina y ACPM", "Impuesto al patrimonio")
    resumen = generar_vencimientos_cliente(cliente, usuario_administrador)

    # 12 meses de gasolina + 1a. cuota de patrimonio (por dígito) + 2a. cuota (todos).
    assert resumen["creados"] >= 14
    assert Vencimiento.objects.filter(
        cliente=cliente, tipo_obligacion="Impuesto al patrimonio", periodo_gravable="2026-2C"
    ).get().fecha_vencimiento == date(2026, 9, 14)


def test_cliente_sin_calculo_por_documento_recibe_las_fechas_unicas(
    cliente_extranjero, usuario_administrador
):
    call_command("cargar_calendario_dian_2026")
    _marcar(cliente_extranjero, "Presencia económica significativa", "IVA bimestral")
    resumen = generar_vencimientos_cliente(cliente_extranjero, usuario_administrador)

    assert resumen["sin_grupo"] is True
    assert resumen["creados"] == 7  # 6 anticipos + declaración anual de la PES
    assert not Vencimiento.objects.filter(
        cliente=cliente_extranjero, tipo_obligacion="IVA bimestral"
    ).exists()


def test_rst_consolidada_corresponde_al_pdf():
    """Abril: consolidada anual; febrero: consolidada de IVA (estaban cruzadas)."""
    call_command("cargar_calendario_dian_2026")
    anual = TablaReferenciaDian.objects.get(
        tipo_obligacion="RST consolidada anual", grupo_nit="1", periodo_gravable="2025"
    )
    iva = TablaReferenciaDian.objects.get(
        tipo_obligacion="RST consolidada anual", grupo_nit="0", periodo_gravable="2026-IVA"
    )
    assert anual.fecha_vencimiento == date(2026, 4, 20)
    assert iva.fecha_vencimiento == date(2026, 2, 20)


# ---------------------------------------------------------------------------
# _parse_fecha
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "valor, esperado",
    [
        ("2026-03-10", date(2026, 3, 10)),
        ("10/03/2026", date(2026, 3, 10)),
        ("10-03-2026", date(2026, 3, 10)),
        (date(2026, 3, 10), date(2026, 3, 10)),
        ("texto", None),
        (None, None),
    ],
)
def test_parse_fecha_formatos(valor, esperado):
    """La fecha se acepta en varios formatos y se rechaza la inválida."""
    assert _parse_fecha(valor) == esperado


# ---------------------------------------------------------------------------
# importar_dian
# ---------------------------------------------------------------------------


def test_importar_dian_carga_filas_validas():
    """Las filas válidas se cargan en la tabla de referencia."""
    archivo = _excel_con_filas(
        [
            ["IVA bimestral", "1", "2026-03-10", "2026-01"],
            ["IVA bimestral", "2", "2026-03-11", "2026-01"],
        ]
    )
    resultado = importar_dian(archivo)

    assert resultado["leidas"] == 2
    assert resultado["cargadas"] == 2
    assert resultado["errores"] == []
    assert TablaReferenciaDian.objects.count() == 2


def test_importar_dian_actualiza_duplicados():
    """Una fila ya existente actualiza la fecha en lugar de duplicar."""
    TablaReferenciaDian.objects.create(
        tipo_obligacion="IVA bimestral",
        grupo_nit="1",
        fecha_vencimiento=date(2026, 3, 10),
        periodo_gravable="2026-01",
    )
    archivo = _excel_con_filas([["IVA bimestral", "1", "2026-03-15", "2026-01"]])
    resultado = importar_dian(archivo)

    assert resultado["cargadas"] == 0
    assert resultado["omitidas"] == 1
    referencia = TablaReferenciaDian.objects.get()
    assert referencia.fecha_vencimiento == date(2026, 3, 15)


def test_importar_dian_reporta_filas_incompletas():
    """Las filas con datos faltantes se reportan con su número."""
    archivo = _excel_con_filas(
        [
            ["IVA bimestral", "1", "2026-03-10", "2026-01"],
            ["IVA bimestral", "", "2026-03-11", "2026-01"],
            ["", "3", "fecha-mala", ""],
        ]
    )
    resultado = importar_dian(archivo)

    assert resultado["cargadas"] == 1
    assert len(resultado["errores"]) == 2
    assert "Fila 3" in resultado["errores"][0]


def test_importar_dian_omite_filas_vacias():
    """Las filas completamente vacías no cuentan como leídas."""
    archivo = _excel_con_filas(
        [
            ["IVA bimestral", "1", "2026-03-10", "2026-01"],
            [None, None, None, None],
        ]
    )
    resultado = importar_dian(archivo)
    assert resultado["leidas"] == 1


def test_importar_dian_archivo_corrupto():
    """Un archivo que no es Excel devuelve un error controlado."""
    with pytest.raises(ValueError, match="No se pudo leer"):
        importar_dian(BytesIO(b"esto no es un excel"))


# ---------------------------------------------------------------------------
# Vista de importación
# ---------------------------------------------------------------------------


def test_vista_importar_dian_con_excel(client, usuario_administrador):
    """El Administrador importa el Excel desde la vista."""
    from django.core.files.uploadedfile import SimpleUploadedFile

    client.force_login(usuario_administrador)
    contenido = _excel_con_filas([["IVA bimestral", "1", "2026-03-10", "2026-01"]])
    archivo = SimpleUploadedFile(
        "calendario.xlsx",
        contenido.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    respuesta = client.post(
        reverse("calendario:importar_dian"),
        {"archivo": archivo},
        format="multipart",
    )
    assert respuesta.status_code == 302
    assert TablaReferenciaDian.objects.count() == 1


def test_vista_importar_dian_solo_administrador(client, usuario_senior):
    """El Contador Senior no puede importar la tabla DIAN."""
    from django.core.files.uploadedfile import SimpleUploadedFile

    client.force_login(usuario_senior)
    contenido = _excel_con_filas([["IVA bimestral", "1", "2026-03-10", "2026-01"]])
    archivo = SimpleUploadedFile("calendario.xlsx", contenido.getvalue())
    respuesta = client.post(
        reverse("calendario:importar_dian"),
        {"archivo": archivo},
        format="multipart",
    )
    assert respuesta.status_code == 403


# ---------------------------------------------------------------------------
# Management command de carga del calendario oficial
# ---------------------------------------------------------------------------


def test_comando_cargar_calendario_dian_2026():
    """El comando carga los 704 registros oficiales (las dos páginas del PDF) y es idempotente."""
    call_command("cargar_calendario_dian_2026")
    total = TablaReferenciaDian.objects.count()
    assert total == 704

    call_command("cargar_calendario_dian_2026")
    assert TablaReferenciaDian.objects.count() == 704


def test_comando_carga_fechas_correctas():
    """Verifica dos fechas oficiales tomadas del calendario DIAN 2026."""
    call_command("cargar_calendario_dian_2026")

    iva = TablaReferenciaDian.objects.get(
        tipo_obligacion="IVA bimestral", grupo_nit="6", periodo_gravable="2026-01"
    )
    assert iva.fecha_vencimiento == date(2026, 3, 17)

    renta = TablaReferenciaDian.objects.get(
        tipo_obligacion="Renta personas naturales", grupo_nit="56", periodo_gravable="2026"
    )
    assert renta.fecha_vencimiento == date(2026, 9, 21)
