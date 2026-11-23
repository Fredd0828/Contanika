"""Pruebas de servicios y selectores del módulo 8: equipo de trabajo, roles y permisos."""

from datetime import date, timedelta

import pytest
from django.core import mail
from django.urls import reverse

from aplicaciones.calendario.models import Vencimiento
from aplicaciones.expediente.models import Anotacion
from aplicaciones.seguridad import selectores, servicios
from aplicaciones.seguridad.formularios import UsuarioCrearForm
from aplicaciones.seguridad.models import Modulo, PermisoRolModulo, Rol, Usuario
from aplicaciones.tareas.models import Tarea

from ..conftest import CLAVE_PRUEBAS

pytestmark = pytest.mark.django_db


def _formulario_crear(rol, correo="nuevo@ejemplo.co", **extra):
    datos = {
        "nombre": "Nuevo Integrante",
        "correo": correo,
        "telefono": "3001112233",
        "rol": rol.pk,
    }
    datos.update(extra)
    formulario = UsuarioCrearForm(datos)
    assert formulario.is_valid(), formulario.errors
    return formulario


# ---------------------------------------------------------------------------
# Reglas de administradores (HU022-5)
# ---------------------------------------------------------------------------


def test_no_puede_quedar_sin_administrador_activo(usuario_administrador, rol_senior):
    with pytest.raises(servicios.ErrorEquipo, match="al menos un Administrador"):
        servicios.validar_administradores(usuario_administrador, rol_senior, Usuario.ACTIVO)


def test_segundo_administrador_exige_confirmacion(usuario_administrador, rol_administrador):
    nuevo = Usuario(nombre="Otro", correo="otro@ejemplo.co", rol=rol_administrador)
    with pytest.raises(servicios.ConfirmacionRequerida, match="Paula Andrea Blanco"):
        servicios.validar_administradores(nuevo, rol_administrador, Usuario.ACTIVO)
    servicios.validar_administradores(nuevo, rol_administrador, Usuario.ACTIVO, confirmado=True)


# ---------------------------------------------------------------------------
# Crear y actualizar usuarios
# ---------------------------------------------------------------------------


def test_crear_usuario_envia_enlace_y_no_una_clave(usuario_administrador, rol_junior, settings):
    settings.URL_SITIO = "https://contanika.ejemplo.co/"
    usuario, enviado, enlace = servicios.crear_usuario(
        _formulario_crear(rol_junior, correo="NUEVO@Ejemplo.co")
    )
    assert enviado is True
    assert usuario.correo == "nuevo@ejemplo.co"
    assert usuario.estado == Usuario.ACTIVO
    assert not usuario.has_usable_password()
    assert enlace.startswith("https://contanika.ejemplo.co/crear-contrasena/")
    assert len(mail.outbox) == 1
    correo = mail.outbox[0]
    assert correo.to == ["nuevo@ejemplo.co"]
    assert correo.subject == "Bienvenido a Contanika"
    assert enlace in correo.body
    assert "Contador Junior" in correo.body
    assert "3 días" in correo.body
    assert "contraseña temporal" not in correo.body.lower()


def test_crear_usuario_aunque_falle_el_correo_devuelve_el_enlace(
    usuario_administrador, rol_junior, monkeypatch
):
    def rechazar(*args, **kwargs):
        raise OSError("SMTP caído")

    monkeypatch.setattr(servicios, "send_mail", rechazar)
    usuario, enviado, enlace = servicios.crear_usuario(_formulario_crear(rol_junior))
    assert enviado is False
    assert "/crear-contrasena/" in enlace
    assert Usuario.objects.filter(pk=usuario.pk).exists()


def test_crear_segundo_administrador_sin_confirmar_no_guarda(usuario_administrador, rol_administrador):
    with pytest.raises(servicios.ConfirmacionRequerida):
        servicios.crear_usuario(_formulario_crear(rol_administrador))
    assert not Usuario.objects.filter(correo="nuevo@ejemplo.co").exists()


