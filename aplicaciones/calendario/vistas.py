"""
Vistas del módulo 2: calendario, vencimientos, tabla DIAN, alertas y anotaciones.

Permisos (CU002 y especificaciones del Módulo 2):
- Todos los roles consultan el calendario y el listado; el Contador Junior
  solo ve los vencimientos de sus clientes asignados.
- Administrador y Contador Senior gestionan vencimientos, alertas y el
  cálculo masivo; el Administrador además carga la tabla DIAN.
- Las anotaciones las crea cualquier usuario; solo el autor o un
  Administrador las elimina.
"""

import calendar
from datetime import date, timedelta

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView, View

from aplicaciones.comunes.paginacion import PaginacionMixin
from aplicaciones.seguridad.models import Modulo, Rol
from aplicaciones.seguridad.permisos import ModuloHabilitadoMixin, RolRequeridoMixin

from .formularios import (
    AnotacionCalendarioForm,
    CambiarEstadoForm,
    ConfiguracionAlertaForm,
    FiltroCalendarioForm,
    FiltroFechaMixin,
    ImportarDianForm,
    TablaReferenciaDianForm,
    VencimientoManualForm,
)
from .importacion import generar_plantilla_dian, importar_dian
from .models import AnotacionCalendario, ConfiguracionAlerta, Vencimiento
from .selectores import (
    anotaciones_visibles,
    filtrar_vencimientos,
    opciones_filtro_calendario,
    vencimientos_proximos,
    vencimientos_vencidos,
)
from .servicios import (
    cambiar_estado_presentacion,
    eliminar_alerta,
    eliminar_anotacion,
    generar_vencimientos_cliente,
    generar_vencimientos_masivo,
    guardar_alerta,
    guardar_anotacion,
    guardar_vencimiento_editado,
    guardar_vencimiento_manual,
    puede_actualizar_estado,
    validar_vencimiento,
)

ROLES_EDITAN = (Rol.ADMINISTRADOR, Rol.CONTADOR_SENIOR)
ROLES_ADMIN = (Rol.ADMINISTRADOR,)

