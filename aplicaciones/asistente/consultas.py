"""
Catálogo de consultas del asistente: las preguntas de validación que el
equipo se hace a diario, respondidas con los datos del sistema.

Cada consulta reutiliza los selectores de su módulo, que ya aplican la
visibilidad de cada rol (por ejemplo, la cartera del Contador Senior y del
Junior se limita a sus clientes asignados). Una consulta solo se ofrece a
quien tiene habilitado su módulo. Ninguna toca credenciales de clientes ni
modifica datos.

Para agregar una consulta: escribir su función `(usuario, cliente, hoy) ->
Respuesta` y registrarla en `CONSULTAS`.
"""

from dataclasses import dataclass, field
from datetime import timedelta

from django.db.models import F
from django.urls import reverse
from django.utils import timezone

from aplicaciones.calendario.models import Vencimiento
from aplicaciones.calendario.selectores import vencimientos_visibles
from aplicaciones.clientes.models import Cliente
from aplicaciones.finanzas.selectores import cartera, clientes_para_cobro, con_abonos, cuentas_cobro_visibles
from aplicaciones.finanzas.templatetags.finanzas_tags import formato_pesos
from aplicaciones.hallazgos.models import Hallazgo
from aplicaciones.hallazgos.selectores import hallazgos_visibles
from aplicaciones.seguridad.models import Modulo
from aplicaciones.tareas.models import Tarea
from aplicaciones.tareas.selectores import tareas_visibles

# Filas que se muestran en una respuesta; el resto se ve en el módulo.
LIMITE_FILAS = 15
DIAS_SEMANA = 7


class ClienteNoPermitido(Exception):
    """El cliente pedido no existe o el usuario no puede consultarlo en esta pregunta."""


@dataclass(frozen=True)
class Respuesta:
    """Resultado de una consulta, listo para mostrarse como tabla corta."""

    titulo: str
    columnas: tuple
    filas: list
    total: int
    vacio: str
    url: str = ""
    etiqueta_url: str = ""
    nota: str = ""

    @property
    def omitidas(self):
        return self.total - len(self.filas)

    @property
    def filas_con_columnas(self):
        """Cada fila como pares (columna, valor): en el teléfono la tabla se apila como tarjetas."""
        return [list(zip(self.columnas, fila, strict=True)) for fila in self.filas]


@dataclass(frozen=True)
class Consulta:
    """Pregunta del asistente y la función que la responde."""

    slug: str
    pregunta: str
    descripcion: str
    icono: str
    modulo: str
    funcion: object = field(repr=False)
    pide_cliente: bool = False
    # Clientes que el usuario puede elegir en esta pregunta: función (usuario) -> QuerySet.
    clientes: object = field(default=None, repr=False)

    def opciones_cliente(self, usuario):
        if not self.pide_cliente:
            return []
        return [(c.pk, f"{c.nombre_razon_social} · {c.nit_cedula}") for c in self.clientes(usuario)]


# ---------------------------------------------------------------------------
# Formato
# ---------------------------------------------------------------------------


def _fecha(valor):
    return valor.strftime("%d/%m/%Y") if valor else "Sin fecha"


def _nombre(usuario):
    return usuario.nombre if usuario else "Sin asignar"


def _recortar(consulta):
    """Total de registros y los primeros `LIMITE_FILAS` (acepta QuerySet o lista)."""
    if isinstance(consulta, list):
        return len(consulta), consulta[:LIMITE_FILAS]
    return consulta.count(), list(consulta[:LIMITE_FILAS])


def _estado_vencimiento(vencimiento, hoy):
    if vencimiento.fecha_vencimiento < hoy:
        return f"{vencimiento.estado_presentacion} · vencido"
    return vencimiento.estado_presentacion


# ---------------------------------------------------------------------------
# Clientes elegibles
# ---------------------------------------------------------------------------


def _clientes_activos(usuario):
    """Todo el equipo consulta todos los clientes y su calendario (decisión del 7-oct-2026)."""
    return Cliente.objects.filter(estado=Cliente.ACTIVO).order_by("nombre_razon_social")


# ---------------------------------------------------------------------------
# Calendario
# ---------------------------------------------------------------------------


def _vencimientos_sin_presentar(usuario):
    return vencimientos_visibles(usuario).exclude(estado_presentacion=Vencimiento.PRESENTADA)


