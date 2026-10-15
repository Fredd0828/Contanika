# AGENTS.md — Contanika

Contexto técnico y convenciones de trabajo para agentes de código que colaboren en el proyecto **Contanika** de Befrec Y Asociados SAS.

---

## 1. Información general

| Campo | Valor |
|---|---|
| Cliente | Befrec Y Asociados SAS |
| Usuaria principal | Paula Andrea Blanco Espinosa |
| Stack | Django 5.2.17 LTS, Django REST Framework, PostgreSQL 16 local / Supabase en producción |
| Frontend | Bootstrap 5 + HTML/CSS/JS propio |
| Reportes | ReportLab (PDF), openpyxl (Excel) |
| Entorno de desarrollo | WSL2 Ubuntu |
| Ruta del proyecto | `/home/fredd/documentos/ubuntu/contanika/codigo/` |
| Servidor local | `.venv/bin/python gestionar.py runserver 127.0.0.1:8000` |
| Calidad | `bash scripts/calidad.sh` |
| Credenciales dev | En `CREDENCIALES_PRUEBA.md` (no se versiona). Nunca escribir contraseñas en archivos del repositorio |
| Repositorio | https://github.com/fredd0828/Contanika |
| Rama de trabajo | `feature/pr01-seguridad` |
| Rama principal | `main` |

**Nota Git:** una rama por módulo, creada a partir de la última rama de trabajo (no siempre desde
`main`, para no perder de la vista lo ya construido mientras el módulo anterior espera aprobación).
`feature/modulo-5-hallazgos` se creó a partir de `feature/modulo-4-documentos` (documentos aún sin
mergear a `main`). El push a GitHub ya funciona sin pedir token manualmente (credenciales
almacenadas por el gestor de credenciales de Git).

---

## 2. Estructura del proyecto

```
codigo/
├── gestionar.py                  # manage.py del proyecto
├── config/                       # settings base/local/produccion, urls, wsgi, asgi
├── aplicaciones/
│   ├── comunes/                  # Adjuntos y utilidades compartidas
│   ├── seguridad/                # Roles, usuarios, módulos, permisos, login, menú
│   ├── clientes/                 # Gestión de clientes, credenciales, importación Excel
│   ├── calendario/               # Calendario tributario, vencimientos, alertas
│   ├── tareas/                   # Tablero Kanban
│   ├── documentos/               # Certificados y documentos
│   ├── hallazgos/                # Hallazgos y revisiones
│   ├── expediente/               # Bitácora por cliente
│   ├── finanzas/                 # Honorarios, cuentas de cobro, abonos
│   ├── comunicaciones/           # Comunicaciones automáticas y manuales
│   └── reportes/                 # Reportes y análisis
├── plantillas/                   # Templates Bootstrap 5
├── estaticos/                    # CSS propio, JS
├── scripts/
│   ├── calidad.sh                # ruff + bandit + pip-audit + pytest + cobertura
│   └── bd/                       # Scripts SQL documentados
├── pruebas/                      # Pruebas por módulo
├── .env / .env.example           # Variables de entorno
├── PLAN_TRABAJO.md               # Cronograma y decisiones técnicas
├── BITACORA.md                   # Registro diario de avance
└── AGENTS.md                     # Este archivo
```

---

## 3. Arquitectura por capas

Cada aplicación sigue el orden:

```
models.py → servicios.py → selectores.py → formularios.py → vistas.py → urls.py → plantillas/
```

- **`models.py`**: definición de tablas, relaciones y restricciones.
- **`servicios.py`**: reglas de negocio, transacciones y cálculos.
- **`selectores.py`**: consultas reutilizables y filtros.
- **`formularios.py`**: validaciones de entrada del usuario.
- **`vistas.py`**: controladores basados en clases o funciones.
- **`urls.py`**: rutas con `app_name`.
- **`plantillas/`**: HTML heredando de `base.html`.

**Regla de oro:** las vistas no escriben directamente en múltiples modelos; delegan en `servicios.py`.

---

## 4. Convenciones de código

- **Idioma:** código, comentarios, nombres de variables, clases y funciones en **español**.
- **Palabras reservadas y APIs de terceros:** no se traducen (ej. `models`, `forms`, `request`, `admin`).
- **Nombres de archivos:** `vistas.py`, `formularios.py`, `selectores.py`, `servicios.py`.
- **Nombres de clases:** `ClienteForm`, `ListaClientesView`, `guardar_cliente`.
- **Estilo:** `ruff` debe pasar sin hallazgos.
- **Selects abiertos:** los campos desplegables permiten escribir valores nuevos cuando aplique.
- **Fechas editables:** ninguna fecha queda bloqueada, aunque el sistema la calcule automáticamente.
- **PDF con la misma hoja (13-oct-2026, pedido por el usuario):** todo PDF
  (reportes, cuentas de cobro, documentos y certificados) se arma con las
  piezas de `aplicaciones/comunes/pdf.py`: `encabezado_documento` (despacho a
  la izquierda, título y datos a la derecha), `estilos_documento`,
  `estilo_tabla`, `cuadro_datos` y `construir_pdf`, que pone la franja
  superior, los márgenes y el pie con los datos del despacho y «Página X de
  Y». Un PDF nuevo no define estilos ni encabezados propios. Los PDF ya
  guardados (documentos y cuentas de cobro) conservan su aspecto anterior
  hasta que se vuelvan a generar.
- **Historial de la tarea:** el detalle muestra solo los últimos 5 movimientos.
- **Filtros desplegables:** todos los listados usan filtros desplegables.
- **Tablas de a 10 (regla del usuario, 13-oct-2026):** ninguna tabla muestra
  más de 10 registros a la vez; lo demás pasa a la página siguiente, como en
  Clientes. Un listado nuevo hereda de `comunes.paginacion.PaginacionMixin`
  (antes de `ListView`) e incluye `comunes/_paginacion.html` (selector de
  10/25/50, números de página y total; `with dentro_de_panel=True` si va
  dentro del panel de la tabla). Las tablas `.tbl` que no salen de un
  `ListView` (reportes, cartera, fichas) las reparte de a 10 el guion de
  `base.html`, sin hacer nada; se saltan las que tienen campos de formulario
  en sus filas y las marcadas con `data-sin-paginar`. Al imprimir sale la
  tabla completa.
