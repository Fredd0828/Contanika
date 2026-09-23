"""
Definición del menú lateral del sistema.

Cada elemento indica su etiqueta, el nombre de la ruta (None si el módulo
todavía no está construido), el ícono de Bootstrap Icons y el código del
módulo al que pertenece (para respetar la visibilidad configurable por rol,
RQF031). A medida que se desarrolla cada módulo se cambia su ruta de None al
nombre real y deja de aparecer como "Próximamente".
"""

from .models import Modulo

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
            ("Tareas", None, "bi-kanban-fill", Modulo.MOD03_TAREAS),
            ("Documentos", None, "bi-file-earmark-text-fill", Modulo.MOD04_DOCUMENTOS),
            ("Hallazgos", None, "bi-search-heart-fill", Modulo.MOD05_HALLAZGOS),
            ("Expediente", None, "bi-journal-text", Modulo.MOD09_EXPEDIENTE),
        ],
    ),
    (
        "Finanzas",
        [
            ("Honorarios", None, "bi-cash-coin", Modulo.MOD06_FINANZAS),
            ("Comunicaciones", None, "bi-chat-dots-fill", Modulo.MOD07_COMUNICACIONES),
            ("Reportes", None, "bi-bar-chart-line-fill", Modulo.MOD10_REPORTES),
        ],
    ),
    (
        "Admin",
        [
            ("Equipo y roles", None, "bi-people", Modulo.MOD08_EQUIPO),
        ],
    ),
]
