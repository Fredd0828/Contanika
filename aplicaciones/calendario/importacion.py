"""
Plantilla anual del calendario tributario DIAN y su importación.

Cada año la DIAN publica el calendario como un PDF con cuadros: una fila por
obligación y período, y en cada cuadro el mes y el día de vencimiento por
último dígito del NIT (o una sola fecha «independientemente del NIT»). La
plantilla de Excel tiene esa misma forma para que el Administrador copie el
PDF casi cuadro por cuadro:

- Hoja «Por último dígito»: una fila por obligación y período, con el mes,
  el año y una columna por dígito (1 … 0), más «Todos los NIT».
- Hoja «Por dos dígitos»: renta de personas naturales (y lo que vaya por los
  dos últimos dígitos), una fila por par de dígitos («01-02»).

La plantilla de un año que ya está cargado sale llena (sirve para revisar o
corregir); la de un año nuevo sale con la misma estructura del año anterior,
los períodos corridos un año y los días en blanco.

Por compatibilidad, `importar_dian` también acepta la lista larga anterior
(una fila por fecha: tipo_obligacion, grupo_nit, fecha_vencimiento,
periodo_gravable).
"""

import re
from collections import defaultdict
from datetime import date, datetime
from io import BytesIO

from django.db import transaction
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from aplicaciones.clientes.models import ObligacionTributaria

from .models import TablaReferenciaDian

TODOS = TablaReferenciaDian.TODOS
HOJA_DIGITO = "Por último dígito"
HOJA_DOS_DIGITOS = "Por dos dígitos"
HOJA_OBLIGACIONES = "Obligaciones"
HOJA_INSTRUCCIONES = "Instrucciones"
FILA_ENCABEZADO = 4
DIGITOS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
MAXIMO_FILAS = 2000

MESES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]
BIMESTRES = [
    "enero - febrero",
    "marzo - abril",
    "mayo - junio",
    "julio - agosto",
    "septiembre - octubre",
    "noviembre - diciembre",
]
CUATRIMESTRES = {"1": "enero - abril", "2": "mayo - agosto", "3": "septiembre - diciembre"}
OBLIGACIONES_MENSUALES = {"Retención en la fuente", "Gasolina y ACPM"}
# Obligaciones que van por los dos últimos dígitos: si no tienen fechas
# cargadas, su fila en blanco va en la hoja «Por dos dígitos».
OBLIGACIONES_DOS_DIGITOS = {
    "Renta personas naturales",
    "Activos exterior personas naturales",
    "Exógena nacional",
}
# Orden del PDF de la DIAN; lo que no esté aquí va al final, en orden alfabético.
ORDEN_OBLIGACIONES = [
    "Renta grandes contribuyentes",
    "Renta personas jurídicas",
    "Renta personas naturales",
    "IVA bimestral",
    "IVA cuatrimestral",
    "Retención en la fuente",
    "Impuesto al consumo",
    "Gasolina y ACPM",
    "Impuesto al carbono",
    "RST anticipo bimestral",
    "RST consolidada anual",
    "Precios transferencia - informativa",
    "Precios transferencia - documentación",
    "Informe país por país",
    "IVA servicios desde el exterior",
    "Impuesto al patrimonio",
    "Plásticos de un solo uso",
    "Bebidas ultraprocesadas",
    "Beneficiarios finales (RUB)",
    "Presencia económica significativa",
    "Activos exterior grandes contribuyentes",
    "Activos exterior personas jurídicas",
    "Activos exterior personas naturales",
    "Activos exterior RST",
    "Exógena nacional grandes contribuyentes",
    "Exógena nacional",
    "Exógena distrital",
]

