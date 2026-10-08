"""
Guías paso a paso de la sección de ayuda (HU053).

Cada guía explica un proceso completo del sistema (por ejemplo, crear un
cliente) con los nombres de botones y campos tal como aparecen en pantalla.
Son contenido fijo, por eso viven en el código y no en la base de datos.

Una guía solo se muestra a quien puede hacer el proceso: su rol debe estar en
`roles` (vacío = cualquier rol) y debe tener habilitado el módulo (`modulo`
en None = no depende de ningún módulo).

Para agregar una guía: crear su `Guia` en `GUIAS`. Si el proceso cambia en
pantalla (un botón, un campo, un permiso), actualizar aquí su guía.
"""

from dataclasses import dataclass

from .models import Modulo, Rol

TODOS = ()
SOLO_ADMINISTRADOR = (Rol.ADMINISTRADOR,)
ADMINISTRADOR_Y_SENIOR = (Rol.ADMINISTRADOR, Rol.CONTADOR_SENIOR)

# Nombre corto de cada módulo (el mismo del menú lateral) y orden de los grupos.
GRUPO_GENERAL = "Mi cuenta"
NOMBRES_MODULO = {
    Modulo.MOD01_CLIENTES: "Clientes",
    Modulo.MOD02_CALENDARIO: "Calendario",
    Modulo.MOD03_TAREAS: "Tareas",
    Modulo.MOD04_DOCUMENTOS: "Documentos",
    Modulo.MOD05_HALLAZGOS: "Hallazgos",
    Modulo.MOD09_EXPEDIENTE: "Expediente",
    Modulo.MOD06_FINANZAS: "Honorarios",
    Modulo.MOD07_COMUNICACIONES: "Comunicaciones",
    Modulo.MOD10_REPORTES: "Reportes",
    Modulo.MOD08_EQUIPO: "Equipo y roles",
}


@dataclass(frozen=True)
class Paso:
    """Un paso de la guía: qué hacer y, si hace falta, el detalle."""

    titulo: str
    detalle: str = ""


@dataclass(frozen=True)
class Guia:
    """Proceso del sistema explicado paso a paso."""

    slug: str
    titulo: str
    resumen: str
    icono: str
    pasos: tuple
    modulo: str | None = None
    roles: tuple = TODOS
    # Nombre de la ruta (sin argumentos) donde empieza el proceso y texto del botón.
    ruta: str | None = None
    etiqueta_ruta: str = ""
    requisitos: tuple = ()
    notas: tuple = ()
    relacionadas: tuple = ()

    @property
    def grupo(self):
        return NOMBRES_MODULO.get(self.modulo, GRUPO_GENERAL)