def test_formulario_de_crear_no_pide_contrasena(rol_junior):
    from aplicaciones.seguridad.formularios import UsuarioEditarForm

    assert not any("clave" in nombre for nombre in UsuarioCrearForm().fields)
    assert not any("clave" in nombre for nombre in UsuarioEditarForm().fields)


def test_formulario_rechaza_correo_repetido(usuario_administrador, rol_junior):
    formulario = UsuarioCrearForm(
        {"nombre": "X", "correo": usuario_administrador.correo, "rol": rol_junior.pk}
    )
    assert not formulario.is_valid()
    assert "correo" in formulario.errors


def test_reenviar_acceso_manda_un_enlace_nuevo_sin_cambiar_la_clave(usuario_junior):
    enviado, enlace = servicios.reenviar_acceso(usuario_junior)
    assert enviado is True
    assert mail.outbox[0].subject == "Contanika: enlace para crear su contraseña"
    assert enlace in mail.outbox[0].body
    usuario_junior.refresh_from_db()
    assert usuario_junior.check_password(CLAVE_PRUEBAS)


def test_reenviar_acceso_a_un_usuario_inactivo_se_rechaza(usuario_junior):
    usuario_junior.estado = Usuario.INACTIVO
    usuario_junior.save()
    with pytest.raises(servicios.ErrorEquipo, match="inactivo"):
        servicios.reenviar_acceso(usuario_junior)
    assert mail.outbox == []


# ---------------------------------------------------------------------------
# Estado y eliminación
# ---------------------------------------------------------------------------


def test_inactivar_bloquea_el_inicio_de_sesion(client, usuario_administrador, usuario_junior):
    servicios.cambiar_estado_usuario(usuario_junior, Usuario.INACTIVO, usuario_administrador)
    respuesta = client.post(
        reverse("seguridad:iniciar_sesion"), {"username": usuario_junior.correo, "password": CLAVE_PRUEBAS}
    )
    assert respuesta.status_code == 200  # vuelve al formulario: no inicia sesión


def test_no_puede_inactivarse_a_si_mismo(usuario_administrador):
    with pytest.raises(servicios.ErrorEquipo, match="propio"):
        servicios.cambiar_estado_usuario(usuario_administrador, Usuario.INACTIVO, usuario_administrador)


def test_activar_otro_administrador_exige_confirmacion(usuario_administrador, rol_administrador):
    otro = Usuario.objects.create_user(
        correo="otro@ejemplo.co", nombre="Otro Admin", password=CLAVE_PRUEBAS, rol=rol_administrador
    )
    otro.estado = Usuario.INACTIVO
    otro.save()
    with pytest.raises(servicios.ConfirmacionRequerida):
        servicios.cambiar_estado_usuario(otro, Usuario.ACTIVO, usuario_administrador)
    servicios.cambiar_estado_usuario(otro, Usuario.ACTIVO, usuario_administrador, confirmado=True)
    otro.refresh_from_db()
    assert otro.estado == Usuario.ACTIVO


def test_eliminar_usuario_sin_historial(usuario_administrador, usuario_junior):
    servicios.eliminar_usuario(usuario_junior, usuario_administrador)
    assert not Usuario.objects.filter(pk=usuario_junior.pk).exists()


def test_no_elimina_usuario_con_historial(usuario_administrador, usuario_junior, cliente):
    Anotacion.objects.create(cliente=cliente, usuario=usuario_junior, tipo_anotacion="Llamada", contenido="x")
    assert servicios.tiene_historial(usuario_junior)
    with pytest.raises(servicios.ErrorEquipo, match="Inactívelo"):
        servicios.eliminar_usuario(usuario_junior, usuario_administrador)
    assert Usuario.objects.filter(pk=usuario_junior.pk).exists()


def test_cliente_asignado_cuenta_como_historial(usuario_junior, cliente_junior):
    assert servicios.tiene_historial(usuario_junior)


def test_no_puede_eliminarse_a_si_mismo(usuario_administrador):
    with pytest.raises(servicios.ErrorEquipo, match="propio"):
        servicios.eliminar_usuario(usuario_administrador, usuario_administrador)


# ---------------------------------------------------------------------------
# Módulos por rol (HU050)
# ---------------------------------------------------------------------------