INSTRUCCIONES = [
    "Cómo llenar esta plantilla con el calendario tributario de la DIAN",
    "",
    "1. Abra el PDF del calendario del año y busque cada obligación.",
    "2. Hoja «Por último dígito»: en cada fila escriba el MES de vencimiento (por ejemplo «marzo»),",
    "   el AÑO (ojo: lo que vence en enero del año siguiente lleva ese año) y el DÍA debajo de",
    "   cada último dígito del NIT (1, 2, … 9, 0), igual que en el cuadro del PDF.",
    "3. Si el PDF dice «Independientemente del Número de Identificación Tributaria», escriba el día",
    "   solo en la columna «Todos los NIT».",
    "4. Si el PDF agrupa los dígitos de a dos (por ejemplo «1-2 → 20»), escriba el mismo día en",
    "   las dos columnas.",
    "5. Hoja «Por dos dígitos» (renta de personas naturales): una fila por par de dígitos",
    "   («01-02», «03-04» … «99-00»), con su mes, año y día.",
    "6. No cambie las columnas Obligación ni Período. Si agrega una fila, use un nombre de la hoja",
    "   «Obligaciones». Una fila sin días no se carga (sirve para dejar algo pendiente).",
    "7. Suba el archivo en Calendario → Tabla DIAN → Importar. Contanika revisa cada celda y le",
    "   dice cuáles tienen error; las filas correctas se cargan.",
    "8. Después pulse «Calcular vencimientos DIAN» en la lista de vencimientos para generar los",
    "   del año en todos los clientes.",
]

_RELLENO_ENCABEZADO = PatternFill("solid", fgColor="0F5E66")
_RELLENO_FIJO = PatternFill("solid", fgColor="EEF4F5")
_BORDE = Border(*(Side(style="thin", color="C9D6D8"),) * 4)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def anio_calendario(fecha, periodo):
    """
    Año del calendario al que pertenece una fecha. Lo que vence en enero por un
    período del año anterior (el último bimestre, diciembre…) sale en el
    calendario de ese año anterior, como en el PDF de la DIAN.
    """
    anios = re.findall(r"\d{4}", periodo or "")
    if fecha.month == 1 and "-" in (periodo or "") and anios and int(anios[0]) == fecha.year - 1:
        return fecha.year - 1
    return fecha.year


def anios_calendario():
    """Años de calendario que tienen fechas cargadas, de menor a mayor."""
    pares = TablaReferenciaDian.objects.values_list("fecha_vencimiento", "periodo_gravable").distinct()
    return sorted({anio_calendario(fecha, periodo) for fecha, periodo in pares})


def describir_periodo(tipo, periodo):
    """Texto de ayuda para la columna «Detalle» (no se usa al importar)."""
    if m := re.fullmatch(r"(\d{4})-(\d{2})", periodo):
        numero = int(m[2])
        if tipo in OBLIGACIONES_MENSUALES and 1 <= numero <= 12:
            return f"{MESES[numero - 1]} {m[1]}"
        if 1 <= numero <= 6:
            return f"{BIMESTRES[numero - 1]} {m[1]}"
    if m := re.fullmatch(r"(\d{4})-C([1-3])", periodo):
        return f"{CUATRIMESTRES[m[2]]} {m[1]}"
    if m := re.fullmatch(r"\d{4}-([1-3])C", periodo):
        return f"{m[1]}a. cuota"
    if m := re.fullmatch(r"\d{4}-T([1-4])", periodo):
        return f"actualización {m[1]} de 4"
    if re.fullmatch(r"\d{4}-IVA", periodo):
        return "consolidada de IVA"
    if re.fullmatch(r"\d{4}", periodo):
        return f"anual ({periodo})"
    return ""


def _correr_periodo(periodo, anios):
    """«2026-01» con anios=1 → «2027-01» (corre cada año escrito en el período)."""
    return re.sub(r"\d{4}", lambda m: str(int(m[0]) + anios), periodo)


def _orden_grupo(grupo):
    """Ordena 1…9, 0 y 01…99, 00 como en el PDF (el 0 va al final)."""
    numero = int(grupo) if grupo.isdigit() else 999
    return numero if numero else (10 if len(grupo) == 1 else 100)


def _orden_obligacion(tipo):
    try:
        return (ORDEN_OBLIGACIONES.index(tipo), tipo)
    except ValueError:
        return (len(ORDEN_OBLIGACIONES), tipo)


