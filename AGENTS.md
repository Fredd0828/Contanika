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
| Credenciales dev | `paula@befrec.co` / `Contanika2026*` |
| Repositorio | https://github.com/fredd0828/Contanika |
| Rama de trabajo | `feature/modulo-6-finanzas` |
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
- **Filtros desplegables:** todos los listados usan filtros desplegables.
- **Visibilidad por rol:** configurable por el Administrador en el módulo de Equipo.

---

## 5. Seguridad

- Autenticación obligatoria: usar `LoginRequiredMixin` o `@login_required`.
- Control de módulos: usar `ModuloHabilitadoMixin` con `codigo_modulo`.
- Control de roles: usar `RolRequeridoMixin` con `roles_permitidos`.
- Contador Junior:
  - Solo consulta clientes asignados (`cliente.responsable == request.user`).
  - No edita ni elimina credenciales, clientes ni vencimientos.
- CSRF: todos los POST deben incluir `{% csrf_token %}`.
- XSS: escapar contenido en templates; no render HTML desde el usuario sin sanitizar.
- Inyección SQL: usar ORM; nunca concatenar SQL manualmente.
- Credenciales: cifradas con Fernet (`CREDENCIAL_CLAVE_CIFRADO` en `.env`).
- Fuerza bruta: django-axes activo.
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
- Contador Junior solo consulta clientes asignados.

### Módulo 2 — Calendario
- Vencimientos nacionales calculados desde `TablaReferenciaDian`.
- Grupo NIT (se guarda el dígito real, no grupos abstractos):
  - Empresas (NIT): último dígito ("0"-"9").
  - Personas naturales (CC): últimos 2 dígitos de la cédula ("00"-"99").
  - Extranjeros: vencimiento manual (sin cálculo automático).
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

### Módulos 7–10
- Ver `PLAN_TRABAJO.md` y `md/Contanika_Especificaciones_Módulos.md`.

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

Última actualización: 25 de septiembre de 2026 (Módulo 6, bloque 3:
abonos con disparador de PostgreSQL y panel de cartera).
