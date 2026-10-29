"""
Vistas del módulo 1: listado, detalle, creación, edición e inactivación.

Permisos (CU002): el Administrador y el Contador Senior gestionan los
clientes; el Contador Junior únicamente consulta los clientes que tiene
asignados. Todas las vistas exigen sesión y el módulo habilitado (RQF031).
"""

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from aplicaciones.comunes.paginacion import PaginacionMixin
from aplicaciones.seguridad.models import Modulo, Rol
from aplicaciones.seguridad.permisos import ModuloHabilitadoMixin, RolRequeridoMixin

from .formularios import ClienteForm, ClienteMunicipioFormSet, CredencialForm, ImportarClientesForm
from .importacion import generar_plantilla_clientes, importar_clientes
from .models import Cliente, Credencial
from .selectores import credenciales_visibles, filtrar_clientes, opciones_filtro
from .servicios import eliminar_credencial, guardar_cliente, guardar_credencial, inactivar_cliente

ROLES_EDITAN = (Rol.ADMINISTRADOR, Rol.CONTADOR_SENIOR)
# Quienes registran y editan clientes: el Contador Junior también (decisión del
# usuario, 1-oct-2026), pero no importa, inactiva ni toca credenciales.
ROLES_GESTIONAN = ROLES_EDITAN + (Rol.CONTADOR_JUNIOR,)
PREFIJO_MUNICIPIOS = "municipios"


class ListaClientesView(ModuloHabilitadoMixin, PaginacionMixin, ListView):
    """Listado de clientes con filtros desplegables y paginación configurable."""

    codigo_modulo = Modulo.MOD01_CLIENTES
    model = Cliente
    template_name = "clientes/lista.html"
    context_object_name = "clientes"

    def get_queryset(self):
        parametros = self.request.GET
        consulta = filtrar_clientes(
            busqueda=parametros.get("busqueda") or None,
            nit=parametros.get("nit") or None,
            regimen_tributario=parametros.get("regimen_tributario") or None,
            responsable_iva=parametros.get("responsable_iva") or None,
            estado=parametros.get("estado") or None,
        )
        return consulta

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["opciones"] = opciones_filtro()
        contexto["filtros"] = self.request.GET
        contexto["puede_editar"] = self.request.user.rol.nombre_rol in ROLES_EDITAN
        contexto["puede_gestionar"] = self.request.user.rol.nombre_rol in ROLES_GESTIONAN
        return contexto


# Pestañas de la ficha del cliente que dependen de otro módulo.
PESTANAS_POR_MODULO = {
    "vencimientos": Modulo.MOD02_CALENDARIO,
    "documentos": Modulo.MOD04_DOCUMENTOS,
    "hallazgos": Modulo.MOD05_HALLAZGOS,
    "honorarios": Modulo.MOD06_FINANZAS,
    "expediente": Modulo.MOD09_EXPEDIENTE,
    "comunicaciones": Modulo.MOD07_COMUNICACIONES,
}


