"""Pruebas del comando que genera el mapa de navegación (entregable 3.3)."""

from django.core.management import call_command

from aplicaciones.seguridad.management.commands.generar_mapa_navegacion import recorrer_rutas
from aplicaciones.seguridad.models import Modulo, Rol


def _por_nombre():
    return {ruta["nombre"]: ruta for ruta in recorrer_rutas()}


def test_recorre_todas_las_rutas_sin_el_admin():
    rutas = _por_nombre()
    assert {"seguridad:panel", "clientes:crear", "reportes:reporte", "seguridad:guia"} <= set(rutas)
    assert not any(nombre.startswith("admin") for nombre in rutas)


def test_toma_modulo_roles_y_metodos_de_cada_vista():
    rutas = _por_nombre()
    abono = rutas["finanzas:registrar_abono"]
    assert abono["modulo"] == Modulo.MOD06_FINANZAS
    assert abono["roles"] == (Rol.ADMINISTRADOR,)
    assert abono["metodos"] == ["POST"]
    assert rutas["clientes:crear"]["metodos"] == ["GET", "POST"]
    assert rutas["seguridad:ayuda"]["modulo"] is None and rutas["seguridad:ayuda"]["roles"] == ()
    assert rutas["finanzas:pdf_publico"]["publica"] is True


def test_genera_el_documento_con_diagramas_y_tablas(tmp_path):
    salida = tmp_path / "mapa.md"
    call_command("generar_mapa_navegacion", salida=str(salida))
    texto = salida.read_text(encoding="utf-8")
    assert texto.startswith("# Mapa de navegación — Contanika")
    assert "```mermaid" in texto and "MOD06 · Honorarios, cartera y cuentas de cobro" in texto
    assert (
        "| `/honorarios/cuentas-cobro/<int:pk>/abonos/` | `finanzas:registrar_abono` | POST | Sí | — | — |"
        in texto
    )
    assert "*(pública, sin sesión)*" in texto
    assert "## 3. Resumen de acceso por rol y módulo" in texto