- **Responsive:** toda pantalla debe acomodarse a teléfono, tableta y
  escritorio; comprobarlo (360, 768, 1024 y 1440 px) antes de darla por
  terminada.
- **Visibilidad por rol:** configurable por el Administrador en el módulo de Equipo.
- **Colores:** solo los de la paleta (`:root` de `estaticos/css/contanika.css`:
  navy, teal, naranja, crema, marrón, verde y rojo). Bootstrap trae un azul
  propio (`#0d6efd`) que no pertenece a la plataforma: está reemplazado en la
  sección «Armonía con Bootstrap» del CSS mediante las variables `--bs-*`. Al
  usar un componente nuevo de Bootstrap, revisar que no lo traiga de vuelta.
  Para PDF, Excel y gráficos usar `aplicaciones/comunes/paleta.py`, nunca
  colores escritos a mano.

---

## 5. Seguridad

- Autenticación obligatoria: usar `LoginRequiredMixin` o `@login_required`.
- Control de módulos: usar `ModuloHabilitadoMixin` con `codigo_modulo`.
- Control de roles: usar `RolRequeridoMixin` con `roles_permitidos`.
- Contador Junior (reglas vigentes desde el 1-oct-2026, decisión del usuario):
  - **Clientes:** ve todos, crea y edita cualquiera (`ROLES_GESTIONAN`). El cliente
    nuevo queda a su nombre; no reasigna responsable ni cambia el estado (el
    formulario no ofrece esos campos). No inactiva, no importa.
  - **Credenciales:** solo las ve (sin editar ni eliminar) en los clientes a su
    cargo (`cliente.responsable == request.user`); en los demás la pestaña no aparece.
  - **Calendario:** ve todos los vencimientos y las anotaciones visibles para él
    (Equipo, su rol o etiquetadas). No edita ni valida vencimientos, pero marca el
    avance (En progreso/Presentada) de los de sus clientes o los que tiene como
    responsable (`calendario.servicios.puede_actualizar_estado`).
  - **Tareas:** ve el tablero completo, como todo el equipo (7-oct-2026); solo
    cambia el estado y agrega observaciones a las suyas
    (`tareas.selectores.puede_actualizar_tarea`).
  - **Regla del usuario (7-oct-2026):** clientes, vencimientos y tareas los ve
    completos **todo el equipo**, para que la información esté sincronizada. No
    filtrar esas tres consultas por rol ni por cliente asignado; lo que se
    restringe por rol es quién puede modificar.
  - **Hallazgos, documentos, expediente y comunicaciones:** LECTURA de todos los
    clientes (los `*_visibles` no filtran por rol). La ESCRITURA sigue limitada a
    sus clientes asignados con selectores aparte: `hallazgos_gestionables`,
    `clientes_para_generar`, `expediente.clientes_anotables`. En la ficha de un
    cliente ajeno los botones de crear se ocultan con `a_cargo`.
  - **Finanzas y reportes:** solo sus clientes asignados (sin cambios).
  - **Valores iniciales desde el 7-oct-2026 (decisión del usuario):** empieza
    sin panel principal, sin el Módulo 6 y sin los reportes de Cartera, Cuentas
    de cobro e Ingresos (`MODULOS_SIN_JUNIOR`/`REPORTES_SIN_JUNIOR` en
    `cargar_datos_iniciales`, solo al crear la fila). Son valores iniciales:
    el Administrador los cambia cuando quiera.
- **Visibilidad configurable (regla del usuario, 7-oct-2026):** lo que ven
  los roles no administradores **no se fija en el código**; lo activa o
  desactiva el Administrador. Antes de ocultar algo por rol con un `if`,
  hacerlo depender de un interruptor:
  - Módulos y **panel principal**: Equipo y roles → «Módulos por rol»
    (`PermisoRolModulo`). El panel es la fila `Modulo.SEC_PANEL` ("PANEL") del
    catálogo `modulo` (migración `seguridad 0005`, que también crea la fila en
    instalaciones con datos). Sin panel, `PanelView` lleva a
    `menu.ruta_de_inicio` (Calendario, Tareas o la primera entrada del menú).
  - Secciones del panel y **pestañas de la ficha del cliente**: siguen al
    módulo dueño (`clientes.vistas.PESTANAS_POR_MODULO` → `pestanas.<nombre>`
    en la plantilla); con el módulo inhabilitado no aparecen ni se consultan.
  - Reportes: Reportes → «Visibilidad por rol» (`PermisoReporteRol`), enlazado
    desde la matriz de módulos.
  - Una sección nueva que deba poder ocultarse por rol: agregarla como fila
    del catálogo `modulo` (constante `SEC_*`, `OPCIONES_CODIGO`, migración y
    datos iniciales) y consultarla con `tiene_modulo_habilitado`.
- Menú lateral: sección «Soporte» → «Ayuda», para todos los roles. La ayuda
  reparte los módulos en tres columnas (`.ay-grupos`, dos en tableta, una en
  teléfono).