class DetalleClienteView(ModuloHabilitadoMixin, DetailView):
    """Ficha completa del cliente con sus servicios, municipios y credenciales."""

    codigo_modulo = Modulo.MOD01_CLIENTES
    model = Cliente
    template_name = "clientes/detalle.html"
    context_object_name = "cliente"

    def get_queryset(self):
        consulta = Cliente.objects.select_related("responsable").prefetch_related(
            "servicios__tipo_servicio",
            "municipios_adicionales",
            "credenciales",
        )
        return consulta

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["puede_editar"] = self.request.user.rol.nombre_rol in ROLES_EDITAN
        contexto["puede_gestionar"] = self.request.user.rol.nombre_rol in ROLES_GESTIONAN
        # Las credenciales del Junior se limitan a sus clientes asignados.
        usuario = self.request.user
        contexto["a_cargo"] = (
            not usuario.es_contador_junior or self.object.responsable_id == usuario.id_usuario
        )
        contexto["puede_ver_credenciales"] = contexto["a_cargo"]
        contexto["es_administrador"] = usuario.es_administrador
        # Cada pestaña pertenece a un módulo: si el Administrador lo inhabilita
        # para el rol, la pestaña no aparece y sus datos no se consultan.
        pestanas = {
            nombre: usuario.tiene_modulo_habilitado(codigo) for nombre, codigo in PESTANAS_POR_MODULO.items()
        }
        contexto["pestanas"] = pestanas
        if pestanas["vencimientos"]:
            from aplicaciones.calendario.selectores import vencimientos_por_cliente

            contexto["vencimientos"] = vencimientos_por_cliente(usuario, self.object)
        if pestanas["documentos"]:
            from aplicaciones.documentos.selectores import documentos_del_cliente

            contexto["documentos"] = documentos_del_cliente(usuario, self.object)
        if pestanas["hallazgos"]:
            from aplicaciones.hallazgos.selectores import hallazgos_del_cliente

            contexto["hallazgos"] = hallazgos_del_cliente(usuario, self.object)
        if pestanas["honorarios"]:
            from aplicaciones.finanzas.selectores import (
                abonos_del_cliente,
                cuentas_del_cliente,
                honorario_del_cliente,
                saldo_del_cliente,
            )

            contexto["honorario"] = honorario_del_cliente(self.object)
            contexto["cuentas_cobro"] = cuentas_del_cliente(usuario, self.object)
            contexto["abonos"] = abonos_del_cliente(usuario, self.object)
            contexto["saldo_cliente"] = saldo_del_cliente(self.object)
        if pestanas["expediente"]:
            from aplicaciones.expediente.selectores import anotaciones_del_cliente

            contexto["anotaciones"] = anotaciones_del_cliente(usuario, self.object)
        if pestanas["comunicaciones"]:
            from aplicaciones.comunicaciones.selectores import comunicaciones_del_cliente
            from aplicaciones.comunicaciones.vistas import ROLES_REGISTRAN

            contexto["comunicaciones"] = comunicaciones_del_cliente(usuario, self.object)
            contexto["puede_registrar_comunicacion"] = usuario.rol.nombre_rol in ROLES_REGISTRAN
        return contexto


class MixinFormularioCliente:
    """Comportamiento común de las vistas de crear y editar cliente."""

    codigo_modulo = Modulo.MOD01_CLIENTES
    roles_permitidos = ROLES_GESTIONAN
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/formulario.html"
    success_url = reverse_lazy("clientes:lista")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario"] = self.request.user
        return kwargs

    def get_formset(self, datos=None):
        """Formset de municipios adicionales, con una fila vacía para agregar."""
        instancia = getattr(self, "object", None) or Cliente()
        return ClienteMunicipioFormSet(datos, instance=instancia, prefix=PREFIJO_MUNICIPIOS)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        # La plantilla usa el nombre `formulario`; Django entrega el formulario
        # en la clave `form` desde FormMixin, así que se expone con ambos nombres.
        contexto.setdefault("formulario", contexto.get("form"))
        contexto.setdefault("formset_municipios", self.get_formset())
        contexto["opciones"] = opciones_filtro()
        return contexto

    def guardar(self, formulario, formset):
        cliente = guardar_cliente(formulario, formset, self.request.user)
        self.object = cliente
        self.calcular_vencimientos(cliente)
        return cliente

    def calcular_vencimientos(self, cliente):
        """
        Calcula los vencimientos DIAN del cliente recién guardado y avisa el resultado.

        Si no marcó obligaciones, pregunta qué impuestos o anticipos presenta
        en lugar de dejar el calendario vacío sin explicación.
        """
        # Import local: calendario ya depende de clientes y evita el ciclo.
        from aplicaciones.calendario.servicios import generar_vencimientos_cliente

        peticion = self.request
        if not peticion.user.tiene_modulo_habilitado(Modulo.MOD02_CALENDARIO):
            return
        if not cliente.obligaciones.exists():
            messages.info(
                peticion,
                "Falta indicar qué impuestos o anticipos presenta este cliente (renta, IVA, "
                "retención en la fuente…). Edítelo y márquelos en «Obligaciones tributarias»: "
                "sus vencimientos se calcularán con su NIT o cédula.",
            )
            return
        resumen = generar_vencimientos_cliente(cliente, peticion.user)
        if resumen["sin_grupo"]:
            messages.warning(
                peticion,
                "Este documento no permite calcular vencimientos DIAN automáticamente "
                "(solo NIT o cédula numéricos); regístrelos de forma manual en el Calendario.",
            )
            return
        if resumen["creados"] or resumen["actualizados"]:
            messages.success(
                peticion,
                f"Vencimientos DIAN calculados: {resumen['creados']} nuevos y "
                f"{resumen['actualizados']} actualizados. Quedan pendientes de validar.",
            )
        if resumen["sin_coincidencia"]:
            messages.warning(
                peticion,
                "No hay fecha DIAN para el documento de este cliente en: "
                + ", ".join(resumen["sin_coincidencia"])
                + ". Revise que esas obligaciones correspondan a su tipo de persona.",
            )
        if resumen["sin_referencia"]:
            messages.warning(
                peticion,
                "Estas obligaciones no tienen fechas cargadas en la tabla DIAN: "
                + ", ".join(resumen["sin_referencia"])
                + ".",
            )


