"""
Utilidades de formularios compartidas por los módulos del sistema.

Estas clases base agregan automáticamente las clases de Bootstrap 5 a los
campos, para que las plantillas no tengan que repetir esa configuración.
"""

from django import forms


class MixinEstilosBootstrap:
    """Asigna las clases de Bootstrap 5 a cada campo del formulario."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            widget = campo.widget
            if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")


class FormularioBase(MixinEstilosBootstrap, forms.Form):
    """Formulario normal con estilos de Bootstrap."""


class ModeloFormularioBase(MixinEstilosBootstrap, forms.ModelForm):
    """Formulario de modelo con estilos de Bootstrap."""


# Archivos de soporte (tabla `adjunto`): hallazgos y anotaciones del expediente.
EXTENSIONES_PERMITIDAS = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg", ".png")
TAMANO_MAXIMO_ADJUNTO = 10 * 1024 * 1024


# Primeros bytes («firma») con los que empieza de verdad cada formato. Cambiarle
# la extensión a un archivo no cambia su firma: así se detecta, por ejemplo, un
# programa renombrado como .pdf (pr01).
_FIRMA_ZIP = (b"PK\x03\x04",)  # .docx y .xlsx son archivos ZIP
_FIRMA_OLE = (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",)  # .doc y .xls antiguos
FIRMAS_POR_EXTENSION = {
    ".pdf": (b"%PDF-",),
    ".docx": _FIRMA_ZIP,
    ".xlsx": _FIRMA_ZIP,
    ".doc": _FIRMA_OLE,
    ".xls": _FIRMA_OLE,
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
}
EXTENSIONES_IMAGEN = (".jpg", ".jpeg", ".png")


def extension_de(nombre):
    """Extensión en minúsculas, con el punto («.pdf»); vacía si no tiene."""
    punto = nombre.rfind(".")
    return nombre[punto:].lower() if punto != -1 else ""


def contenido_coincide_con_extension(archivo):
    """Indica si el archivo empieza con la firma del formato que dice su extensión."""
    firmas = FIRMAS_POR_EXTENSION.get(extension_de(archivo.name))
    if not firmas:
        return False
    posicion = archivo.tell()
    archivo.seek(0)
    inicio = archivo.read(16)
    archivo.seek(posicion)
    return inicio.startswith(firmas)


def validar_archivo_adjunto(archivo):
    """Rechaza formatos no permitidos, contenido que no corresponde y archivos de más de 10 MB."""
    if not archivo.name.lower().endswith(EXTENSIONES_PERMITIDAS):
        raise forms.ValidationError(
            f"«{archivo.name}»: formato no permitido. Use PDF, Word, Excel o una imagen (JPG/PNG)."
        )
    if archivo.size > TAMANO_MAXIMO_ADJUNTO:
        raise forms.ValidationError(f"«{archivo.name}»: el archivo no debe superar los 10 MB.")
    if not contenido_coincide_con_extension(archivo):
        raise forms.ValidationError(
            f"«{archivo.name}»: el contenido no corresponde a un archivo {extension_de(archivo.name)}."
        )
    return archivo


def validar_excel_subido(archivo, megas=5):
    """Archivo de importación: extensión .xlsx, contenido de Excel y tamaño máximo."""
    if extension_de(archivo.name) != ".xlsx":
        raise forms.ValidationError("El archivo debe estar en formato Excel (.xlsx).")
    if archivo.size > megas * 1024 * 1024:
        raise forms.ValidationError(f"El archivo no debe superar los {megas} MB.")
    if not contenido_coincide_con_extension(archivo):
        raise forms.ValidationError("El contenido no corresponde a un archivo de Excel (.xlsx).")
    return archivo


def validar_imagen_subida(archivo, descripcion, tamano_maximo):
    """
    Imagen subida (foto, firma, membrete): solo JPG o PNG y con tamaño máximo.
    `ImageField` ya comprueba con Pillow que sea una imagen real. No se valida
    el archivo que ya estaba guardado (no trae `content_type`).
    """
    if not archivo or not hasattr(archivo, "content_type"):
        return archivo
    if extension_de(archivo.name) not in EXTENSIONES_IMAGEN:
        raise forms.ValidationError(f"La imagen de {descripcion} debe ser JPG o PNG.")
    if archivo.size > tamano_maximo:
        megas = tamano_maximo // (1024 * 1024)
        raise forms.ValidationError(f"La imagen de {descripcion} no debe superar los {megas} MB.")
    return archivo


class EntradaVariosArchivos(forms.ClearableFileInput):
    """Selector de archivos que permite elegir varios a la vez."""

    allow_multiple_selected = True


class CampoVariosArchivos(forms.FileField):
    """
    Campo que recibe una lista de archivos (patrón de la documentación de
    Django para subir varios archivos con un solo input).
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", EntradaVariosArchivos())
        super().__init__(*args, **kwargs)

    def clean(self, datos, inicial=None):
        if isinstance(datos, (list, tuple)):
            return [super(CampoVariosArchivos, self).clean(dato, inicial) for dato in datos]
        if not datos:
            return []
        return [super().clean(datos, inicial)]
