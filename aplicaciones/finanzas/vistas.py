"""
Vistas del módulo 6: honorarios, cartera y cuentas de cobro.

Permisos (HU016-HU018, HU044, HU049):
- Solo el Administrador configura honorarios, gestiona los catálogos
  (conceptos facturables, cuentas bancarias, métodos de pago) y genera o
  elimina cuentas de cobro.
- El Contador Senior y el Contador Junior solo consultan, y únicamente la
  información de los clientes que tienen asignados.
- La cuenta de cobro individual se descarga desde este módulo (excepción
  expresa a la regla de descargas centralizadas en el Módulo 10).
- Envíos (HU045-HU047), programación, bandeja de WhatsApp y configuración
  del cobro automático: solo el Administrador. El historial de envíos de
  una cuenta lo consulta quien puede ver la cuenta.
- El PDF público (enlace firmado que recibe el cliente por WhatsApp) es la
  única vista sin sesión del módulo: el token es infalsificable y vence.
"""

from django.contrib import messages
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import ListView, View

from aplicaciones.clientes.models import Cliente
from aplicaciones.seguridad.models import Modulo, Rol
from aplicaciones.seguridad.permisos import ModuloHabilitadoMixin, RolRequeridoMixin

from . import envios, selectores, servicios
from .formularios import (
    ENVIAR_AHORA,
    AbonoForm,
    ConceptoFacturableForm,
    ConfiguracionCobroForm,
    CuentaBancariaForm,
    CuentaCobroForm,
    EnvioForm,
    EnvioMasivoForm,
    FiltroCuentasCobroForm,
    HonorarioForm,
    LineasCobroFormSet,
    MetodoPagoForm,
    campo_fecha_cuenta,
)
from .models import (
    ConceptoFacturable,
    ConfiguracionCobro,
    CuentaBancaria,
    CuentaCobro,
    EnvioProgramado,
    MetodoPago,
)
from .templatetags.finanzas_tags import formato_pesos

ROLES_ADMIN = (Rol.ADMINISTRADOR,)

# Catálogos del módulo: clave usada en la URL → modelo, formulario y títulos.
CATALOGOS = {
    "conceptos": {
        "modelo": ConceptoFacturable,
        "formulario": ConceptoFacturableForm,
        "titulo": "Conceptos facturables",
        "singular": "concepto facturable",
        "icono": "bi-tags",
    },
    "cuentas-bancarias": {
        "modelo": CuentaBancaria,
        "formulario": CuentaBancariaForm,
        "titulo": "Cuentas bancarias del despacho",
        "singular": "cuenta bancaria",
        "icono": "bi-bank",
    },
    "metodos-pago": {
        "modelo": MetodoPago,
        "formulario": MetodoPagoForm,
        "titulo": "Métodos de pago",
        "singular": "método de pago",
        "icono": "bi-wallet2",
    },
}


def _catalogo_o_404(clave):
    if clave not in CATALOGOS:
        raise Http404("Catálogo inexistente.")
    return CATALOGOS[clave]


# ---------------------------------------------------------------------------
# Cuentas de cobro
# ---------------------------------------------------------------------------


class HistoricoCuentasCobroView(ModuloHabilitadoMixin, ListView):
    """Histórico de cuentas de cobro, filtrable por cliente, estado, período y fechas."""

    codigo_modulo = Modulo.MOD06_FINANZAS
    template_name = "finanzas/historico.html"
    context_object_name = "cuentas"
    paginate_by = 20

    def get_queryset(self):
        self.formulario_filtro = FiltroCuentasCobroForm(self.request.GET or None, usuario=self.request.user)
        filtros = {}
        if self.formulario_filtro.is_valid():
            filtros = {
                campo: self.formulario_filtro.cleaned_data.get(campo)
                for campo in ("cliente", "estado_pago", "periodo", "desde", "hasta")
            }
        return selectores.filtrar_cuentas_cobro(self.request.user, **filtros)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["formulario_filtro"] = self.formulario_filtro
        contexto["es_administrador"] = self.request.user.es_administrador
        if self.request.user.es_administrador:
            contexto["pendientes_whatsapp"] = selectores.bandeja_whatsapp().count()
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto["querystring"] = parametros.urlencode()
        return contexto