def _filas_vencimientos(vencimientos, hoy, con_cliente=True):
    filas = []
    for v in vencimientos:
        fila = [_fecha(v.fecha_vencimiento)]
        if con_cliente:
            fila.append(v.cliente.nombre_razon_social)
        fila += [v.tipo_obligacion, _estado_vencimiento(v, hoy), _nombre(v.responsable)]
        filas.append(tuple(fila))
    return filas


def vencimientos_semana(usuario, cliente=None, hoy=None):
    hoy = hoy or timezone.localdate()
    fin = hoy + timedelta(days=DIAS_SEMANA - 1)
    consulta = (
        _vencimientos_sin_presentar(usuario)
        .filter(fecha_vencimiento__range=(hoy, fin))
        .order_by("fecha_vencimiento", "cliente__nombre_razon_social")
    )
    total, vencimientos = _recortar(consulta)
    return Respuesta(
        titulo=f"Vencimientos sin presentar del {_fecha(hoy)} al {_fecha(fin)}: {total}",
        columnas=("Fecha", "Cliente", "Obligación", "Estado", "Responsable"),
        filas=_filas_vencimientos(vencimientos, hoy),
        total=total,
        vacio="No hay vencimientos pendientes en los próximos 7 días.",
        url=reverse("calendario:lista"),
        etiqueta_url="Ver el listado de vencimientos",
    )


def vencimientos_atrasados(usuario, cliente=None, hoy=None):
    hoy = hoy or timezone.localdate()
    consulta = (
        _vencimientos_sin_presentar(usuario)
        .filter(fecha_vencimiento__lt=hoy)
        .order_by("fecha_vencimiento", "cliente__nombre_razon_social")
    )
    total, vencimientos = _recortar(consulta)
    return Respuesta(
        titulo=f"Vencimientos con fecha pasada y sin presentar: {total}",
        columnas=("Fecha", "Cliente", "Obligación", "Estado", "Responsable"),
        filas=_filas_vencimientos(vencimientos, hoy),
        total=total,
        vacio="No hay vencimientos atrasados. Todo lo vencido está presentado.",
        url=reverse("calendario:lista"),
        etiqueta_url="Ver el listado de vencimientos",
        nota="Si alguno ya se presentó, márquelo como «Presentada» en el calendario." if total else "",
    )


def vencimientos_cliente(usuario, cliente=None, hoy=None):
    hoy = hoy or timezone.localdate()
    consulta = _vencimientos_sin_presentar(usuario).filter(cliente=cliente).order_by("fecha_vencimiento")
    total, vencimientos = _recortar(consulta)
    return Respuesta(
        titulo=f"Vencimientos sin presentar de {cliente.nombre_razon_social}: {total}",
        columnas=("Fecha", "Obligación", "Estado", "Responsable"),
        filas=_filas_vencimientos(vencimientos, hoy, con_cliente=False),
        total=total,
        vacio="Este cliente no tiene vencimientos pendientes.",
        url=reverse("clientes:detalle", args=[cliente.pk]),
        etiqueta_url="Ver la ficha del cliente",
    )


# ---------------------------------------------------------------------------
# Tareas
# ---------------------------------------------------------------------------


def _tareas_abiertas(usuario):
    return (
        tareas_visibles(usuario)
        .exclude(estado=Tarea.TERMINADO)
        .order_by(F("fecha_vencimiento").asc(nulls_last=True), "titulo")
    )


def _fecha_tarea(tarea, hoy):
    atrasada = tarea.fecha_vencimiento and tarea.fecha_vencimiento < hoy
    return _fecha(tarea.fecha_vencimiento) + (" · atrasada" if atrasada else "")


def mis_tareas(usuario, cliente=None, hoy=None):
    hoy = hoy or timezone.localdate()
    total, tareas = _recortar(_tareas_abiertas(usuario).filter(responsable=usuario))
    filas = [
        (t.titulo, t.cliente.nombre_razon_social, t.prioridad, t.estado, _fecha_tarea(t, hoy)) for t in tareas
    ]
    return Respuesta(
        titulo=f"Sus tareas sin terminar: {total}",
        columnas=("Tarea", "Cliente", "Prioridad", "Estado", "Fecha límite"),
        filas=filas,
        total=total,
        vacio="No tiene tareas pendientes asignadas.",
        url=reverse("tareas:tablero"),
        etiqueta_url="Abrir el tablero de tareas",
    )