- CSRF: todos los POST deben incluir `{% csrf_token %}`.
- XSS: escapar contenido en templates; no render HTML desde el usuario sin sanitizar.
- Inyección SQL: usar ORM; nunca concatenar SQL manualmente.
- Credenciales: cifradas con Fernet (`CREDENCIAL_CLAVE_CIFRADO` en `.env`).
- Fuerza bruta: django-axes activo.
- **pr01 (endurecimiento, 7-oct-2026)** — detalle en `documentacion/PR01_SEGURIDAD.md`:
  - Cabeceras: `comunes.middleware.CabecerasSeguridadMiddleware` envía la CSP
    (`CSP_DIRECTIVAS` en `settings/base.py`). **Al cargar algo de un dominio
    nuevo (script, estilo, fuente, imagen, destino de un formulario), agregarlo
    a `CSP_DIRECTIVAS`** o el navegador lo bloquea. Todo lo que venga de un CDN
    lleva `integrity` (SRI) y `crossorigin`; al cambiar de versión, recalcular
    la huella (`curl -s URL | openssl dgst -sha384 -binary | openssl base64 -A`).
  - Archivos subidos: no hay ruta estática de `media/`. `comunes.vistas.MediaProtegidaView`
    solo entrega fotos, firmas y membrete a quien corresponde. Un archivo nuevo
    que deba verse por dirección se autoriza ahí; los demás se descargan por
    una vista del módulo que valide rol y cliente.
  - Subidas: validar con `comunes.formularios` (`validar_archivo_adjunto`,
    `validar_excel_subido`, `validar_imagen_subida`), que comprueban extensión,
    tamaño y que el contenido sea del formato que dice la extensión.
  - Rutas públicas (sin sesión): solo la página web de inicio (`/`,
    `seguridad:inicio`), el inicio de sesión, `robots.txt` y el PDF firmado.
    La página de inicio presenta la plataforma y lleva al inicio de sesión;
    no consulta la base de datos ni muestra datos del despacho (su calendario
    es un dibujo de ejemplo). El panel quedó en `/panel/`. Estilos `.pw-*`.
    Es la única página que los buscadores pueden indexar (`robots.txt` y su
    propia cabecera `X-Robots-Tag`); el resto del sistema sigue con «noindex».
    La marca es solo «Contanika»: ni la página web ni el inicio de sesión
    nombran al despacho que usa la plataforma. Una nueva debe heredar de `comunes.vistas.LimitePeticionesMixin` y
    agregarse a `RUTAS_PUBLICAS` del mapa de navegación.
  - Registros en `registros/` (no se versionan): `seguridad.log` y
    `consultas.log` (consultas lentas, `MonitorConsultasMiddleware`).
  - Producción (`settings/produccion.py`) no arranca con secretos de
    desarrollo ni con `BD_USUARIO=postgres`. Scripts de BD para el despliegue:
    `scripts/bd/03_rol_aplicacion.sql` y `04_activar_rls.sql`.
  - Nunca escribir contraseñas ni claves en archivos versionados: hay una
    prueba que lo impide.
- Variables sensibles: solo en `.env`, nunca en el código.

---

## 6. Calidad y pruebas

### Comandos esenciales

```bash
cd /home/fredd/documentos/ubuntu/contanika/codigo
source .venv/bin/activate
python gestionar.py runserver 127.0.0.1:8000
python gestionar.py makemigrations
python gestionar.py migrate
python gestionar.py cargar_datos_iniciales --correo-admin=correo@dominio.co --clave-admin=...
bash scripts/calidad.sh
```

### Definición de Terminado (DoD)

Ninguna funcionalidad se da por terminada sin:

1. CRUD funcional y navegable, con permisos por rol probados.
2. Migraciones aplicadas y script SQL documentado regenerado.
3. Pruebas unitarias del módulo en verde (modelos, servicios, formularios, vistas).
4. Pruebas de seguridad del módulo.
5. Cobertura ≥ 70 % del módulo (≥ 85 % en servicios críticos: cálculo DIAN, cartera/abonos, permisos, PDF).
6. `ruff` sin errores, `bandit` sin hallazgos medios/altos, `pip-audit` sin vulnerabilidades críticas.
7. `python gestionar.py check` y `check --deploy` sin errores.
8. Código comentado en español.
9. Evidencia guardada para el documento Word (captura, tabla CRUD, salida de pruebas).

---

## 7. Datos iniciales

- Usar el management command: `python gestionar.py cargar_datos_iniciales`.
- También existe el script SQL: `scripts/bd/02_datos_iniciales.sql`.
- El command crea roles, módulos, reportes, permisos, catálogos base y un administrador.
- Cada vez que se agreguen datos iniciales nuevos, actualizar tanto el command como el SQL.

---

## 8. Notas por módulo

### Módulo 1 — Clientes
- CRUD completo, filtros, importación Excel, credenciales cifradas.
- Contador Junior: ve todos los clientes y los crea/edita (ver sección 5).
- Reporte de credenciales: por cliente (`reporte_credenciales`) y consolidado de
  todos (`reporte_credenciales_todos`, con filtros por cliente y estado), solo en
  pantalla y sin descarga. El Junior solo ve las de sus clientes a cargo.
- Tablas `obligacion_tributaria` (catálogo, 10 sembradas) y `cliente_obligacion`
  (qué presenta cada cliente): son las 41 y 42; faltaban en el script SQL y ya
  están incluidas.

### Módulo 2 — Calendario
- Vencimientos nacionales calculados desde `TablaReferenciaDian`.
- Grupo NIT (se guarda el dígito real, no grupos abstractos): el grupo depende
  de la **obligación**, no del tipo de documento. `calcular_grupos_dian`
  devuelve el último dígito y los dos últimos del NIT o cédula, y la búsqueda
  en `TablaReferenciaDian` usa el que exista para cada obligación (IVA,
  retención, renta PJ y RST: 1 dígito; renta PN: 2 dígitos "00"-"99"). Así una
  persona natural con NIT o con cédula calcula bien todas sus obligaciones.
  - Documentos que no son NIT/CC o no numéricos (CE, TI, pasaporte, RUT):
    vencimiento manual (sin cálculo automático).
- **Alertas automáticas (HU040):** `configuracion_alerta` ganó `fecha_envio`
  (DATE, migración `calendario 0004`): día en que se envió la alerta; evita
  repetirla mientras el vencimiento no cambie de fecha (si se corre más tarde,
  `fecha_aviso` supera a `fecha_envio` y vuelve a avisar). Una alerta está «en
  curso» desde `fecha_vencimiento - dias_anticipacion` hasta el vencimiento,
  mientras no esté presentado (`selectores.alertas_en_curso`). Va al
  responsable del vencimiento o, si no tiene, al del cliente.
  - Comando `procesar_alertas` (cron, p. ej. cada hora: `0 * * * * cd
    /ruta/codigo && .venv/bin/python gestionar.py procesar_alertas`):
    **Correo** → envía al responsable y registra una `Comunicacion` Automática
    (`modulo_origen="Calendario"`); si falla, no marca y reintenta en la
    próxima corrida. **Notificación interna** → queda registrada. **WhatsApp** →
    no se marca: `wa.me` exige que una persona pulse Enviar (decisión T2).
  - La **campana** de la barra superior (`context_processors.avisos_vencimientos`,
    en todas las páginas) muestra, por cada vencimiento próximo con alerta
    en curso, un aviso con enlace al detalle y, si hay alerta por WhatsApp y el
    responsable tiene celular, el enlace `wa.me`. Se muestra siempre,
    aunque falle el correo (HU040-5).
