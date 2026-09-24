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
| Rama de trabajo | `feature/modulo-3-tareas` |
| Rama principal | `main` |

**Nota Git:** una rama por módulo, creada a partir de la última rama de trabajo (no siempre desde
`main`, para no perder de la vista lo ya construido mientras el módulo anterior espera aprobación).
`feature/modulo-3-tareas` se creó a partir de `feature/modulo-2-calendario` (calendario aún sin
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

### Módulos 4–10
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

Última actualización: 23 de septiembre de 2026 (Módulo 3, bloque 1: tablero
Kanban navegable).