class GenerarCuentaCobroView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """
    Genera una cuenta de cobro (solo Administrador). Al elegir el cliente
    (`?cliente=<id>`) se sugieren el valor total según su honorario y una
    línea por cada tipo de servicio que recibe (HU049).
    """

    codigo_modulo = Modulo.MOD06_FINANZAS
    roles_permitidos = ROLES_ADMIN
    template_name = "finanzas/cuenta_cobro_formulario.html"

    def _render(self, request, formulario, formset, cliente=None):
        # Nombre y valor sugerido de cada concepto, para autocompletar la línea al elegirlo.
        conceptos_json = {
            str(concepto.pk): {
                "nombre": concepto.nombre_concepto,
                "valor": str(concepto.valor_sugerido or ""),
            }
            for concepto in ConceptoFacturable.objects.all()
        }
        contexto = {
            "formulario": formulario,
            "formset": formset,
            "cliente": cliente,
            "conceptos_json": conceptos_json,
        }
        return render(request, self.template_name, contexto)

    def get(self, request):
        inicial = {"fecha_inicio_periodo": timezone.localdate().replace(day=1)}
        lineas_iniciales = []
        cliente = None
        if request.GET.get("cliente"):
            cliente = selectores.clientes_para_cobro(request.user).filter(pk=request.GET["cliente"]).first()
        if cliente:
            sugerencia = selectores.sugerencia_cuenta_cobro(cliente)
            inicial["cliente"] = cliente.pk
            if sugerencia["valor_total"]:
                inicial["valor_total"] = sugerencia["valor_total"]
            lineas_iniciales = sugerencia["lineas"]
        formulario = CuentaCobroForm(initial=inicial, usuario=request.user)
        formset = LineasCobroFormSet(initial=lineas_iniciales or [{}], prefix="lineas")
        return self._render(request, formulario, formset, cliente)

    def post(self, request):
        formulario = CuentaCobroForm(request.POST, usuario=request.user)
        formset = LineasCobroFormSet(request.POST, prefix="lineas")
        formulario_valido = formulario.is_valid()
        formset.valor_total = formulario.cleaned_data.get("valor_total") if formulario_valido else None
        if formulario_valido and formset.is_valid():
            datos = formulario.cleaned_data
            cuenta = servicios.generar_cuenta_cobro(
                cliente=datos["cliente"],
                periodo_facturado=datos["periodo_facturado"],
                fecha_inicio_periodo=datos["fecha_inicio_periodo"],
                fecha_fin_periodo=datos["fecha_fin_periodo"],
                valor_total=datos["valor_total"],
                cuenta_bancaria=datos.get("cuenta_bancaria"),
                metodo_pago=datos.get("metodo_pago"),
                fecha_vencimiento_pago=datos["fecha_vencimiento_pago"],
                lineas=formset.lineas(),
            )
            messages.success(request, f"La cuenta de cobro No. {cuenta.pk} se generó correctamente.")
            return redirect("finanzas:detalle", pk=cuenta.pk)
        formset.is_valid()
        return self._render(request, formulario, formset, formulario.cleaned_data.get("cliente"))


class DetalleCuentaCobroView(ModuloHabilitadoMixin, View):
    """Detalle de una cuenta de cobro visible para el usuario."""

    codigo_modulo = Modulo.MOD06_FINANZAS

    def get(self, request, pk):
        cuenta = get_object_or_404(selectores.cuentas_cobro_visibles(request.user), pk=pk)
        contexto = {
            "cuenta": cuenta,
            "lineas": cuenta.detalles.select_related("concepto"),
            "es_administrador": request.user.es_administrador,
            "envios": selectores.envios_de_cuenta(cuenta),
            "formulario_envio": EnvioForm(),
            "numero_whatsapp": envios.numero_whatsapp(cuenta.cliente),
            "abonos": cuenta.abonos.select_related("metodo_pago", "responsable"),
            "formulario_abono": AbonoForm(cuenta=cuenta),
        }
        return render(request, "finanzas/cuenta_cobro_detalle.html", contexto)


