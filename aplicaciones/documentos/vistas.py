"""
Vistas del módulo 4: expedición de documentos y certificados.

Permisos:
- Los 3 roles generan y consultan documentos; el Contador Junior solo para
  los clientes que tiene asignados (mismo criterio que `clientes`/`tareas`).
- Solo Administrador y Contador Senior pueden tener firma guardada y
  aparecer como firmantes; solo ellos pueden eliminar un documento generado.
- Solo el Administrador gestiona el catálogo de plantillas.

El panel de generación funciona en dos pasos: `GenerarDocumentoView` valida
el formulario común y los campos propios de la plantilla elegida (simples y
repetibles) y guarda los datos ya validados en la sesión; `ConfirmarDocumentoView`
muestra la previsualización (GET) y genera el documento y el PDF (POST). Los
datos nunca viajan como campos ocultos manipulables por el cliente: se
re-validan igualmente contra las consultas visibles del usuario antes de
generar, y se limpian de la sesión al terminar.
"""

from django.contrib import messages
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import ListView, View

from aplicaciones.seguridad.models import Modulo, Rol
from aplicaciones.seguridad.permisos import ModuloHabilitadoMixin, RolRequeridoMixin

from . import selectores, servicios
from .formularios import (
    CampoPlantillaFormSet,
    FiltroHistoricoForm,
    GenerarDocumentoForm,
    MiFirmaForm,
    PlantillaForm,
    construir_formset_filas_repetibles,
    construir_formulario_campos_simples,
    valores_desde_cleaned_data,
)
from .models import Plantilla

ROLES_ELIMINAN = (Rol.ADMINISTRADOR, Rol.CONTADOR_SENIOR)
ROLES_ADMIN = (Rol.ADMINISTRADOR,)
ROLES_FIRMANTES = (Rol.ADMINISTRADOR, Rol.CONTADOR_SENIOR)

CLAVE_SESION_DOCUMENTO_PENDIENTE = "documento_pendiente"
PREFIJO_CAMPOS = "campos"


def _es_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _redirigir_o_recargar(request, nombre_ruta, **kwargs):
    """Redirige de forma normal, o fuerza la recarga cuando la petición es AJAX."""
    url = reverse(nombre_ruta, kwargs=kwargs)
    if _es_ajax(request):
        return HttpResponse(f'<script>window.location.href = "{url}";</script>', content_type="text/html")
    return redirect(url)


class HistoricoDocumentosView(ModuloHabilitadoMixin, ListView):
    """Histórico de documentos generados, filtrable por tipo y rango de fechas."""

    codigo_modulo = Modulo.MOD04_DOCUMENTOS
    template_name = "documentos/historico.html"
    context_object_name = "documentos"
    paginate_by = 20

    def get_queryset(self):
        self.formulario_filtro = FiltroHistoricoForm(self.request.GET or None)
        plantilla = desde = hasta = None
        if self.formulario_filtro.is_valid():
            plantilla = self.formulario_filtro.cleaned_data.get("plantilla")
            desde = self.formulario_filtro.cleaned_data.get("desde")
            hasta = self.formulario_filtro.cleaned_data.get("hasta")
        return selectores.filtrar_historico(self.request.user, plantilla=plantilla, desde=desde, hasta=hasta)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["formulario_filtro"] = self.formulario_filtro
        contexto["puede_eliminar"] = self.request.user.rol.nombre_rol in ROLES_ELIMINAN
        return contexto


