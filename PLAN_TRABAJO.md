# Plan de trabajo — Contanika

**Fase 3 Ejecución + Fase 4 Evaluación · del lunes 21 de septiembre de 2026 al 1 de enero de 2027**

## 1. Punto de partida

| Insumo | Estado |
|---|---|
| Stack cerrado (D1) | Django 5.2 LTS + DRF + PostgreSQL 15 (Supabase) + Bootstrap 5 + HTML/CSS/JS + ReportLab |

> **Actualización de versión (21 sep 2026):** la serie Django 4.2 LTS terminó su soporte
> extendido en abril de 2026 y `pip-audit` detectó 7 vulnerabilidades sin parche para esa
> serie. Con aprobación del aprendiz se migró a **Django 5.2 LTS** (soporte de seguridad
> hasta abril de 2028), conservando el resto del stack. Pendiente actualizar D1 y RQNF002
> en el documento Word: donde dice "Django 4.2 LTS" debe decir "Django 5.2 LTS".
| Alcance | 10 módulos, 3 roles, 33 RQF, 5 RQNF, 53 HU (HU036 anulada), 11 CU |
| Modelo de datos | 36 tablas definidas en el diccionario de datos (numeral 2.5 del documento v11) |
| Reglas transversales | Descargas centralizadas (M10), selects abiertos, fechas editables, filtros desplegables, visibilidad configurable por rol |
| Estándar de código (D6) | Clean code, identificadores y comentarios en español; palabras reservadas/APIs de terceros sin traducir |
| Entregables Fase 3 | 3.1 Código BD · 3.2 Código documentado por capa · 3.3 Mapa de navegación |

Decisiones confirmadas: PostgreSQL local + Supabase en producción; modelos Django como
fuente de verdad con script SQL documentado generado; herramientas completas de calidad;
código en `contanika/codigo/`.

## 2. Arquitectura del código

```
codigo/
├── gestionar.py                  (manage.py)
├── config/                       settings base/local/produccion, urls, wsgi, asgi
├── aplicaciones/
│   ├── comunes/                  (1 tabla: adjunto)
│   ├── seguridad/                (5: rol, usuario, modulo, permiso_rol_modulo, configuracion_despacho)
│   ├── clientes/                 (5: cliente, cliente_municipio, tipo_servicio, cliente_servicio, credencial)
│   ├── calendario/               (5: tabla_referencia_dian, vencimiento, configuracion_alerta, anotacion_calendario, anotacion_calendario_destinatario)
│   ├── tareas/                   (3: tarea, historial_tarea, observacion_tarea)
│   ├── documentos/               (5: plantilla, campo_plantilla, documento, documento_valor, documento_detalle)
│   ├── hallazgos/                (1: hallazgo)
│   ├── expediente/               (1: anotacion)
│   ├── finanzas/                 (7: honorario, concepto_facturable, cuenta_bancaria, metodo_pago, cuenta_cobro, cuenta_cobro_detalle, abono)
│   ├── comunicaciones/           (1: comunicacion)
│   └── reportes/                 (2: reporte, permiso_reporte_rol)
├── plantillas/                   templates Bootstrap 5
├── estaticos/                    css propio, js
├── scripts/calidad.sh            ruff + bandit + pip-audit + pytest + cobertura
└── pruebas/                      pruebas por módulo
```

**Capas por app** (numeral 3.2): `models.py` → `servicios.py` (reglas de negocio) →
`selectores.py` (consultas) → `formularios.py` / `serializadores.py` (AJAX) →
`vistas.py` → `urls.py` → `plantillas/`.

**Decisión T1:** modelo `Usuario` propio sobre `AbstractBaseUser` con `db_table="usuario"`
(reutiliza hash, login y sesiones de Django — RQNF004). El rol vive en la tabla `rol` y los
permisos en `permiso_rol_modulo` y `permiso_reporte_rol` (RQF031). Se agregan tres columnas
estándar de Django (`is_staff`, `is_superuser`, `last_login`) que se documentan como
ampliación del diccionario.

## 3. Estrategia de calidad (transversal)

**Herramientas:** pytest-django, pytest-cov, factory-boy, ruff, bandit, pip-audit,
django-axes, `check --deploy`.

**Definición de Terminado (DoD) — ninguna historia se cierra sin los 9 puntos:**

1. CRUD funcional y navegable, con permisos por rol probados.
2. Migraciones aplicadas y script SQL documentado regenerado.
3. Pruebas unitarias del módulo en verde (modelos, servicios, formularios, vistas).
4. Pruebas de seguridad del módulo.
5. Cobertura ≥ 70 % del módulo (≥ 85 % en servicios críticos: cálculo DIAN, cartera/abonos, permisos, PDF).
6. `ruff` sin errores, `bandit` sin hallazgos medios/altos, `pip-audit` sin vulnerabilidades críticas.
7. `manage.py check` y `check --deploy` sin errores.
8. Código comentado en español según D6.
9. Evidencia guardada para el Word (captura, tabla CRUD del módulo, salida de pruebas).

**Pruebas de seguridad obligatorias por módulo:**

| Riesgo | Prueba automatizada |
|---|---|
| Acceso sin sesión | URLs redirigen a login (parametrizado) |
| Escalada por rol | Rol sin permiso recibe 403; Junior solo estado de sus tareas |
| Módulo inhabilitado | Bloqueo por URL al deshabilitar módulo por rol (RQF031) |
| Acceso a datos ajenos | Junior no accede a clientes no asignados |
| Contraseñas | Nunca en texto plano; hash verificable |
| CSRF / XSS | POST sin token rechazado; `<script>` se escapa |
| Inyección SQL | Payloads en búsqueda incremental vía ORM |
| Credenciales M1 | Enmascaradas; Junior ve pero no edita ni elimina |
| Fuerza bruta | django-axes bloquea intentos repetidos |
| Ley 1581 | Checklist de datos personales y control de acceso |