GUIAS = (
    # ------------------------------------------------------------------
    # Módulo 1 · Clientes
    # ------------------------------------------------------------------
    Guia(
        slug="crear-cliente",
        titulo="Crear un cliente",
        resumen="Registre un cliente nuevo con sus datos fiscales, servicios y obligaciones tributarias.",
        icono="bi-person-plus",
        modulo=Modulo.MOD01_CLIENTES,
        ruta="clientes:crear",
        etiqueta_ruta="Ir a Nuevo cliente",
        requisitos=(
            "Tenga a la mano el RUT del cliente: de ahí salen el número de documento, "
            "el régimen y las obligaciones.",
        ),
        pasos=(
            Paso(
                "Abra el formulario",
                "En el menú lateral entre a «Clientes» y pulse el botón «Nuevo cliente».",
            ),
            Paso(
                "Diligencie la ficha del cliente",
                "Los campos con asterisco son obligatorios: «Nombre o razón social», «Número de "
                "documento», «Tipo de documento» y «Tipo de persona». El número lleva solo dígitos "
                "(máximo 10), sin puntos ni guiones, y no puede repetirse entre clientes.",
            ),
            Paso(
                "Revise el régimen tributario",
                "Al elegir el tipo de persona el sistema sugiere un régimen (Natural: «No "
                "responsable»; Jurídica: «Régimen ordinario»). Puede elegir otro de la lista o "
                "escribir uno nuevo. Marque «Responsable de IVA» si aplica.",
            ),
            Paso(
                "Complete ubicación y contacto",
                "«Ciudad», «Municipio principal», «Teléfono» y «Correo del cliente». El correo y el "
                "celular son los que se usan después para enviarle las cuentas de cobro.",
            ),
            Paso(
                "Asigne el responsable",
                "En «Responsable asignado» elija quién del equipo atiende al cliente. Si usted es "
                "Contador Junior este campo no aparece: el cliente queda a su nombre.",
            ),
            Paso(
                "Marque los tipos de servicio contable",
                "Seleccione los servicios contratados. Si alguno no está en la lista, escríbalo en "
                "«Otro tipo de servicio».",
            ),
            Paso(
                "Marque las obligaciones tributarias",
                "En «Obligaciones tributarias y vencimientos que le aplican» seleccione los impuestos "
                "y anticipos que presenta el cliente. Con ellas el sistema calcula sus vencimientos.",
            ),
            Paso(
                "Agregue municipios adicionales (si tiene)",
                "Si el cliente declara ICA en varios municipios, pulse «Agregar municipio» por cada uno.",
            ),
            Paso(
                "Guarde",
                "Pulse «Guardar». Se abre la ficha del cliente con todas sus pestañas y, si su rol "
                "tiene el Calendario habilitado, quedan calculados sus vencimientos DIAN.",
            ),
        ),
        notas=(
            "Si no marca obligaciones, el sistema le avisa: sin ellas no puede calcular vencimientos.",
            "Los vencimientos solo se calculan solos para NIT y cédula. Con otros documentos "
            "(cédula de extranjería, pasaporte) se registran a mano.",
            "Un cliente no se elimina: el Administrador o el Contador Senior lo inactivan y conserva "
            "todo su historial.",
        ),
        relacionadas=("importar-clientes", "registrar-credencial", "configurar-honorario"),
    ),
    Guia(
        slug="importar-clientes",
        titulo="Importar clientes desde Excel",
        resumen="Cargue varios clientes de una sola vez con la plantilla de Excel.",
        icono="bi-upload",
        modulo=Modulo.MOD01_CLIENTES,
        roles=ADMINISTRADOR_Y_SENIOR,
        ruta="clientes:importar",
        etiqueta_ruta="Ir a Importar clientes",
        pasos=(
            Paso("Abra la importación", "En «Clientes» pulse «Importar»."),
            Paso(
                "Descargue la plantilla",
                "Pulse «Descargar plantilla». La hoja «Instrucciones» explica qué lleva cada columna.",
            ),
            Paso(
                "Diligencie una fila por cliente",
                "No cambie los títulos de las columnas y guarde el archivo en formato .xlsx.",
            ),
            Paso(
                "Suba el archivo",
                "En «Suba el archivo diligenciado» elija el archivo y pulse «Importar».",
            ),
            Paso(
                "Revise el resultado",
                "El sistema muestra cuántas filas leyó, cuántas importó y, por cada fila con error, "
                "su número y el motivo. Las filas correctas quedan importadas aunque otras fallen.",
            ),
            Paso(
                "Corrija las filas con error",
                "Arregle en el Excel solo las filas rechazadas y vuelva a subirlas.",
            ),
        ),
        notas=(
            "Después de importar, abra cada cliente para marcar sus obligaciones tributarias y "
            "configurar su honorario.",
        ),
        relacionadas=("crear-cliente",),
    ),
    Guia(
        slug="registrar-credencial",
        titulo="Guardar una credencial de un cliente",
        resumen="Registre el usuario y la contraseña de un portal (DIAN, Hacienda, firma electrónica).",
        icono="bi-key",
        modulo=Modulo.MOD01_CLIENTES,
        roles=ADMINISTRADOR_Y_SENIOR,
        ruta="clientes:lista",
        etiqueta_ruta="Ir a Clientes",
        pasos=(
            Paso("Abra la ficha del cliente", "En «Clientes» pulse sobre el cliente."),
            Paso("Entre a la pestaña «Credenciales»", "Verá las credenciales ya registradas."),
            Paso("Pulse «Agregar credencial»", "Se abre el formulario en una ventana."),
            Paso(
                "Diligencie los datos",
                "Indique el portal o entidad (por ejemplo DIAN o Secretaría de Hacienda), el usuario "
                "de acceso y la contraseña.",
            ),
            Paso(
                "Guarde",
                "La contraseña queda cifrada y se muestra enmascarada. Para verla, pulse el botón "
                "del ojo junto a ella.",
            ),
        ),
        notas=(
            "«Ver reporte» muestra todas las credenciales del cliente en pantalla; en «Clientes», "
            "«Reporte de credenciales» las muestra de todos los clientes. No se descargan.",
            "El Contador Junior solo consulta las credenciales de los clientes que tiene a cargo.",
        ),
        relacionadas=("crear-cliente",),
    ),
    # ------------------------------------------------------------------
    # Módulo 2 · Calendario
    # ------------------------------------------------------------------
    Guia(
        slug="calcular-vencimientos",
        titulo="Calcular los vencimientos DIAN",
        resumen="Genere los vencimientos nacionales de un cliente o de todos según el calendario DIAN.",
        icono="bi-arrow-repeat",
        modulo=Modulo.MOD02_CALENDARIO,
        roles=ADMINISTRADOR_Y_SENIOR,
        ruta="calendario:lista",
        etiqueta_ruta="Ir a Vencimientos",
        requisitos=(
            "El cliente debe tener marcadas sus obligaciones tributarias en la ficha.",
            "El calendario DIAN del año debe estar cargado; lo carga el Administrador desde el Calendario.",
        ),
        pasos=(
            Paso(
                "Para todos los clientes",
                "Entre a «Calendario», pulse «Lista» y luego «Calcular vencimientos DIAN». Confirme el "
                "mensaje: se calculan los de todos los clientes activos.",
            ),
            Paso(
                "Para un solo cliente",
                "Abra la ficha del cliente, pestaña «Vencimientos», y pulse «Calcular vencimientos DIAN».",
            ),
            Paso(
                "Revise el resultado",
                "El sistema indica cuántos vencimientos creó y qué obligaciones no encontraron fecha "
                "para el documento del cliente.",
            ),
            Paso(
                "Valide cada vencimiento",
                "Abra el vencimiento, compare la fecha con el calendario oficial y pulse «Validar "
                "vencimiento».",
            ),
        ),
        notas=(
            "Recalcular no duplica vencimientos ni cambia los que ya están validados.",
            "La fecha siempre se puede editar, aunque la haya calculado el sistema.",
        ),
        relacionadas=("registrar-vencimiento", "configurar-alerta", "presentar-vencimiento"),
    ),
    Guia(
        slug="registrar-vencimiento",
        titulo="Registrar un vencimiento manual",
        resumen="Agregue un vencimiento distrital, municipal o especial que el sistema no calcula.",
        icono="bi-calendar2-plus",
        modulo=Modulo.MOD02_CALENDARIO,
        roles=ADMINISTRADOR_Y_SENIOR,
        ruta="calendario:crear_vencimiento",
        etiqueta_ruta="Ir a Nuevo vencimiento",
        pasos=(
            Paso(
                "Abra el formulario",
                "En «Calendario» pulse «Vencimiento», o en la lista de vencimientos «Nuevo "
                "vencimiento». Desde la ficha del cliente («Vencimientos» → «Agregar vencimiento») "
                "el cliente ya viene elegido.",
            ),
            Paso(
                "Elija cliente y obligación",
                "En «Tipo de obligación» elija una de la lista o escriba una nueva (por ejemplo ICA "
                "o Retención de ICA).",
            ),
            Paso(
                "Indique ámbito, municipio y fecha",
                "«Ámbito» (nacional, distrital o municipal), «Municipio» y «Fecha de vencimiento».",
            ),
            Paso(
                "Asigne responsable y estado",
                "Quien queda como «Responsable» recibe las alertas de ese vencimiento.",
            ),
            Paso("Guarde", "Pulse «Registrar vencimiento». Aparece en el calendario y en la lista."),
        ),
        relacionadas=("configurar-alerta", "presentar-vencimiento"),
    ),
    Guia(
        slug="configurar-alerta",
        titulo="Configurar una alerta de vencimiento",
        resumen="Programe un aviso días antes de que venza una obligación.",
        icono="bi-bell",
        modulo=Modulo.MOD02_CALENDARIO,
        roles=ADMINISTRADOR_Y_SENIOR,
        ruta="calendario:lista",
        etiqueta_ruta="Ir a Vencimientos",
        pasos=(
            Paso(
                "Abra el vencimiento",
                "En «Calendario» pulse sobre el vencimiento, o búsquelo en «Lista».",
            ),
            Paso(
                "Vaya a «Alertas configuradas»",
                "Indique los «Días de anticipación» y el «Canal»: Correo, WhatsApp o Notificación interna.",
            ),
            Paso("Pulse «Agregar»", "Puede agregar varias alertas al mismo vencimiento."),
        ),
        notas=(
            "El aviso va al responsable del vencimiento o, si no tiene, al responsable del cliente.",
            "Desde el día del aviso y hasta que se presente, el vencimiento aparece en la campana "
            "de la barra superior.",
            "Por WhatsApp el sistema deja el mensaje listo en la campana: alguien debe pulsar "
            "«Enviar por WhatsApp».",
        ),
        relacionadas=("presentar-vencimiento",),
    ),
    Guia(
        slug="presentar-vencimiento",
        titulo="Marcar un vencimiento como presentado",
        resumen="Actualice el avance de una obligación: Pendiente, En progreso o Presentada.",
        icono="bi-check2-circle",
        modulo=Modulo.MOD02_CALENDARIO,
        ruta="calendario:lista",
        etiqueta_ruta="Ir a Vencimientos",
        pasos=(
            Paso(
                "Abra el vencimiento",
                "Desde el calendario, la lista de vencimientos o la campana de la barra superior.",
            ),
            Paso(
                "Cambie el estado",
                "En «Cambiar estado» elija «En progreso» o «Presentada» y pulse el botón de "
                "confirmación que está al lado.",
            ),
        ),
        notas=(
            "El Contador Junior solo cambia el estado de los vencimientos de sus clientes o de los "
            "que tiene como responsable.",
            "Un vencimiento presentado deja de generar alertas y de contar como vencido en el panel.",
        ),
        relacionadas=("anotar-expediente",),
    ),
    # ------------------------------------------------------------------
    # Módulo 3 · Tareas
    # ------------------------------------------------------------------
    Guia(
        slug="crear-tarea",
        titulo="Crear una tarea",
        resumen="Agregue una tarjeta al tablero Kanban y asígnela a un miembro del equipo.",
        icono="bi-kanban",
        modulo=Modulo.MOD03_TAREAS,
        roles=ADMINISTRADOR_Y_SENIOR,
        ruta="tareas:tablero",
        etiqueta_ruta="Ir al Tablero de tareas",
        pasos=(
            Paso("Abra el tablero", "En el menú lateral entre a «Tareas» y pulse «Nueva tarea»."),
            Paso(
                "Diligencie la tarea",
                "Cliente, título, «Tipo de tarea» (de la lista o uno nuevo), responsable, prioridad y "
                "fecha de vencimiento. En la descripción explique qué se espera.",
            ),
            Paso(
                "Decida si va al calendario",
                "Marque «Mostrar en calendario» para que la fecha de la tarea aparezca también allí; "
                "en ese caso la fecha de vencimiento es obligatoria.",
            ),
            Paso("Guarde", "Pulse «Crear tarea». La tarjeta queda en la columna «Por hacer»."),
        ),
        relacionadas=("avanzar-tarea",),
    ),
    Guia(
        slug="avanzar-tarea",
        titulo="Actualizar el avance de una tarea",
        resumen="Mueva la tarjeta de columna y deje observaciones del trabajo hecho.",
        icono="bi-arrow-left-right",
        modulo=Modulo.MOD03_TAREAS,
        ruta="tareas:tablero",
        etiqueta_ruta="Ir al Tablero de tareas",
        pasos=(
            Paso(
                "Mueva la tarjeta",
                "Arrástrela a la columna que corresponda: «Por hacer», «En progreso», «En revisión» "
                "o «Terminado». En el teléfono, abra la tarjeta y use «Cambiar estado».",
            ),
            Paso(
                "Registre el avance",
                "Abra la tarjeta, escriba en «Registrar avance…» y agregue la observación.",
            ),
            Paso(
                "Consulte el historial",
                "En la misma tarjeta queda cada cambio de estado con quién lo hizo y cuándo.",
            ),
        ),
        notas=(
            "El Contador Junior solo cambia el estado y comenta las tareas asignadas a él.",
            "«Notificaciones» muestra los cambios que otra persona hizo en sus tareas en los últimos 7 días.",
        ),
        relacionadas=("crear-tarea",),
    ),
    # ------------------------------------------------------------------
    # Módulo 4 · Documentos
    # ------------------------------------------------------------------
    Guia(
        slug="generar-documento",
        titulo="Generar un certificado o documento",
        resumen="Cree un certificado en PDF con el membrete del despacho y la firma del contador.",
        icono="bi-file-earmark-plus",
        modulo=Modulo.MOD04_DOCUMENTOS,
        ruta="documentos:generar",
        etiqueta_ruta="Ir a Generar documento",
        requisitos=(
            "El contador que firma debe haber cargado su firma y su tarjeta profesional "
            "(Documentos → «Mi firma»).",
            "Para que salga el membrete, el Administrador lo carga en Documentos → «Datos del despacho».",
        ),
        pasos=(
            Paso("Abra el panel", "En «Documentos» pulse «Generar documento»."),
            Paso(
                "Elija cliente y plantilla",
                "Al elegir la plantilla aparecen debajo los campos propios de ese certificado.",
            ),
            Paso(
                "Complete los datos",
                "«Fecha o período», «Firma a usar», una descripción opcional y los campos de la "
                "plantilla (valores, conceptos, filas).",
            ),
            Paso("Pulse «Previsualizar»", "Revise el texto completo del certificado antes de generarlo."),
            Paso(
                "Confirme",
                "Pulse «Confirmar y generar PDF». El documento queda en el histórico y en la pestaña "
                "«Documentos» del cliente, listo para descargar.",
            ),
        ),
        notas=(
            "El Contador Junior solo genera documentos de los clientes que tiene asignados.",
            "Un documento generado no se edita: si quedó mal, genere uno nuevo. Administrador y "
            "Contador Senior pueden eliminar el anterior.",
        ),
        relacionadas=("mi-perfil",),
    ),
    # ------------------------------------------------------------------
    # Módulo 5 · Hallazgos
    # ------------------------------------------------------------------
    Guia(
        slug="registrar-hallazgo",
        titulo="Registrar y cerrar un hallazgo",
        resumen="Documente lo encontrado en una revisión, adjunte soportes y ciérrelo con su observación.",
        icono="bi-search-heart",
        modulo=Modulo.MOD05_HALLAZGOS,
        ruta="hallazgos:lista",
        etiqueta_ruta="Ir a Hallazgos",
        pasos=(
            Paso("Abra el registro", "En «Hallazgos» pulse «Registrar hallazgo»."),
            Paso(
                "Diligencie el hallazgo",
                "Cliente, «Tipo de hallazgo», inicio y fin del período revisado, responsable, "
                "prioridad y la descripción de lo encontrado.",
            ),
            Paso("Guarde", "El hallazgo queda en estado «Abierto» y aparece en el listado."),
            Paso(
                "Adjunte los soportes",
                "Abra el hallazgo, elija el archivo y pulse «Adjuntar». Se suben de uno en uno.",
            ),
            Paso(
                "Actualice el estado",
                "En el detalle elija el nuevo estado y pulse «Cambiar».",
            ),
            Paso(
                "Ciérrelo",
                "Al pasar a «Cerrado» el sistema exige la «Observación de cierre»: escriba cómo se resolvió.",
            ),
        ),
        notas=(
            "El Contador Junior consulta los hallazgos de todos los clientes, pero solo registra y "
            "gestiona los de sus clientes asignados.",
            "Solo Administrador y Contador Senior eliminan hallazgos.",
        ),
    ),
    # ------------------------------------------------------------------
    # Módulo 9 · Expediente
    # ------------------------------------------------------------------
    Guia(
        slug="anotar-expediente",
        titulo="Agregar una anotación al expediente",
        resumen="Deje constancia de una gestión con el cliente, con sus archivos de soporte.",
        icono="bi-journal-plus",
        modulo=Modulo.MOD09_EXPEDIENTE,
        ruta="expediente:lista",
        etiqueta_ruta="Ir al Expediente",
        pasos=(
            Paso(
                "Abra la anotación",
                "En «Expediente» pulse «Nueva anotación». Desde la ficha del cliente, pestaña "
                "«Expediente», el cliente ya viene elegido.",
            ),
            Paso(
                "Diligencie la anotación",
                "Cliente, «Tipo de anotación» (de la lista o uno nuevo), «Fecha» del hecho y «Contenido».",
            ),
            Paso(
                "Adjunte los soportes",
                "En «Archivos de soporte» puede elegir varios a la vez (PDF, Word, Excel o imagen, "
                "máximo 10 MB cada uno).",
            ),
            Paso("Guarde", "Pulse «Registrar anotación». Queda con su nombre y la fecha y hora exactas."),
        ),
        notas=(
            "La bitácora es inmutable: una anotación no se edita ni se elimina. Si se equivocó, "
            "registre una anotación aclaratoria; el Administrador puede archivar la incorrecta.",
            "Los archivos solo se adjuntan al crear la anotación.",
            "Para ver las archivadas marque el filtro «Incluir archivadas».",
        ),
    ),
    # ------------------------------------------------------------------
    # Módulo 6 · Honorarios
    # ------------------------------------------------------------------
    Guia(
        slug="configurar-honorario",
        titulo="Configurar el honorario de un cliente",
        resumen="Defina cuánto se le cobra al cliente: un monto fijo mensual o un valor por servicio.",
        icono="bi-cash-coin",
        modulo=Modulo.MOD06_FINANZAS,
        roles=SOLO_ADMINISTRADOR,
        ruta="clientes:lista",
        etiqueta_ruta="Ir a Clientes",
        pasos=(
            Paso("Abra la ficha del cliente", "En «Clientes» pulse sobre el cliente."),
            Paso(
                "Entre a la pestaña «Honorarios»",
                "Pulse «Configurar honorario» (o «Editar honorario» si ya tiene uno).",
            ),
            Paso(
                "Elija el tipo de honorario",
                "Con monto fijo, escriba el «Monto fijo mensual». Con «Por servicio», escriba el "
                "monto de cada tipo de servicio del cliente; el total es la suma.",
            ),
            Paso("Guarde", "Pulse «Guardar». Queda registrado quién hizo el cambio y cuándo."),
        ),
        notas=(
            "Cambiar el honorario no modifica las cuentas de cobro ya generadas: cada una conserva su valor.",
        ),
        relacionadas=("generar-cuenta-cobro",),
    ),
    Guia(
        slug="generar-cuenta-cobro",
        titulo="Generar una cuenta de cobro",
        resumen="Cree la cuenta de cobro de un cliente en PDF con el membrete del despacho.",
        icono="bi-receipt",
        modulo=Modulo.MOD06_FINANZAS,
        roles=SOLO_ADMINISTRADOR,
        ruta="finanzas:generar",
        etiqueta_ruta="Ir a Generar cuenta de cobro",
        requisitos=(
            "Tenga creados en «Catálogos» la cuenta bancaria y el método de pago que verá el cliente.",
            "Conviene que el cliente ya tenga su honorario configurado: el valor se propone solo.",
        ),
        pasos=(
            Paso(
                "Abra el formulario",
                "En «Honorarios» pulse «Generar cuenta de cobro», o hágalo desde la pestaña "
                "«Honorarios» de la ficha del cliente.",
            ),
            Paso(
                "Elija cliente y período",
                "«Período facturado» e «Inicio del período». El fin se calcula solo, salvo en el "
                "período personalizado.",
            ),
            Paso(
                "Indique el valor y el pago",
                "«Valor total a cobrar», «Fecha de vencimiento del pago», «Cuenta bancaria para el "
                "pago» y «Método de pago».",
            ),
            Paso(
                "Describa el servicio",
                "Con «Agregar línea» detalle los conceptos. Si pone valor a las líneas, deben sumar "
                "el total. Las flechas cambian el orden.",
            ),
            Paso(
                "Genere",
                "Pulse «Generar cuenta de cobro». Se abre su detalle, desde donde puede descargar "
                "el PDF, enviarla y registrar pagos.",
            ),
        ),
        notas=(
            "Una cuenta con pagos registrados no se puede eliminar.",
            "Con «Cobro automático» el sistema genera y envía sola la cuenta mensual de cada cliente.",
        ),
        relacionadas=("enviar-cuenta-cobro", "registrar-abono"),
    ),
    Guia(
        slug="enviar-cuenta-cobro",
        titulo="Enviar una cuenta de cobro al cliente",
        resumen="Envíe la cuenta o un recordatorio por correo o WhatsApp, ahora o en una fecha programada.",
        icono="bi-send",
        modulo=Modulo.MOD06_FINANZAS,
        roles=SOLO_ADMINISTRADOR,
        ruta="finanzas:historico",
        etiqueta_ruta="Ir a Honorarios",
        requisitos=(
            "El cliente necesita correo registrado para el envío por correo y un celular válido "
            "para WhatsApp.",
        ),
        pasos=(
            Paso("Abra la cuenta", "En «Honorarios» pulse sobre la cuenta de cobro."),
            Paso(
                "Vaya a «Enviar al cliente»",
                "Elija «Qué enviar» (la cuenta o un recordatorio), el «Canal» y «Cuándo» (ahora o "
                "programado, con su fecha y hora).",
            ),
            Paso("Pulse «Enviar / programar»", "El envío queda en el «Historial de envíos» de la cuenta."),
            Paso(
                "Si es por WhatsApp",
                "Pulse «Abrir WhatsApp»: se abre el chat con el mensaje y el enlace al PDF ya "
                "escritos. Solo falta pulsar Enviar en WhatsApp.",
            ),
            Paso(
                "Para varios clientes a la vez",
                "Use «Envío masivo de cuentas»: seleccione las cuentas, elija canal y momento, "
                "revise el listado y confirme.",
            ),
        ),
        notas=(
            "Los WhatsApp programados o masivos esperan en la bandeja de WhatsApp pendientes.",
            "Un correo que falla queda como «Fallido» y se puede reintentar.",
            "Cada envío queda registrado solo en Comunicaciones.",
        ),
        relacionadas=("generar-cuenta-cobro", "registrar-abono"),
    ),
    Guia(
        slug="registrar-abono",
        titulo="Registrar un pago o abono",
        resumen="Registre lo que pagó el cliente; el saldo y el estado de la cuenta se calculan solos.",
        icono="bi-cash-stack",
        modulo=Modulo.MOD06_FINANZAS,
        roles=SOLO_ADMINISTRADOR,
        ruta="finanzas:historico",
        etiqueta_ruta="Ir a Honorarios",
        pasos=(
            Paso("Abra la cuenta", "En «Honorarios» pulse sobre la cuenta de cobro."),
            Paso(
                "Vaya a «Pagos y abonos»",
                "Indique la «Fecha del pago», el «Monto» y el «Medio de pago». Debajo del monto se "
                "muestra el saldo actual.",
            ),
            Paso(
                "Pulse «Registrar pago»",
                "El sistema calcula el saldo resultante y cambia el estado a «Abonada» o «Pagada».",
            ),
        ),
        notas=(
            "Los pagos registrados no se modifican ni se eliminan. Revise fecha y monto antes de guardar.",
            "El monto no puede ser mayor que el saldo de la cuenta.",
            "El PDF de la cuenta se actualiza con los abonos y el saldo pendiente.",
        ),
        relacionadas=("consultar-cartera",),
    ),
    Guia(
        slug="consultar-cartera",
        titulo="Consultar la cartera",
        resumen="Vea cuánto se ha facturado y cobrado a cada cliente, su saldo y los días de mora.",
        icono="bi-wallet2",
        modulo=Modulo.MOD06_FINANZAS,
        ruta="finanzas:cartera",
        etiqueta_ruta="Ir a Cartera",
        pasos=(
            Paso("Abra la cartera", "En «Honorarios» pulse «Cartera»."),
            Paso(
                "Lea el panel",
                "Por cliente: facturado, cobrado, saldo pendiente, cuentas pendientes y mora. En "
                "rojo, los que llevan más de 30 días en mora.",
            ),
            Paso(
                "Incluya los clientes al día",
                "Por defecto solo salen los que deben. Pulse «Incluir clientes al día» para verlos todos.",
            ),
        ),
        notas=(
            "Contador Senior y Contador Junior ven solo la cartera de sus clientes asignados.",
            "Para llevarla a Excel o PDF use el reporte de cartera en «Reportes».",
        ),
        relacionadas=("descargar-reporte",),
    ),
    # ------------------------------------------------------------------
    # Módulo 7 · Comunicaciones
    # ------------------------------------------------------------------
    Guia(
        slug="registrar-comunicacion",
        titulo="Registrar una comunicación con el cliente",
        resumen="Deje constancia de una llamada, una reunión u otro contacto hecho fuera del sistema.",
        icono="bi-telephone-plus",
        modulo=Modulo.MOD07_COMUNICACIONES,
        roles=ADMINISTRADOR_Y_SENIOR,
        ruta="comunicaciones:lista",
        etiqueta_ruta="Ir a Comunicaciones",
        pasos=(
            Paso(
                "Abra el registro",
                "En «Comunicaciones» pulse «Registrar comunicación». Desde la ficha del cliente, "
                "pestaña «Comunicaciones», el cliente ya viene elegido.",
            ),
            Paso(
                "Diligencie el contacto",
                "Cliente, «Canal» (de la lista o uno nuevo), «Fecha y hora» en que ocurrió y el "
                "«Resumen del contenido».",
            ),
            Paso("Guarde", "Pulse «Registrar comunicación». Queda marcada como «Manual»."),
        ),
        notas=(
            "Los correos y WhatsApp enviados desde Contanika se registran solos como «Automática»: "
            "no hay que anotarlos.",
            "Las comunicaciones no se editan ni se eliminan. No se aceptan fechas futuras.",
        ),
    ),
    # ------------------------------------------------------------------
    # Módulo 10 · Reportes
    # ------------------------------------------------------------------
    Guia(
        slug="descargar-reporte",
        titulo="Generar y descargar un reporte",
        resumen="Filtre la información y llévela a Excel o PDF.",
        icono="bi-bar-chart-line",
        modulo=Modulo.MOD10_REPORTES,
        ruta="reportes:inicio",
        etiqueta_ruta="Ir a Reportes",
        pasos=(
            Paso("Elija el reporte", "En «Reportes» pulse la tarjeta del reporte que necesita."),
            Paso(
                "Aplique los filtros",
                "Período, responsable y los propios de cada reporte; luego «Aplicar filtros». La "
                "vista previa muestra hasta 200 filas por sección.",
            ),
            Paso(
                "Descargue",
                "Pulse «Excel» o «PDF». El archivo trae todas las filas, con los filtros aplicados.",
            ),
        ),
        notas=(
            "Contador Senior y Contador Junior ven solo los datos de sus clientes asignados.",
            "Si no ve un reporte, el Administrador no lo tiene habilitado para su rol.",
            "Cada descarga queda registrada: quién, cuándo, en qué formato y con qué filtros.",
        ),
    ),
    # ------------------------------------------------------------------
    # Módulo 8 · Equipo y roles
    # ------------------------------------------------------------------
    Guia(
        slug="crear-usuario",
        titulo="Crear un usuario del equipo",
        resumen="Dé acceso a un nuevo miembro del despacho con su rol y una contraseña temporal.",
        icono="bi-person-gear",
        modulo=Modulo.MOD08_EQUIPO,
        roles=SOLO_ADMINISTRADOR,
        ruta="seguridad:crear_usuario",
        etiqueta_ruta="Ir a Nuevo usuario",
        pasos=(
            Paso(
                "Abra el formulario",
                "En «Equipo y roles» entre a la pestaña «Usuarios» y pulse «Nuevo usuario».",
            ),
            Paso(
                "Diligencie los datos",
                "Nombre, «Correo electrónico» (será su usuario), teléfono y rol. A la derecha se "
                "muestran los módulos que ve ese rol.",
            ),
            Paso(
                "Escriba la «Contraseña temporal»",
                "Debe cumplir las reglas de seguridad que indica el formulario.",
            ),
            Paso(
                "Guarde",
                "Pulse «Crear usuario y enviar acceso». El sistema le envía un correo con su usuario "
                "y la contraseña temporal.",
            ),
            Paso(
                "Pídale que cambie la contraseña",
                "La contraseña temporal la conoce usted: recomiéndele cambiarla en «Mi perfil» al "
                "entrar por primera vez.",
            ),
        ),
        notas=(
            "Si el correo no sale, el usuario queda creado igual y el sistema le avisa: entréguele "
            "la contraseña por otro medio.",
            "Para crear otro Administrador debe marcar la casilla de confirmación.",
            "Un usuario con historial no se elimina: se inactiva.",
        ),
        relacionadas=("modulos-por-rol", "mi-perfil"),
    ),
    Guia(
        slug="modulos-por-rol",
        titulo="Habilitar o inhabilitar módulos y secciones por rol",
        resumen="Decida qué módulos, pestañas, reportes y panel ve cada rol.",
        icono="bi-toggles",
        modulo=Modulo.MOD08_EQUIPO,
        roles=SOLO_ADMINISTRADOR,
        ruta="seguridad:permisos",
        etiqueta_ruta="Ir a Módulos por rol",
        pasos=(
            Paso("Abra la matriz", "En «Equipo y roles» entre a la pestaña «Módulos por rol»."),
            Paso(
                "Active o desactive",
                "Cada interruptor corresponde a un módulo y un rol. La fila «Panel principal» "
                "decide si el rol ve el panel; sin él, entra directo a su primer módulo.",
            ),
            Paso("Guarde", "Pulse «Guardar configuración». El cambio aplica de inmediato."),
        ),
        notas=(
            "Un módulo inhabilitado desaparece del menú, de la ficha del cliente (su pestaña) y del "
            "panel principal (su sección), y tampoco abre por dirección directa. Sus datos no se borran.",
            "El Administrador siempre conserva «Equipo y roles», para no quedar bloqueado.",
            "Cada reporte se habilita aparte con el botón «Reportes por rol» de esa misma pantalla "
            "(o en Reportes → «Visibilidad por rol»).",
        ),
        relacionadas=("crear-usuario",),
    ),
    # ------------------------------------------------------------------
    # Mi cuenta (no depende de ningún módulo)
    # ------------------------------------------------------------------
    Guia(
        slug="mi-perfil",
        titulo="Actualizar mi perfil y cambiar la contraseña",
        resumen="Mantenga al día sus datos, su foto, su firma y su contraseña.",
        icono="bi-person-circle",
        ruta="seguridad:perfil",
        etiqueta_ruta="Ir a Mi perfil",
        pasos=(
            Paso(
                "Abra su perfil",
                "Pulse su nombre en la parte inferior del menú lateral o su foto en la barra superior.",
            ),
            Paso(
                "Actualice sus datos",
                "Nombre, teléfono y «Foto de perfil». Administrador y Contador Senior también cargan "
                "aquí la «Imagen de la firma», la identificación y la tarjeta profesional que salen "
                "en los certificados. Pulse «Guardar cambios».",
            ),
            Paso(
                "Cambie la contraseña",
                "En «Cambiar contraseña» escriba la actual y dos veces la nueva, y pulse «Cambiar "
                "contraseña». La sesión sigue abierta.",
            ),
        ),
        notas=(
            "El correo y el rol solo los cambia el Administrador.",
            "Si olvidó la contraseña, pídale al Administrador una temporal y cámbiela al entrar.",
            "Tras varios intentos fallidos el acceso se bloquea por un tiempo, por seguridad.",
        ),
    ),
)

POR_SLUG = {guia.slug: guia for guia in GUIAS}


def es_visible(guia, usuario):
    """Indica si el usuario puede hacer el proceso de la guía (rol y módulo habilitado)."""
    if guia.roles and usuario.rol.nombre_rol not in guia.roles:
        return False
    return not guia.modulo or usuario.tiene_modulo_habilitado(guia.modulo)


def guias_visibles(usuario):
    """Guías que aplican al usuario, en el orden del catálogo."""
    return [guia for guia in GUIAS if es_visible(guia, usuario)]


def guias_por_grupo(usuario):
    """Guías visibles agrupadas por módulo: lista de `{"nombre": ..., "guias": [...]}`."""
    grupos = {}
    for guia in guias_visibles(usuario):
        grupos.setdefault(guia.grupo, []).append(guia)
    return [{"nombre": nombre, "guias": guias} for nombre, guias in grupos.items()]
