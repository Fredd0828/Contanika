"""Pruebas de las reglas de negocio del módulo 2: cálculo DIAN y vencimientos."""

from datetime import date

import pytest
from django.core.exceptions import PermissionDenied

from aplicaciones.calendario.models import (
    AnotacionCalendario,
    ConfiguracionAlerta,
    TablaReferenciaDian,
    Vencimiento,
)
from aplicaciones.calendario.servicios import (
    calcular_grupo_nit,
    cambiar_estado_presentacion,
    eliminar_anotacion,
    generar_vencimientos_cliente,
    generar_vencimientos_masivo,
    guardar_anotacion,
    guardar_vencimiento_manual,
    obligaciones_por_cliente,
    validar_vencimiento,
)
from aplicaciones.clientes.models import Cliente

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# calcular_grupo_nit
# ---------------------------------------------------------------------------


def test_grupo_nit_empresa_usa_ultimo_digito(cliente):
    """Empresas (NIT): el grupo DIAN es el último dígito del NIT."""
    assert cliente.nit_cedula == "900123456"
    assert calcular_grupo_nit(cliente) == "6"


def test_grupo_nit_persona_natural_usa_dos_ultimos_digitos(cliente_natural):
    """Personas naturales (CC): el grupo son los dos últimos dígitos."""
    assert cliente_natural.nit_cedula == "1032456789"
    assert calcular_grupo_nit(cliente_natural) == "89"


def test_grupo_nit_extranjero_no_es_calculable(cliente_extranjero):
    """Documentos extranjeros no tienen cálculo automático (registro manual)."""
    assert calcular_grupo_nit(cliente_extranjero) is None


def test_grupo_nit_sin_digitos_no_es_calculable(usuario_administrador):
    """Un documento sin dígitos no puede calcular grupo."""
    cliente = Cliente.objects.create(
        nombre_razon_social="Sin Número SAS",
        nit_cedula="ABC",
        tipo_documento=Cliente.NIT,
        tipo_persona=Cliente.JURIDICA,
        responsable=usuario_administrador,
    )
    assert calcular_grupo_nit(cliente) is None


# ---------------------------------------------------------------------------
# obligaciones_por_cliente
# ---------------------------------------------------------------------------


def test_obligaciones_juridica_ordinaria_con_iva(cliente):
    """Jurídica ordinaria responsable de IVA: renta PJ, retención e IVA."""
    obligaciones = obligaciones_por_cliente(cliente)
    assert "Renta personas jurídicas" in obligaciones
    assert "Retención en la fuente" in obligaciones
    assert "IVA bimestral" in obligaciones


def test_obligaciones_juridica_ordinaria_sin_iva(cliente):
    """Sin responsabilidad de IVA no se genera la obligación de IVA."""
    cliente.responsable_iva = False
    obligaciones = obligaciones_por_cliente(cliente)
    assert "IVA bimestral" not in obligaciones


def test_obligaciones_regimen_simple(cliente):
    """Régimen simple (cualquier variante del nombre) genera obligaciones RST."""
    cliente.regimen_tributario = "Régimen simple de tributación"
    assert obligaciones_por_cliente(cliente) == [
        "RST anticipo bimestral",
        "RST consolidada anual",
    ]
    cliente.regimen_tributario = "Régimen simplificado"
    assert obligaciones_por_cliente(cliente) == [
        "RST anticipo bimestral",
        "RST consolidada anual",
    ]


def test_obligaciones_persona_natural(cliente_natural):
    """Persona natural: renta PN; con IVA agrega IVA y retención."""
    assert obligaciones_por_cliente(cliente_natural) == ["Renta personas naturales"]
    cliente_natural.responsable_iva = True
    assert obligaciones_por_cliente(cliente_natural) == [
        "Renta personas naturales",
        "IVA bimestral",
        "Retención en la fuente",
    ]