class GenerarDocumentoView(ModuloHabilitadoMixin, View):
    """
    Paso 1 del panel de generación: cliente, plantilla, período, descripción,
    firma y los campos propios de la plantilla elegida (cargados por AJAX).
    """

    codigo_modulo = Modulo.MOD04_DOCUMENTOS
    template_name = "documentos/generar_formulario.html"

    def get(self, request):
        inicial = {}
        if request.GET.get("cliente"):
            inicial["cliente"] = request.GET["cliente"]
        plantilla = self._plantilla_seleccionada(request.GET.get("plantilla"))
        contexto = {
            "formulario": GenerarDocumentoForm(usuario=request.user, initial=inicial),
            "plantilla_seleccionada": plantilla,
            "formulario_campos": construir_formulario_campos_simples(plantilla) if plantilla else None,
            "formset_filas": construir_formset_filas_repetibles(plantilla) if plantilla else None,
        }
        return render(request, self.template_name, contexto)

    def post(self, request):
        formulario = GenerarDocumentoForm(request.POST, usuario=request.user)
        plantilla = self._plantilla_seleccionada(request.POST.get("plantilla"))

        formulario_campos = (
            construir_formulario_campos_simples(plantilla, request.POST) if plantilla else None
        )
        formset_filas = construir_formset_filas_repetibles(plantilla, request.POST) if plantilla else None

        valido = formulario.is_valid()
        valido = (formulario_campos is None or formulario_campos.is_valid()) and valido
        valido = (formset_filas is None or formset_filas.is_valid()) and valido

        if valido:
            request.session[CLAVE_SESION_DOCUMENTO_PENDIENTE] = {
                "cliente_id": formulario.cleaned_data["cliente"].pk,
                "plantilla_id": formulario.cleaned_data["plantilla"].pk,
                "periodo": formulario.cleaned_data["periodo"],
                "descripcion": formulario.cleaned_data["descripcion"],
                "usuario_firmante_id": formulario.cleaned_data["usuario_firmante"].pk,
                "valores_simples": (
                    valores_desde_cleaned_data(formulario_campos.cleaned_data) if formulario_campos else {}
                ),
                "filas_repetibles": self._filas_repetibles(formset_filas),
            }
            return redirect("documentos:confirmar")

        contexto = {
            "formulario": formulario,
            "plantilla_seleccionada": plantilla,
            "formulario_campos": formulario_campos,
            "formset_filas": formset_filas,
        }
        return render(request, self.template_name, contexto)

    def _plantilla_seleccionada(self, plantilla_id):
        if not plantilla_id:
            return None
        return selectores.plantillas_activas().filter(pk=plantilla_id).first()

    def _filas_repetibles(self, formset_filas):
        if formset_filas is None:
            return []
        filas = []
        for formulario_fila in formset_filas.forms:
            if formset_filas.can_delete and formulario_fila.cleaned_data.get("DELETE"):
                continue
            valores = valores_desde_cleaned_data(formulario_fila.cleaned_data)
            if any(valor for valor in valores.values()):
                filas.append(valores)
        return filas


class CamposPlantillaParcialView(ModuloHabilitadoMixin, View):
    """Fragmento AJAX con los campos propios de la plantilla elegida en el panel de generación."""

    codigo_modulo = Modulo.MOD04_DOCUMENTOS

    def get(self, request):
        plantilla = get_object_or_404(selectores.plantillas_activas(), pk=request.GET.get("plantilla"))
        contexto = {
            "plantilla_seleccionada": plantilla,
            "formulario_campos": construir_formulario_campos_simples(plantilla),
            "formset_filas": construir_formset_filas_repetibles(plantilla),
        }
        return render(request, "documentos/_campos_dinamicos.html", contexto)