def _clase_grupo(grupo):
    if grupo == TODOS:
        return "todos"
    return "uno" if len(grupo) == 1 else "dos"


def _vacio(valor):
    return valor is None or (isinstance(valor, str) and not valor.strip())


def _texto(valor):
    return "" if valor is None else str(valor).strip()


def _parse_fecha(valor):
    """Convierte una celda de Excel o texto a date; None si no es válida."""
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(valor.strip(), formato).date()
            except ValueError:
                continue
    return None


def _parse_mes(valor):
    """«marzo», «Mar», «3» o 3 → 3; None si no es un mes."""
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return int(valor) if 1 <= int(valor) <= 12 and int(valor) == valor else None
    texto = _texto(valor).lower().replace("setiembre", "septiembre")
    if texto.isdigit():
        return int(texto) if 1 <= int(texto) <= 12 else None
    for numero, nombre in enumerate(MESES, start=1):
        if len(texto) >= 3 and nombre.startswith(texto):
            return numero
    return None


def _parse_entero(valor):
    if isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        return int(valor) if int(valor) == valor else None
    texto = _texto(valor)
    return int(texto) if texto.isdigit() else None


def _expandir_dos_digitos(valor):
    """«01-02» → ["01", "02"]; «99-00» → ["99", "00"]; 5 → ["05"]. None si no se entiende."""
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        valor = str(int(valor))
    texto = _texto(valor).replace(" ", "")
    if texto.upper() == TODOS:
        return [TODOS]
    partes = texto.split("-")
    if not 1 <= len(partes) <= 2 or not all(p.isdigit() and len(p) <= 2 for p in partes):
        return None
    inicio, fin = (int(p) or 100 for p in (partes[0], partes[-1]))
    if fin < inicio:
        return None
    return [str(numero % 100).zfill(2) for numero in range(inicio, fin + 1)]


# ---------------------------------------------------------------------------
# Plantilla
# ---------------------------------------------------------------------------
def _registros_del_anio(anio):
    """Fechas cargadas del calendario `anio` como lista de diccionarios."""
    filas = TablaReferenciaDian.objects.filter(fecha_vencimiento__year__in=(anio, anio + 1)).values(
        "tipo_obligacion", "grupo_nit", "fecha_vencimiento", "periodo_gravable"
    )
    return [
        fila for fila in filas if anio_calendario(fila["fecha_vencimiento"], fila["periodo_gravable"]) == anio
    ]


def _estructura(anio):
    """
    Devuelve (registros, en_blanco). Si el año está cargado, sus registros.
    Si no, los del año anterior más cercano (o los de 2026 del código) para
    copiar la estructura con los días en blanco.
    """
    registros = _registros_del_anio(anio)
    if registros:
        return registros, False
    anteriores = [a for a in anios_calendario() if a < anio]
    if anteriores:
        return _registros_del_anio(anteriores[-1]), True
    from .datos_dian_2026 import generar_registros_dian_2026

    return generar_registros_dian_2026(), anio != 2026


