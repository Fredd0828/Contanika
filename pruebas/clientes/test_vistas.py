"""Pruebas de vistas, permisos y seguridad del módulo 1: clientes."""

import pytest
from django.test import Client
from django.urls import reverse

from aplicaciones.calendario.models import TablaReferenciaDian, Vencimiento
from aplicaciones.clientes.models import Cliente, ObligacionTributaria

pytestmark = pytest.mark.django_db


def _datos_cliente(**extra):
    """Datos válidos del formulario de cliente, incluido el formset de municipios."""
    datos = {
        "nombre_razon_social": "Panadería El Trigal SAS",
        "nit_cedula": "901222333",
        "tipo_documento": Cliente.NIT,
        "tipo_persona": Cliente.JURIDICA,
        "regimen_tributario": "Régimen ordinario",
        "ciudad": "Bogotá D.C.",
        "municipio_principal": "Bogotá D.C.",
        "informacion_contacto": "3101234567",
        "correo_cliente": "contacto@trigal.co",
        "estado": Cliente.ACTIVO,
        "responsable": "",
        "municipios-TOTAL_FORMS": "1",
        "municipios-INITIAL_FORMS": "0",
        "municipios-MIN_NUM_FORMS": "0",
        "municipios-MAX_NUM_FORMS": "1000",
        "municipios-0-municipio": "Soacha",
    }
    datos.update(extra)
    return datos


def test_listado_requiere_sesion(client):
    """Sin sesión, el listado redirige al inicio de sesión."""
    respuesta = client.get(reverse("clientes:lista"))
    assert respuesta.status_code == 302
    assert reverse("seguridad:iniciar_sesion") in respuesta.url


def test_administrador_ve_el_listado(client, usuario_administrador, cliente):
    """El Administrador ve todos los clientes."""
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("clientes:lista"))
    assert respuesta.status_code == 200
    assert "Comercializadora La Rebaja" in respuesta.content.decode()


def test_junior_ve_todos_los_clientes(client, usuario_junior, cliente):
    """El Contador Junior consulta el listado completo de clientes del despacho."""
    Cliente.objects.create(
        nombre_razon_social="Cliente del Junior",
        nit_cedula="800999888",
        tipo_persona=Cliente.NATURAL,
        responsable=usuario_junior,
    )
    client.force_login(usuario_junior)
    contenido = client.get(reverse("clientes:lista")).content.decode()
    assert "Cliente del Junior" in contenido
    assert "Comercializadora La Rebaja" in contenido


def test_junior_ve_la_ficha_de_un_cliente_ajeno_sin_credenciales(client, usuario_junior, cliente):
    """La ficha de un cliente ajeno carga, pero sus credenciales no se muestran al Junior."""
    from aplicaciones.clientes.models import Credencial

    Credencial.objects.create(cliente=cliente, concepto="DIAN", usuario_acceso="900123456", clave_cifrada="x")
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("clientes:detalle", args=[cliente.pk]))
    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert "tab-credenciales" not in contenido
    assert respuesta.context["puede_ver_credenciales"] is False


def test_junior_ve_las_credenciales_de_sus_clientes(client, usuario_junior, cliente):
    """El Junior sigue viendo (sin editar) las credenciales de los clientes a su cargo."""
    cliente.responsable = usuario_junior
    cliente.save()
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("clientes:detalle", args=[cliente.pk]))
    assert "tab-credenciales" in respuesta.content.decode()
    assert respuesta.context["puede_editar"] is False


def test_junior_crea_cliente_a_su_nombre(client, usuario_junior, usuario_administrador):
    """El Junior registra clientes; quedan a su nombre aunque intente asignar otro responsable."""
    client.force_login(usuario_junior)
    respuesta = client.post(
        reverse("clientes:crear"),
        _datos_cliente(responsable=usuario_administrador.pk, estado=Cliente.INACTIVO),
    )
    assert respuesta.status_code == 302
    creado = Cliente.objects.get(nit_cedula="901222333")
    assert creado.responsable == usuario_junior
    assert creado.estado == Cliente.ACTIVO


