"""
Datos oficiales del calendario tributario DIAN 2026.

Fuente: "Plazos para el cumplimiento de las obligaciones tributarias
administradas por la UAE DIAN" (Calendario_Tributario_2026.pdf).

Convención de `grupo_nit`:
- Empresas (NIT) y grandes contribuyentes: último dígito del NIT ("0" a "9").
- Personas naturales (renta): últimos dos dígitos de la cédula ("00" a "99").
- Extranjeros: no se calculan automáticamente; se registran como vencimiento manual.
- Obligaciones con una sola fecha para todos («independientemente del NIT»):
  grupo "TODOS"; le aplican a cualquier cliente que tenga la obligación.
"""

# ---------------------------------------------------------------------------
# IVA bimestral 2026 (empresas, último dígito del NIT)
# ---------------------------------------------------------------------------
# (periodo_gravable, año_vencimiento, mes_vencimiento, {dígito: día})
IVA_BIMESTRAL_2026 = [
    (
        "2026-01",
        2026,
        3,
        {"1": 10, "2": 11, "3": 12, "4": 13, "5": 16, "6": 17, "7": 18, "8": 19, "9": 20, "0": 24},
    ),
    (
        "2026-02",
        2026,
        5,
        {"1": 12, "2": 13, "3": 14, "4": 15, "5": 19, "6": 20, "7": 21, "8": 22, "9": 25, "0": 26},
    ),
    (
        "2026-03",
        2026,
        7,
        {"1": 9, "2": 10, "3": 14, "4": 15, "5": 16, "6": 17, "7": 21, "8": 22, "9": 23, "0": 24},
    ),
    (
        "2026-04",
        2026,
        9,
        {"1": 9, "2": 10, "3": 11, "4": 14, "5": 15, "6": 16, "7": 17, "8": 18, "9": 21, "0": 22},
    ),
    (
        "2026-05",
        2026,
        11,
        {"1": 11, "2": 12, "3": 13, "4": 17, "5": 18, "6": 19, "7": 20, "8": 23, "9": 24, "0": 25},
    ),
    (
        "2026-06",
        2027,
        1,
        {"1": 13, "2": 14, "3": 15, "4": 18, "5": 19, "6": 20, "7": 21, "8": 22, "9": 25, "0": 26},
    ),
]

# ---------------------------------------------------------------------------
# IVA cuatrimestral 2026 (empresas, último dígito del NIT)
# ---------------------------------------------------------------------------
IVA_CUATRIMESTRAL_2026 = [
    (
        "2026-C1",
        2026,
        5,
        {"1": 12, "2": 13, "3": 14, "4": 15, "5": 19, "6": 20, "7": 21, "8": 22, "9": 25, "0": 26},
    ),
    (
        "2026-C2",
        2026,
        9,
        {"1": 9, "2": 10, "3": 11, "4": 14, "5": 15, "6": 16, "7": 17, "8": 18, "9": 21, "0": 22},
    ),
    (
        "2026-C3",
        2027,
        1,
        {"1": 13, "2": 14, "3": 15, "4": 18, "5": 19, "6": 20, "7": 21, "8": 22, "9": 25, "0": 26},
    ),
]