class DescargarCuentaCobroView(ModuloHabilitadoMixin, View):
    """Descarga el PDF de una cuenta de cobro visible para el usuario."""

    codigo_modulo = Modulo.MOD06_FINANZAS

    def get(self, request, pk):
        cuenta = get_object_or_404(selectores.cuentas_cobro_visibles(request.user), pk=pk)
        if not cuenta.archivo:
            raise Http404("La cuenta de cobro no tiene PDF generado.")
        return FileResponse(
            cuenta.archivo.open("rb"), as_attachment=True, filename=f"cuenta_cobro_{cuenta.pk}.pdf"
        )


class EliminarCuentaCobroView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Elimina una cuenta de cobro sin abonos (solo Administrador)."""

    codigo_modulo = Modulo.MOD06_FINANZAS
    roles_permitidos = ROLES_ADMIN

    def post(self, request, pk):
        cuenta = get_object_or_404(CuentaCobro, pk=pk)
        try:
            servicios.eliminar_cuenta_cobro(cuenta)
        except ValueError as error:
            messages.error(request, str(error))
            return redirect("finanzas:detalle", pk=pk)
        messages.success(request, "La cuenta de cobro se eliminó correctamente.")
        return redirect("finanzas:historico")


# ---------------------------------------------------------------------------
# Honorario del cliente
# ---------------------------------------------------------------------------


class ConfigurarHonorarioView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Configura el tipo y monto del honorario de un cliente (solo Administrador)."""

    codigo_modulo = Modulo.MOD06_FINANZAS
    roles_permitidos = ROLES_ADMIN
    template_name = "finanzas/honorario_formulario.html"

    def _inicial(self, cliente):
        honorario = selectores.honorario_del_cliente(cliente)
        if not honorario:
            return {}
        inicial = {"tipo": honorario.tipo, "monto": honorario.monto}
        for linea in honorario.servicios.all():
            inicial[f"servicio_{linea.tipo_servicio_id}"] = linea.monto
        return inicial

    def get(self, request, pk):
        cliente = get_object_or_404(Cliente, pk=pk)
        formulario = HonorarioForm(initial=self._inicial(cliente), cliente=cliente)
        return render(request, self.template_name, {"formulario": formulario, "cliente": cliente})

    def post(self, request, pk):
        cliente = get_object_or_404(Cliente, pk=pk)
        formulario = HonorarioForm(request.POST, cliente=cliente)
        if formulario.is_valid():
            servicios.configurar_honorario(
                cliente,
                formulario.cleaned_data["tipo"],
                formulario.cleaned_data.get("monto"),
                formulario.montos_por_servicio(),
                request.user,
            )
            messages.success(request, "El honorario del cliente se guardó correctamente.")
            return redirect(f"{reverse('clientes:detalle', args=[cliente.pk])}#tab-honorarios")
        return render(request, self.template_name, {"formulario": formulario, "cliente": cliente})


# ---------------------------------------------------------------------------
# Catálogos (solo Administrador)
# ---------------------------------------------------------------------------


class CatalogosView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Conceptos facturables, cuentas bancarias y métodos de pago en una sola pantalla."""

    codigo_modulo = Modulo.MOD06_FINANZAS
    roles_permitidos = ROLES_ADMIN

    def get(self, request):
        catalogos = [
            {"clave": clave, **config, "elementos": config["modelo"].objects.all()}
            for clave, config in CATALOGOS.items()
        ]
        return render(request, "finanzas/catalogos.html", {"catalogos": catalogos})


class ElementoCatalogoView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Crea (sin `pk`) o edita (con `pk`) un elemento de cualquiera de los catálogos."""

    codigo_modulo = Modulo.MOD06_FINANZAS
    roles_permitidos = ROLES_ADMIN
    template_name = "finanzas/catalogo_formulario.html"

    def _contexto(self, catalogo, formulario, elemento):
        return {"catalogo": catalogo, "formulario": formulario, "elemento": elemento}

    def get(self, request, catalogo, pk=None):
        config = _catalogo_o_404(catalogo)
        elemento = get_object_or_404(config["modelo"], pk=pk) if pk else None
        formulario = config["formulario"](instance=elemento)
        return render(request, self.template_name, self._contexto(config, formulario, elemento))

    def post(self, request, catalogo, pk=None):
        config = _catalogo_o_404(catalogo)
        elemento = get_object_or_404(config["modelo"], pk=pk) if pk else None
        formulario = config["formulario"](request.POST, instance=elemento)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, f"El {config['singular']} se guardó correctamente.")
            return redirect("finanzas:catalogos")
        return render(request, self.template_name, self._contexto(config, formulario, elemento))