def _filas_plantilla(anio):
    """Arma las filas de las dos hojas a partir de lo cargado (o de su estructura)."""
    registros, en_blanco = _estructura(anio)
    base = min(
        (anio_calendario(r["fecha_vencimiento"], r["periodo_gravable"]) for r in registros), default=anio
    )
    corrimiento = anio - base

    por_llave = defaultdict(dict)
    for registro in registros:
        llave = (registro["tipo_obligacion"], registro["periodo_gravable"])
        por_llave[llave][registro["grupo_nit"]] = registro["fecha_vencimiento"]

    filas_digito, filas_dos = [], []
    for (tipo, periodo), fechas in por_llave.items():
        periodo_nuevo = _correr_periodo(periodo, corrimiento)
        detalle = describir_periodo(tipo, periodo_nuevo)
        clases = {_clase_grupo(g) for g in fechas}
        meses = {(f.year, f.month) for f in fechas.values()}
        if clases <= {"uno", "todos"} and len(meses) == 1:
            ((anio_venc, mes),) = meses
            dias = {g: (None if en_blanco else f.day) for g, f in fechas.items()}
            filas_digito.append((tipo, periodo_nuevo, detalle, MESES[mes - 1], anio_venc + corrimiento, dias))
            continue
        # Por dos dígitos (o mezcla de meses): una fila por tramo seguido con la misma fecha.
        tramo = []
        for grupo in sorted(fechas, key=_orden_grupo) + [None]:
            if tramo and (grupo is None or fechas[grupo] != fechas[tramo[0]]):
                fecha = fechas[tramo[0]]
                rango = tramo[0] if len(tramo) == 1 else f"{tramo[0]}-{tramo[-1]}"
                filas_dos.append(
                    (
                        tipo,
                        periodo_nuevo,
                        detalle,
                        rango,
                        MESES[fecha.month - 1],
                        fecha.year + corrimiento,
                        None if en_blanco else fecha.day,
                    )
                )
                tramo = []
            if grupo is not None:
                tramo.append(grupo)

    # Filas en blanco para las obligaciones del catálogo sin fechas (p. ej. exógena).
    con_filas = {fila[0] for fila in filas_digito + filas_dos}
    for nombre in ObligacionTributaria.objects.values_list("nombre", flat=True):
        if nombre in con_filas:
            continue
        periodo = str(anio - 1)
        if nombre in OBLIGACIONES_DOS_DIGITOS:
            filas_dos.append((nombre, periodo, describir_periodo(nombre, periodo), "", "", anio, None))
        else:
            filas_digito.append((nombre, periodo, describir_periodo(nombre, periodo), "", anio, {}))

    filas_digito.sort(key=lambda f: (_orden_obligacion(f[0]), f[1]))
    filas_dos.sort(key=lambda f: (_orden_obligacion(f[0]), f[1], _orden_grupo(f[3].split("-")[0] or "999")))
    return filas_digito, filas_dos, en_blanco


def _titulo(hoja, texto, ayuda, columnas):
    hoja["A1"] = texto
    hoja["A1"].font = Font(bold=True, size=14, color="0F5E66")
    hoja["A2"] = ayuda
    hoja["A2"].font = Font(italic=True, size=10, color="5B6B6E")
    hoja.merge_cells(start_row=2, start_column=1, end_row=2, end_column=columnas)


def _encabezado(hoja, columnas, anchos):
    for indice, (texto, ancho) in enumerate(zip(columnas, anchos, strict=True), start=1):
        celda = hoja.cell(row=FILA_ENCABEZADO, column=indice, value=texto)
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = _RELLENO_ENCABEZADO
        celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        celda.border = _BORDE
        hoja.column_dimensions[get_column_letter(indice)].width = ancho
    hoja.row_dimensions[FILA_ENCABEZADO].height = 30


def _validaciones(hoja, columna_obligacion, columna_mes, ultima_fila):
    obligaciones = DataValidation(type="list", formula1=f"={HOJA_OBLIGACIONES}!$A$2:$A$200", allow_blank=True)
    meses = DataValidation(type="list", formula1='"' + ",".join(MESES) + '"', allow_blank=True)
    hoja.add_data_validation(obligaciones)
    hoja.add_data_validation(meses)
    obligaciones.add(f"{columna_obligacion}{FILA_ENCABEZADO + 1}:{columna_obligacion}{ultima_fila}")
    meses.add(f"{columna_mes}{FILA_ENCABEZADO + 1}:{columna_mes}{ultima_fila}")


