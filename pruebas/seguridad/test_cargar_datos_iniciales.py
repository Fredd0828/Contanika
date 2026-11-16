"""Pruebas del comando `cargar_datos_iniciales` al instalar Contanika para un despacho nuevo."""

from io import StringIO

import pytest
from django.core import mail
from django.core.management import call_command

from aplicaciones.seguridad.management.commands import cargar_datos_iniciales as comando
from aplicaciones.seguridad.models import ConfiguracionDespacho, Rol, Usuario

pytestmark = pytest.mark.django_db


def _correr(**opciones):
    salida = StringIO()
    call_command("cargar_datos_iniciales", stdout=salida, **opciones)
    return salida.getvalue()


def test_instalacion_nueva_usa_el_nombre_del_despacho_indicado():
    _correr(nombre_despacho="Contadores Asociados SAS", ciudad_despacho="Medellín")
    despacho = ConfiguracionDespacho.objects.get()
    assert despacho.nombre_despacho == "Contadores Asociados SAS"
    assert despacho.ciudad == "Medellín"


def test_sin_nombre_queda_uno_provisional_y_no_el_de_otro_despacho():
    _correr()
    assert ConfiguracionDespacho.objects.get().nombre_despacho == comando.NOMBRE_DESPACHO_INICIAL


def test_volver_a_correrlo_no_pisa_los_datos_del_despacho():
    _correr(nombre_despacho="Primero SAS")
    salida = _correr(nombre_despacho="Segundo SAS")
    assert ConfiguracionDespacho.objects.get().nombre_despacho == "Primero SAS"
    assert "no se cambió" in salida


def test_el_primer_administrador_recibe_un_enlace_para_crear_su_clave():
    salida = _correr(correo_admin="Gerente@Despacho.co", nombre_admin="Gerente")
    admin = Usuario.objects.get(correo="gerente@despacho.co")
    assert admin.rol.nombre_rol == Rol.ADMINISTRADOR
    assert admin.is_superuser
    assert not admin.has_usable_password()
    assert len(mail.outbox) == 1
    assert "/crear-contrasena/" in mail.outbox[0].body
    assert "enlace para crear su contraseña" in salida


def test_si_el_correo_falla_el_enlace_se_muestra_en_la_terminal(monkeypatch):
    from aplicaciones.seguridad import servicios

    def rechazar(*args, **kwargs):
        raise OSError("SMTP caído")

    monkeypatch.setattr(servicios, "send_mail", rechazar)
    salida = _correr(correo_admin="gerente@despacho.co")
    assert "No se pudo enviar el correo" in salida
    assert "/crear-contrasena/" in salida


def test_con_clave_el_administrador_queda_listo_sin_correo():
    _correr(correo_admin="gerente@despacho.co", clave_admin="Clave-Inicial-2026")
    assert Usuario.objects.get(correo="gerente@despacho.co").check_password("Clave-Inicial-2026")
    assert mail.outbox == []


def test_no_duplica_un_administrador_que_ya_existe():
    _correr(correo_admin="gerente@despacho.co", clave_admin="Clave-Inicial-2026")
    salida = _correr(correo_admin="GERENTE@despacho.co")
    assert Usuario.objects.filter(correo__iexact="gerente@despacho.co").count() == 1
    assert "ya existe" in salida
