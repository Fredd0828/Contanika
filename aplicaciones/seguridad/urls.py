"""Rutas de autenticación, panel principal, equipo de trabajo y perfil propio."""

from django.urls import path

from . import vistas

app_name = "seguridad"

urlpatterns = [
    path("", vistas.PanelView.as_view(), name="panel"),
    path("iniciar-sesion/", vistas.IniciarSesionView.as_view(), name="iniciar_sesion"),
    path("cerrar-sesion/", vistas.CerrarSesionView.as_view(), name="cerrar_sesion"),
    path("perfil/", vistas.PerfilView.as_view(), name="perfil"),
    path("ayuda/", vistas.AyudaView.as_view(), name="ayuda"),
    path("perfil/contrasena/", vistas.CambiarClaveView.as_view(), name="cambiar_clave"),
    path("equipo/", vistas.PanelEquipoView.as_view(), name="equipo"),
    path("equipo/usuarios/", vistas.ListaUsuariosView.as_view(), name="usuarios"),
    path("equipo/usuarios/nuevo/", vistas.CrearUsuarioView.as_view(), name="crear_usuario"),
    path("equipo/usuarios/<int:pk>/editar/", vistas.EditarUsuarioView.as_view(), name="editar_usuario"),
    path(
        "equipo/usuarios/<int:pk>/estado/", vistas.CambiarEstadoUsuarioView.as_view(), name="estado_usuario"
    ),
    path("equipo/usuarios/<int:pk>/eliminar/", vistas.EliminarUsuarioView.as_view(), name="eliminar_usuario"),
    path("equipo/permisos/", vistas.PermisosModulosView.as_view(), name="permisos"),
]