class ConfirmarDocumentoView(ModuloHabilitadoMixin, View):
    """Paso 2: previsualización (GET) y generación del documento y su PDF (POST)."""

    codigo_modulo = Modulo.MOD04_DOCUMENTOS
    template_name = "documentos/generar_confirmar.html"

    def get(self, request):
        datos = request.session.get(CLAVE_SESION_DOCUMENTO_PENDIENTE)
        if not datos:
            messages.error(request, "No hay ningún documento pendiente de confirmar.")
            return redirect("documentos:generar")

        referencias = self._referencias(request, datos)
        if referencias is None:
            return redirect("documentos:generar")
        cliente, plantilla, usuario_firmante = referencias

        contexto_texto = selectores.contexto_previsualizacion(
            cliente=cliente,
            periodo=datos["periodo"],
            descripcion=datos["descripcion"],
            valores_simples={int(k): v for k, v in datos["valores_simples"].items()},
            filas_repetibles=[{int(k): v for k, v in fila.items()} for fila in datos["filas_repetibles"]],
        )
        contexto = {
            "cliente": cliente,
            "plantilla": plantilla,
            "periodo": datos["periodo"],
            "descripcion": datos["descripcion"],
            "usuario_firmante": usuario_firmante,
            "texto_renderizado": selectores.renderizar_texto(plantilla.texto_predeterminado, contexto_texto),
        }
        return render(request, self.template_name, contexto)

    def post(self, request):
        datos = request.session.get(CLAVE_SESION_DOCUMENTO_PENDIENTE)
        if not datos:
            messages.error(request, "No hay ningún documento pendiente de confirmar.")
            return redirect("documentos:generar")

        referencias = self._referencias(request, datos)
        if referencias is None:
            return redirect("documentos:generar")
        cliente, plantilla, usuario_firmante = referencias

        documento = servicios.generar_documento(
            cliente=cliente,
            plantilla=plantilla,
            periodo=datos["periodo"],
            descripcion=datos["descripcion"],
            usuario_firmante=usuario_firmante,
            usuario_generador=request.user,
            valores_simples={int(k): v for k, v in datos["valores_simples"].items()},
            filas_repetibles=[{int(k): v for k, v in fila.items()} for fila in datos["filas_repetibles"]],
        )
        del request.session[CLAVE_SESION_DOCUMENTO_PENDIENTE]
        messages.success(request, "El documento se generó correctamente.")
        return redirect("documentos:detalle", pk=documento.pk)

    def _referencias(self, request, datos):
        """
        Vuelve a validar que el cliente, la plantilla y el firmante elegidos
        en el paso 1 siguen siendo válidos para este usuario, en vez de
        confiar en los ids guardados en la sesión.
        """
        cliente = selectores.clientes_para_generar(request.user).filter(pk=datos["cliente_id"]).first()
        plantilla = selectores.plantillas_activas().filter(pk=datos["plantilla_id"]).first()
        usuario_firmante = selectores.firmantes_disponibles().filter(pk=datos["usuario_firmante_id"]).first()
        if not (cliente and plantilla and usuario_firmante):
            messages.error(request, "Los datos del documento ya no son válidos. Intente de nuevo.")
            request.session.pop(CLAVE_SESION_DOCUMENTO_PENDIENTE, None)
            return None
        return cliente, plantilla, usuario_firmante


class DetalleDocumentoView(ModuloHabilitadoMixin, View):
    """Detalle de un documento generado, con el texto del certificado renderizado."""

    codigo_modulo = Modulo.MOD04_DOCUMENTOS

    def get(self, request, pk):
        documento = get_object_or_404(
            selectores.documentos_visibles(request.user).select_related("cliente", "plantilla"), pk=pk
        )
        contexto = {
            "documento": documento,
            "texto_renderizado": selectores.texto_certificado_renderizado(documento),
            "puede_eliminar": request.user.rol.nombre_rol in ROLES_ELIMINAN,
        }
        return render(request, "documentos/documento_detalle.html", contexto)


class DescargarDocumentoView(ModuloHabilitadoMixin, View):
    """
    Descarga individual del PDF ya generado.

    Excepción expresa a la regla de centralización de descargas del sistema:
    el certificado individual sí se descarga desde este módulo, para
    cualquiera de los tres roles que pueda ver el documento.
    """

    codigo_modulo = Modulo.MOD04_DOCUMENTOS

    def get(self, request, pk):
        documento = get_object_or_404(selectores.documentos_visibles(request.user), pk=pk)
        return FileResponse(
            documento.archivo.open("rb"),
            as_attachment=True,
            filename=f"{documento.plantilla.nombre_plantilla} - {documento.cliente.nombre_razon_social}.pdf",
        )