# ---------------------------------------------------------------------------
# Retención en la fuente mensual 2026 (empresas, último dígito del NIT)
# ---------------------------------------------------------------------------
RETENCION_MENSUAL_2026 = [
    (
        "2026-01",
        2026,
        2,
        {"1": 10, "2": 11, "3": 12, "4": 13, "5": 16, "6": 17, "7": 18, "8": 19, "9": 20, "0": 23},
    ),
    (
        "2026-02",
        2026,
        3,
        {"1": 10, "2": 11, "3": 12, "4": 13, "5": 16, "6": 17, "7": 18, "8": 19, "9": 20, "0": 24},
    ),
    (
        "2026-03",
        2026,
        4,
        {"1": 13, "2": 14, "3": 15, "4": 16, "5": 20, "6": 21, "7": 22, "8": 23, "9": 24, "0": 27},
    ),
    (
        "2026-04",
        2026,
        5,
        {"1": 12, "2": 13, "3": 14, "4": 15, "5": 19, "6": 20, "7": 21, "8": 22, "9": 25, "0": 26},
    ),
    (
        "2026-05",
        2026,
        6,
        {"1": 10, "2": 11, "3": 12, "4": 16, "5": 17, "6": 18, "7": 19, "8": 22, "9": 23, "0": 24},
    ),
    (
        "2026-06",
        2026,
        7,
        {"1": 9, "2": 10, "3": 14, "4": 15, "5": 16, "6": 17, "7": 21, "8": 22, "9": 23, "0": 24},
    ),
    (
        "2026-07",
        2026,
        8,
        {"1": 12, "2": 13, "3": 14, "4": 18, "5": 19, "6": 20, "7": 21, "8": 24, "9": 25, "0": 26},
    ),
    (
        "2026-08",
        2026,
        9,
        {"1": 9, "2": 10, "3": 11, "4": 14, "5": 15, "6": 16, "7": 17, "8": 18, "9": 21, "0": 22},
    ),
    (
        "2026-09",
        2026,
        10,
        {"1": 9, "2": 13, "3": 14, "4": 15, "5": 16, "6": 19, "7": 20, "8": 21, "9": 22, "0": 23},
    ),
    (
        "2026-10",
        2026,
        11,
        {"1": 11, "2": 12, "3": 13, "4": 17, "5": 18, "6": 19, "7": 20, "8": 23, "9": 24, "0": 25},
    ),
    (
        "2026-11",
        2026,
        12,
        {"1": 10, "2": 11, "3": 14, "4": 15, "5": 16, "6": 17, "7": 18, "8": 21, "9": 22, "0": 23},
    ),
    (
        "2026-12",
        2027,
        1,
        {"1": 13, "2": 14, "3": 15, "4": 18, "5": 19, "6": 20, "7": 21, "8": 22, "9": 25, "0": 26},
    ),
]

# ---------------------------------------------------------------------------
# Renta personas jurídicas 2026 (último dígito del NIT)
# ---------------------------------------------------------------------------
RENTA_PERSONAS_JURIDICAS_2026 = [
    (
        "2026-1C",
        2026,
        5,
        {"1": 12, "2": 13, "3": 14, "4": 15, "5": 19, "6": 20, "7": 21, "8": 22, "9": 25, "0": 26},
    ),
    (
        "2026-2C",
        2026,
        7,
        {"1": 9, "2": 10, "3": 14, "4": 15, "5": 16, "6": 17, "7": 21, "8": 22, "9": 23, "0": 24},
    ),
]

# ---------------------------------------------------------------------------
# Renta grandes contribuyentes 2026 (último dígito del NIT)
# ---------------------------------------------------------------------------
RENTA_GRANDES_CONTRIBUYENTES_2026 = [
    (
        "2026-1C",
        2026,
        2,
        {"1": 10, "2": 11, "3": 12, "4": 13, "5": 16, "6": 17, "7": 18, "8": 19, "9": 20, "0": 23},
    ),
    (
        "2026-2C",
        2026,
        4,
        {"1": 13, "2": 14, "3": 15, "4": 16, "5": 20, "6": 21, "7": 22, "8": 23, "9": 24, "0": 27},
    ),
    (
        "2026-3C",
        2026,
        6,
        {"1": 10, "2": 11, "3": 12, "4": 16, "5": 17, "6": 18, "7": 19, "8": 22, "9": 23, "0": 24},
    ),
]