class EliminarElementoCatalogoView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Elimina un elemento de catálogo que no esté usado en cuentas de cobro o abonos."""

    codigo_modulo = Modulo.MOD06_FINANZAS
    roles_permitidos = ROLES_ADMIN

    def post(self, request, catalogo, pk):
        config = _catalogo_o_404(catalogo)
        elemento = get_object_or_404(config["modelo"], pk=pk)
        try:
            servicios.eliminar_elemento_catalogo(elemento)
        except ValueError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, f"El {config['singular']} se eliminó correctamente.")
        return redirect("finanzas:catalogos")


# ---------------------------------------------------------------------------
# Abonos y cartera (HU016-HU018)
# ---------------------------------------------------------------------------


class RegistrarAbonoView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Registra un pago o abono a una cuenta de cobro (solo Administrador, HU016)."""

    codigo_modulo = Modulo.MOD06_FINANZAS
    roles_permitidos = ROLES_ADMIN

    def post(self, request, pk):
        cuenta = get_object_or_404(CuentaCobro, pk=pk)
        formulario = AbonoForm(request.POST, cuenta=cuenta)
        if not formulario.is_valid():
            for errores in formulario.errors.values():
                for error in errores:
                    messages.error(request, error)
            return redirect("finanzas:detalle", pk=pk)
        datos = formulario.cleaned_data
        try:
            abono = servicios.registrar_abono(
                cuenta,
                fecha=datos["fecha"],
                monto=datos["monto"],
                metodo_pago=datos.get("metodo_pago"),
                metodo_nuevo=datos.get("metodo_nuevo") or "",
                usuario=request.user,
            )
        except ValueError as error:
            messages.error(request, str(error))
        else:
            messages.success(
                request,
                f"Abono registrado. Saldo anterior {formato_pesos(abono.saldo_anterior)}, "
                f"saldo actual {formato_pesos(abono.saldo_resultante)}.",
            )
        return redirect("finanzas:detalle", pk=pk)


class CarteraView(ModuloHabilitadoMixin, View):
    """
    Panel de cartera (HU016-4, HU017): por cliente, facturado, cobrado, saldo
    y días en mora, con indicador rojo a más de 30 días. El Contador Senior y
    el Junior ven solo sus clientes asignados.
    """

    codigo_modulo = Modulo.MOD06_FINANZAS

    def get(self, request):
        incluir_al_dia = request.GET.get("todos") == "1"
        filas = selectores.cartera(request.user, solo_con_saldo=not incluir_al_dia)
        contexto = {
            "filas": filas,
            "totales": selectores.totales_cartera(filas),
            "incluir_al_dia": incluir_al_dia,
            "dias_mora_critica": selectores.DIAS_MORA_CRITICA,
        }
        return render(request, "finanzas/cartera.html", contexto)


# ---------------------------------------------------------------------------
# Envíos (HU045-HU047) y programación
# ---------------------------------------------------------------------------

CLAVE_SESION_RESUMEN = "finanzas_resumen_envio"


def _siguiente(request, defecto):
    """URL de regreso enviada por el formulario, solo si es del propio sitio."""
    url = request.POST.get("siguiente", "")
    if url and url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()}):
        return url
    return defecto


