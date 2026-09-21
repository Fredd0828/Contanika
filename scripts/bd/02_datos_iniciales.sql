-- ============================================================================
-- Datos iniciales del sistema Contanika (anexo del entregable 3.1)
-- Catálogos: roles, módulos, reportes, permisos por rol, tipos de servicio,
-- métodos de pago, conceptos facturables, plantillas base y configuración
-- del despacho. No incluye usuarios ni credenciales por seguridad.
-- ============================================================================

--
-- PostgreSQL database dump
--

\restrict DlhcVzAMlHU3rbBKuu48WtybAsVHO7X4Xz3HfXpoocEw34y33mWaOUJpSjGn8im

-- Dumped from database version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: concepto_facturable; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.concepto_facturable VALUES (1, 'Contabilidad mensual', 0.00);
INSERT INTO public.concepto_facturable VALUES (2, 'Nómina', 0.00);
INSERT INTO public.concepto_facturable VALUES (3, 'Declaración de renta', 0.00);
INSERT INTO public.concepto_facturable VALUES (4, 'Declaración de IVA', 0.00);
INSERT INTO public.concepto_facturable VALUES (5, 'Revisoría fiscal', 0.00);


--
-- Data for Name: configuracion_despacho; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.configuracion_despacho VALUES (1, 'Befrec Y Asociados SAS', '', '', 'Bogotá D.C.', '', '', '');


--
-- Data for Name: metodo_pago; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.metodo_pago VALUES (1, 'Transferencia');
INSERT INTO public.metodo_pago VALUES (2, 'Consignación');
INSERT INTO public.metodo_pago VALUES (3, 'Efectivo');
INSERT INTO public.metodo_pago VALUES (4, 'Nequi');
INSERT INTO public.metodo_pago VALUES (5, 'Daviplata');


--
-- Data for Name: modulo; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.modulo VALUES (11, 'Gestión de clientes', 'MOD01');
INSERT INTO public.modulo VALUES (12, 'Calendario', 'MOD02');
INSERT INTO public.modulo VALUES (13, 'Tablero de tareas Kanban', 'MOD03');
INSERT INTO public.modulo VALUES (14, 'Expedición de documentos y certificados', 'MOD04');
INSERT INTO public.modulo VALUES (15, 'Hallazgos y revisiones', 'MOD05');
INSERT INTO public.modulo VALUES (16, 'Honorarios, cartera y cuentas de cobro', 'MOD06');
INSERT INTO public.modulo VALUES (17, 'Comunicaciones integradas', 'MOD07');
INSERT INTO public.modulo VALUES (18, 'Gestión de equipo y roles', 'MOD08');
INSERT INTO public.modulo VALUES (19, 'Expediente y bitácora por cliente', 'MOD09');
INSERT INTO public.modulo VALUES (20, 'Reportes y análisis', 'MOD10');


--
-- Data for Name: reporte; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.reporte VALUES (3, 'Clientes', 'Gestión de clientes');
INSERT INTO public.reporte VALUES (4, 'Vencimientos tributarios', 'Calendario');
INSERT INTO public.reporte VALUES (5, 'Cartera', 'Honorarios y cartera');
INSERT INTO public.reporte VALUES (6, 'Cuentas de cobro', 'Honorarios y cartera');
INSERT INTO public.reporte VALUES (7, 'Tareas del Kanban', 'Tablero Kanban');
INSERT INTO public.reporte VALUES (8, 'Ingresos mensuales del despacho', 'Honorarios y cartera');


--
-- Data for Name: rol; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.rol VALUES (4, 'Administrador');
INSERT INTO public.rol VALUES (5, 'Contador Senior');
INSERT INTO public.rol VALUES (6, 'Contador Junior');


--
-- Data for Name: permiso_reporte_rol; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.permiso_reporte_rol VALUES (1, true, 3, 4);
INSERT INTO public.permiso_reporte_rol VALUES (2, true, 4, 4);
INSERT INTO public.permiso_reporte_rol VALUES (3, true, 5, 4);
INSERT INTO public.permiso_reporte_rol VALUES (4, true, 6, 4);
INSERT INTO public.permiso_reporte_rol VALUES (5, true, 7, 4);
INSERT INTO public.permiso_reporte_rol VALUES (6, true, 8, 4);
INSERT INTO public.permiso_reporte_rol VALUES (7, true, 3, 5);
INSERT INTO public.permiso_reporte_rol VALUES (8, true, 4, 5);
INSERT INTO public.permiso_reporte_rol VALUES (9, true, 5, 5);
INSERT INTO public.permiso_reporte_rol VALUES (10, true, 6, 5);
INSERT INTO public.permiso_reporte_rol VALUES (11, true, 7, 5);
INSERT INTO public.permiso_reporte_rol VALUES (12, true, 8, 5);
INSERT INTO public.permiso_reporte_rol VALUES (13, true, 3, 6);
INSERT INTO public.permiso_reporte_rol VALUES (14, true, 4, 6);
INSERT INTO public.permiso_reporte_rol VALUES (15, true, 5, 6);
INSERT INTO public.permiso_reporte_rol VALUES (16, true, 6, 6);
INSERT INTO public.permiso_reporte_rol VALUES (17, true, 7, 6);
INSERT INTO public.permiso_reporte_rol VALUES (18, true, 8, 6);