def generar_plantilla_dian(anio=None):
    """
    Construye la plantilla Excel del calendario DIAN de `anio`.

    Args:
        anio: año del calendario. Por defecto, el último cargado (o 2026).

    Returns:
        BytesIO: archivo .xlsx listo para descargar.
    """
    disponibles = anios_calendario()
    anio = int(anio or (disponibles[-1] if disponibles else 2026))
    filas_digito, filas_dos, en_blanco = _filas_plantilla(anio)
    estado = (
        "Días en blanco: cópielos del PDF de la DIAN."
        if en_blanco
        else "Fechas cargadas hoy en Contanika: corrija lo que haga falta y vuelva a subirla."
    )

    libro = Workbook()
    hoja = libro.active
    hoja.title = HOJA_DIGITO
    columnas = ["Obligación", "Período", "Detalle", "Mes", "Año", *DIGITOS, "Todos los NIT"]
    _titulo(hoja, f"Calendario tributario DIAN {anio} · por último dígito del NIT", estado, len(columnas))
    _encabezado(hoja, columnas, [38, 11, 24, 12, 7, *([5] * 10), 10])
    for numero, (tipo, periodo, detalle, mes, anio_venc, dias) in enumerate(
        filas_digito, start=FILA_ENCABEZADO + 1
    ):
        valores = [tipo, periodo, detalle, mes, anio_venc, *(dias.get(d) for d in DIGITOS), dias.get(TODOS)]
        for columna, valor in enumerate(valores, start=1):
            celda = hoja.cell(row=numero, column=columna, value=valor)
            celda.border = _BORDE
            if columna <= 3:
                celda.fill = _RELLENO_FIJO
            if columna >= 5:
                celda.alignment = Alignment(horizontal="center")
    hoja.freeze_panes = hoja.cell(row=FILA_ENCABEZADO + 1, column=6)
    _validaciones(hoja, "A", "D", FILA_ENCABEZADO + len(filas_digito) + 50)

    dos = libro.create_sheet(HOJA_DOS_DIGITOS)
    columnas = ["Obligación", "Período", "Detalle", "Últimos dos dígitos", "Mes", "Año", "Día"]
    _titulo(dos, f"Calendario tributario DIAN {anio} · por los dos últimos dígitos", estado, len(columnas))
    _encabezado(dos, columnas, [38, 11, 24, 14, 12, 7, 7])
    for numero, fila in enumerate(filas_dos, start=FILA_ENCABEZADO + 1):
        for columna, valor in enumerate(fila, start=1):
            celda = dos.cell(row=numero, column=columna, value=valor)
            celda.border = _BORDE
            if columna <= 3:
                celda.fill = _RELLENO_FIJO
            if columna >= 4:
                celda.alignment = Alignment(horizontal="center")
    dos.freeze_panes = dos.cell(row=FILA_ENCABEZADO + 1, column=5)
    _validaciones(dos, "A", "E", FILA_ENCABEZADO + len(filas_dos) + 50)

    catalogo = libro.create_sheet(HOJA_OBLIGACIONES)
    catalogo["A1"] = "Obligaciones del catálogo (use estos nombres exactos)"
    catalogo["A1"].font = Font(bold=True)
    catalogo.column_dimensions["A"].width = 45
    nombres = sorted(ObligacionTributaria.objects.values_list("nombre", flat=True), key=_orden_obligacion)
    for numero, nombre in enumerate(nombres, start=2):
        catalogo.cell(row=numero, column=1, value=nombre)

    ayuda = libro.create_sheet(HOJA_INSTRUCCIONES)
    ayuda.column_dimensions["A"].width = 100
    for numero, linea in enumerate(INSTRUCCIONES, start=1):
        ayuda.cell(row=numero, column=1, value=linea)
    ayuda["A1"].font = Font(bold=True, size=13, color="0F5E66")

    buffer = BytesIO()
    libro.save(buffer)
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------------------
# Importación
# ---------------------------------------------------------------------------
def importar_dian(archivo):
    """
    Procesa el Excel del calendario DIAN (plantilla por dígito o lista larga).

    Returns:
        dict: `leidas` (filas con datos), `cargadas` (fechas nuevas),
            `omitidas` (fechas que ya existían y se actualizaron),
            `sin_cambios`, `eliminadas` y `errores` (lista de textos).
    """
    resultado = {"leidas": 0, "cargadas": 0, "omitidas": 0, "sin_cambios": 0, "eliminadas": 0, "errores": []}
    try:
        libro = load_workbook(archivo, read_only=True, data_only=True)
    except Exception as error:
        raise ValueError(f"No se pudo leer el archivo de Excel: {error}") from error
    try:
        if HOJA_DIGITO in libro.sheetnames:
            _importar_plantilla(libro, resultado)
        else:
            _importar_lista(libro.active, resultado)
    finally:
        libro.close()
    return resultado


