"""
Definición del menú lateral del sistema.

Cada elemento indica su etiqueta, el nombre de la ruta (None si el módulo
todavía no está construido), el ícono de Bootstrap Icons y el código del
módulo al que pertenece (para respetar la visibilidad configurable por rol,
RQF031). A medida que se desarrolla cada módulo se cambia su ruta de None al
nombre real y deja de aparecer como "Próximamente".
"""

from .models import Modulo, Rol

SECCIONES_MENU = [
    (
        "Principal",
        [
            ("Panel", "seguridad:panel", "bi-grid-fill", None),
            ("Clientes", "clientes:lista", "bi-people-fill", Modulo.MOD01_CLIENTES),
        ],
    ),
    (
        "Operaciones",
        [
            ("Calendario", "calendario:calendario", "bi-calendar2-check-fill", Modulo.MOD02_CALENDARIO),
            ("Tareas", "tareas:tablero", "bi-kanban-fill", Modulo.MOD03_TAREAS),
            ("Documentos", "documentos:historico", "bi-file-earmark-text-fill", Modulo.MOD04_DOCUMENTOS),
            ("Hallazgos", "hallazgos:lista", "bi-search-heart-fill", Modulo.MOD05_HALLAZGOS),
            ("Expediente", "expediente:lista", "bi-journal-text", Modulo.MOD09_EXPEDIENTE),
        ],
    ),
    (
        "Finanzas",
        [
            ("Honorarios", "finanzas:historico", "bi-cash-coin", Modulo.MOD06_FINANZAS),
            ("Comunicaciones", "comunicaciones:lista", "bi-chat-dots-fill", Modulo.MOD07_COMUNICACIONES),
            ("Reportes", "reportes:inicio", "bi-bar-chart-line-fill", Modulo.MOD10_REPORTES),
        ],
    ),
    (
        "Admin",
        [
            ("Equipo y roles", "seguridad:equipo", "bi-people", Modulo.MOD08_EQUIPO),
        ],
    ),
    (
        "Soporte",
        [
            ("Ayuda", "seguridad:ayuda", "bi-question-circle-fill", None),
        ],
    ),
]

RUTA_PANEL = "seguridad:panel"

# Rutas del menú que, además del módulo habilitado, exigen ciertos roles. El
# Contador Junior no tiene funciones en Equipo y roles (su perfil propio está
# siempre disponible desde la barra lateral) ni usa el panel principal: su
# trabajo está en los módulos operativos (decisión del usuario, 7-oct-2026).
ROLES_POR_RUTA = {
    RUTA_PANEL: (Rol.ADMINISTRADOR, Rol.CONTADOR_SENIOR),
    "seguridad:equipo": (Rol.ADMINISTRADOR, Rol.CONTADOR_SENIOR),
}

# Pantalla a la que llega quien no ve el panel: la primera de esta lista que
# tenga habilitada; si no tiene ninguna, la primera entrada de su menú.
INICIO_SIN_PANEL = ("calendario:calendario", "tareas:tablero")


def rutas_visibles(usuario):
    """Nombres de las rutas del menú que el usuario puede ver, en el orden del menú."""
    visibles = []
    for _titulo, elementos in SECCIONES_MENU:
        for _etiqueta, nombre_ruta, _icono, codigo_modulo in elementos:
            if codigo_modulo and not usuario.tiene_modulo_habilitado(codigo_modulo):
                continue
            roles = ROLES_POR_RUTA.get(nombre_ruta)
            if roles and usuario.rol.nombre_rol not in roles:
                continue
            visibles.append(nombre_ruta)
    return visibles


def ruta_de_inicio(usuario):
    """Nombre de la ruta donde empieza el usuario: el panel o, si no lo ve, su primer módulo."""
    visibles = rutas_visibles(usuario)
    if RUTA_PANEL in visibles:
        return RUTA_PANEL
    for nombre_ruta in INICIO_SIN_PANEL:
        if nombre_ruta in visibles:
            return nombre_ruta
    return visibles[0]
