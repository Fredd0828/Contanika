"""
Genera el mapa de navegación del sistema (entregable 3.3) en Markdown.

Lee las rutas reales del proyecto, así el documento no se desactualiza: por
cada ruta toma la vista, el módulo que exige (`codigo_modulo`), los roles
permitidos (`roles_permitidos`) y la primera frase de su documentación.

Uso:
    python gestionar.py generar_mapa_navegacion
    python gestionar.py generar_mapa_navegacion --salida otra/ruta.md
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import URLPattern, URLResolver, get_resolver
from django.utils import timezone

from aplicaciones.seguridad.menu import ROLES_POR_RUTA, SECCIONES_MENU
from aplicaciones.seguridad.models import Modulo, Rol

SALIDA_PREDETERMINADA = Path("documentacion") / "MAPA_NAVEGACION.md"
ROLES = (Rol.ADMINISTRADOR, Rol.CONTADOR_SENIOR, Rol.CONTADOR_JUNIOR)
NOMBRES_MODULO = dict(Modulo.OPCIONES_CODIGO)
# Rutas que se abren sin iniciar sesión.
RUTAS_PUBLICAS = ("seguridad:inicio", "seguridad:iniciar_sesion", "finanzas:pdf_publico", "robots")
SI, NO = "Sí", "—"


def recorrer_rutas(patrones=None, espacio=""):
    """Devuelve un diccionario por cada ruta del sistema (sin el admin de Django)."""
    if patrones is None:
        patrones = get_resolver().url_patterns
    rutas = []
    for patron in patrones:
        if isinstance(patron, URLResolver):
            if patron.namespace != "admin":
                rutas.extend(recorrer_rutas(patron.url_patterns, patron.namespace or espacio))
        elif isinstance(patron, URLPattern):
            vista = getattr(patron.callback, "view_class", None)
            if vista is None:
                continue
            nombre = f"{espacio}:{patron.name}" if espacio else patron.name
            metodos = [metodo.upper() for metodo in ("get", "post") if hasattr(vista, metodo)]
            rutas.append(
                {
                    "ruta": "/" + str(patron.pattern),
                    "nombre": nombre,
                    "app": espacio,
                    "modulo": getattr(vista, "codigo_modulo", None),
                    "roles": tuple(getattr(vista, "roles_permitidos", ()) or ()),
                    "metodos": metodos,
                    "publica": nombre in RUTAS_PUBLICAS,
                    "descripcion": _primera_frase(vista.__doc__),
                }
            )
    return rutas


def _primera_frase(documentacion):
    """Primer párrafo de la documentación de la vista, en una sola línea y sin `|`."""
    parrafo = (documentacion or "").strip().split("\n\n")[0]
    return " ".join(parrafo.split()).replace("|", "/")


def _acceso(ruta, rol):
    """Indica si el rol puede abrir la ruta (sin contar la habilitación del módulo)."""
    return SI if not ruta["roles"] or rol in ruta["roles"] else NO


def _identificador(nombre):
    return nombre.replace(":", "_").replace("-", "_")


class Command(BaseCommand):
    help = "Genera documentacion/MAPA_NAVEGACION.md a partir de las rutas del sistema."

    def add_arguments(self, parser):
        parser.add_argument("--salida", default=None, help="Archivo de salida (Markdown).")

    def handle(self, *args, **opciones):
        salida = Path(opciones["salida"] or settings.RUTA_BASE / SALIDA_PREDETERMINADA)
        salida.parent.mkdir(parents=True, exist_ok=True)
        rutas = recorrer_rutas()
        salida.write_text(self.armar_documento(rutas), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Mapa de navegación generado: {salida} ({len(rutas)} rutas)"))

    # ------------------------------------------------------------------
    # Documento
    # ------------------------------------------------------------------

    def armar_documento(self, rutas):
        por_nombre = {ruta["nombre"]: ruta for ruta in rutas}
        partes = [
            "# Mapa de navegación — Contanika",
            "",
            f"Entregable 3.3. Generado el {timezone.localdate():%d/%m/%Y} con "
            "`python gestionar.py generar_mapa_navegacion` a partir de las rutas del sistema. "
            "No editar a mano: volver a generarlo cuando cambien las rutas.",
            "",
            f"El sistema tiene **{len(rutas)} rutas**: "
            f"{sum(1 for r in rutas if 'GET' in r['metodos'])} pantallas o descargas (GET) y "
            f"{sum(1 for r in rutas if r['metodos'] == ['POST'])} acciones que solo reciben "
            "formularios (POST).",
            "",
            "## 1. Navegación general",
            "",
            "Toda pantalla exige sesión, salvo la página web de inicio, el inicio de sesión, `robots.txt` "
            "y el enlace firmado del PDF de la cuenta de cobro que recibe el cliente. El menú lateral, "
            "la campana de vencimientos, la ayuda y el perfil están disponibles desde cualquier pantalla.",
            "",
            "```mermaid",
            "flowchart LR",
            '    web(["Página web de inicio"]) --> inicio(["Inicio de sesión"])',
            '    inicio --> panel["Panel principal"]',
        ]
        for titulo, elementos in SECCIONES_MENU:
            partes.append(f'    subgraph {_identificador(titulo)}["Menú · {titulo}"]')
            for etiqueta, nombre_ruta, _icono, codigo in elementos:
                if nombre_ruta == "seguridad:panel":
                    continue
                marca = f" ({codigo})" if codigo else ""
                partes.append(f'        {_identificador(nombre_ruta)}["{etiqueta}{marca}"]')
            partes.append("    end")
        for _titulo, elementos in SECCIONES_MENU:
            for _etiqueta, nombre_ruta, _icono, _codigo in elementos:
                if nombre_ruta != "seguridad:panel":
                    partes.append(f"    panel --> {_identificador(nombre_ruta)}")
        partes += [
            '    panel --> barra["Barra superior"]',
            '    barra --> ayuda["Ayuda y guías paso a paso"]',
            '    barra --> perfil["Mi perfil"]',
            '    barra --> campana["Campana de vencimientos"]',
            '    barra --> buscador["Buscador de clientes"]',
            "    buscador --> clientes_lista",
            "    campana --> calendario_calendario",
            "```",
            "",
            "## 2. Rutas por módulo",
            "",
            "Columnas de rol: «Sí» = el rol puede abrir la ruta; «—» = recibe 403. Además, un módulo "
            "inhabilitado para el rol (Equipo y roles → Módulos por rol) bloquea todas sus rutas. "
            "Dentro de una ruta permitida, los datos se restringen según las reglas de cada módulo "
            "(por ejemplo, el Contador Junior solo escribe en sus clientes asignados).",
            "",
        ]
        grupos = {}
        for ruta in rutas:
            grupos.setdefault(ruta["modulo"], []).append(ruta)
        for codigo in sorted(grupos, key=lambda valor: valor or ""):
            titulo = (
                f"{codigo} · {NOMBRES_MODULO.get(codigo, codigo)}"
                if codigo
                else "Sin módulo (sesión, panel, ayuda)"
            )
            partes += [f"### {titulo}", ""]
            partes += self._diagrama_modulo(codigo, grupos[codigo], por_nombre)
            partes += [
                "| Ruta | Nombre | Métodos | Admin. | Senior | Junior | Qué hace |",
                "|---|---|---|---|---|---|---|",
            ]
            for ruta in grupos[codigo]:
                accesos = [SI if ruta["publica"] else _acceso(ruta, rol) for rol in ROLES]
                nota = " *(pública, sin sesión)*" if ruta["publica"] else ""
                partes.append(
                    f"| `{ruta['ruta']}` | `{ruta['nombre']}` | {' · '.join(ruta['metodos']) or 'GET'} | "
                    f"{' | '.join(accesos)} | {ruta['descripcion']}{nota} |"
                )
            partes.append("")
        partes += self._matriz_resumen(grupos)
        return "\n".join(partes) + "\n"

    def _diagrama_modulo(self, codigo, rutas, por_nombre):
        """Diagrama del módulo: de su entrada del menú a cada pantalla (GET) sin parámetros de más."""
        entrada = next(
            (
                nombre_ruta
                for _titulo, elementos in SECCIONES_MENU
                for _etiqueta, nombre_ruta, _icono, codigo_menu in elementos
                if codigo and codigo_menu == codigo
            ),
            None,
        )
        if entrada is None or entrada not in por_nombre:
            return []
        lineas = [
            "```mermaid",
            "flowchart LR",
            f'    {_identificador(entrada)}(["{por_nombre[entrada]["ruta"]}"])',
        ]
        for ruta in rutas:
            if ruta["nombre"] == entrada or "GET" not in ruta["metodos"]:
                continue
            etiqueta = ruta["nombre"].split(":")[1].replace("_", " ")
            lineas.append(f'    {_identificador(entrada)} --> {_identificador(ruta["nombre"])}["{etiqueta}"]')
        lineas += ["```", ""]
        return lineas

    def _matriz_resumen(self, grupos):
        """Cuántas rutas de cada módulo puede abrir cada rol."""
        lineas = [
            "## 3. Resumen de acceso por rol y módulo",
            "",
            "Número de rutas que cada rol puede abrir, sobre el total del módulo.",
            "",
            "| Módulo | Rutas | Administrador | Contador Senior | Contador Junior |",
            "|---|---|---|---|---|",
        ]
        for codigo in sorted(grupos, key=lambda valor: valor or ""):
            rutas = grupos[codigo]
            cuentas = [str(sum(1 for ruta in rutas if _acceso(ruta, rol) == SI)) for rol in ROLES]
            nombre = f"{codigo} · {NOMBRES_MODULO.get(codigo, codigo)}" if codigo else "Sin módulo"
            lineas.append(f"| {nombre} | {len(rutas)} | {' | '.join(cuentas)} |")
        restringidas = sorted(f"`{ruta}`" for ruta in ROLES_POR_RUTA)
        lineas += [
            "",
            f"Entradas del menú que además se ocultan por rol: {', '.join(restringidas)}.",
        ]
        return lineas