def test_formulario_del_junior_no_ofrece_responsable_ni_estado(client, usuario_junior):
    client.force_login(usuario_junior)
    formulario = client.get(reverse("clientes:crear")).context["formulario"]
    assert "responsable" not in formulario.fields
    assert "estado" not in formulario.fields


def test_junior_edita_cliente_ajeno_sin_cambiar_responsable_ni_estado(
    client, usuario_junior, usuario_administrador, cliente
):
    """El Junior corrige los datos de cualquier cliente, pero no lo reasigna ni lo inactiva."""
    client.force_login(usuario_junior)
    datos = _datos_cliente(
        nombre_razon_social="Comercializadora La Rebaja Ltda",
        nit_cedula=cliente.nit_cedula,
        responsable=usuario_junior.pk,
        estado=Cliente.INACTIVO,
    )
    respuesta = client.post(reverse("clientes:editar", args=[cliente.pk]), datos)
    assert respuesta.status_code == 302
    cliente.refresh_from_db()
    assert cliente.nombre_razon_social == "Comercializadora La Rebaja Ltda"
    assert cliente.responsable == usuario_administrador
    assert cliente.estado == Cliente.ACTIVO


def test_junior_no_inactiva_ni_importa_clientes(client, usuario_junior, cliente):
    """Inactivar e importar siguen siendo del Administrador y el Contador Senior."""
    client.force_login(usuario_junior)
    assert client.post(reverse("clientes:inactivar", args=[cliente.pk])).status_code == 403
    assert client.get(reverse("clientes:importar")).status_code == 403
    cliente.refresh_from_db()
    assert cliente.estado == Cliente.ACTIVO


def test_senior_crea_cliente_con_municipio(client, usuario_senior):
    """El Contador Senior crea un cliente con municipio adicional."""
    client.force_login(usuario_senior)
    respuesta = client.post(reverse("clientes:crear"), _datos_cliente())
    assert respuesta.status_code == 302
    creado = Cliente.objects.get(nit_cedula="901222333")
    assert creado.responsable == usuario_senior
    assert creado.municipios_adicionales.filter(municipio="Soacha").exists()


def test_crear_cliente_calcula_sus_vencimientos_dian(client, usuario_senior):
    """Al guardar un cliente con obligaciones marcadas se calculan sus vencimientos."""
    from datetime import date

    renta, _ = ObligacionTributaria.objects.get_or_create(nombre="Renta personas naturales")
    TablaReferenciaDian.objects.create(
        tipo_obligacion=renta.nombre,
        grupo_nit="33",
        fecha_vencimiento=date(2026, 8, 21),
        periodo_gravable="2026",
    )
    client.force_login(usuario_senior)
    respuesta = client.post(
        reverse("clientes:crear"),
        _datos_cliente(
            nit_cedula="1019087733",
            tipo_documento=Cliente.NIT,
            tipo_persona=Cliente.NATURAL,
            obligaciones_tributarias=[renta.pk],
        ),
        follow=True,
    )
    creado = Cliente.objects.get(nit_cedula="1019087733")
    vencimiento = Vencimiento.objects.get(cliente=creado)
    assert vencimiento.fecha_vencimiento == date(2026, 8, 21)
    assert "Vencimientos DIAN calculados" in respuesta.content.decode()


def test_crear_cliente_sin_obligaciones_pregunta_que_impuestos_presenta(client, usuario_senior):
    """Sin obligaciones marcadas, el sistema avisa en lugar de dejar el calendario vacío."""
    client.force_login(usuario_senior)
    respuesta = client.post(reverse("clientes:crear"), _datos_cliente(), follow=True)
    creado = Cliente.objects.get(nit_cedula="901222333")
    assert not Vencimiento.objects.filter(cliente=creado).exists()
    assert "qué impuestos o anticipos presenta" in respuesta.content.decode()


