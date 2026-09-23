"""Pruebas de credenciales: cifrado, formularios, vistas y permisos."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from aplicaciones.clientes.formularios import CredencialForm
from aplicaciones.clientes.models import Cliente, Credencial
from aplicaciones.clientes.servicios import eliminar_credencial, guardar_credencial


@pytest.fixture
def cliente_otro(usuario_senior):
    """Cliente asignado a otro usuario (no al junior)."""
    return Cliente.objects.create(
        nombre_razon_social="Otro Cliente SAS",
        nit_cedula="900999888",
        tipo_documento=Cliente.NIT,
        tipo_persona=Cliente.JURIDICA,
        regimen_tributario="Régimen ordinario",
        ciudad="Medellín",
        municipio_principal="Medellín",
        responsable=usuario_senior,
    )


pytestmark = pytest.mark.django_db


class TestCredencialCifrado:
    """Pruebas del cifrado y descifrado de contraseñas."""

    def test_establecer_y_obtener_clave(self, cliente):
        """Cifrar y descifrar una contraseña funciona correctamente."""
        credencial = Credencial.objects.create(
            cliente=cliente,
            concepto="DIAN",
            usuario_acceso="usuario@test.com",
            clave_cifrada="",  # Se sobrescribe
        )
        clave_original = "MiClaveSegura123!"
        credencial.establecer_clave(clave_original)
        credencial.save()

        # Verificar que se guardó cifrada (no es la original)
        credencial.refresh_from_db()
        assert credencial.clave_cifrada != clave_original
        assert len(credencial.clave_cifrada) > 20

        # Verificar que se puede descifrar
        assert credencial.obtener_clave() == clave_original

    def test_propiedad_clave_plana(self, cliente):
        """La propiedad clave_plana retorna la clave descifrada."""
        credencial = Credencial.objects.create(
            cliente=cliente,
            concepto="Secretaría de Hacienda",
            usuario_acceso="usuario-hacienda",
            clave_cifrada="",
        )
        credencial.establecer_clave("OtraClave456@")
        credencial.save()

        assert credencial.clave_plana == "OtraClave456@"

    def test_clave_diferente_por_instancia(self, cliente):
        """Cada credencial tiene su propia clave cifrada única."""
        cred1 = Credencial.objects.create(
            cliente=cliente,
            concepto="DIAN",
            usuario_acceso="user1",
            clave_cifrada="",
        )
        cred2 = Credencial.objects.create(
            cliente=cliente,
            concepto="Hacienda",
            usuario_acceso="user2",
            clave_cifrada="",
        )
        cred1.establecer_clave("ClaveComun123")
        cred2.establecer_clave("ClaveComun123")
        cred1.save()
        cred2.save()

        # Aunque la clave original es igual, el cifrado produce valores diferentes (por nonce)
        assert cred1.clave_cifrada != cred2.clave_cifrada
        assert cred1.obtener_clave() == "ClaveComun123"
        assert cred2.obtener_clave() == "ClaveComun123"


class TestCredencialForm:
    """Pruebas del formulario de credenciales."""

    def test_form_valido_crear(self, cliente):
        """Formulario válido para crear credencial."""
        form = CredencialForm(
            data={
                "concepto": "DIAN",
                "usuario_acceso": "usuario@dian.gov.co",
                "clave": "MiClaveSegura123!",
            }
        )
        assert form.is_valid(), form.errors
        credencial = form.save(commit=False)
        credencial.cliente = cliente
        credencial.save()
        assert credencial.concepto == "DIAN"
        assert credencial.obtener_clave() == "MiClaveSegura123!"

    def test_form_valido_editar_sin_cambiar_clave(self, cliente):
        """Formulario válido al editar sin cambiar la contraseña."""
        credencial = Credencial.objects.create(
            cliente=cliente,
            concepto="DIAN",
            usuario_acceso="usuario@dian.gov.co",
            clave_cifrada="",
        )
        credencial.establecer_clave("ClaveOriginal123")
        credencial.save()

        form = CredencialForm(
            instance=credencial,
            data={
                "concepto": "DIAN Actualizado",
                "usuario_acceso": "nuevo@dian.gov.co",
                "clave": "",  # Vacío = mantener actual
            },
        )
        assert form.is_valid(), form.errors
        credencial_actualizada = form.save()
        assert credencial_actualizada.concepto == "DIAN Actualizado"
        assert credencial_actualizada.obtener_clave() == "ClaveOriginal123"

    def test_form_valido_editar_cambiando_clave(self, cliente):
        """Formulario válido al editar y cambiar la contraseña."""
        credencial = Credencial.objects.create(
            cliente=cliente,
            concepto="DIAN",
            usuario_acceso="usuario@dian.gov.co",
            clave_cifrada="",
        )
        credencial.establecer_clave("ClaveOriginal123")
        credencial.save()

        form = CredencialForm(
            instance=credencial,
            data={
                "concepto": "DIAN",
                "usuario_acceso": "usuario@dian.gov.co",
                "clave": "NuevaClave456!",
            },
        )
        assert form.is_valid(), form.errors
        credencial_actualizada = form.save()
        assert credencial_actualizada.obtener_clave() == "NuevaClave456!"

    def test_form_invalido_sin_clave_crear(self, cliente):
        """Formulario inválido si no se proporciona clave al crear."""
        form = CredencialForm(
            data={
                "concepto": "DIAN",
                "usuario_acceso": "usuario@dian.gov.co",
                "clave": "",
            }
        )
        assert not form.is_valid()
        assert "clave" in form.errors

    def test_form_invalido_sin_concepto(self, cliente):
        """Formulario inválido sin concepto."""
        form = CredencialForm(
            data={
                "concepto": "",
                "usuario_acceso": "usuario@dian.gov.co",
                "clave": "MiClave123!",
            }
        )
        assert not form.is_valid()
        assert "concepto" in form.errors


class TestCredencialServicios:
    """Pruebas de las funciones de servicio para credenciales."""

    def test_guardar_credencial(self, cliente, usuario_administrador):
        """guardar_credencial crea la credencial correctamente."""
        form = CredencialForm(
            data={
                "concepto": "DIAN",
                "usuario_acceso": "usuario@dian.gov.co",
                "clave": "MiClaveSegura123!",
            }
        )
        assert form.is_valid()
        credencial = guardar_credencial(form, cliente, usuario_administrador)
        assert credencial.pk is not None
        assert credencial.cliente == cliente
        assert credencial.concepto == "DIAN"
        assert credencial.obtener_clave() == "MiClaveSegura123!"

    def test_eliminar_credencial(self, cliente):
        """eliminar_credencial elimina la credencial."""
        credencial = Credencial.objects.create(
            cliente=cliente,
            concepto="DIAN",
            usuario_acceso="usuario@dian.gov.co",
            clave_cifrada="",
        )
        credencial.establecer_clave("Clave123")
        credencial.save()
        pk = credencial.pk

        resultado = eliminar_credencial(credencial)
        assert resultado is True
        assert not Credencial.objects.filter(pk=pk).exists()


class TestCredencialVistas:
    """Pruebas de las vistas de credenciales (permisos y CRUD)."""

    def test_crear_credencial_admin(self, client, cliente, usuario_administrador):
        """Admin puede crear credencial."""
        client.force_login(usuario_administrador)
        url = reverse("clientes:credencial_crear", kwargs={"pk_cliente": cliente.pk})
        response = client.post(
            url,
            {
                "concepto": "DIAN",
                "usuario_acceso": "admin@dian.gov.co",
                "clave": "AdminClave123!",
            },
        )
        assert response.status_code == 302
        assert Credencial.objects.filter(cliente=cliente, concepto="DIAN").exists()

    def test_crear_credencial_senior(self, client, cliente, usuario_senior):
        """Contador Senior puede crear credencial."""
        client.force_login(usuario_senior)
        url = reverse("clientes:credencial_crear", kwargs={"pk_cliente": cliente.pk})
        response = client.post(
            url,
            {
                "concepto": "Hacienda",
                "usuario_acceso": "senior@hacienda.gov.co",
                "clave": "SeniorClave123!",
            },
        )
        assert response.status_code == 302
        assert Credencial.objects.filter(cliente=cliente, concepto="Hacienda").exists()

    def test_crear_credencial_junior_denegado(self, client, cliente, usuario_junior):
        """Contador Junior NO puede crear credencial (403)."""
        client.force_login(usuario_junior)
        url = reverse("clientes:credencial_crear", kwargs={"pk_cliente": cliente.pk})
        response = client.post(
            url,
            {
                "concepto": "DIAN",
                "usuario_acceso": "junior@dian.gov.co",
                "clave": "JuniorClave123!",
            },
        )
        # Debe redirigir o dar 403
        assert response.status_code in (302, 403)
        assert not Credencial.objects.filter(concepto="DIAN").exists()

    def test_editar_credencial_admin(self, client, cliente, usuario_administrador):
        """Admin puede editar credencial."""
        credencial = Credencial.objects.create(
            cliente=cliente,
            concepto="DIAN",
            usuario_acceso="original@dian.gov.co",
            clave_cifrada="",
        )
        credencial.establecer_clave("Original123")
        credencial.save()

        client.force_login(usuario_administrador)
        url = reverse("clientes:credencial_editar", kwargs={"pk_cliente": cliente.pk, "pk": credencial.pk})
        response = client.post(
            url,
            {
                "concepto": "DIAN Actualizado",
                "usuario_acceso": "actualizado@dian.gov.co",
                "clave": "NuevaClave456!",
            },
        )
        assert response.status_code == 302
        credencial.refresh_from_db()
        assert credencial.concepto == "DIAN Actualizado"
        assert credencial.obtener_clave() == "NuevaClave456!"

    def test_editar_credencial_junior_denegado(self, client, cliente, usuario_junior):
        """Contador Junior NO puede editar credencial."""
        credencial = Credencial.objects.create(
            cliente=cliente,
            concepto="DIAN",
            usuario_acceso="original@dian.gov.co",
            clave_cifrada="",
        )
        credencial.establecer_clave("Original123")
        credencial.save()

        client.force_login(usuario_junior)
        url = reverse("clientes:credencial_editar", kwargs={"pk_cliente": cliente.pk, "pk": credencial.pk})
        response = client.post(
            url,
            {
                "concepto": "DIAN Hackeado",
                "usuario_acceso": "hack@dian.gov.co",
                "clave": "HackClave123!",
            },
        )
        assert response.status_code in (302, 403)
        credencial.refresh_from_db()
        assert credencial.concepto == "DIAN"  # No cambió

    def test_eliminar_credencial_admin(self, client, cliente, usuario_administrador):
        """Admin puede eliminar credencial."""
        credencial = Credencial.objects.create(
            cliente=cliente,
            concepto="DIAN",
            usuario_acceso="a@b.c",
            clave_cifrada="",
        )
        credencial.establecer_clave("Clave123")
        credencial.save()
        pk = credencial.pk

        client.force_login(usuario_administrador)
        url = reverse("clientes:credencial_eliminar", kwargs={"pk_cliente": cliente.pk, "pk": pk})
        response = client.post(url)
        assert response.status_code == 302
        assert not Credencial.objects.filter(pk=pk).exists()

    def test_eliminar_credencial_junior_denegado(self, client, cliente, usuario_junior):
        """Contador Junior NO puede eliminar credencial."""
        credencial = Credencial.objects.create(
            cliente=cliente,
            concepto="DIAN",
            usuario_acceso="a@b.c",
            clave_cifrada="",
        )
        credencial.establecer_clave("Clave123")
        credencial.save()
        pk = credencial.pk

        client.force_login(usuario_junior)
        url = reverse("clientes:credencial_eliminar", kwargs={"pk_cliente": cliente.pk, "pk": pk})
        response = client.post(url)
        assert response.status_code in (302, 403)
        assert Credencial.objects.filter(pk=pk).exists()

    def test_reporte_credenciales_admin(self, client, cliente, usuario_administrador):
        """Admin puede ver reporte de credenciales."""
        cred1 = Credencial.objects.create(
            cliente=cliente,
            concepto="DIAN",
            usuario_acceso="user1@dian.gov.co",
            clave_cifrada="",
        )
        cred1.establecer_clave("Clave1")
        cred1.save()

        cred2 = Credencial.objects.create(
            cliente=cliente,
            concepto="Hacienda",
            usuario_acceso="user2@hacienda.gov.co",
            clave_cifrada="",
        )
        cred2.establecer_clave("Clave2")
        cred2.save()

        client.force_login(usuario_administrador)
        url = reverse("clientes:reporte_credenciales", kwargs={"pk_cliente": cliente.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert b"DIAN" in response.content
        assert b"Hacienda" in response.content

    def test_reporte_credenciales_junior_solo_sus_clientes(self, client, usuario_junior, cliente_otro):
        """Junior solo ve reporte de sus clientes asignados."""
        # Cliente asignado al junior
        cliente_propio = Cliente.objects.create(
            nombre_razon_social="Cliente del Junior",
            nit_cedula="900111222",
            tipo_documento=Cliente.NIT,
            tipo_persona=Cliente.JURIDICA,
            regimen_tributario="Régimen ordinario",
            ciudad="Bogotá D.C.",
            municipio_principal="Bogotá D.C.",
            responsable=usuario_junior,
        )

        # Credencial en cliente asignado al junior
        credencial_propia = Credencial.objects.create(
            cliente=cliente_propio,
            concepto="DIAN",
            usuario_acceso="propio@test.com",
            clave_cifrada="",
        )
        credencial_propia.establecer_clave("Clave1")
        credencial_propia.save()

        # Credencial en cliente NO asignado (asignado a senior)
        credencial_ajena = Credencial.objects.create(
            cliente=cliente_otro,
            concepto="DIAN",
            usuario_acceso="ajeno@test.com",
            clave_cifrada="",
        )
        credencial_ajena.establecer_clave("Clave2")
        credencial_ajena.save()

        client.force_login(usuario_junior)
        # Debe poder ver el reporte de su cliente
        url_propio = reverse("clientes:reporte_credenciales", kwargs={"pk_cliente": cliente_propio.pk})
        response = client.get(url_propio)
        assert response.status_code == 200

        # No debe poder ver el reporte de cliente ajeno
        url_ajeno = reverse("clientes:reporte_credenciales", kwargs={"pk_cliente": cliente_otro.pk})
        response = client.get(url_ajeno)
        assert response.status_code in (302, 404)


class TestCredencial90Dias:
    """Pruebas del indicador de 90 días."""

    def test_credencial_antigua_requiere_actualizacion(self, cliente):
        """Credencial con más de 90 días marca requiere_actualizacion."""
        credencial = Credencial.objects.create(
            cliente=cliente,
            concepto="DIAN",
            usuario_acceso="user@test.com",
            clave_cifrada="",
        )
        credencial.establecer_clave("Clave123")
        # Simular 91 días atrás
        Credencial.objects.filter(pk=credencial.pk).update(
            fecha_ultima_actualizacion=timezone.now() - timedelta(days=91)
        )
        credencial.refresh_from_db()
        assert credencial.dias_sin_actualizacion >= 91
        assert credencial.requiere_actualizacion is True

    def test_credencial_reciente_no_requiere_actualizacion(self, cliente):
        """Credencial reciente no marca requiere_actualizacion."""
        credencial = Credencial.objects.create(
            cliente=cliente,
            concepto="DIAN",
            usuario_acceso="user@test.com",
            clave_cifrada="",
        )
        credencial.establecer_clave("Clave123")
        assert credencial.requiere_actualizacion is False

    def test_credencial_exactamente_90_dias(self, cliente):
        """Credencial con exactamente 90 días NO requiere actualización (>90)."""
        credencial = Credencial.objects.create(
            cliente=cliente,
            concepto="DIAN",
            usuario_acceso="user@test.com",
            clave_cifrada="",
        )
        credencial.establecer_clave("Clave123")
        Credencial.objects.filter(pk=credencial.pk).update(
            fecha_ultima_actualizacion=timezone.now() - timedelta(days=90)
        )
        credencial.refresh_from_db()
        assert credencial.dias_sin_actualizacion == 90
        assert credencial.requiere_actualizacion is False  # Es >90, no >=90
