"""
Importación masiva de la tabla de referencia DIAN desde Excel.

El Administrador descarga una plantilla, la diligencia con las columnas
`tipo_obligacion`, `grupo_nit`, `fecha_vencimiento` y `periodo_gravable`,
y el sistema valida cada fila antes de cargarla (resumen de errores).
"""

from datetime import date, datetime
from io import BytesIO

from openpyxl import Workbook, load_workbook

from .models import TablaReferenciaDian

ENCABEZADOS = ["tipo_obligacion", "grupo_nit", "fecha_vencimiento", "periodo_gravable"]

INSTRUCCIONES = [
    "Cada fila es un vencimiento oficial de la DIAN.",
    "tipo_obligacion: nombre de la obligación (ej. IVA bimestral).",
    "grupo_nit: último dígito del NIT (0-9) o últimos dos dígitos de la cédula (00-99).",
    "fecha_vencimiento: fecha en formato AAAA-MM-DD o celda de fecha de Excel.",
    "periodo_gravable: período de la obligación (ej. 2026-01, 2026, 2026-C1).",
    "No se permiten filas duplicadas (obligación + grupo + período).",
]


def generar_plantilla_dian():
    """
    Construye la plantilla Excel de carga masiva de la tabla DIAN.

    Returns:
        BytesIO: archivo .xlsx listo para descargar.
    """
    libro = Workbook()
    hoja = libro.active
    hoja.title = "calendario_dian"
    hoja.append(ENCABEZADOS)
    hoja.append(["IVA bimestral", "1", "2026-03-10", "2026-01"])

    ayuda = libro.create_sheet("instrucciones")
    ayuda.append(["Instrucciones de diligenciamiento"])
    for linea in INSTRUCCIONES:
        ayuda.append([linea])

    buffer = BytesIO()
    libro.save(buffer)
    buffer.seek(0)
    return buffer


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


def importar_dian(archivo):
    """
    Procesa el Excel de la tabla DIAN fila por fila.

    Solo cargan las filas válidas; las que fallan se reportan con su motivo.

    Args:
        archivo: archivo Excel subido por el Administrador.

    Returns:
        dict: resumen con filas leídas, cargadas, omitidas y lista de errores.
    """
    resultado = {"leidas": 0, "cargadas": 0, "omitidas": 0, "errores": []}

    try:
        libro = load_workbook(archivo, read_only=True, data_only=True)
    except Exception as error:
        raise ValueError(f"No se pudo leer el archivo de Excel: {error}") from error

    hoja = libro.active
    filas = hoja.iter_rows(min_row=2, values_only=True)

    for numero, fila in enumerate(filas, start=2):
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

    libro.close()
    return resultado