- Al crear o editar un cliente (M1) se calculan sus vencimientos si el rol
  tiene el M2 habilitado; si no marcó obligaciones, un aviso le pide elegir
  qué impuestos o anticipos presenta. `resumen["sin_coincidencia"]` lista las
  obligaciones con fechas cargadas pero ninguna para ese documento.
- Obligaciones por régimen: simple/simplificado → RST; jurídica ordinaria →
  renta PJ + retención (+ IVA si responsable); natural → renta PN (+ IVA y
  retención si responsable).
- Datos oficiales 2026 en `datos_dian_2026.py` (440 registros); comando
  `cargar_calendario_dian_2026` idempotente.
- Calendario día/semana/mes con grilla renderizada en el servidor (sin JS pesado).
- Vencimientos distritales/municipales manuales; alertas por vencimiento;
  anotaciones con visibilidad configurable.
- Perfil del cliente: panel de vencimientos con cálculo individual y botón de
  registro con cliente preseleccionado (`?cliente=pk`).

### Módulo 3 — Tareas
- Kanban (Por hacer/En progreso/En revisión/Terminado) con historial de
  cambios (`historial_tarea`) y observaciones de avance (`observacion_tarea`).
- Permisos: Administrador y Contador Senior gestionan cualquier tarea; el
  Contador Junior solo cambia el estado y comenta las tareas asignadas a él.
- Campo `mostrar_en_calendario`: sincroniza un `Vencimiento` (Módulo 2) con
  `tarea` asociado; se actualiza o elimina automáticamente al editar la tarea
  (`aplicaciones/tareas/servicios.sincronizar_vencimiento`).
- Notificaciones: no hay tabla `notificacion` en el diccionario de datos
  (decisión de sesión, Módulo 3 bloque 1); se calculan a partir de
  `historial_tarea` (cambios de los últimos 7 días hechos por otra persona),
  sin leído/no leído persistente. Si se requiere en el futuro un badge con
  estado leído/no leído confiable, evaluar agregar una tabla `notificacion`
  (pasaría de 36 a 37 tablas; requeriría actualizar el numeral 2.5 del Word).

### Módulo 4 — Documentos y certificados
- 6 plantillas base sembradas por `cargar_datos_iniciales` (texto predeterminado
  con sintaxis de plantillas de Django + `CampoPlantilla` simples/repetibles);
  el texto solo se fija al crear la plantilla, nunca se pisa en corridas
  posteriores del comando (para no perder ediciones del Administrador).
- `Documento.archivo` (`FileField`) y `Usuario.firma` (`ImageField`) — primer
  uso real de subida de archivos en el proyecto; hasta el Módulo 3 todo campo
  "tipo archivo" (`foto_url`, `firma_url`, `membrete_url`, `Adjunto.archivo_url`)
  era un `URLField` sin mecanismo de subida. `config/urls.py` ahora sirve
  `media/` en `DEBUG` (antes no estaba configurado, no hacía falta hasta ahora).
- Generación en dos pasos (`GenerarDocumentoView` → `ConfirmarDocumentoView`):
  los datos validados del formulario dinámico (campos simples y filas
  repetibles por plantilla) se guardan en `request.session`, no en campos
  ocultos; se re-validan contra las consultas visibles del usuario antes de
  generar el PDF.
- Firma del contador: campo `firma`/`identificacion`/`numero_tarjeta_profesional`
  ya existían en `Usuario` (pensados para este módulo) pero no había forma de
  cargarlos; se agregó una vista mínima "Mi firma" dentro de `documentos`
  (Administrador y Contador Senior) en vez de construir el Módulo 8 completo.
- `ConfiguracionDespacho.membrete_url` → `membrete` (`ImageField`,
  `upload_to="despacho/"`), cargado por el Administrador en la vista "Datos
  del despacho" (`documentos:datos_despacho`). `servicios.encabezado_despacho()`
  arma el encabezado del PDF: la imagen escalada sin deformar al ancho útil
  (alto máximo 3 cm) o, si no hay membrete, nombre y ciudad como texto. El
  Módulo 6 (cuenta de cobro "con membrete") debe reutilizar esta función.
- Séptima plantilla: sin definir en el spec; no se siembra, el Administrador
  la crea desde "Gestión de plantillas" cuando se defina.

### Módulo 5 — Hallazgos y revisiones
- El modelo `Hallazgo` ya existía completo (migrado desde antes de este
  bloque) y coincide exactamente con el spec; no se modificó.
- `comunes.Adjunto.archivo_url` (`URLField` sin uso real, mismo diagnóstico
  del Módulo 4) → `archivo` (`FileField`, `upload_to="adjuntos/hallazgos/%Y/%m/"`).
  `Adjunto` es genérico (`tabla_origen`/`id_origen`, sin FK real); al no tener
  `on_delete` de la base de datos, `eliminar_hallazgo` borra a mano el
  archivo físico y la fila de cada adjunto antes de borrar el hallazgo.
- Permisos: la HU015 dice que el Junior solo consulta, pero el usuario
  confirmó (25-sep-2026) mantener este criterio. Originalmente se decidió con
  el usuario seguir el patrón de
  Documentos/Calendario — Contador Junior gestiona hallazgos solo de sus
  clientes asignados (crea, edita, cambia estado, adjunta), no elimina;
  Administrador y Contador Senior gestionan cualquiera.
- Cambio de estado en un solo formulario (`CambiarEstadoHallazgoForm`), que
  exige observación de cierre únicamente al pasar a "Cerrado" y reutiliza
  `Hallazgo.cerrar()`, ya existente en el modelo.
- Sin patrón de subida múltiple en el proyecto: los adjuntos se suben de uno
  en uno desde el detalle del hallazgo, cada uno con su propio botón de
  descarga/eliminar (en vez de construir un formset de archivos nuevo).
- Reutiliza clases CSS ya existentes para estado y prioridad
  (`.badge-est`/`.kb-prio`) — sin CSS nuevo.