def _informar_resultados(request, procesados):
    """Mensajes de éxito, fallo o WhatsApp pendiente para un envío individual."""
    for envio in procesados:
        if envio.estado == EnvioProgramado.ENVIADO:
            messages.success(request, f"{envio.tipo} enviada por {envio.canal.lower()}.")
        elif envio.estado == EnvioProgramado.FALLIDO:
            messages.error(request, f"Falló el envío por {envio.canal.lower()}: {envio.detalle_error}")
        elif envio.estado == EnvioProgramado.PENDIENTE_WHATSAPP:
            messages.info(
                request, "El WhatsApp quedó listo: pulse «Abrir WhatsApp» en el historial de envíos."
            )


class EnviarCuentaCobroView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Envía o programa el envío de una cuenta de cobro o de un recordatorio (HU045, HU047)."""

    codigo_modulo = Modulo.MOD06_FINANZAS
    roles_permitidos = ROLES_ADMIN

    def post(self, request, pk):
        cuenta = get_object_or_404(CuentaCobro, pk=pk)
        formulario = EnvioForm(request.POST)
        if not formulario.is_valid():
            for errores in formulario.errors.values():
                for error in errores:
                    messages.error(request, error)
            return redirect("finanzas:detalle", pk=pk)
        datos = formulario.cleaned_data
        if datos["modo"] == ENVIAR_AHORA:
            procesados = servicios.enviar_ahora([cuenta], datos["tipo"], datos["canal"], request.user)
            _informar_resultados(request, procesados)
        else:
            servicios.programar_envio(
                cuenta, datos["tipo"], datos["canal"], datos["fecha_programada"], request.user
            )
            fecha = timezone.localtime(datos["fecha_programada"]).strftime("%d/%m/%Y %H:%M")
            messages.success(request, f"{datos['tipo']} programada para el {fecha}.")
        return redirect("finanzas:detalle", pk=pk)


class AbrirWhatsappView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """
    Registra como enviado un WhatsApp pendiente y redirige al enlace `wa.me`
    con el mensaje ya escrito. Se usa por POST (con token CSRF) porque cambia
    el estado del envío.
    """

    codigo_modulo = Modulo.MOD06_FINANZAS
    roles_permitidos = ROLES_ADMIN

    def post(self, request, pk):
        envio = get_object_or_404(EnvioProgramado, pk=pk)
        try:
            enlace = servicios.confirmar_whatsapp(envio, request.user)
        except ValueError as error:
            messages.error(request, str(error))
            return redirect(_siguiente(request, reverse("finanzas:bandeja_whatsapp")))
        return redirect(enlace)


class ReintentarEnvioView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Reintenta un correo fallido (HU045-2)."""

    codigo_modulo = Modulo.MOD06_FINANZAS
    roles_permitidos = ROLES_ADMIN

    def post(self, request, pk):
        envio = get_object_or_404(EnvioProgramado, pk=pk)
        try:
            _informar_resultados(request, [servicios.reintentar_envio(envio, request.user)])
        except ValueError as error:
            messages.error(request, str(error))
        return redirect(_siguiente(request, reverse("finanzas:detalle", args=[envio.cuenta_cobro_id])))