# ---------------------------------------------------------------------------
# Renta personas naturales 2026 (últimos dos dígitos de la cédula)
# ---------------------------------------------------------------------------
# (periodo_gravable, año_vencimiento, mes_vencimiento, {rango_o_dígitos: día})
RENTA_PERSONAS_NATURALES_2026 = [
    (
        "2026",
        2026,
        8,
        {
            "01": 12,
            "02": 12,
            "03": 13,
            "04": 13,
            "05": 14,
            "06": 14,
            "07": 18,
            "08": 18,
            "09": 19,
            "10": 19,
            "11": 20,
            "12": 20,
            "13": 21,
            "14": 21,
            "15": 24,
            "16": 24,
            "17": 25,
            "18": 25,
            "19": 26,
            "20": 26,
            "21": 27,
            "22": 27,
            "23": 28,
            "24": 28,
            "25": 31,
            "26": 31,
        },
    ),
    (
        "2026",
        2026,
        9,
        {
            "27": 1,
            "28": 1,
            "29": 2,
            "30": 2,
            "31": 3,
            "32": 3,
            "33": 4,
            "34": 4,
            "35": 7,
            "36": 7,
            "37": 8,
            "38": 8,
            "39": 9,
            "40": 9,
            "41": 10,
            "42": 10,
            "43": 11,
            "44": 11,
            "45": 14,
            "46": 14,
            "47": 15,
            "48": 15,
            "49": 16,
            "50": 16,
            "51": 17,
            "52": 17,
            "53": 18,
            "54": 18,
            "55": 21,
            "56": 21,
            "57": 22,
            "58": 22,
            "59": 23,
            "60": 23,
            "61": 24,
            "62": 24,
            "63": 25,
            "64": 25,
            "65": 28,
            "66": 28,
        },
    ),
    (
        "2026",
        2026,
        10,
        {
            "67": 1,
            "68": 1,
            "69": 2,
            "70": 2,
            "71": 5,
            "72": 5,
            "73": 6,
            "74": 6,
            "75": 7,
            "76": 7,
            "77": 8,
            "78": 8,
            "79": 9,
            "80": 9,
            "81": 13,
            "82": 13,
            "83": 14,
            "84": 14,
            "85": 15,
            "86": 15,
            "87": 16,
            "88": 16,
            "89": 19,
            "90": 19,
            "91": 20,
            "92": 20,
            "93": 21,
            "94": 21,
            "95": 22,
            "96": 22,
            "97": 23,
            "98": 23,
            "99": 26,
            "00": 26,
        },
    ),
]


# ---------------------------------------------------------------------------
# RST — Anticipo bimestral 2026 (último dígito del NIT)
# ---------------------------------------------------------------------------
RST_ANTICIPO_BIMESTRAL_2026 = [
    (
        "2026-01",
        2026,
        5,
        {"1": 12, "2": 13, "3": 14, "4": 15, "5": 19, "6": 20, "7": 21, "8": 22, "9": 25, "0": 26},
    ),
    (
        "2026-02",
        2026,
        6,
        {"1": 10, "2": 11, "3": 12, "4": 16, "5": 17, "6": 18, "7": 19, "8": 22, "9": 23, "0": 24},
    ),
    (
        "2026-03",
        2026,
        7,
        {"1": 9, "2": 10, "3": 14, "4": 15, "5": 16, "6": 17, "7": 21, "8": 22, "9": 23, "0": 24},
    ),
    (
        "2026-04",
        2026,
        9,
        {"1": 9, "2": 10, "3": 11, "4": 14, "5": 15, "6": 16, "7": 17, "8": 18, "9": 21, "0": 22},
    ),
    (
        "2026-05",
        2026,
        11,
        {"1": 11, "2": 12, "3": 13, "4": 17, "5": 18, "6": 19, "7": 20, "8": 23, "9": 24, "0": 25},
    ),
    (
        "2026-06",
        2027,
        1,
        {"1": 13, "2": 14, "3": 15, "4": 18, "5": 19, "6": 20, "7": 21, "8": 22, "9": 25, "0": 26},
    ),
]