- El filtro de fechas del listado busca por traslape con el período revisado
  (`fecha_fin_periodo >= desde` y `fecha_inicio_periodo <= hasta`).

### Módulo 6 — Honorarios, cartera y cuentas de cobro
- Se construye en 3 bloques: (1) honorarios, catálogos y cuentas de cobro con
  PDF; (2) envíos por correo/WhatsApp, recordatorios y programación (incluye la
  ampliación de alcance: cobro mensual y recordatorios automáticos); (3) abonos
  con disparador PostgreSQL y panel de cartera. El reporte de ingresos (HU048)
  va en el M10.
- Permisos: solo el Administrador configura honorarios, gestiona catálogos y
  genera/elimina cuentas de cobro. Senior y Junior solo consultan, y solo la
  información de sus clientes asignados (`Cliente.responsable`), vía
  `selectores._restringir_a_asignados`.
- Tabla nueva `honorario_servicio` (37 tablas en total, decisión con el
  usuario): monto por tipo de servicio cuando el honorario es "Por servicio"
  (HU044); el `Honorario.monto` pasa a ser la suma. `Honorario` ganó
  `usuario_actualizacion`/`fecha_actualizacion` (HU044, criterio 4).
- `CuentaCobro.archivo_url` → `archivo` (`FileField`); se agregaron
  `fecha_inicio_periodo`/`fecha_fin_periodo` (el fin se calcula con
  `servicios.calcular_fin_periodo` salvo en el período personalizado).
- Líneas de servicio (HU049) con `formset_factory` sin modelo
  (`LineasCobroFormSet`): la vista asigna `formset.valor_total` antes de
  validar, y el formset exige que la suma de valores por línea sea igual al
  total si se indicó alguno. El orden visual se conserva renumerando los
  nombres de los campos con JavaScript al subir/bajar líneas.
- `aplicaciones/comunes/pdf.py::encabezado_despacho` es el encabezado común
  de los PDF (membrete o texto) para Documentos y Cuentas de cobro.
- Montos en pesos: filtro `{{ valor|pesos }}` y función `formato_pesos` en
  `finanzas/templatetags/finanzas_tags.py` (`$ 1.200.000`).
- La ficha del cliente abre la pestaña indicada en el `#hash` de la URL
  (p. ej. `#tab-honorarios`).
- **Bloque 2 (envíos, ampliación de alcance):** canales en `finanzas/envios.py`
  (correo con `EmailMessage` y PDF adjunto; WhatsApp por enlace `wa.me` con el
  texto ya escrito y un enlace público firmado al PDF — `TimestampSigner`,
  30 días, vista `finanzas:pdf_publico` sin sesión). Textos en
  `plantillas/finanzas/mensajes/*.txt` (`{% autoescape off %}`, son texto plano).
- Todo envío pasa por `EnvioProgramado` (incluso el inmediato: se crea con la
  hora actual y se despacha al momento), así el historial de la cuenta es uno
  solo. Estados: Programado → Enviado/Fallido (correo) o Pendiente WhatsApp
  (bandeja; pasa a Enviado cuando el Administrador pulsa «Abrir WhatsApp»,
  por POST con CSRF). Cada envío registra una `comunicaciones.Comunicacion`.
- `servicios.procesar_cobros(ahora)` (comando `procesar_cobros`, cron cada
  15 min, y botón «Ejecutar ahora»): marca vencidas, genera el cobro mensual
  (una vez por cliente y mes), programa recordatorios automáticos y despacha
  los envíos cuya hora llegó. Idempotente; se prueba con `ahora` simulado.
- `ConfiguracionCobro.obtener()` devuelve la única fila (se siembra
  desactivada en `cargar_datos_iniciales`).
- Correo en local: consola de `runserver` mientras `CORREO_HOST` esté vacío
  en `.env`; con SMTP configurado, envía de verdad. `URL_SITIO` (`.env`) es la
  base de los enlaces públicos: en producción debe ser el dominio real.
- Pruebas: el `addopts` del proyecto ya trae `-q`; no agregar otro `-q` o se
  oculta la línea de resumen de pytest.
- **Bloque 3 (abonos y cartera):** el **disparador** de PostgreSQL (migración
  `finanzas 0004`, `RunSQL`) es la autoridad sobre los saldos:
  `trg_abono_calcular_saldo` (BEFORE INSERT, bloquea la cuenta `FOR UPDATE`,
  fija `saldo_anterior`/`saldo_resultante` y rechaza montos ≤ 0 o mayores que
  el saldo), `trg_abono_actualizar_estado` (AFTER INSERT: Pagada / Vencida /
  Abonada) y `trg_abono_inmutable` (BEFORE UPDATE OR DELETE). En Python,
  `servicios.registrar_abono` crea el abono con saldos provisionales, captura
  el `IntegrityError` del disparador y devuelve su mensaje; luego hace
  `refresh_from_db`. No editar ni borrar abonos desde el ORM (el disparador
  lo impide) y no crear abonos con `bulk_create` sin probarlo contra el
  disparador. Las pruebas corren sobre PostgreSQL, así que lo ejercitan.
- Cartera (`selectores.cartera`): por cliente, facturado, cobrado, saldo y
  días de mora de la cuenta más atrasada; rojo a más de
  `DIAS_MORA_CRITICA` (30). Senior y Junior ven solo sus clientes.
- Abonos en tablas: `selectores.con_abonos(consulta)` anota `abonado` y
  `saldo` y precarga los abonos en orden cronológico; fija `order_by` porque
  Django **no aplica `Meta.ordering` en consultas agregadas**. Lo usan el
  histórico, la ficha del cliente y el envío masivo (parciales
  `finanzas/_celdas_abonos.html` y `_fila_abonos.html`, desplegable).
- PDF de la cuenta: `_seccion_abonos_pdf` agrega abonos, total abonado y
  **saldo pendiente por pagar**; `registrar_abono` llama a
  `actualizar_pdf_cuenta_cobro` para rehacer el archivo guardado (el que se
  descarga, se adjunta al correo y abre el enlace público).
- Envío masivo con fecha por cliente: al programar, cada cuenta puede traer
  su campo `fecha_<id>` (`formularios.campo_fecha_cuenta`); sin él usa la
  fecha general. `cleaned_data["fechas"]` = `{id_cuenta: datetime}`. Opción
  `incluir_enviadas=1` para reenviar cuentas ya enviadas.