def test_crear_cliente_con_servicio_nuevo(client, usuario_senior):
    """El campo de servicio abierto crea un tipo de servicio nuevo."""
    client.force_login(usuario_senior)
    respuesta = client.post(
        reverse("clientes:crear"),
        _datos_cliente(nuevo_tipo_servicio="Auditoría tributaria"),
    )
    assert respuesta.status_code == 302
    creado = Cliente.objects.get(nit_cedula="901222333")
    assert creado.servicios.filter(tipo_servicio__nombre_servicio="Auditoría tributaria").exists()


def test_no_permite_nit_duplicado(client, usuario_senior, cliente):
    """No se permiten dos clientes con el mismo NIT o cédula."""
    client.force_login(usuario_senior)
    respuesta = client.post(
        reverse("clientes:crear"),
        _datos_cliente(nit_cedula=cliente.nit_cedula),
    )
    assert respuesta.status_code == 200
    assert "Ya existe un cliente" in respuesta.content.decode()


def test_rechaza_nit_con_mas_de_10_digitos(client, usuario_senior):
    """El formulario rechaza un NIT con más de 10 dígitos."""
    client.force_login(usuario_senior)
    respuesta = client.post(
        reverse("clientes:crear"),
        _datos_cliente(nit_cedula="12345678901"),
    )
    assert respuesta.status_code == 200
    assert "como máximo 10 caracteres" in respuesta.content.decode()


def test_rechaza_nit_con_letras(client, usuario_senior):
    """El formulario rechaza un NIT que contenga letras."""
    client.force_login(usuario_senior)
    respuesta = client.post(
        reverse("clientes:crear"),
        _datos_cliente(nit_cedula="123ABC456"),
    )
    assert respuesta.status_code == 200
    assert "solo debe contener dígitos" in respuesta.content.decode()


def test_inactivar_conserva_el_cliente(client, usuario_administrador, cliente):
    """Inactivar un cliente no lo elimina y conserva su historial."""
    client.force_login(usuario_administrador)
    respuesta = client.post(reverse("clientes:inactivar", args=[cliente.pk]))
    assert respuesta.status_code == 302
    cliente.refresh_from_db()
    assert cliente.estado == Cliente.INACTIVO
    assert Cliente.objects.filter(pk=cliente.pk).exists()


def test_filtro_por_estado(client, usuario_administrador, cliente):
    """El filtro desplegable por estado funciona en el listado."""
    Cliente.objects.create(
        nombre_razon_social="Cliente Inactivo",
        nit_cedula="700111222",
        tipo_persona=Cliente.NATURAL,
        estado=Cliente.INACTIVO,
        responsable=usuario_administrador,
    )
    client.force_login(usuario_administrador)
    contenido = client.get(reverse("clientes:lista"), {"estado": "Inactivo"}).content.decode()
    assert "Cliente Inactivo" in contenido
    assert "Comercializadora La Rebaja" not in contenido


def test_csrf_protege_la_creacion(usuario_senior):
    """Un POST sin token CSRF es rechazado (RQNF004)."""
    cliente_csrf = Client(enforce_csrf_checks=True)
    cliente_csrf.force_login(usuario_senior)
    respuesta = cliente_csrf.post(reverse("clientes:crear"), _datos_cliente())
    assert respuesta.status_code == 403


def test_paginacion_default_10_registros(client, usuario_administrador):
    """El listado muestra 10 clientes por pagina por defecto."""
    for indice in range(12):
        Cliente.objects.create(
            nombre_razon_social=f"Cliente Paginado {indice}",
            nit_cedula=f"{900000000 + indice}",
            tipo_documento=Cliente.NIT,
            tipo_persona=Cliente.JURIDICA,
            responsable=usuario_administrador,
        )
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("clientes:lista"))
    assert respuesta.status_code == 200
    assert len(respuesta.context["clientes"]) == 10
    assert respuesta.context["is_paginated"] is True