DIAS_SEMANA = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
MESES = [
    "",
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


def _fecha_param(request, nombre, defecto):
    """Lee una fecha 'AAAA-MM-DD' de GET; devuelve el defecto si es inválida."""
    return FiltroFechaMixin.parse_fecha(request.GET.get(nombre)) or defecto


class CalendarioView(ModuloHabilitadoMixin, View):
    """
    Calendario en vista mensual, semanal o diaria.

    La grilla se construye en el servidor y los eventos (vencimientos y
    anotaciones) se entregan agrupados por día, sin JavaScript pesado.
    """

    codigo_modulo = Modulo.MOD02_CALENDARIO
    template_name = "calendario/calendario.html"

    def get(self, request):
        hoy = date.today()
        vista = request.GET.get("vista", "mes")
        if vista not in ("mes", "semana", "dia"):
            vista = "mes"

        fecha_base = _fecha_param(request, "fecha", hoy)

        if vista == "mes":
            fecha_inicio = fecha_base.replace(day=1)
            siguiente_mes = (fecha_inicio.replace(day=28) + timedelta(days=4)).replace(day=1)
            fecha_fin = siguiente_mes - timedelta(days=1)
        elif vista == "semana":
            fecha_inicio = fecha_base - timedelta(days=fecha_base.weekday())
            fecha_fin = fecha_inicio + timedelta(days=6)
        else:
            fecha_inicio = fecha_fin = fecha_base

        filtros = {
            "cliente": request.GET.get("cliente") or None,
            "ambito": request.GET.get("ambito") or None,
            "estado_presentacion": request.GET.get("estado_presentacion") or None,
            "tipo_obligacion": request.GET.get("tipo_obligacion") or None,
            "responsable": request.GET.get("responsable") or None,
            "origen": request.GET.get("origen") or None,
        }

        vencimientos = filtrar_vencimientos(
            request.user, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, **filtros
        )
        anotaciones = anotaciones_visibles(request.user, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

        eventos = {}
        for vencimiento in vencimientos:
            eventos.setdefault(vencimiento.fecha_vencimiento, []).append(
                {"tipo": "vencimiento", "objeto": vencimiento}
            )
        for anotacion in anotaciones:
            eventos.setdefault(anotacion.fecha, []).append({"tipo": "anotacion", "objeto": anotacion})

        contexto = {
            "vista": vista,
            "fecha_base": fecha_base,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "eventos": eventos,
            "dias_semana": DIAS_SEMANA,
            "nombre_mes": MESES[fecha_base.month],
            "formulario_filtro": FiltroCalendarioForm(
                request.GET or None,
                usuario=request.user,
                opciones=opciones_filtro_calendario(),
            ),
            "puede_editar": request.user.rol.nombre_rol in ROLES_EDITAN,
            "es_administrador": request.user.es_administrador,
            "hoy": hoy,
        }

        if vista == "mes":
            contexto["semanas"] = calendar.Calendar(firstweekday=0).monthdatescalendar(
                fecha_base.year, fecha_base.month
            )
            contexto["anterior"] = (fecha_inicio - timedelta(days=1)).replace(day=1)
            contexto["siguiente"] = (fecha_fin + timedelta(days=1)).replace(day=1)
        elif vista == "semana":
            contexto["dias"] = [fecha_inicio + timedelta(days=i) for i in range(7)]
            contexto["anterior"] = fecha_inicio - timedelta(days=7)
            contexto["siguiente"] = fecha_inicio + timedelta(days=7)
        else:
            contexto["anterior"] = fecha_base - timedelta(days=1)
            contexto["siguiente"] = fecha_base + timedelta(days=1)

        return render(request, self.template_name, contexto)


class ListaVencimientosView(ModuloHabilitadoMixin, PaginacionMixin, ListView):
    """Listado tabular de vencimientos con filtros desplegables."""

    codigo_modulo = Modulo.MOD02_CALENDARIO
    model = Vencimiento
    template_name = "calendario/lista.html"
    context_object_name = "vencimientos"
    PARAMETROS_LISTADO_COMPLETO = (
        "desde",
        "hasta",
        "cliente",
        "ambito",
        "estado_presentacion",
        "tipo_obligacion",
        "responsable",
        "origen",
        "page",
    )

    def get_queryset(self):
        parametros = self.request.GET
        return filtrar_vencimientos(
            self.request.user,
            fecha_inicio=FiltroFechaMixin.parse_fecha(parametros.get("desde")),
            fecha_fin=FiltroFechaMixin.parse_fecha(parametros.get("hasta")),
            cliente=parametros.get("cliente") or None,
            ambito=parametros.get("ambito") or None,
            estado_presentacion=parametros.get("estado_presentacion") or None,
            tipo_obligacion=parametros.get("tipo_obligacion") or None,
            responsable=parametros.get("responsable") or None,
            origen=parametros.get("origen") or None,
        )

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["formulario_filtro"] = FiltroCalendarioForm(
            self.request.GET or None,
            usuario=self.request.user,
            opciones=opciones_filtro_calendario(),
        )
        contexto["puede_editar"] = self.request.user.rol.nombre_rol in ROLES_EDITAN
        contexto["proximos"] = vencimientos_proximos(self.request.user)
        contexto["vencidos"] = vencimientos_vencidos(self.request.user)
        contexto["hoy"] = date.today()
        contexto["ayer"] = date.today() - timedelta(days=1)
        contexto["mostrar_completo"] = any(
            self.request.GET.get(parametro) for parametro in self.PARAMETROS_LISTADO_COMPLETO
        )
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto["querystring"] = parametros.urlencode()
        return contexto


class DetalleVencimientoView(ModuloHabilitadoMixin, DetailView):
    """Detalle del vencimiento con sus alertas configuradas."""

    codigo_modulo = Modulo.MOD02_CALENDARIO
    model = Vencimiento
    template_name = "calendario/detalle.html"
    context_object_name = "vencimiento"

    def get_queryset(self):
        return Vencimiento.objects.select_related("cliente", "responsable").prefetch_related("alertas")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["puede_editar"] = self.request.user.rol.nombre_rol in ROLES_EDITAN
        contexto["puede_actualizar_estado"] = puede_actualizar_estado(self.request.user, self.object)
        contexto["formulario_alerta"] = ConfiguracionAlertaForm()
        contexto["formulario_estado"] = CambiarEstadoForm(
            initial={"estado_presentacion": self.object.estado_presentacion}
        )
        return contexto


class CrearVencimientoView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Registra un vencimiento manual (distrital, municipal o caso especial)."""

    codigo_modulo = Modulo.MOD02_CALENDARIO
    roles_permitidos = ROLES_EDITAN
    template_name = "calendario/vencimiento_formulario.html"

    def get(self, request):
        inicial = {}
        # Permite llegar desde el perfil del cliente con el cliente preseleccionado.
        if request.GET.get("cliente"):
            inicial["cliente"] = request.GET["cliente"]
        return render(
            request,
            self.template_name,
            {
                "formulario": VencimientoManualForm(usuario=request.user, initial=inicial),
                "accion": "crear",
                "opciones": opciones_filtro_calendario(),
            },
        )

    def post(self, request):
        formulario = VencimientoManualForm(request.POST, usuario=request.user)
        if formulario.is_valid():
            vencimiento = guardar_vencimiento_manual(formulario, request.user)
            messages.success(request, "El vencimiento se registró correctamente.")
            return redirect("calendario:detalle", pk=vencimiento.pk)
        return render(
            request,
            self.template_name,
            {
                "formulario": formulario,
                "accion": "crear",
                "opciones": opciones_filtro_calendario(),
            },
        )


class EditarVencimientoView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Edita un vencimiento existente; la fecha siempre es editable."""

    codigo_modulo = Modulo.MOD02_CALENDARIO
    roles_permitidos = ROLES_EDITAN
    template_name = "calendario/vencimiento_formulario.html"

    def get_object(self, pk):
        return get_object_or_404(Vencimiento, pk=pk)

    def get(self, request, pk):
        vencimiento = self.get_object(pk)
        return render(
            request,
            self.template_name,
            {
                "formulario": VencimientoManualForm(instance=vencimiento, usuario=request.user),
                "accion": "editar",
                "vencimiento": vencimiento,
                "opciones": opciones_filtro_calendario(),
            },
        )

    def post(self, request, pk):
        vencimiento = self.get_object(pk)
        formulario = VencimientoManualForm(request.POST, instance=vencimiento, usuario=request.user)
        if formulario.is_valid():
            guardar_vencimiento_editado(formulario)
            messages.success(request, "El vencimiento se actualizó correctamente.")
            return redirect("calendario:detalle", pk=vencimiento.pk)
        return render(
            request,
            self.template_name,
            {
                "formulario": formulario,
                "accion": "editar",
                "vencimiento": vencimiento,
                "opciones": opciones_filtro_calendario(),
            },
        )


class CambiarEstadoVencimientoView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Actualiza el estado de presentación de un vencimiento (el Junior, solo los de sus clientes)."""

    codigo_modulo = Modulo.MOD02_CALENDARIO
    roles_permitidos = ROLES_EDITAN + (Rol.CONTADOR_JUNIOR,)

    def post(self, request, pk):
        vencimiento = get_object_or_404(Vencimiento.objects.select_related("cliente"), pk=pk)
        if not puede_actualizar_estado(request.user, vencimiento):
            raise PermissionDenied("Solo puede actualizar vencimientos de sus clientes.")
        formulario = CambiarEstadoForm(request.POST)
        if formulario.is_valid():
            cambiar_estado_presentacion(vencimiento, formulario.cleaned_data["estado_presentacion"])
            messages.success(request, "El estado de presentación se actualizó.")
        return redirect("calendario:detalle", pk=vencimiento.pk)


class ValidarVencimientoView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Marca un vencimiento automático DIAN como validado o pendiente."""

    codigo_modulo = Modulo.MOD02_CALENDARIO
    roles_permitidos = ROLES_EDITAN

    def post(self, request, pk):
        vencimiento = get_object_or_404(Vencimiento, pk=pk)
        validar_vencimiento(vencimiento, validado=request.POST.get("accion") == "validar")
        messages.success(request, "El estado de validación se actualizó.")
        return redirect("calendario:detalle", pk=vencimiento.pk)


class GenerarVencimientosView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Calcula los vencimientos DIAN de todos los clientes activos."""

    codigo_modulo = Modulo.MOD02_CALENDARIO
    roles_permitidos = ROLES_EDITAN

    def post(self, request):
        resumen = generar_vencimientos_masivo(request.user)
        messages.success(
            request,
            f"Cálculo completado: {resumen['clientes']} clientes, "
            f"{resumen['creados']} vencimientos creados, "
            f"{resumen['actualizados']} actualizados, "
            f"{resumen['omitidos']} sin cambios, "
            f"{resumen['sin_grupo']} clientes sin grupo calculable.",
        )
        if resumen["sin_referencia"]:
            messages.warning(
                request,
                "Estas obligaciones no generaron ningún vencimiento porque no tienen "
                "fechas cargadas en la tabla DIAN: "
                + ", ".join(resumen["sin_referencia"])
                + ". Cárguelas en Calendario → Cargar tabla DIAN.",
            )
        return redirect("calendario:lista")


class CalcularVencimientosClienteView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Calcula los vencimientos DIAN de un solo cliente, desde su perfil."""

    codigo_modulo = Modulo.MOD02_CALENDARIO
    roles_permitidos = ROLES_EDITAN

    def post(self, request, pk_cliente):
        from aplicaciones.clientes.models import Cliente

        cliente = get_object_or_404(Cliente, pk=pk_cliente)
        resumen = generar_vencimientos_cliente(cliente, request.user)
        if resumen["sin_grupo"]:
            messages.warning(
                request,
                "Este cliente no tiene grupo DIAN calculable (documento extranjero); "
                "registre sus vencimientos de forma manual.",
            )
        else:
            messages.success(
                request,
                f"Cálculo completado: {resumen['creados']} vencimientos creados, "
                f"{resumen['actualizados']} actualizados, "
                f"{resumen['omitidos']} sin cambios.",
            )
        if resumen["sin_coincidencia"]:
            messages.warning(
                request,
                "No hay fecha DIAN para el documento de este cliente en: "
                + ", ".join(resumen["sin_coincidencia"])
                + ". Revise que esas obligaciones correspondan a su tipo de persona.",
            )
        if not cliente.obligaciones.exists():
            messages.info(
                request,
                "Este cliente no tiene obligaciones marcadas: edítelo y elija qué impuestos "
                "o anticipos presenta para calcular sus vencimientos.",
            )
        if resumen["sin_referencia"]:
            messages.warning(
                request,
                "Estas obligaciones no generaron vencimiento porque no tienen fechas "
                "cargadas en la tabla DIAN: "
                + ", ".join(resumen["sin_referencia"])
                + ". Cárguelas en Calendario → Cargar tabla DIAN.",
            )
        return redirect("clientes:detalle", pk=cliente.pk)


class CargarDianView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Carga manual de una fila de la tabla de referencia DIAN (Administrador)."""

    codigo_modulo = Modulo.MOD02_CALENDARIO
    roles_permitidos = ROLES_ADMIN
    template_name = "calendario/cargar_dian.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {
                "formulario": TablaReferenciaDianForm(),
                "formulario_importar": ImportarDianForm(),
                "opciones": opciones_filtro_calendario(),
            },
        )

    def post(self, request):
        formulario = TablaReferenciaDianForm(request.POST)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, "La referencia DIAN se guardó correctamente.")
            return redirect("calendario:cargar_dian")
        return render(
            request,
            self.template_name,
            {
                "formulario": formulario,
                "formulario_importar": ImportarDianForm(),
                "opciones": opciones_filtro_calendario(),
            },
        )


class ImportarDianView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Carga masiva de la tabla DIAN desde Excel (Administrador)."""

    codigo_modulo = Modulo.MOD02_CALENDARIO
    roles_permitidos = ROLES_ADMIN

    def post(self, request):
        formulario = ImportarDianForm(request.POST, request.FILES)
        if formulario.is_valid():
            try:
                resultado = importar_dian(formulario.cleaned_data["archivo"])
                messages.success(
                    request,
                    f"Importación completada: {resultado['cargadas']} filas cargadas, "
                    f"{resultado['omitidas']} actualizadas, "
                    f"{len(resultado['errores'])} con error.",
                )
                for error in resultado["errores"][:10]:
                    messages.warning(request, error)
            except ValueError as error:
                messages.error(request, str(error))
        else:
            messages.error(request, "Revise el archivo: solo .xlsx de máximo 5 MB.")
        return redirect("calendario:cargar_dian")


class DescargarPlantillaDianView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Descarga la plantilla Excel de la tabla DIAN (Administrador)."""

    codigo_modulo = Modulo.MOD02_CALENDARIO
    roles_permitidos = ROLES_ADMIN

    def get(self, request):
        archivo = generar_plantilla_dian()
        respuesta = HttpResponse(
            archivo.getvalue(),
            content_type=("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        )
        respuesta["Content-Disposition"] = 'attachment; filename="plantilla_calendario_dian.xlsx"'
        return respuesta


class CrearAlertaView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Agrega una alerta automática a un vencimiento."""

    codigo_modulo = Modulo.MOD02_CALENDARIO
    roles_permitidos = ROLES_EDITAN

    def post(self, request, pk_vencimiento):
        vencimiento = get_object_or_404(Vencimiento, pk=pk_vencimiento)
        formulario = ConfiguracionAlertaForm(request.POST)
        if formulario.is_valid():
            guardar_alerta(formulario, vencimiento)
            messages.success(request, "La alerta se configuró correctamente.")
        else:
            messages.error(request, "Revise los datos de la alerta.")
        return redirect("calendario:detalle", pk=vencimiento.pk)


class EliminarAlertaView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Elimina una alerta configurada."""

    codigo_modulo = Modulo.MOD02_CALENDARIO
    roles_permitidos = ROLES_EDITAN

    def post(self, request, pk):
        alerta = get_object_or_404(ConfiguracionAlerta, pk=pk)
        vencimiento_pk = alerta.vencimiento_id
        eliminar_alerta(alerta)
        messages.success(request, "La alerta se eliminó correctamente.")
        return redirect("calendario:detalle", pk=vencimiento_pk)


class CrearAnotacionView(ModuloHabilitadoMixin, View):
    """Crea una anotación libre del calendario (cualquier rol)."""

    codigo_modulo = Modulo.MOD02_CALENDARIO
    template_name = "calendario/anotacion_formulario.html"

    def get(self, request):
        inicial = {}
        fecha = FiltroFechaMixin.parse_fecha(request.GET.get("fecha"))
        if fecha:
            inicial["fecha"] = fecha
        return render(
            request,
            self.template_name,
            {"formulario": AnotacionCalendarioForm(initial=inicial)},
        )

    def post(self, request):
        formulario = AnotacionCalendarioForm(request.POST)
        if formulario.is_valid():
            anotacion = guardar_anotacion(
                formulario,
                request.user,
                destinatarios=formulario.cleaned_data.get("destinatarios"),
            )
            messages.success(request, "La anotación se guardó correctamente.")
            return redirect(f"{redirect('calendario:calendario').url}?fecha={anotacion.fecha}")
        return render(request, self.template_name, {"formulario": formulario})


class EliminarAnotacionView(ModuloHabilitadoMixin, View):
    """Elimina una anotación; solo el autor o un Administrador."""

    codigo_modulo = Modulo.MOD02_CALENDARIO

    def post(self, request, pk):
        anotacion = get_object_or_404(AnotacionCalendario, pk=pk)
        try:
            eliminar_anotacion(anotacion, request.user)
            messages.success(request, "La anotación se eliminó correctamente.")
        except PermissionDenied as error:
            messages.error(request, str(error))
        return redirect("calendario:calendario")