--
-- Data for Name: permiso_rol_modulo; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.permiso_rol_modulo VALUES (1, true, 11, 4);
INSERT INTO public.permiso_rol_modulo VALUES (2, true, 12, 4);
INSERT INTO public.permiso_rol_modulo VALUES (3, true, 13, 4);
INSERT INTO public.permiso_rol_modulo VALUES (4, true, 14, 4);
INSERT INTO public.permiso_rol_modulo VALUES (5, true, 15, 4);
INSERT INTO public.permiso_rol_modulo VALUES (6, true, 16, 4);
INSERT INTO public.permiso_rol_modulo VALUES (7, true, 17, 4);
INSERT INTO public.permiso_rol_modulo VALUES (8, true, 18, 4);
INSERT INTO public.permiso_rol_modulo VALUES (9, true, 19, 4);
INSERT INTO public.permiso_rol_modulo VALUES (10, true, 20, 4);
INSERT INTO public.permiso_rol_modulo VALUES (11, true, 11, 5);
INSERT INTO public.permiso_rol_modulo VALUES (12, true, 12, 5);
INSERT INTO public.permiso_rol_modulo VALUES (13, true, 13, 5);
INSERT INTO public.permiso_rol_modulo VALUES (14, true, 14, 5);
INSERT INTO public.permiso_rol_modulo VALUES (15, true, 15, 5);
INSERT INTO public.permiso_rol_modulo VALUES (16, true, 16, 5);
INSERT INTO public.permiso_rol_modulo VALUES (17, true, 17, 5);
INSERT INTO public.permiso_rol_modulo VALUES (18, true, 18, 5);
INSERT INTO public.permiso_rol_modulo VALUES (19, true, 19, 5);
INSERT INTO public.permiso_rol_modulo VALUES (20, true, 20, 5);
INSERT INTO public.permiso_rol_modulo VALUES (21, true, 11, 6);
INSERT INTO public.permiso_rol_modulo VALUES (22, true, 12, 6);
INSERT INTO public.permiso_rol_modulo VALUES (23, true, 13, 6);
INSERT INTO public.permiso_rol_modulo VALUES (24, true, 14, 6);
INSERT INTO public.permiso_rol_modulo VALUES (25, true, 15, 6);
INSERT INTO public.permiso_rol_modulo VALUES (26, true, 16, 6);
INSERT INTO public.permiso_rol_modulo VALUES (27, true, 17, 6);
INSERT INTO public.permiso_rol_modulo VALUES (28, true, 18, 6);
INSERT INTO public.permiso_rol_modulo VALUES (29, true, 19, 6);
INSERT INTO public.permiso_rol_modulo VALUES (30, true, 20, 6);


--
-- Data for Name: plantilla; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.plantilla VALUES (1, 'Certificación de ingresos para independientes', '', 'Certificación de ingresos para independientes');
INSERT INTO public.plantilla VALUES (2, 'Certificado de ingresos y retenciones (Art. 378 ET)', '', 'Certificado de ingresos y retenciones (Art. 378 ET)');
INSERT INTO public.plantilla VALUES (3, 'Certificado de composición accionaria', '', 'Certificado de composición accionaria');
INSERT INTO public.plantilla VALUES (4, 'Certificado de patrimonio', '', 'Certificado de patrimonio');
INSERT INTO public.plantilla VALUES (5, 'Certificado de dependiente económico', '', 'Certificado de dependiente económico');
INSERT INTO public.plantilla VALUES (6, 'Certificación de no obligación a declarar renta', '', 'Certificación de no obligación a declarar renta');


--
-- Data for Name: tipo_servicio; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.tipo_servicio VALUES (1, 'Declaración de renta');
INSERT INTO public.tipo_servicio VALUES (2, 'Declaración de IVA');
INSERT INTO public.tipo_servicio VALUES (3, 'Retención en la fuente');
INSERT INTO public.tipo_servicio VALUES (4, 'Contabilidad mensual');
INSERT INTO public.tipo_servicio VALUES (5, 'Nómina');
INSERT INTO public.tipo_servicio VALUES (6, 'Información exógena');
INSERT INTO public.tipo_servicio VALUES (7, 'Medios magnéticos');
INSERT INTO public.tipo_servicio VALUES (8, 'Industria y comercio (ICA)');


--
-- Name: concepto_facturable_id_concepto_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.concepto_facturable_id_concepto_seq', 5, true);


--
-- Name: configuracion_despacho_id_configuracion_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.configuracion_despacho_id_configuracion_seq', 1, false);


--
-- Name: metodo_pago_id_metodo_pago_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.metodo_pago_id_metodo_pago_seq', 5, true);


--
-- Name: modulo_id_modulo_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.modulo_id_modulo_seq', 20, true);


--
-- Name: permiso_reporte_rol_id_permiso_reporte_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.permiso_reporte_rol_id_permiso_reporte_seq', 18, true);


--
-- Name: permiso_rol_modulo_id_permiso_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.permiso_rol_modulo_id_permiso_seq', 30, true);


--
-- Name: plantilla_id_plantilla_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.plantilla_id_plantilla_seq', 6, true);


--
-- Name: reporte_id_reporte_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.reporte_id_reporte_seq', 8, true);


--
-- Name: rol_id_rol_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.rol_id_rol_seq', 6, true);


--
-- Name: tipo_servicio_id_tipo_servicio_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tipo_servicio_id_tipo_servicio_seq', 8, true);


--
-- PostgreSQL database dump complete
--

\unrestrict DlhcVzAMlHU3rbBKuu48WtybAsVHO7X4Xz3HfXpoocEw34y33mWaOUJpSjGn8im