# ---------------------------------------------------------------------------
# RST — Consolidada anual 2026 (último dígito del NIT; el PDF agrupa de a dos)
# ---------------------------------------------------------------------------
# Abril 2026: consolidada del año gravable 2025; Febrero 2026: consolidada de
# IVA. (Corregido el 16-nov-2026: antes estaban cruzadas con respecto al PDF.)
RST_CONSOLIDADA_2026 = [
    (
        "2025",
        2026,
        4,
        {"1": 20, "2": 20, "3": 21, "4": 21, "5": 22, "6": 22, "7": 23, "8": 23, "9": 24, "0": 24},
    ),
    (
        "2026-IVA",
        2026,
        2,
        {"1": 16, "2": 16, "3": 17, "4": 17, "5": 18, "6": 18, "7": 19, "8": 19, "9": 20, "0": 20},
    ),
]

# ---------------------------------------------------------------------------
# Obligaciones con una sola fecha para todos los NIT («Independientemente del
# Número de Identificación Tributaria»). El grupo es TODOS.
# ---------------------------------------------------------------------------
TODOS = "TODOS"

# Gasolina y ACPM: declaración mensual y pago.
GASOLINA_ACPM_2026 = [
    ("2026-01", 2026, 2, {TODOS: 13}),
    ("2026-02", 2026, 3, {TODOS: 13}),
    ("2026-03", 2026, 4, {TODOS: 16}),
    ("2026-04", 2026, 5, {TODOS: 15}),
    ("2026-05", 2026, 6, {TODOS: 16}),
    ("2026-06", 2026, 7, {TODOS: 15}),
    ("2026-07", 2026, 8, {TODOS: 18}),
    ("2026-08", 2026, 9, {TODOS: 14}),
    ("2026-09", 2026, 10, {TODOS: 15}),
    ("2026-10", 2026, 11, {TODOS: 17}),
    ("2026-11", 2026, 12, {TODOS: 15}),
    ("2026-12", 2027, 1, {TODOS: 18}),
]

# Bimestral con fecha única: carbono, IVA de prestadores de servicios desde el
# exterior, bebidas ultraprocesadas y anticipos de la PES (mismas fechas).
BIMESTRAL_FECHA_UNICA_2026 = [
    ("2026-01", 2026, 3, {TODOS: 13}),
    ("2026-02", 2026, 5, {TODOS: 15}),
    ("2026-03", 2026, 7, {TODOS: 15}),
    ("2026-04", 2026, 9, {TODOS: 14}),
    ("2026-05", 2026, 11, {TODOS: 17}),
    ("2026-06", 2027, 1, {TODOS: 18}),
]

# Presencia económica significativa: anticipos bimestrales + declaración anual.
PES_2026 = [*BIMESTRAL_FECHA_UNICA_2026, ("2025", 2026, 4, {TODOS: 23})]

# Impuesto al patrimonio: 1a. cuota por último dígito; 2a. cuota fecha única.
PATRIMONIO_2026 = [
    (
        "2026-1C",
        2026,
        5,
        {"1": 12, "2": 13, "3": 14, "4": 15, "5": 19, "6": 20, "7": 21, "8": 22, "9": 25, "0": 26},
    ),
    ("2026-2C", 2026, 9, {TODOS: 14}),
]

# Precios de transferencia: declaración informativa y documentación
# comprobatoria (informe local e informe maestro), mismas fechas.
PRECIOS_TRANSFERENCIA_2026 = [
    (
        "2025",
        2026,
        9,
        {"1": 9, "2": 10, "3": 11, "4": 14, "5": 15, "6": 16, "7": 17, "8": 18, "9": 21, "0": 22},
    ),
]
INFORME_PAIS_POR_PAIS_2026 = [("2025", 2026, 12, {TODOS: 15})]
PLASTICOS_UN_SOLO_USO_2026 = [("2025", 2026, 2, {TODOS: 13})]

# Registro Único de Beneficiarios Finales: actualización trimestral.
RUB_2026 = [
    ("2026-T1", 2026, 2, {TODOS: 2}),
    ("2026-T2", 2026, 5, {TODOS: 4}),
    ("2026-T3", 2026, 8, {TODOS: 3}),
    ("2026-T4", 2026, 11, {TODOS: 3}),
]