def tareas_atrasadas(usuario, cliente=None, hoy=None):
    hoy = hoy or timezone.localdate()
    total, tareas = _recortar(_tareas_abiertas(usuario).filter(fecha_vencimiento__lt=hoy))
    filas = [
        (t.titulo, t.cliente.nombre_razon_social, _nombre(t.responsable), t.estado, _fecha_tarea(t, hoy))
        for t in tareas
    ]
    return Respuesta(
        titulo=f"Tareas con fecha límite vencida y sin terminar: {total}",
        columnas=("Tarea", "Cliente", "Responsable", "Estado", "Fecha límite"),
        filas=filas,
        total=total,
        vacio="No hay tareas atrasadas.",
        url=reverse("tareas:tablero"),
        etiqueta_url="Abrir el tablero de tareas",
    )


# ---------------------------------------------------------------------------
# Hallazgos
# ---------------------------------------------------------------------------


def hallazgos_abiertos(usuario, cliente=None, hoy=None):
    consulta = (
        hallazgos_visibles(usuario)
        .exclude(estado=Hallazgo.CERRADO)
        .order_by("cliente__nombre_razon_social", "-fecha_inicio_periodo")
    )
    total, hallazgos = _recortar(consulta)
    filas = [
        (h.cliente.nombre_razon_social, h.tipo_hallazgo, h.prioridad, h.estado, _nombre(h.responsable))
        for h in hallazgos
    ]
    return Respuesta(
        titulo=f"Hallazgos sin cerrar: {total}",
        columnas=("Cliente", "Tipo", "Prioridad", "Estado", "Responsable"),
        filas=filas,
        total=total,
        vacio="No hay hallazgos abiertos.",
        url=reverse("hallazgos:lista"),
        etiqueta_url="Ver los hallazgos",
    )


# ---------------------------------------------------------------------------
# Finanzas (respeta la restricción a clientes asignados de `finanzas.selectores`)
# ---------------------------------------------------------------------------


def cartera_pendiente(usuario, cliente=None, hoy=None):
    hoy = hoy or timezone.localdate()
    filas_cartera = cartera(usuario, hoy=hoy)
    total, primeras = _recortar(filas_cartera)
    saldo_total = sum((fila["saldo"] for fila in filas_cartera), 0)
    filas = [
        (
            fila["cliente"].nombre_razon_social,
            formato_pesos(fila["saldo"]),
            str(fila["cuentas_pendientes"]),
            f"{fila['dias_mora']} días" if fila["dias_mora"] else "Al día",
        )
        for fila in primeras
    ]
    return Respuesta(
        titulo=f"Clientes con saldo pendiente: {total}",
        columnas=("Cliente", "Saldo", "Cuentas pendientes", "Mora"),
        filas=filas,
        total=total,
        vacio="Ningún cliente tiene saldo pendiente.",
        url=reverse("finanzas:cartera"),
        etiqueta_url="Abrir la cartera",
        nota=f"Saldo total pendiente: {formato_pesos(saldo_total)}." if total else "",
    )


def saldo_cliente(usuario, cliente=None, hoy=None):
    hoy = hoy or timezone.localdate()
    cuentas = [
        cuenta
        for cuenta in con_abonos(cuentas_cobro_visibles(usuario).filter(cliente=cliente))
        if cuenta.saldo > 0
    ]
    cuentas.sort(key=lambda cuenta: cuenta.fecha_vencimiento_pago)
    total, primeras = _recortar(cuentas)
    saldo_total = sum((cuenta.saldo for cuenta in cuentas), 0)
    filas = [
        (
            f"N.º {c.pk}",
            formato_pesos(c.valor_total),
            formato_pesos(c.saldo),
            _fecha(c.fecha_vencimiento_pago) + (" · en mora" if c.fecha_vencimiento_pago < hoy else ""),
        )
        for c in primeras
    ]
    return Respuesta(
        titulo=f"Saldo pendiente de {cliente.nombre_razon_social}: {formato_pesos(saldo_total)}",
        columnas=("Cuenta de cobro", "Valor", "Saldo", "Fecha de pago"),
        filas=filas,
        total=total,
        vacio="Este cliente no tiene cuentas de cobro con saldo pendiente.",
        url=reverse("finanzas:historico"),
        etiqueta_url="Ver las cuentas de cobro",
    )