class CrearClienteView(MixinFormularioCliente, ModuloHabilitadoMixin, RolRequeridoMixin, CreateView):
    """Registra un cliente nuevo con sus municipios y servicios."""

    def post(self, request, *args, **kwargs):
        self.object = None
        formulario = self.get_form()
        formset = self.get_formset(request.POST)
        if formulario.is_valid() and formset.is_valid():
            self.guardar(formulario, formset)
            messages.success(request, "El cliente se creó correctamente.")
            return redirect(self.success_url)
        return self.render_to_response(self.get_context_data(form=formulario, formset_municipios=formset))


class EditarClienteView(MixinFormularioCliente, ModuloHabilitadoMixin, RolRequeridoMixin, UpdateView):
    """Actualiza la ficha de un cliente existente."""

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        formulario = self.get_form()
        formset = self.get_formset(request.POST)
        if formulario.is_valid() and formset.is_valid():
            self.guardar(formulario, formset)
            messages.success(request, "El cliente se actualizó correctamente.")
            return redirect("clientes:detalle", pk=self.object.pk)
        return self.render_to_response(self.get_context_data(form=formulario, formset_municipios=formset))


class InactivarClienteView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Inactiva un cliente conservando todo su historial."""

    codigo_modulo = Modulo.MOD01_CLIENTES
    roles_permitidos = ROLES_EDITAN

    def post(self, request, pk):
        cliente = get_object_or_404(Cliente, pk=pk)
        inactivar_cliente(cliente)
        messages.success(request, "El cliente se inactivó correctamente; su historial se conserva.")
        return redirect("clientes:detalle", pk=cliente.pk)


class DescargarPlantillaClientesView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Descarga la plantilla de Excel para la importación masiva de clientes."""

    codigo_modulo = Modulo.MOD01_CLIENTES
    roles_permitidos = ROLES_EDITAN

    def get(self, request):
        archivo = generar_plantilla_clientes()
        respuesta = HttpResponse(
            archivo.getvalue(),
            content_type=("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        )
        respuesta["Content-Disposition"] = 'attachment; filename="plantilla_clientes_contanika.xlsx"'
        return respuesta


class ImportarClientesView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Carga un archivo Excel, valida cada fila e importa las filas válidas."""

    codigo_modulo = Modulo.MOD01_CLIENTES
    roles_permitidos = ROLES_EDITAN
    template_name = "clientes/importar.html"

    def get(self, request):
        return render(request, self.template_name, {"formulario": ImportarClientesForm()})

    def post(self, request):
        formulario = ImportarClientesForm(request.POST, request.FILES)
        resultado = None
        if formulario.is_valid():
            try:
                resultado = importar_clientes(formulario.cleaned_data["archivo"], request.user)
                messages.success(request, "El archivo se procesó correctamente.")
            except ValueError as error:
                formulario.add_error("archivo", str(error))
        return render(
            request,
            self.template_name,
            {"formulario": formulario, "resultado": resultado},
        )


class CredencialCrearView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Crea una nueva credencial para un cliente."""

    codigo_modulo = Modulo.MOD01_CLIENTES
    roles_permitidos = ROLES_EDITAN

    def _get_template(self, request):
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        return "clientes/credencial_form_modal.html" if is_ajax else "clientes/credencial_form.html"

    def get(self, request, pk_cliente):
        cliente = get_object_or_404(Cliente, pk=pk_cliente)
        if request.user.es_contador_junior and cliente.responsable != request.user:
            return redirect("clientes:detalle", pk=cliente.pk)
        formulario = CredencialForm()
        return render(
            request,
            self._get_template(request),
            {"formulario": formulario, "cliente": cliente, "accion": "crear"},
        )

    def post(self, request, pk_cliente):
        cliente = get_object_or_404(Cliente, pk=pk_cliente)
        if request.user.es_contador_junior and cliente.responsable != request.user:
            return redirect("clientes:detalle", pk=cliente.pk)
        formulario = CredencialForm(request.POST)
        if formulario.is_valid():
            guardar_credencial(formulario, cliente, request.user)
            messages.success(request, "La credencial se creó correctamente.")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                url = reverse("clientes:detalle", kwargs={"pk": cliente.pk})
                return HttpResponse(
                    f'<script>window.location.href = "{url}";</script>',
                    content_type="text/html",
                )
            return redirect("clientes:detalle", pk=cliente.pk)
        return render(
            request,
            self._get_template(request),
            {"formulario": formulario, "cliente": cliente, "accion": "crear"},
        )


class CredencialEditarView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Edita una credencial existente."""

    codigo_modulo = Modulo.MOD01_CLIENTES
    roles_permitidos = ROLES_EDITAN

    def _get_template(self, request):
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        return "clientes/credencial_form_modal.html" if is_ajax else "clientes/credencial_form.html"

    def get(self, request, pk_cliente, pk):
        credencial = get_object_or_404(Credencial, pk=pk, cliente_id=pk_cliente)
        if request.user.es_contador_junior and credencial.cliente.responsable != request.user:
            return redirect("clientes:detalle", pk=credencial.cliente.pk)
        formulario = CredencialForm(instance=credencial)
        return render(
            request,
            self._get_template(request),
            {
                "formulario": formulario,
                "cliente": credencial.cliente,
                "credencial": credencial,
                "accion": "editar",
            },
        )

    def post(self, request, pk_cliente, pk):
        credencial = get_object_or_404(Credencial, pk=pk, cliente_id=pk_cliente)
        if request.user.es_contador_junior and credencial.cliente.responsable != request.user:
            return redirect("clientes:detalle", pk=credencial.cliente.pk)
        formulario = CredencialForm(request.POST, instance=credencial)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, "La credencial se actualizó correctamente.")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                url = reverse("clientes:detalle", kwargs={"pk": credencial.cliente.pk})
                return HttpResponse(
                    f'<script>window.location.href = "{url}";</script>',
                    content_type="text/html",
                )
            return redirect("clientes:detalle", pk=credencial.cliente.pk)
        return render(
            request,
            self._get_template(request),
            {
                "formulario": formulario,
                "cliente": credencial.cliente,
                "credencial": credencial,
                "accion": "editar",
            },
        )


class CredencialEliminarView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Elimina una credencial de acceso."""

    codigo_modulo = Modulo.MOD01_CLIENTES
    roles_permitidos = ROLES_EDITAN

    def post(self, request, pk_cliente, pk):
        credencial = get_object_or_404(Credencial, pk=pk, cliente_id=pk_cliente)
        if request.user.es_contador_junior and credencial.cliente.responsable != request.user:
            return redirect("clientes:detalle", pk=credencial.cliente.pk)
        eliminar_credencial(credencial)
        messages.success(request, "La credencial se eliminó correctamente.")
        return redirect("clientes:detalle", pk=credencial.cliente.pk)


class ReporteCredencialesTodosView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Reporte consolidado de credenciales de todos los clientes (solo en pantalla, sin descarga)."""

    codigo_modulo = Modulo.MOD01_CLIENTES
    roles_permitidos = ROLES_EDITAN + (Rol.CONTADOR_JUNIOR,)
    template_name = "clientes/reporte_credenciales_todos.html"

    def get(self, request):
        cliente = request.GET.get("cliente") or None
        estado = request.GET.get("estado") or None
        credenciales = credenciales_visibles(request.user, cliente=cliente, estado=estado)
        clientes = Cliente.objects.order_by("nombre_razon_social")
        if request.user.es_contador_junior:
            clientes = clientes.filter(responsable=request.user)
        return render(
            request,
            self.template_name,
            {
                "credenciales": credenciales,
                "alertas": sum(1 for c in credenciales if c.requiere_actualizacion),
                "clientes": clientes,
                "filtros": request.GET,
            },
        )


class ReporteCredencialesView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Reporte de credenciales de un cliente (solo en pantalla, sin descarga)."""

    codigo_modulo = Modulo.MOD01_CLIENTES
    roles_permitidos = ROLES_EDITAN + (Rol.CONTADOR_JUNIOR,)
    template_name = "clientes/reporte_credenciales.html"

    def get(self, request, pk_cliente):
        cliente = get_object_or_404(Cliente, pk=pk_cliente)
        if request.user.es_contador_junior and cliente.responsable != request.user:
            return redirect("clientes:detalle", pk=cliente.pk)
        credenciales = cliente.credenciales.all().order_by("concepto")
        alertas = sum(1 for c in credenciales if c.requiere_actualizacion)
        return render(
            request,
            self.template_name,
            {"cliente": cliente, "credenciales": credenciales, "alertas": alertas},
        )