# ---------------------------------------------------------------------------
# generar_vencimientos_cliente
# ---------------------------------------------------------------------------


def test_generar_vencimientos_crea_desde_tabla_dian(cliente, usuario_administrador, referencia_dian):
    """El cálculo crea vencimientos nacionales pendientes de validar."""
    resumen = generar_vencimientos_cliente(cliente, usuario_administrador)

    assert resumen["creados"] == 1
    vencimiento = Vencimiento.objects.get(cliente=cliente)
    assert vencimiento.tipo_obligacion == "IVA bimestral"
    assert vencimiento.ambito == Vencimiento.NACIONAL
    assert vencimiento.fecha_vencimiento == date(2026, 3, 17)
    assert vencimiento.estado_validacion == Vencimiento.PENDIENTE_VALIDAR
    assert vencimiento.es_automatico_dian is True
    assert vencimiento.responsable == cliente.responsable


def test_generar_vencimientos_no_duplica(cliente, usuario_administrador, referencia_dian):
    """Volver a calcular no duplica los vencimientos ya creados."""
    generar_vencimientos_cliente(cliente, usuario_administrador)
    resumen = generar_vencimientos_cliente(cliente, usuario_administrador)

    assert resumen["creados"] == 0
    assert resumen["omitidos"] == 1
    assert Vencimiento.objects.filter(cliente=cliente).count() == 1


def test_generar_vencimientos_sin_grupo_no_crea(cliente_extranjero, usuario_administrador):
    """Un cliente sin grupo calculable no genera vencimientos automáticos."""
    resumen = generar_vencimientos_cliente(cliente_extranjero, usuario_administrador)

    assert resumen["sin_grupo"] is True
    assert resumen["creados"] == 0
    assert Vencimiento.objects.filter(cliente=cliente_extranjero).count() == 0


def test_generar_vencimientos_persona_natural_usa_dos_digitos(cliente_natural, usuario_administrador):
    """La renta de persona natural busca la referencia con dos dígitos."""
    TablaReferenciaDian.objects.create(
        tipo_obligacion="Renta personas naturales",
        grupo_nit="89",
        fecha_vencimiento=date(2026, 10, 19),
        periodo_gravable="2026",
    )
    resumen = generar_vencimientos_cliente(cliente_natural, usuario_administrador)

    assert resumen["creados"] == 1
    vencimiento = Vencimiento.objects.get(cliente=cliente_natural)
    assert vencimiento.tipo_obligacion == "Renta personas naturales"


def test_generar_vencimientos_masivo_solo_activos(
    cliente, cliente_natural, usuario_administrador, referencia_dian
):
    """El cálculo masivo omite clientes inactivos."""
    cliente_natural.inactivar()
    resumen = generar_vencimientos_masivo(usuario_administrador, solo_activos=True)

    assert resumen["clientes"] == 1
    assert Vencimiento.objects.filter(cliente=cliente).count() == 1
    assert Vencimiento.objects.filter(cliente=cliente_natural).count() == 0


# ---------------------------------------------------------------------------
# Vencimiento manual, validación y estado
# ---------------------------------------------------------------------------


def test_guardar_vencimiento_manual_asigna_responsable(cliente, usuario_administrador):
    """El vencimiento manual queda con el usuario que lo registra si no hay responsable."""
    from aplicaciones.calendario.formularios import VencimientoManualForm

    formulario = VencimientoManualForm(
        data={
            "cliente": cliente.pk,
            "tipo_obligacion": "ICA municipal",
            "ambito": Vencimiento.MUNICIPAL,
            "municipio": "Bogotá D.C.",
            "fecha_vencimiento": "2026-05-15",
            "estado_presentacion": Vencimiento.PENDIENTE,
        },
        usuario=usuario_administrador,
    )
    assert formulario.is_valid(), formulario.errors
    vencimiento = guardar_vencimiento_manual(formulario, usuario_administrador)

    assert vencimiento.responsable == usuario_administrador
    assert vencimiento.estado_validacion == ""
    assert vencimiento.es_automatico_dian is False