# ---------------------------------------------------------------------------
# Catálogo
# ---------------------------------------------------------------------------

CONSULTAS = (
    Consulta(
        slug="vencimientos-semana",
        pregunta="¿Qué vence esta semana?",
        descripcion="Vencimientos sin presentar de hoy a 7 días, de todos los clientes.",
        icono="bi-calendar-week",
        modulo=Modulo.MOD02_CALENDARIO,
        funcion=vencimientos_semana,
    ),
    Consulta(
        slug="vencimientos-atrasados",
        pregunta="¿Qué vencimientos están atrasados?",
        descripcion="Vencimientos con fecha pasada que todavía no se marcan como presentados.",
        icono="bi-exclamation-triangle",
        modulo=Modulo.MOD02_CALENDARIO,
        funcion=vencimientos_atrasados,
    ),
    Consulta(
        slug="vencimientos-cliente",
        pregunta="¿Qué tiene pendiente un cliente?",
        descripcion="Vencimientos sin presentar de un cliente, atrasados y próximos.",
        icono="bi-person-lines-fill",
        modulo=Modulo.MOD02_CALENDARIO,
        funcion=vencimientos_cliente,
        pide_cliente=True,
        clientes=_clientes_activos,
    ),
    Consulta(
        slug="mis-tareas",
        pregunta="¿Qué tareas tengo pendientes?",
        descripcion="Tareas asignadas a usted que no están terminadas.",
        icono="bi-person-check",
        modulo=Modulo.MOD03_TAREAS,
        funcion=mis_tareas,
    ),
    Consulta(
        slug="tareas-atrasadas",
        pregunta="¿Qué tareas están atrasadas?",
        descripcion="Tareas del equipo con fecha límite vencida y sin terminar.",
        icono="bi-hourglass-bottom",
        modulo=Modulo.MOD03_TAREAS,
        funcion=tareas_atrasadas,
    ),
    Consulta(
        slug="hallazgos-abiertos",
        pregunta="¿Qué hallazgos siguen abiertos?",
        descripcion="Hallazgos que no están cerrados, por cliente.",
        icono="bi-search",
        modulo=Modulo.MOD05_HALLAZGOS,
        funcion=hallazgos_abiertos,
    ),
    Consulta(
        slug="cartera-pendiente",
        pregunta="¿Qué clientes tienen saldo pendiente?",
        descripcion="Cartera por cliente con saldo y días en mora.",
        icono="bi-cash-stack",
        modulo=Modulo.MOD06_FINANZAS,
        funcion=cartera_pendiente,
    ),
    Consulta(
        slug="saldo-cliente",
        pregunta="¿Cuánto debe un cliente?",
        descripcion="Cuentas de cobro con saldo pendiente de un cliente.",
        icono="bi-wallet2",
        modulo=Modulo.MOD06_FINANZAS,
        funcion=saldo_cliente,
        pide_cliente=True,
        clientes=clientes_para_cobro,
    ),
)

POR_SLUG = {consulta.slug: consulta for consulta in CONSULTAS}


def consultas_visibles(usuario):
    """Consultas de los módulos que el rol del usuario tiene habilitados."""
    return [consulta for consulta in CONSULTAS if usuario.tiene_modulo_habilitado(consulta.modulo)]


def obtener_visible(usuario, slug):
    """La consulta del slug si el usuario puede usarla; None en otro caso."""
    consulta = POR_SLUG.get(slug)
    if consulta is None or not usuario.tiene_modulo_habilitado(consulta.modulo):
        return None
    return consulta


def ejecutar(usuario, consulta, cliente_id=None, hoy=None):
    """
    Responde la consulta. Si pide cliente, solo acepta uno de los que el
    usuario puede elegir en esa pregunta (evita consultar clientes ajenos
    cambiando el número en la petición).
    """
    cliente = None
    if consulta.pide_cliente:
        try:
            cliente = consulta.clientes(usuario).get(pk=int(cliente_id))
        except (TypeError, ValueError, Cliente.DoesNotExist) as error:
            raise ClienteNoPermitido from error
    return consulta.funcion(usuario, cliente=cliente, hoy=hoy)