### Módulo 9 — Expediente y bitácora por cliente
- Rama `feature/modulo-9-expediente`, creada desde `feature/modulo-6-finanzas`.
- **Bitácora inmutable** (decisión del usuario, 1-oct-2026): no hay vistas ni
  rutas para editar o eliminar anotaciones; `Anotacion.delete()` archiva. Solo
  el Administrador archiva/restaura (`expediente:archivar`/`restaurar`). Las
  archivadas se ocultan por defecto; cualquier rol las ve con el filtro
  «Incluir archivadas». El admin de Django deja todo en solo lectura menos
  `archivado`.
- Columna nueva `anotacion.fecha` (DATE, editable, por defecto hoy): fecha del
  evento anotado. `fecha_hora` sigue siendo el registro exacto automático
  (HU025-2). Orden y filtros de rango usan `fecha`. Ampliación del diccionario
  de datos pendiente de reflejar en el Word.
- Permisos: los tres roles consultan, descargan y anotan; el Junior solo en
  sus clientes asignados (`selectores.clientes_visibles`), pero ve las
  anotaciones de todos los usuarios en esos clientes (HU027-5).
- Adjuntos: máximo 5 por anotación (3 para el Junior), solo al crearla. Un
  solo input múltiple con `comunes.formularios.CampoVariosArchivos`; la
  validación de formato y tamaño (`validar_archivo_adjunto`) quedó en
  `comunes` y la reutiliza Hallazgos. `Adjunto.archivo` usa
  `comunes.models.ruta_adjunto`: `adjuntos/hallazgos/…` o
  `adjuntos/anotaciones/…` según `tabla_origen`.
- `selectores.con_adjuntos(anotaciones)` carga los adjuntos de la página en
  una sola consulta (no hay FK real para `prefetch_related`) y los deja en
  `anotacion.lista_adjuntos`.
- Accesos: menú/panel → `expediente:lista` (bitácora general con filtro por
  cliente); ficha del cliente → pestaña «Expediente» (últimas 10) y
  `expediente:cliente`; Kanban → `clientes:detalle#tab-expediente`.
- Tipos de anotación: `Anotacion.TIPOS_SUGERIDOS` (los 9 del spec) más los ya
  usados, en un `datalist` (selección abierta).

### Módulo 7 — Comunicaciones integradas
- Rama `feature/modulo-7-comunicaciones`, creada desde `feature/modulo-9-expediente`.
- **Automática vs. manual** (según el spec): "Automática" = la registra el
  sistema al enviar un correo o WhatsApp (aunque el envío lo dispare una
  persona); "Manual" = contacto registrado a mano (llamada, reunión, otro).
  En el M6 los envíos disparados por el usuario quedaban como "Manual": se
  corrigió `finanzas.envios.registrar_comunicacion` (siempre Automática) y la
  migración `comunicaciones 0002` actualiza los registros anteriores.
- `Comunicacion.canal` es de selección abierta (sin `choices`;
  `CANALES_SUGERIDOS` + los ya usados en un `datalist`). `fecha_hora` pasó de
  `auto_now_add` a `default=timezone.now` para que el registro manual indique
  cuándo fue el contacto (no se aceptan fechas futuras). Sin cambio de
  columnas en la BD.
- Permisos (HU019-HU021): los tres roles consultan; el Junior solo sus
  clientes asignados. Solo Administrador y Senior registran manuales. Nadie
  edita ni elimina (sin rutas; admin de Django en solo lectura).
- Accesos: menú → `comunicaciones:lista` (filtro por cliente, canal, tipo y
  fechas); ficha del cliente → pestaña «Comunicaciones» (últimas 10) y
  `comunicaciones:cliente`. Distinción visual: etiqueta `be-teal`
  «Automática» (con el módulo de origen) y `be-n` «Manual».
- Calendario (alertas por correo) ya registra su `Comunicacion` Automática
  (`modulo_origen="Calendario"`), como hace `finanzas/envios.py`. Documentos no
  envía nada (el spec del M4 no lo pide); si algún día envía, debe registrarla igual.

### Módulo 8 — Gestión de equipo y roles
- Rama `feature/modulo-8-equipo`, creada desde `feature/modulo-7-comunicaciones`.
  Vive en la app `seguridad` (sus tablas ya estaban ahí): `servicios.py`,
  `selectores.py`, `formularios.py` y plantillas en `seguridad/equipo/`.
- **Usuarios** (solo Administrador): crear con contraseña temporal (validada
  con `AUTH_PASSWORD_VALIDATORS`) y correo de bienvenida con usuario y clave
  (`seguridad/correos/acceso.txt`, decisión del usuario 1-oct-2026); editar
  datos, correo, rol y opcionalmente una nueva clave temporal (también se
  envía); activar/inactivar; eliminar **solo sin historial**
  (`servicios.tiene_historial` recorre todas las relaciones inversas de
  `Usuario`); con historial se ofrece inactivar. Si el correo falla, el
  usuario queda creado y se muestra un aviso.
- **Administradores** (`servicios.validar_administradores`): siempre queda al
  menos uno activo; más de uno activo exige la casilla/confirmación
  (`ConfirmacionRequerida`). Nadie se inactiva ni se elimina a sí mismo.
- **Módulos por rol** (HU050): matriz de interruptores sobre
  `PermisoRolModulo` (sin fila = habilitado). El par Administrador × MOD08 es
  fijo (`PERMISOS_FIJOS`) para no bloquearse. Inicio de sesión y perfil no son
  módulos, así que nunca se inhabilitan. Plantilla `403.html` amigable.
- **Menú**: `menu.ROLES_POR_RUTA` restringe además por rol (Equipo y roles
  oculto para el Junior).