## 4. Cronograma de ejecución

### Semana 0 — Arranque (21 al 27 de septiembre)

| Día | Trabajo |
|---|---|
| Lun 21 | PostgreSQL local, `git init`, venv, dependencias, estructura, settings base/local/producción, 36 modelos, migraciones, datos iniciales, pruebas base, `calidad.sh`, primer commit |
| Mar 22 | Usuario personalizado, backend de permisos, login/logout (CU001), layout Bootstrap, menú dinámico |
| Mié 23 | Cierre 3.1: script SQL documentado generado; ajustes de modelos; pruebas de permisos |
| Jue 24 | Mapa de navegación v1 y arranque del módulo 1 (si aplica) |
| Vie 25 | Datos iniciales completos, plantillas base, verificación de calidad semanal |
| Sáb 26 – Dom 27 | Buffer, documentación de la semana para 3.1/3.2 |

### Sprints de desarrollo (28 de septiembre → 30 de noviembre)

| Sprint | Fechas | Módulo(s) | HU principales | Entregable clave |
|---|---|---|---|---|
| S1 | 28 sep – 4 oct | M1 Clientes + credenciales | HU001-003, 030-035, 037 | CRUD, filtros, importación Excel, credenciales enmascaradas |
| S2 | 5 – 11 oct | M2 Calendario | HU004-006, 038-040 | Cálculo DIAN por NIT/régimen, vistas día/semana/mes, alertas |
| S3 | 12 – 18 oct | M3 Kanban | HU007-009, 041, 052 | Tablero, historial, notificaciones, vista calendario |
| S4 | 19 – 25 oct | Cierre M1-M3 + M9 Expediente | HU025-027 | Hito del cronograma + bitácora inmutable |
| S5 | 26 oct – 1 nov | M6 Honorarios y cuentas de cobro (A) + M5 Hallazgos | HU013-015, 043, 044-047 | Catálogos, PDF de cuenta de cobro, hallazgos |
| S6 | 2 – 8 nov | M6 (B) + M7 Comunicaciones | HU016-021, 048-049 | Abonos con saldo automático + trigger, cartera, envíos |
| S7 | 9 – 15 nov | M4 Documentos y certificados | HU010-012, 042 | Plantillas dinámicas + seis certificados en PDF |
| S8 | 16 – 22 nov | M8 Equipo y roles + M10 Reportes (A) | HU022-024, 050, 028-029, 051 | Gestión de usuarios, permisos configurables, reportes planos |
| S9 | 23 – 29 nov | M10 Reportes (B) + 3.3 | HU053 | Seis reportes Excel/PDF, dos gráficos, mapa de navegación |
| — | 30 nov | Cierre de desarrollo | — | Suite en verde, script SQL final, documentación 3.1/3.2 |

La guía SENA exige mínimo 3 reportes planos, 2 gráficos y 1 disparador: los seis reportes
de M10 los cubren; el trigger de saldo por abono queda implementado en S6.

### Fase 4 — Pruebas y calidad (1 al 15 de diciembre)

| Bloque | Trabajo |
|---|---|
| 1 – 4 dic | Regresión completa; seguridad integral (matriz rol × módulo × acción); bandit, pip-audit, check --deploy |
| 5 – 8 dic | Matriz CRUD por módulo (evidencia SENA); validación de campos y excepciones; usabilidad |
| 9 – 12 dic | UAT con Paula Andrea y corrección de hallazgos |
| 13 – 15 dic | Congelamiento, último pase de calidad y respaldo de evidencias |

### Fase 5 — Documentación y entrega (16 dic → 1 ene)

Numerales 3.1, 3.2 y 3.3, conclusiones (4, una por objetivo), presentación y sustentación.

> **Desviación de alcance (25 sep 2026):** a pedido del usuario, el Módulo 6 incluye además
> programación de envíos, cobro mensual automático y recordatorios automáticos de pago (no
> estaban en el spec). El M6 se construye en 3 bloques: (1) honorarios, catálogos y cuentas de
> cobro; (2) envíos, recordatorios y programación; (3) abonos con disparador y cartera.
> Tablas nuevas: `honorario_servicio`, `configuracion_cobro`, `envio_programado` (39 en total).
>
> **Módulo 10 (1 oct 2026):** tabla nueva `descarga_reporte` para registrar quién descarga
> cada reporte, cuándo, en qué formato y con qué filtros (HU028-5). Son 40 tablas en total.

## 5. Decisiones técnicas abiertas (con recomendación)

| # | Tema | Recomendación por defecto |
|---|---|---|
| T2 | WhatsApp | **Resuelta (25-sep-2026, M6):** correo por SMTP (variables `CORREO_*`) + WhatsApp por enlace `wa.me` con registro en Comunicaciones; los WhatsApp programados o masivos quedan en una bandeja de pendientes. API Business como mejora futura |
| T3 | Alertas automáticas | **Resuelta para el M6 (25-sep-2026):** comando `procesar_cobros` + cron cada 15 min, probado con fechas simuladas. Las alertas del Calendario (M2) reutilizarán el mismo esquema |
| T4 | API DRF | Solo endpoints AJAX necesarios (Kanban, calendario, búsqueda incremental, notificaciones) |
| T5 | Despliegue | Hosting con soporte Python + BD Supabase en la semana del 7 de diciembre |

## 6. Comandos de trabajo

```bash
source .venv/bin/activate
python gestionar.py makemigrations
python gestionar.py migrate
python gestionar.py cargar_datos_iniciales --correo-admin=correo@dominio.co --clave-admin=...
python gestionar.py runserver
bash scripts/calidad.sh
```