def _importar_lista(hoja, resultado):
    """Formato anterior: una fila por fecha (obligación, grupo, fecha, período)."""
    for numero, fila in enumerate(hoja.iter_rows(min_row=2, values_only=True), start=2):
        if not any(valor not in (None, "") for valor in fila):
            continue
        resultado["leidas"] += 1

        tipo_obligacion = str(fila[0]).strip() if len(fila) > 0 and fila[0] else ""
        grupo_nit = str(fila[1]).strip() if len(fila) > 1 and fila[1] is not None else ""
        fecha = _parse_fecha(fila[2]) if len(fila) > 2 else None
        periodo = str(fila[3]).strip() if len(fila) > 3 and fila[3] else ""

        if not tipo_obligacion or not grupo_nit or fecha is None or not periodo:
            resultado["errores"].append(
                f"Fila {numero}: complete obligación, grupo, fecha (AAAA-MM-DD) y período."
            )
            continue

        _, creado = TablaReferenciaDian.objects.update_or_create(
            tipo_obligacion=tipo_obligacion,
            grupo_nit=grupo_nit,
            periodo_gravable=periodo,
            defaults={"fecha_vencimiento": fecha},
        )
        if creado:
            resultado["cargadas"] += 1
        else:
            resultado["omitidas"] += 1


def _leer_comunes(fila, numero, hoja, catalogo, columna_mes, columna_anio):
    """Valida obligación, período, mes y año de una fila. Devuelve (datos, errores)."""
    tipo, periodo = _texto(fila[0]), _texto(fila[1])
    mes, anio = _parse_mes(fila[columna_mes]), _parse_entero(fila[columna_anio])
    errores = []
    lugar = f"{hoja}, fila {numero}"
    if tipo not in catalogo:
        errores.append(
            f"{lugar}: «{tipo or 'vacío'}» no es una obligación del catálogo (vea la hoja «Obligaciones»)."
        )
    if not periodo or len(periodo) > 10:
        errores.append(f"{lugar}: escriba el período (máximo 10 caracteres, por ejemplo 2027-01).")
    if mes is None:
        errores.append(f"{lugar}: el mes «{_texto(fila[columna_mes])}» no es válido (por ejemplo «marzo»).")
    if anio is None or not 2000 <= anio <= 2100:
        errores.append(f"{lugar}: el año «{_texto(fila[columna_anio])}» no es válido.")
    return (tipo, periodo, mes, anio), errores


def _fecha_o_error(anio, mes, valor, lugar):
    dia = _parse_entero(valor)
    try:
        return date(anio, mes, dia), None
    except (TypeError, ValueError):
        return None, f"{lugar}: el día «{_texto(valor)}» no existe en {MESES[mes - 1]} de {anio}."