def test_validar_vencimiento_alterna_estado(cliente):
    """La validación cambia entre pendiente y validado."""
    vencimiento = Vencimiento.objects.create(
        cliente=cliente,
        tipo_obligacion="IVA bimestral",
        fecha_vencimiento=date(2026, 3, 17),
        estado_validacion=Vencimiento.PENDIENTE_VALIDAR,
    )
    validar_vencimiento(vencimiento, validado=True)
    assert vencimiento.estado_validacion == Vencimiento.VALIDADO
    validar_vencimiento(vencimiento, validado=False)
    assert vencimiento.estado_validacion == Vencimiento.PENDIENTE_VALIDAR


def test_cambiar_estado_presentacion_rechaza_estado_invalido(cliente):
    """No se acepta un estado fuera de las opciones del modelo."""
    vencimiento = Vencimiento.objects.create(
        cliente=cliente,
        tipo_obligacion="IVA bimestral",
        fecha_vencimiento=date(2026, 3, 17),
    )
    with pytest.raises(ValueError):
        cambiar_estado_presentacion(vencimiento, "Estado inventado")


# ---------------------------------------------------------------------------
# Anotaciones
# ---------------------------------------------------------------------------


def test_guardar_anotacion_con_destinatarios(usuario_administrador, usuario_junior):
    """Una anotación por etiqueta registra a sus destinatarios."""
    from aplicaciones.calendario.formularios import AnotacionCalendarioForm

    formulario = AnotacionCalendarioForm(
        data={
            "fecha": "2026-10-05",
            "contenido": "Reunión de cierre contable",
            "visibilidad": AnotacionCalendario.POR_ETIQUETA,
            "destinatarios": [usuario_junior.pk],
        }
    )
    assert formulario.is_valid(), formulario.errors
    anotacion = guardar_anotacion(
        formulario,
        usuario_administrador,
        destinatarios=formulario.cleaned_data["destinatarios"],
    )

    assert anotacion.autor == usuario_administrador
    assert anotacion.destinatarios.count() == 1
    assert anotacion.destinatarios.first().usuario == usuario_junior


def test_eliminar_anotacion_solo_autor_o_admin(usuario_administrador, usuario_senior, usuario_junior):
    """Otro usuario no puede eliminar la anotación; el administrador sí."""
    anotacion = AnotacionCalendario.objects.create(
        fecha=date(2026, 10, 5),
        contenido="Nota privada",
        autor=usuario_junior,
        visibilidad=AnotacionCalendario.PRIVADA,
    )
    with pytest.raises(PermissionDenied):
        eliminar_anotacion(anotacion, usuario_senior)

    eliminar_anotacion(anotacion, usuario_administrador)
    assert AnotacionCalendario.objects.count() == 0


def test_eliminar_anotacion_por_su_autor(usuario_junior):
    """El autor puede eliminar su propia anotación."""
    anotacion = AnotacionCalendario.objects.create(
        fecha=date(2026, 10, 5),
        contenido="Nota propia",
        autor=usuario_junior,
        visibilidad=AnotacionCalendario.PRIVADA,
    )
    eliminar_anotacion(anotacion, usuario_junior)
    assert AnotacionCalendario.objects.count() == 0


def test_alerta_se_asocia_al_vencimiento(cliente):
    """Las alertas quedan asociadas a su vencimiento."""
    vencimiento = Vencimiento.objects.create(
        cliente=cliente,
        tipo_obligacion="IVA bimestral",
        fecha_vencimiento=date(2026, 3, 17),
    )
    alerta = ConfiguracionAlerta.objects.create(
        vencimiento=vencimiento,
        dias_anticipacion=7,
        canal=ConfiguracionAlerta.WHATSAPP,
    )
    assert alerta.vencimiento == vencimiento
    assert vencimiento.alertas.count() == 1