class EliminarDocumentoView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Elimina un documento generado (operación irreversible)."""

    codigo_modulo = Modulo.MOD04_DOCUMENTOS
    roles_permitidos = ROLES_ELIMINAN

    def post(self, request, pk):
        documento = get_object_or_404(selectores.documentos_visibles(request.user), pk=pk)
        servicios.eliminar_documento(documento)
        messages.success(request, "El documento se eliminó correctamente.")
        return redirect("documentos:historico")


class ListaPlantillasView(ModuloHabilitadoMixin, RolRequeridoMixin, ListView):
    """Catálogo de plantillas de documento (solo Administrador)."""

    codigo_modulo = Modulo.MOD04_DOCUMENTOS
    roles_permitidos = ROLES_ADMIN
    template_name = "documentos/plantilla_lista.html"
    context_object_name = "plantillas"
    queryset = Plantilla.objects.all()


class CrearPlantillaView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Crea una plantilla nueva con sus campos propios (solo Administrador)."""

    codigo_modulo = Modulo.MOD04_DOCUMENTOS
    roles_permitidos = ROLES_ADMIN
    template_name = "documentos/plantilla_formulario.html"

    def get(self, request):
        contexto = {
            "formulario": PlantillaForm(),
            "formset_campos": CampoPlantillaFormSet(instance=Plantilla(), prefix=PREFIJO_CAMPOS),
            "accion": "crear",
        }
        return render(request, self.template_name, contexto)

    def post(self, request):
        formulario = PlantillaForm(request.POST)
        formset_campos = CampoPlantillaFormSet(request.POST, instance=Plantilla(), prefix=PREFIJO_CAMPOS)
        if formulario.is_valid() and formset_campos.is_valid():
            servicios.crear_plantilla(formulario, formset_campos)
            messages.success(request, "La plantilla se creó correctamente.")
            return redirect("documentos:plantillas")
        return render(
            request,
            self.template_name,
            {"formulario": formulario, "formset_campos": formset_campos, "accion": "crear"},
        )


class EditarPlantillaView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Edita el texto predeterminado y los campos de una plantilla (solo Administrador)."""

    codigo_modulo = Modulo.MOD04_DOCUMENTOS
    roles_permitidos = ROLES_ADMIN
    template_name = "documentos/plantilla_formulario.html"

    def get(self, request, pk):
        plantilla = get_object_or_404(Plantilla, pk=pk)
        contexto = {
            "formulario": PlantillaForm(instance=plantilla),
            "formset_campos": CampoPlantillaFormSet(instance=plantilla, prefix=PREFIJO_CAMPOS),
            "accion": "editar",
            "plantilla": plantilla,
        }
        return render(request, self.template_name, contexto)

    def post(self, request, pk):
        plantilla = get_object_or_404(Plantilla, pk=pk)
        formulario = PlantillaForm(request.POST, instance=plantilla)
        formset_campos = CampoPlantillaFormSet(request.POST, instance=plantilla, prefix=PREFIJO_CAMPOS)
        if formulario.is_valid() and formset_campos.is_valid():
            try:
                servicios.actualizar_plantilla(plantilla, formulario, formset_campos)
            except ValueError as error:
                messages.error(request, str(error))
            else:
                messages.success(request, "La plantilla se actualizó correctamente.")
                return redirect("documentos:plantillas")
        return render(
            request,
            self.template_name,
            {
                "formulario": formulario,
                "formset_campos": formset_campos,
                "accion": "editar",
                "plantilla": plantilla,
            },
        )


class MiFirmaView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Carga o reemplaza la firma, identificación y tarjeta profesional propias."""

    codigo_modulo = Modulo.MOD04_DOCUMENTOS
    roles_permitidos = ROLES_FIRMANTES

    def _template(self, request):
        return "documentos/mi_firma_form_modal.html" if _es_ajax(request) else "documentos/mi_firma_form.html"

    def get(self, request):
        formulario = MiFirmaForm(instance=request.user)
        return render(request, self._template(request), {"formulario": formulario})

    def post(self, request):
        formulario = MiFirmaForm(request.POST, request.FILES, instance=request.user)
        if formulario.is_valid():
            servicios.actualizar_firma(request.user, formulario)
            messages.success(request, "Su firma se guardó correctamente.")
            return _redirigir_o_recargar(request, "documentos:generar")
        return render(request, self._template(request), {"formulario": formulario})