def _importar_plantilla(libro, resultado):
    """Plantilla con la forma del PDF: hoja por último dígito y hoja por dos dígitos."""
    catalogo = set(ObligacionTributaria.objects.values_list("nombre", flat=True))
    fechas = defaultdict(dict)  # (tipo, periodo) -> {grupo: fecha}
    con_error = set()

    def agregar(llave, grupo, fecha, lugar):
        if grupo in fechas[llave] and fechas[llave][grupo] != fecha:
            resultado["errores"].append(f"{lugar}: el grupo {grupo} de {llave[0]} {llave[1]} está repetido.")
            con_error.add(llave)
        fechas[llave][grupo] = fecha

    hoja = libro[HOJA_DIGITO]
    for numero, fila in enumerate(
        hoja.iter_rows(min_row=FILA_ENCABEZADO + 1, max_row=MAXIMO_FILAS, values_only=True),
        start=FILA_ENCABEZADO + 1,
    ):
        fila = [*fila, *([None] * 16)][:16]
        celdas = [(g, v) for g, v in zip([*DIGITOS, TODOS], fila[5:16], strict=True) if not _vacio(v)]
        if not celdas:
            continue
        resultado["leidas"] += 1
        (tipo, periodo, mes, anio), errores = _leer_comunes(fila, numero, HOJA_DIGITO, catalogo, 3, 4)
        if not errores:
            for grupo, valor in celdas:
                columna = "Todos los NIT" if grupo == TODOS else f"dígito {grupo}"
                fecha, error = _fecha_o_error(anio, mes, valor, f"{HOJA_DIGITO}, fila {numero}, {columna}")
                if error:
                    errores.append(error)
                else:
                    agregar((tipo, periodo), grupo, fecha, f"{HOJA_DIGITO}, fila {numero}")
        if errores:
            resultado["errores"].extend(errores)
            con_error.add((tipo, periodo))

    if HOJA_DOS_DIGITOS in libro.sheetnames:
        hoja = libro[HOJA_DOS_DIGITOS]
        for numero, fila in enumerate(
            hoja.iter_rows(min_row=FILA_ENCABEZADO + 1, max_row=MAXIMO_FILAS, values_only=True),
            start=FILA_ENCABEZADO + 1,
        ):
            fila = [*fila, *([None] * 7)][:7]
            if _vacio(fila[6]):
                continue
            resultado["leidas"] += 1
            lugar = f"{HOJA_DOS_DIGITOS}, fila {numero}"
            (tipo, periodo, mes, anio), errores = _leer_comunes(
                fila, numero, HOJA_DOS_DIGITOS, catalogo, 4, 5
            )
            grupos = _expandir_dos_digitos(fila[3])
            if not grupos:
                errores.append(
                    f"{lugar}: los dígitos «{_texto(fila[3])}» no son válidos (por ejemplo «01-02»)."
                )
            if not errores:
                fecha, error = _fecha_o_error(anio, mes, fila[6], lugar)
                if error:
                    errores.append(error)
                else:
                    for grupo in grupos:
                        agregar((tipo, periodo), grupo, fecha, lugar)
            if errores:
                resultado["errores"].extend(errores)
                con_error.add((tipo, periodo))

    for llave, grupos in fechas.items():
        if llave in con_error:
            continue
        if len({_clase_grupo(g) for g in grupos}) > 1:
            resultado["errores"].append(
                f"{llave[0]} {llave[1]}: no mezcle en el mismo período fechas por un dígito, por dos "
                "dígitos y «Todos los NIT». No se cargó."
            )
            con_error.add(llave)

    with transaction.atomic():
        for (tipo, periodo), grupos in fechas.items():
            if (tipo, periodo) in con_error:
                continue
            existentes = TablaReferenciaDian.objects.filter(tipo_obligacion=tipo, periodo_gravable=periodo)
            # El archivo manda: lo que ya no está en ese período se quita.
            sobrantes = existentes.exclude(grupo_nit__in=list(grupos))
            resultado["eliminadas"] += sobrantes.count()
            sobrantes.delete()
            actuales = dict(existentes.values_list("grupo_nit", "fecha_vencimiento"))
            for grupo, fecha in grupos.items():
                if grupo not in actuales:
                    TablaReferenciaDian.objects.create(
                        tipo_obligacion=tipo,
                        grupo_nit=grupo,
                        periodo_gravable=periodo,
                        fecha_vencimiento=fecha,
                    )
                    resultado["cargadas"] += 1
                elif actuales[grupo] != fecha:
                    existentes.filter(grupo_nit=grupo).update(fecha_vencimiento=fecha)
                    resultado["omitidas"] += 1
                else:
                    resultado["sin_cambios"] += 1