- **Panel principal** (`seguridad:panel`, tablero gráfico desde el 2-oct-2026;
  ya no lista los módulos, que están en el menú lateral): `seguridad/panel.py`
  arma una sección por módulo (`seccion_vencimientos`, `seccion_tareas`,
  `seccion_finanzas`, `seccion_hallazgos`, `seccion_clientes`,
  `seccion_equipo`) y `armar_tablero(usuario, hoy)` las reúne con la franja de
  cifras. Cada sección usa el selector de visibilidad de su módulo
  (`vencimientos_visibles`, `tareas_visibles`, `cuentas_cobro_visibles`,
  `hallazgos_visibles`), así el panel muestra lo mismo que el módulo; queda en
  `None` si el rol no tiene el módulo habilitado. Carga del equipo: solo
  Administrador y Senior. Para agregar una sección: su función en `panel.py`,
  la clave en `armar_tablero` y su bloque en `plantillas/seguridad/panel.html`
  (clases `.pp-*` del CSS).
  - Gráficos con Chart.js (vencimientos por semana y facturado/cobrado por
    mes), datos por `json_script` y colores de `comunes/paleta.py`. Pares de
    color verificados para daltonismo: naranja + verde y teal + naranja; **no
    poner teal junto a verde ni naranja junto a rojo** en un mismo gráfico (se
    confunden). Cada gráfico lleva su tabla («Ver los datos en tabla»).
  - Distribución (11-oct-2026, pedida por el usuario): las seis cifras en una
    fila arriba (`.pp-kpis`); en medio Vencimientos y Tareas (`.pp-medio`);
    abajo Finanzas (doble ancho), Hallazgos y Carga del equipo en una misma
    línea (`.pp-abajo`; si no caben las tres, Finanzas arriba y las otras dos
    debajo). Dentro de Vencimientos y Finanzas el gráfico y la lista van
    lado a lado (`.pp-duo`) cuando caben. Si por el rol falta una sección, la
    vecina ocupa su lugar (`:has`/`:only-child`); no dejar huecos.
  - Responsive: todo se decide con `@container`, nunca con el ancho de la
    pantalla: el tablero (`.pp-tablero`, contenedor `tablero`) reparte filas y
    columnas, y cada sección y cada mitad de `.pp-duo` acomoda su interior.
    Así responde igual al plegar el menú lateral. Revisado en 390, 768, 1024,
    1280 y 1440 px, con el menú plegado y desplegado.
  - Colores (11-oct-2026; resumen y encabezados cambiados el 13-oct-2026 a
    pedido del usuario): cada color tiene un solo oficio. **Navy**: banda del
    encabezado de cada sección (`.pp-tablero .ph`), en degradado de navy a
    teal (`--pp-oscuro`, el mismo en todas), con título blanco, ícono en un
    recuadro teal, botones de contorno claro y el principal en blanco. El
    otro degradado es `--pp-teal` (íconos, barras y medidores); los colores
    de estado van siempre planos. **Blanco**: el resumen de arriba
    (`.pp-resumen`) son seis tarjetas blancas sobre el lienzo, sin bloque
    que las envuelva; el estado de cada cifra (`--pp-tono`) va en la franja
    superior de la tarjeta y en el punto junto al detalle, con leyenda
    Vencido / Próximo / Al día. **Teal**: barras, medidores y enlaces.
    **Rojo**: vencido, atrasado o en mora. **Naranja**: por vencer. **Verde**:
    cumplido o al día (barra «Terminado» y avance del tablero). **Marrón**:
    texto de las etiquetas rojas y naranjas (por contraste). En las listas el
    estado va sin fondo: punto de color o ícono y texto oscuro. La prioridad
    Baja va en gris solo dentro del panel (en el Kanban sigue verde: pendiente
    de decidir si se unifica). Versiones descartadas por el usuario, no volver
    a ellas: un tinte distinto por tarjeta con fondos degradados en los
    recuadros («no es armonioso»), encabezados de sección en teal suave
    (se veían azulados), y el resumen sobre un bloque oscuro
    (13-oct-2026: no le agradó).
  - Gráfico de Finanzas: Facturado en `paleta.TEAL_CLARO` y Cobrado en
    `paleta.TEAL` (se distinguen por claridad); el naranja no se usa ahí para
    que no signifique dos cosas. En «Tareas por estado» la barra verde de
    Terminado convive con las teal porque cada barra lleva su nombre al lado.
- **Misma estructura en todos los módulos** (13-oct-2026, pedido por el
  usuario): el `.ph` que abre un `.panel` (`.panel > .ph:first-child`) es en
  toda la plataforma una banda en el degradado oscuro (`--grad-oscuro`), con
  título blanco e ícono en recuadro teal; no hace falta ninguna clase extra.
  Un `.ph` que no es el primer hijo del panel queda como rótulo sencillo.
  Botones: el principal es `.ph-btn` (o `.btn-primary`), en `--grad-teal`, y
  el secundario `.ph-link` (o `.btn-outline-secondary`), de contorno; mismas
  medidas para todos, también los `.btn` de Bootstrap. Sobre la banda se
  invierten solos (principal blanco, secundario de contorno claro). Una
  pantalla nueva usa esta estructura y no define encabezados ni botones
  propios. Los dos degradados están en `:root` (`--grad-oscuro`,
  `--grad-teal`); los colores de estado van siempre planos.
- **Menú lateral en degradado** (13-oct-2026, pedido por el usuario): fondo
  de navy (arriba) a teal (abajo), el mismo de las bandas del panel. Por eso
  el texto de las entradas va en blanco al 78 % y la entrada activa se marca
  con blanco translúcido y borde teal claro (el teal ya no se distingue abajo).
- **Menú lateral plegable** (11-oct-2026): el botón de la barra superior
  (`#btnMenu`) lo reduce en escritorio a una franja de íconos (clase
  `menu-plegado` en `<html>`, que cambia `--ancho-menu`) y lo recuerda en
  `localStorage` (`contanika.menu`); un script en el `<head>` lo aplica antes
  de pintar. En teléfono y tableta sigue siendo un cajón, con velo y cierre
  con Escape. El texto de cada entrada va en `.ni-txt` y lleva `title`.
  Con poca altura el menú se compacta por tramos (`max-height` 800, 680 y
  620 px) para caber sin barra de desplazamiento; si aun así no cabe, la
  barra es delgada, del tono del menú y solo se ve al pasar el cursor. Al
  agregar una entrada al menú, volver a comprobarlo a 1366×657 y 1280×600.
- **Panel de equipo** (HU023, Administrador y Senior, solo consulta): tareas
  activas, % completado de las tareas que vencen en el mes, vencimientos no
  presentados de los próximos 7 días y alerta con más de 10 pendientes. Se
  recarga cada minuto.