def _como_declaracion_anual(bloque, periodo="2025"):
    """
    Activos en el exterior: «las mismas fechas de renta». Toma las fechas de
    la declaración de renta del grupo y las rotula con el año gravable.
    """
    return [(periodo, anio, mes, dias) for _, anio, mes, dias in bloque]


# Grandes contribuyentes declaran con la 2a. cuota (abril); personas
# jurídicas con la 1a. (mayo); personas naturales de agosto a octubre; RST
# con la consolidada anual (abril).
ACTIVOS_EXTERIOR_GRANDES_2026 = _como_declaracion_anual(RENTA_GRANDES_CONTRIBUYENTES_2026[1:2])
ACTIVOS_EXTERIOR_JURIDICAS_2026 = _como_declaracion_anual(RENTA_PERSONAS_JURIDICAS_2026[:1])
ACTIVOS_EXTERIOR_NATURALES_2026 = _como_declaracion_anual(RENTA_PERSONAS_NATURALES_2026)
ACTIVOS_EXTERIOR_RST_2026 = _como_declaracion_anual(RST_CONSOLIDADA_2026[:1])


def generar_registros_dian_2026():
    """
    Genera la lista de registros de la tabla de referencia DIAN 2026.

    Cada registro es un diccionario con las llaves:
    tipo_obligacion, grupo_nit, fecha_vencimiento (date) y periodo_gravable.

    Returns:
        list[dict]: Registros listos para insertar en TablaReferenciaDian.
    """
    from datetime import date

    registros = []

    bloques = [
        ("IVA bimestral", IVA_BIMESTRAL_2026),
        ("IVA cuatrimestral", IVA_CUATRIMESTRAL_2026),
        ("Retención en la fuente", RETENCION_MENSUAL_2026),
        ("Renta personas jurídicas", RENTA_PERSONAS_JURIDICAS_2026),
        ("Renta grandes contribuyentes", RENTA_GRANDES_CONTRIBUYENTES_2026),
        ("Renta personas naturales", RENTA_PERSONAS_NATURALES_2026),
        ("RST anticipo bimestral", RST_ANTICIPO_BIMESTRAL_2026),
        ("RST consolidada anual", RST_CONSOLIDADA_2026),
        # Página 2 del calendario (agregadas el 16-nov-2026).
        ("Impuesto al consumo", IVA_BIMESTRAL_2026),
        ("Gasolina y ACPM", GASOLINA_ACPM_2026),
        ("Impuesto al carbono", BIMESTRAL_FECHA_UNICA_2026),
        ("IVA servicios desde el exterior", BIMESTRAL_FECHA_UNICA_2026),
        ("Bebidas ultraprocesadas", BIMESTRAL_FECHA_UNICA_2026),
        ("Presencia económica significativa", PES_2026),
        ("Impuesto al patrimonio", PATRIMONIO_2026),
        ("Precios transferencia - informativa", PRECIOS_TRANSFERENCIA_2026),
        ("Precios transferencia - documentación", PRECIOS_TRANSFERENCIA_2026),
        ("Informe país por país", INFORME_PAIS_POR_PAIS_2026),
        ("Plásticos de un solo uso", PLASTICOS_UN_SOLO_USO_2026),
        ("Beneficiarios finales (RUB)", RUB_2026),
        ("Activos exterior grandes contribuyentes", ACTIVOS_EXTERIOR_GRANDES_2026),
        ("Activos exterior personas jurídicas", ACTIVOS_EXTERIOR_JURIDICAS_2026),
        ("Activos exterior personas naturales", ACTIVOS_EXTERIOR_NATURALES_2026),
        ("Activos exterior RST", ACTIVOS_EXTERIOR_RST_2026),
    ]

    for tipo_obligacion, bloque in bloques:
        for periodo, anio, mes, dias_por_grupo in bloque:
            for grupo, dia in dias_por_grupo.items():
                registros.append(
                    {
                        "tipo_obligacion": tipo_obligacion,
                        "grupo_nit": grupo,
                        "fecha_vencimiento": date(anio, mes, dia),
                        "periodo_gravable": periodo,
                    }
                )
    return registros