class CancelarEnvioView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Cancela un envío programado o un WhatsApp pendiente."""

    codigo_modulo = Modulo.MOD06_FINANZAS
    roles_permitidos = ROLES_ADMIN

    def post(self, request, pk):
        envio = get_object_or_404(EnvioProgramado, pk=pk)
        try:
            servicios.cancelar_envio(envio)
            messages.success(request, "El envío se canceló.")
        except ValueError as error:
            messages.error(request, str(error))
        return redirect(_siguiente(request, reverse("finanzas:programados")))


class EnvioMasivoView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """
    Envío masivo de cuentas de cobro o recordatorios (HU046, HU047) en tres
    pasos: selección de cuentas, canal y momento → confirmación del listado
    → resumen de éxitos y fallos.
    """

    codigo_modulo = Modulo.MOD06_FINANZAS
    roles_permitidos = ROLES_ADMIN

    def _tipo(self, datos):
        tipo = datos.get("tipo", EnvioProgramado.CUENTA_COBRO)
        valido = tipo in dict(EnvioProgramado.OPCIONES_TIPO)
        return tipo if valido else EnvioProgramado.CUENTA_COBRO

    def _candidatas(self, request, datos):
        tipo = self._tipo(datos)
        incluir_enviadas = datos.get("incluir_enviadas") == "1"
        return (
            tipo,
            incluir_enviadas,
            selectores.cuentas_para_envio_masivo(request.user, tipo, incluir_enviadas),
        )

    def _render_seleccion(self, request, formulario, tipo, incluir_enviadas, candidatas, datos=None):
        """Listado de selección: cada fila con su casilla, su fecha propia y su error de fecha."""
        datos = datos or {}
        seleccionadas = datos.getlist("cuentas") if datos else []
        filas = [
            {
                "cuenta": cuenta,
                "seleccionada": str(cuenta.pk) in seleccionadas,
                "campo_fecha": campo_fecha_cuenta(cuenta.pk),
                "fecha": datos.get(campo_fecha_cuenta(cuenta.pk), ""),
                "error_fecha": formulario.errores_fecha.get(cuenta.pk),
            }
            for cuenta in candidatas
        ]
        contexto = {
            "formulario": formulario,
            "candidatas": candidatas,
            "filas": filas,
            "tipo": tipo,
            "incluir_enviadas": incluir_enviadas,
        }
        return render(request, "finanzas/envio_masivo.html", contexto)

    def get(self, request):
        tipo, incluir_enviadas, candidatas = self._candidatas(request, request.GET)
        formulario = EnvioMasivoForm(initial={"tipo": tipo}, candidatas=candidatas)
        return self._render_seleccion(request, formulario, tipo, incluir_enviadas, candidatas)

    def post(self, request):
        tipo, incluir_enviadas, candidatas = self._candidatas(request, request.POST)
        formulario = EnvioMasivoForm(request.POST, candidatas=candidatas)
        if not formulario.is_valid():
            return self._render_seleccion(
                request, formulario, tipo, incluir_enviadas, candidatas, request.POST
            )
        datos = formulario.cleaned_data
        # Se toman de las candidatas para conservar su orden, su saldo y sus abonos.
        ids = {cuenta.pk for cuenta in datos["cuentas"]}
        cuentas = [cuenta for cuenta in candidatas if cuenta.pk in ids]
        if "confirmar" not in request.POST:
            filas = [{"cuenta": cuenta, "fecha": datos["fechas"].get(cuenta.pk)} for cuenta in cuentas]
            fechas_distintas = {fila["fecha"] for fila in filas}
            contexto = {
                "formulario": formulario,
                "filas": filas,
                "datos": datos,
                "incluir_enviadas": incluir_enviadas,
                "fecha_unica": fechas_distintas.pop() if len(fechas_distintas) == 1 else None,
            }
            return render(request, "finanzas/envio_masivo_confirmar.html", contexto)
        if datos["modo"] == ENVIAR_AHORA:
            procesados = servicios.enviar_ahora(cuentas, datos["tipo"], datos["canal"], request.user)
        else:
            procesados = [
                envio
                for cuenta in cuentas
                for envio in servicios.programar_envio(
                    cuenta, datos["tipo"], datos["canal"], datos["fechas"][cuenta.pk], request.user
                )
            ]
        request.session[CLAVE_SESION_RESUMEN] = [envio.pk for envio in procesados]
        return redirect("finanzas:envio_masivo_resumen")


class ResumenEnvioMasivoView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Resumen del último envío masivo con el detalle de cada caso (HU046-4)."""

    codigo_modulo = Modulo.MOD06_FINANZAS
    roles_permitidos = ROLES_ADMIN

    def get(self, request):
        ids = request.session.get(CLAVE_SESION_RESUMEN, [])
        envios_resumen = list(
            EnvioProgramado.objects.filter(pk__in=ids)
            .select_related("cuenta_cobro__cliente")
            .order_by("cuenta_cobro__cliente__nombre_razon_social", "canal")
        )
        estados = [envio.estado for envio in envios_resumen]
        conteo = {
            "enviados": estados.count(EnvioProgramado.ENVIADO),
            "fallidos": estados.count(EnvioProgramado.FALLIDO),
            "whatsapp": estados.count(EnvioProgramado.PENDIENTE_WHATSAPP),
            "programados": estados.count(EnvioProgramado.PROGRAMADO),
        }
        return render(
            request, "finanzas/envio_masivo_resumen.html", {"envios": envios_resumen, "conteo": conteo}
        )