- **Perfil propio** (HU024, cualquier usuario, solo `LoginRequiredMixin`):
  nombre, teléfono, foto; firma, identificación y tarjeta profesional solo
  para Administrador y Senior (firmantes del M4). Cambio de clave con
  `PasswordChangeForm` + `update_session_auth_hash`. `Usuario.foto_url` →
  `foto` (`ImageField`, `fotos/`, migración `seguridad 0004` con
  `RenameField`). La vista `documentos:mi_firma` del M4 se conserva.
- Pruebas: `client.login` falla con django-axes (exige `request`); usar
  `force_login` o un POST al formulario de inicio de sesión.

### Módulo 10 — Reportes y análisis (y Ayuda, HU053)
- Rama `feature/modulo-10-reportes`, creada desde `feature/modulo-8-equipo`.
- Arquitectura: `reportes/definiciones.py` tiene una clase por reporte
  (`ReporteClientes`, `ReporteVencimientos`, `ReporteCartera`,
  `ReporteCuentasCobro`, `ReporteTareas`, `ReporteIngresos`; registro en
  `REPORTES`/`POR_SLUG`) con su formulario de filtros
  (`reportes/formularios.py`, base `FiltroBase` con período y responsable).
  Cada una devuelve un `ResultadoReporte` (`reportes/resultados.py`:
  secciones con columnas tipadas texto/pesos/fecha/número/porcentaje, filas
  resaltadas en rojo, resumen, gráfico y notas). La misma estructura se pinta
  en pantalla y se exporta (`reportes/exportadores.py`): Excel con openpyxl
  (números reales con formato, filas rojas, hoja «Gráfico» con `BarChart`
  nativo) y PDF horizontal con ReportLab (membrete, resumen, gráfico de
  barras y tablas).
- Para agregar un reporte: crear su clase en `definiciones.py`, agregarla a
  `REPORTES`, sembrar la fila en `reporte` (`cargar_datos_iniciales`).
- Datos por rol: los reportes de clientes, vencimientos y tareas traen todo el
  despacho para cualquier rol (7-oct-2026, modifica HU029-1 y HU051-4;
  `todo_el_equipo = True` en su formulario de filtros). En cartera y cuentas
  de cobro, Senior y Junior solo sus clientes asignados (`_restringir`).
  Ingresos es siempre el consolidado del despacho (spec), usa
  `_UsuarioConsolidado` para leer la cartera completa.
- Ingresos: facturado = cuentas generadas en el mes; cobrado = abonos
  recibidos en el mes; pendiente/en mora = saldo actual de las cuentas del
  mes según si ya vencieron. Comparativo último mes vs. anterior, promedios
  y top 3 de saldo. Los dos gráficos de la guía SENA: evolución mensual de
  ingresos y deuda por cliente (cartera, top 10).
- Visibilidad por reporte y rol (`reportes:visibilidad`, sobre
  `PermisoReporteRol`; el Administrador ve todo, fijo). Un reporte oculto no
  aparece ni abre por URL (403).
- Descargas: tabla nueva `descarga_reporte` (decisión del usuario 1-oct-2026,
  40 tablas): reporte, usuario, formato, filtros en texto
  (`FiltroBase.resumen_filtros`), fecha. Historial en `reportes:descargas`
  (solo Administrador). En pantalla se muestran 200 filas por sección; la
  descarga trae todas.
- El gráfico web usa Chart.js (jsDelivr) con los datos vía `json_script`
  (escapa nombres de clientes).
- Ayuda (HU053): `seguridad:ayuda`, ícono en la barra superior, guía de los
  10 módulos, preguntas frecuentes y contacto desde `ConfiguracionDespacho`.
  - **Guías paso a paso** (6-oct-2026): catálogo fijo en
    `seguridad/guias.py` (`Guia` y `Paso`, sin tablas). Cada guía declara su
    `modulo` y sus `roles`; `guias.es_visible` la muestra solo a quien puede
    hacer el proceso (otra guía → 403). Vista `seguridad:guia`
    (`/ayuda/guias/<slug>/`), plantilla `seguridad/guia.html`, clases `.ay-*`.
    **Al cambiar un botón, un campo o un permiso de una pantalla, actualizar
    su guía**; al construir un proceso nuevo, agregarle la suya.
- Buscador de la barra superior: formulario GET a `clientes:lista`
  (`busqueda`); `puede_buscar_clientes` sale de `context_processors.menu_lateral`.
- Mapa de navegación (entregable 3.3): `python gestionar.py
  generar_mapa_navegacion` regenera `documentacion/MAPA_NAVEGACION.md` desde las
  rutas (módulo, roles y descripción de cada vista). Volver a correrlo cuando
  se agreguen o cambien rutas. `documentacion/CAMBIOS_WORD.md` lleva lo que
  falta pasar al Word.
- Cron: `bash scripts/instalar_cron.sh` (`--ver`, `--quitar`) programa
  `procesar_cobros` y `procesar_alertas`. No instalarlo sin avisar al usuario:
  con el cobro automático activo genera cuentas de cobro reales.
- El reporte de credenciales sigue en el M1 sin descarga (spec), aunque la
  HU028 lo liste.

---

## 9. Documentación a mantener actualizada

- **`BITACORA.md`**: registrar cada bloque de trabajo con qué se hizo, cómo verificarlo, resultado de pruebas, evidencias y pendientes.
- **`PLAN_TRABAJO.md`**: actualizar si hay desviaciones o decisiones técnicas importantes.
- **`AGENTS.md`**: actualizar cuando cambien convenciones, stack o decisiones arquitectónicas.
- **`scripts/bd/02_datos_iniciales.sql`**: regenerar cuando cambien los datos base.

---

## 10. Comunicación y commits

- No ejecutar `git commit`, `git push`, `git reset`, `git rebase` salvo que el usuario lo pida explícitamente.
- Antes de cualquier mutación de Git, pedir confirmación.
- Mensajes de commit en español, estilo: `feat(modulo): descripción corta`.

---

Última actualización: 7 de octubre de 2026 (Contador Junior sin panel ni
honorarios; Ayuda en el menú lateral).
