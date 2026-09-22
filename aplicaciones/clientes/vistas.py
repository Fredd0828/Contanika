"""
Vistas del módulo 1: listado, detalle, creación, edición e inactivación.

Permisos (CU002): el Administrador y el Contador Senior gestionan los
clientes; el Contador Junior únicamente consulta los clientes que tiene
asignados. Todas las vistas exigen sesión y el módulo habilitado (RQF031).
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from aplicaciones.seguridad.models import Modulo, Rol
from aplicaciones.seguridad.permisos import ModuloHabilitadoMixin, RolRequeridoMixin

from .formularios import ClienteForm, ClienteMunicipioFormSet, ImportarClientesForm
from .importacion import generar_plantilla_clientes, importar_clientes
from .models import Cliente
from .selectores import filtrar_clientes, opciones_filtro
from .servicios import guardar_cliente, inactivar_cliente

Usuario = get_user_model()

ROLES_EDITAN = (Rol.ADMINISTRADOR, Rol.CONTADOR_SENIOR)
PREFIJO_MUNICIPIOS = "municipios"


class ListaClientesView(ModuloHabilitadoMixin, ListView):
    """Listado de clientes con filtros desplegables y paginación."""

    codigo_modulo = Modulo.MOD01_CLIENTES
    model = Cliente
    template_name = "clientes/lista.html"
    context_object_name = "clientes"
    paginate_by = 20

    def get_queryset(self):
        parametros = self.request.GET
        consulta = filtrar_clientes(
            ciudad=parametros.get("ciudad") or None,
            municipio=parametros.get("municipio") or None,
            regimen_tributario=parametros.get("regimen_tributario") or None,
            tipo_persona=parametros.get("tipo_persona") or None,
            responsable=parametros.get("responsable") or None,
            estado=parametros.get("estado") or None,
            fecha_desde=parametros.get("fecha_desde") or None,
            fecha_hasta=parametros.get("fecha_hasta") or None,
        )
        # El Contador Junior solo consulta los clientes asignados a él.
        if self.request.user.es_contador_junior:
            consulta = consulta.filter(responsable=self.request.user)
        return consulta

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["opciones"] = opciones_filtro()
        contexto["filtros"] = self.request.GET
        contexto["responsables"] = Usuario.objects.filter(estado=Usuario.ACTIVO).order_by("nombre")
        contexto["puede_editar"] = self.request.user.rol.nombre_rol in ROLES_EDITAN
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto["querystring"] = parametros.urlencode()
        return contexto


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
        # Un Contador Junior no puede ver clientes que no le fueron asignados.
        if self.request.user.es_contador_junior:
            consulta = consulta.filter(responsable=self.request.user)
        return consulta

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["puede_editar"] = self.request.user.rol.nombre_rol in ROLES_EDITAN
        return contexto


class MixinFormularioCliente:
    """Comportamiento común de las vistas de crear y editar cliente."""

    codigo_modulo = Modulo.MOD01_CLIENTES
    roles_permitidos = ROLES_EDITAN
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/formulario.html"
    success_url = reverse_lazy("clientes:lista")

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
        return guardar_cliente(formulario, formset, self.request.user)


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