class BandejaWhatsappView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """WhatsApp programados o masivos que esperan que alguien pulse "Enviar"."""

    codigo_modulo = Modulo.MOD06_FINANZAS
    roles_permitidos = ROLES_ADMIN

    def get(self, request):
        pendientes = [
            {"envio": envio, "numero": envios.numero_whatsapp(envio.cuenta_cobro.cliente)}
            for envio in selectores.bandeja_whatsapp()
        ]
        return render(request, "finanzas/bandeja_whatsapp.html", {"pendientes": pendientes})


class EnviosProgramadosView(ModuloHabilitadoMixin, RolRequeridoMixin, ListView):
    """Control de los envíos programados: próximos, procesados y cancelados."""

    codigo_modulo = Modulo.MOD06_FINANZAS
    roles_permitidos = ROLES_ADMIN
    template_name = "finanzas/programados.html"
    context_object_name = "envios"
    paginate_by = 20

    def get_queryset(self):
        estado = self.request.GET.get("estado")
        return selectores.envios_programados(
            estado if estado in dict(EnvioProgramado.OPCIONES_ESTADO) else None
        )

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["estados"] = [estado for estado, _ in EnvioProgramado.OPCIONES_ESTADO]
        contexto["estado_actual"] = self.request.GET.get("estado", "")
        return contexto


class ConfiguracionCobroView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Configura el cobro mensual automático y los recordatorios automáticos."""

    codigo_modulo = Modulo.MOD06_FINANZAS
    roles_permitidos = ROLES_ADMIN
    template_name = "finanzas/configuracion_cobro.html"

    def get(self, request):
        configuracion = ConfiguracionCobro.obtener()
        formulario = ConfiguracionCobroForm(instance=configuracion)
        return render(request, self.template_name, {"formulario": formulario, "configuracion": configuracion})

    def post(self, request):
        configuracion = ConfiguracionCobro.obtener()
        formulario = ConfiguracionCobroForm(request.POST, instance=configuracion)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, "La configuración del cobro automático se guardó correctamente.")
            return redirect("finanzas:configuracion")
        return render(request, self.template_name, {"formulario": formulario, "configuracion": configuracion})


class EjecutarProcesoCobroView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Ejecuta ya el proceso automático (lo mismo que hace el cron con `procesar_cobros`)."""

    codigo_modulo = Modulo.MOD06_FINANZAS
    roles_permitidos = ROLES_ADMIN

    def post(self, request):
        resumen = servicios.procesar_cobros()
        messages.success(
            request,
            "Proceso ejecutado: "
            f"{resumen['cuentas_generadas']} cuenta(s) generada(s), "
            f"{resumen['recordatorios_programados']} recordatorio(s) programado(s), "
            f"{resumen['correos_enviados']} correo(s) enviado(s), "
            f"{resumen['correos_fallidos']} fallido(s), "
            f"{resumen['whatsapp_pendientes']} WhatsApp pendiente(s) y "
            f"{resumen['cuentas_vencidas']} cuenta(s) marcada(s) como vencida(s).",
        )
        return redirect("finanzas:configuracion")


class PdfPublicoView(View):
    """
    PDF de la cuenta de cobro para el cliente, sin sesión, por el enlace
    firmado que recibe en WhatsApp o en el recordatorio. Un token alterado o
    vencido responde 404.
    """

    def get(self, request, token):
        cuenta = envios.cuenta_desde_token(token)
        if not cuenta or not cuenta.archivo:
            raise Http404("Enlace inválido o vencido.")
        return FileResponse(cuenta.archivo.open("rb"), filename=f"cuenta_cobro_{cuenta.pk}.pdf")