@pytest.fixture
def modulo_equipo(db):
    return Modulo.objects.create(codigo_modulo=Modulo.MOD08_EQUIPO, nombre_modulo="Gestión de equipo y roles")


def test_guardar_permisos_inhabilita_lo_no_marcado(
    rol_administrador, rol_junior, modulo_clientes, modulo_equipo
):
    servicios.guardar_permisos_modulos({(rol_administrador.pk, modulo_clientes.pk)})
    assert PermisoRolModulo.objects.get(rol=rol_administrador, modulo=modulo_clientes).habilitado
    assert not PermisoRolModulo.objects.get(rol=rol_junior, modulo=modulo_clientes).habilitado


def test_administrador_conserva_siempre_el_modulo_de_equipo(rol_administrador, modulo_equipo):
    servicios.guardar_permisos_modulos(set())
    assert PermisoRolModulo.objects.get(rol=rol_administrador, modulo=modulo_equipo).habilitado


def test_matriz_considera_habilitado_lo_no_guardado(rol_senior, modulo_clientes):
    roles, filas = selectores.matriz_permisos()
    assert roles == [rol_senior]
    assert filas[0]["celdas"][0]["habilitado"] is True


# ---------------------------------------------------------------------------
# Panel de equipo (HU023)
# ---------------------------------------------------------------------------


def test_resumen_equipo_cuenta_tareas_y_vencimientos(usuario_administrador, usuario_junior, cliente):
    hoy = date(2026, 10, 15)
    for estado in (Tarea.TERMINADO, Tarea.POR_HACER, Tarea.EN_PROGRESO):
        Tarea.objects.create(
            cliente=cliente,
            titulo=f"T {estado}",
            responsable=usuario_junior,
            estado=estado,
            fecha_vencimiento=hoy,
        )
    Tarea.objects.create(
        cliente=cliente, titulo="Otro mes", responsable=usuario_junior, fecha_vencimiento=date(2026, 11, 3)
    )
    Vencimiento.objects.create(
        cliente=cliente,
        tipo_obligacion="IVA",
        fecha_vencimiento=hoy + timedelta(days=3),
        responsable=usuario_junior,
    )
    Vencimiento.objects.create(
        cliente=cliente,
        tipo_obligacion="Renta",
        fecha_vencimiento=hoy + timedelta(days=20),
        responsable=usuario_junior,
    )
    fila = next(f for f in selectores.resumen_equipo(hoy) if f["usuario"] == usuario_junior)
    assert fila["tareas_activas"] == 3
    assert (fila["terminadas_mes"], fila["tareas_mes"], fila["porcentaje_mes"]) == (1, 3, 33)
    assert [v.tipo_obligacion for v in fila["vencimientos"]] == ["IVA"]
    assert fila["alerta"] is False


def test_resumen_marca_alerta_con_mas_de_10_pendientes(usuario_junior, cliente):
    for numero in range(11):
        Tarea.objects.create(cliente=cliente, titulo=f"T{numero}", responsable=usuario_junior)
    fila = next(f for f in selectores.resumen_equipo() if f["usuario"] == usuario_junior)
    assert fila["alerta"] is True
    assert fila["porcentaje_mes"] is None


def test_resumen_excluye_inactivos(usuario_administrador, usuario_junior):
    usuario_junior.estado = Usuario.INACTIVO
    usuario_junior.save()
    assert [f["usuario"] for f in selectores.resumen_equipo()] == [usuario_administrador]


def test_modulos_por_rol(rol_junior, modulo_clientes, modulo_equipo):
    PermisoRolModulo.objects.create(rol=rol_junior, modulo=modulo_equipo, habilitado=False)
    assert selectores.modulos_por_rol()[rol_junior.pk] == [modulo_clientes.nombre_modulo]


def test_roles_existentes_en_el_formulario(rol_administrador, rol_senior, rol_junior):
    formulario = UsuarioCrearForm()
    assert [r.nombre_rol for r in formulario.fields["rol"].queryset] == [
        Rol.ADMINISTRADOR,
        Rol.CONTADOR_SENIOR,
        Rol.CONTADOR_JUNIOR,
    ]
