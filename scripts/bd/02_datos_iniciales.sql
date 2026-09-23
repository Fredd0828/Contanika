-- ============================================================================
-- Datos iniciales del sistema Contanika (anexo del entregable 3.1)
-- Catálogos: roles, módulos, reportes, permisos por rol, tipos de servicio,
-- métodos de pago, conceptos facturables, plantillas base, configuración
-- del despacho y calendario oficial DIAN 2026. No incluye usuarios ni
-- credenciales por seguridad.
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
-- Data for Name: tabla_referencia_dian; Type: TABLE DATA; Schema: public; Owner: -
-- Calendario oficial DIAN 2026 (obligaciones nacionales por grupo de NIT)
--

INSERT INTO public.tabla_referencia_dian VALUES (1, 'IVA bimestral', '1', '2026-03-10', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (2, 'IVA bimestral', '2', '2026-03-11', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (3, 'IVA bimestral', '3', '2026-03-12', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (4, 'IVA bimestral', '4', '2026-03-13', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (5, 'IVA bimestral', '5', '2026-03-16', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (6, 'IVA bimestral', '6', '2026-03-17', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (7, 'IVA bimestral', '7', '2026-03-18', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (8, 'IVA bimestral', '8', '2026-03-19', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (9, 'IVA bimestral', '9', '2026-03-20', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (10, 'IVA bimestral', '0', '2026-03-24', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (11, 'IVA bimestral', '1', '2026-05-12', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (12, 'IVA bimestral', '2', '2026-05-13', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (13, 'IVA bimestral', '3', '2026-05-14', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (14, 'IVA bimestral', '4', '2026-05-15', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (15, 'IVA bimestral', '5', '2026-05-19', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (16, 'IVA bimestral', '6', '2026-05-20', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (17, 'IVA bimestral', '7', '2026-05-21', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (18, 'IVA bimestral', '8', '2026-05-22', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (19, 'IVA bimestral', '9', '2026-05-25', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (20, 'IVA bimestral', '0', '2026-05-26', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (21, 'IVA bimestral', '1', '2026-07-09', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (22, 'IVA bimestral', '2', '2026-07-10', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (23, 'IVA bimestral', '3', '2026-07-14', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (24, 'IVA bimestral', '4', '2026-07-15', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (25, 'IVA bimestral', '5', '2026-07-16', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (26, 'IVA bimestral', '6', '2026-07-17', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (27, 'IVA bimestral', '7', '2026-07-21', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (28, 'IVA bimestral', '8', '2026-07-22', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (29, 'IVA bimestral', '9', '2026-07-23', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (30, 'IVA bimestral', '0', '2026-07-24', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (31, 'IVA bimestral', '1', '2026-09-09', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (32, 'IVA bimestral', '2', '2026-09-10', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (33, 'IVA bimestral', '3', '2026-09-11', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (34, 'IVA bimestral', '4', '2026-09-14', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (35, 'IVA bimestral', '5', '2026-09-15', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (36, 'IVA bimestral', '6', '2026-09-16', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (37, 'IVA bimestral', '7', '2026-09-17', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (38, 'IVA bimestral', '8', '2026-09-18', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (39, 'IVA bimestral', '9', '2026-09-21', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (40, 'IVA bimestral', '0', '2026-09-22', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (41, 'IVA bimestral', '1', '2026-11-11', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (42, 'IVA bimestral', '2', '2026-11-12', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (43, 'IVA bimestral', '3', '2026-11-13', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (44, 'IVA bimestral', '4', '2026-11-17', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (45, 'IVA bimestral', '5', '2026-11-18', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (46, 'IVA bimestral', '6', '2026-11-19', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (47, 'IVA bimestral', '7', '2026-11-20', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (48, 'IVA bimestral', '8', '2026-11-23', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (49, 'IVA bimestral', '9', '2026-11-24', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (50, 'IVA bimestral', '0', '2026-11-25', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (51, 'IVA bimestral', '1', '2027-01-13', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (52, 'IVA bimestral', '2', '2027-01-14', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (53, 'IVA bimestral', '3', '2027-01-15', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (54, 'IVA bimestral', '4', '2027-01-18', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (55, 'IVA bimestral', '5', '2027-01-19', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (56, 'IVA bimestral', '6', '2027-01-20', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (57, 'IVA bimestral', '7', '2027-01-21', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (58, 'IVA bimestral', '8', '2027-01-22', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (59, 'IVA bimestral', '9', '2027-01-25', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (60, 'IVA bimestral', '0', '2027-01-26', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (61, 'IVA cuatrimestral', '1', '2026-05-12', '2026-C1');
INSERT INTO public.tabla_referencia_dian VALUES (62, 'IVA cuatrimestral', '2', '2026-05-13', '2026-C1');
INSERT INTO public.tabla_referencia_dian VALUES (63, 'IVA cuatrimestral', '3', '2026-05-14', '2026-C1');
INSERT INTO public.tabla_referencia_dian VALUES (64, 'IVA cuatrimestral', '4', '2026-05-15', '2026-C1');
INSERT INTO public.tabla_referencia_dian VALUES (65, 'IVA cuatrimestral', '5', '2026-05-19', '2026-C1');
INSERT INTO public.tabla_referencia_dian VALUES (66, 'IVA cuatrimestral', '6', '2026-05-20', '2026-C1');
INSERT INTO public.tabla_referencia_dian VALUES (67, 'IVA cuatrimestral', '7', '2026-05-21', '2026-C1');
INSERT INTO public.tabla_referencia_dian VALUES (68, 'IVA cuatrimestral', '8', '2026-05-22', '2026-C1');
INSERT INTO public.tabla_referencia_dian VALUES (69, 'IVA cuatrimestral', '9', '2026-05-25', '2026-C1');
INSERT INTO public.tabla_referencia_dian VALUES (70, 'IVA cuatrimestral', '0', '2026-05-26', '2026-C1');
INSERT INTO public.tabla_referencia_dian VALUES (71, 'IVA cuatrimestral', '1', '2026-09-09', '2026-C2');
INSERT INTO public.tabla_referencia_dian VALUES (72, 'IVA cuatrimestral', '2', '2026-09-10', '2026-C2');
INSERT INTO public.tabla_referencia_dian VALUES (73, 'IVA cuatrimestral', '3', '2026-09-11', '2026-C2');
INSERT INTO public.tabla_referencia_dian VALUES (74, 'IVA cuatrimestral', '4', '2026-09-14', '2026-C2');
INSERT INTO public.tabla_referencia_dian VALUES (75, 'IVA cuatrimestral', '5', '2026-09-15', '2026-C2');
INSERT INTO public.tabla_referencia_dian VALUES (76, 'IVA cuatrimestral', '6', '2026-09-16', '2026-C2');
INSERT INTO public.tabla_referencia_dian VALUES (77, 'IVA cuatrimestral', '7', '2026-09-17', '2026-C2');
INSERT INTO public.tabla_referencia_dian VALUES (78, 'IVA cuatrimestral', '8', '2026-09-18', '2026-C2');
INSERT INTO public.tabla_referencia_dian VALUES (79, 'IVA cuatrimestral', '9', '2026-09-21', '2026-C2');
INSERT INTO public.tabla_referencia_dian VALUES (80, 'IVA cuatrimestral', '0', '2026-09-22', '2026-C2');
INSERT INTO public.tabla_referencia_dian VALUES (81, 'IVA cuatrimestral', '1', '2027-01-13', '2026-C3');
INSERT INTO public.tabla_referencia_dian VALUES (82, 'IVA cuatrimestral', '2', '2027-01-14', '2026-C3');
INSERT INTO public.tabla_referencia_dian VALUES (83, 'IVA cuatrimestral', '3', '2027-01-15', '2026-C3');
INSERT INTO public.tabla_referencia_dian VALUES (84, 'IVA cuatrimestral', '4', '2027-01-18', '2026-C3');
INSERT INTO public.tabla_referencia_dian VALUES (85, 'IVA cuatrimestral', '5', '2027-01-19', '2026-C3');
INSERT INTO public.tabla_referencia_dian VALUES (86, 'IVA cuatrimestral', '6', '2027-01-20', '2026-C3');
INSERT INTO public.tabla_referencia_dian VALUES (87, 'IVA cuatrimestral', '7', '2027-01-21', '2026-C3');
INSERT INTO public.tabla_referencia_dian VALUES (88, 'IVA cuatrimestral', '8', '2027-01-22', '2026-C3');
INSERT INTO public.tabla_referencia_dian VALUES (89, 'IVA cuatrimestral', '9', '2027-01-25', '2026-C3');
INSERT INTO public.tabla_referencia_dian VALUES (90, 'IVA cuatrimestral', '0', '2027-01-26', '2026-C3');
INSERT INTO public.tabla_referencia_dian VALUES (91, 'Retención en la fuente', '1', '2026-02-10', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (92, 'Retención en la fuente', '2', '2026-02-11', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (93, 'Retención en la fuente', '3', '2026-02-12', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (94, 'Retención en la fuente', '4', '2026-02-13', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (95, 'Retención en la fuente', '5', '2026-02-16', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (96, 'Retención en la fuente', '6', '2026-02-17', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (97, 'Retención en la fuente', '7', '2026-02-18', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (98, 'Retención en la fuente', '8', '2026-02-19', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (99, 'Retención en la fuente', '9', '2026-02-20', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (100, 'Retención en la fuente', '0', '2026-02-23', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (101, 'Retención en la fuente', '1', '2026-03-10', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (102, 'Retención en la fuente', '2', '2026-03-11', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (103, 'Retención en la fuente', '3', '2026-03-12', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (104, 'Retención en la fuente', '4', '2026-03-13', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (105, 'Retención en la fuente', '5', '2026-03-16', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (106, 'Retención en la fuente', '6', '2026-03-17', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (107, 'Retención en la fuente', '7', '2026-03-18', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (108, 'Retención en la fuente', '8', '2026-03-19', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (109, 'Retención en la fuente', '9', '2026-03-20', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (110, 'Retención en la fuente', '0', '2026-03-24', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (111, 'Retención en la fuente', '1', '2026-04-13', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (112, 'Retención en la fuente', '2', '2026-04-14', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (113, 'Retención en la fuente', '3', '2026-04-15', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (114, 'Retención en la fuente', '4', '2026-04-16', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (115, 'Retención en la fuente', '5', '2026-04-20', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (116, 'Retención en la fuente', '6', '2026-04-21', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (117, 'Retención en la fuente', '7', '2026-04-22', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (118, 'Retención en la fuente', '8', '2026-04-23', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (119, 'Retención en la fuente', '9', '2026-04-24', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (120, 'Retención en la fuente', '0', '2026-04-27', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (121, 'Retención en la fuente', '1', '2026-05-12', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (122, 'Retención en la fuente', '2', '2026-05-13', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (123, 'Retención en la fuente', '3', '2026-05-14', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (124, 'Retención en la fuente', '4', '2026-05-15', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (125, 'Retención en la fuente', '5', '2026-05-19', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (126, 'Retención en la fuente', '6', '2026-05-20', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (127, 'Retención en la fuente', '7', '2026-05-21', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (128, 'Retención en la fuente', '8', '2026-05-22', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (129, 'Retención en la fuente', '9', '2026-05-25', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (130, 'Retención en la fuente', '0', '2026-05-26', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (131, 'Retención en la fuente', '1', '2026-06-10', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (132, 'Retención en la fuente', '2', '2026-06-11', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (133, 'Retención en la fuente', '3', '2026-06-12', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (134, 'Retención en la fuente', '4', '2026-06-16', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (135, 'Retención en la fuente', '5', '2026-06-17', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (136, 'Retención en la fuente', '6', '2026-06-18', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (137, 'Retención en la fuente', '7', '2026-06-19', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (138, 'Retención en la fuente', '8', '2026-06-22', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (139, 'Retención en la fuente', '9', '2026-06-23', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (140, 'Retención en la fuente', '0', '2026-06-24', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (141, 'Retención en la fuente', '1', '2026-07-09', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (142, 'Retención en la fuente', '2', '2026-07-10', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (143, 'Retención en la fuente', '3', '2026-07-14', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (144, 'Retención en la fuente', '4', '2026-07-15', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (145, 'Retención en la fuente', '5', '2026-07-16', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (146, 'Retención en la fuente', '6', '2026-07-17', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (147, 'Retención en la fuente', '7', '2026-07-21', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (148, 'Retención en la fuente', '8', '2026-07-22', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (149, 'Retención en la fuente', '9', '2026-07-23', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (150, 'Retención en la fuente', '0', '2026-07-24', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (151, 'Retención en la fuente', '1', '2026-08-12', '2026-07');
INSERT INTO public.tabla_referencia_dian VALUES (152, 'Retención en la fuente', '2', '2026-08-13', '2026-07');
INSERT INTO public.tabla_referencia_dian VALUES (153, 'Retención en la fuente', '3', '2026-08-14', '2026-07');
INSERT INTO public.tabla_referencia_dian VALUES (154, 'Retención en la fuente', '4', '2026-08-18', '2026-07');
INSERT INTO public.tabla_referencia_dian VALUES (155, 'Retención en la fuente', '5', '2026-08-19', '2026-07');
INSERT INTO public.tabla_referencia_dian VALUES (156, 'Retención en la fuente', '6', '2026-08-20', '2026-07');
INSERT INTO public.tabla_referencia_dian VALUES (157, 'Retención en la fuente', '7', '2026-08-21', '2026-07');
INSERT INTO public.tabla_referencia_dian VALUES (158, 'Retención en la fuente', '8', '2026-08-24', '2026-07');
INSERT INTO public.tabla_referencia_dian VALUES (159, 'Retención en la fuente', '9', '2026-08-25', '2026-07');
INSERT INTO public.tabla_referencia_dian VALUES (160, 'Retención en la fuente', '0', '2026-08-26', '2026-07');
INSERT INTO public.tabla_referencia_dian VALUES (161, 'Retención en la fuente', '1', '2026-09-09', '2026-08');
INSERT INTO public.tabla_referencia_dian VALUES (162, 'Retención en la fuente', '2', '2026-09-10', '2026-08');
INSERT INTO public.tabla_referencia_dian VALUES (163, 'Retención en la fuente', '3', '2026-09-11', '2026-08');
INSERT INTO public.tabla_referencia_dian VALUES (164, 'Retención en la fuente', '4', '2026-09-14', '2026-08');
INSERT INTO public.tabla_referencia_dian VALUES (165, 'Retención en la fuente', '5', '2026-09-15', '2026-08');
INSERT INTO public.tabla_referencia_dian VALUES (166, 'Retención en la fuente', '6', '2026-09-16', '2026-08');
INSERT INTO public.tabla_referencia_dian VALUES (167, 'Retención en la fuente', '7', '2026-09-17', '2026-08');
INSERT INTO public.tabla_referencia_dian VALUES (168, 'Retención en la fuente', '8', '2026-09-18', '2026-08');
INSERT INTO public.tabla_referencia_dian VALUES (169, 'Retención en la fuente', '9', '2026-09-21', '2026-08');
INSERT INTO public.tabla_referencia_dian VALUES (170, 'Retención en la fuente', '0', '2026-09-22', '2026-08');
INSERT INTO public.tabla_referencia_dian VALUES (171, 'Retención en la fuente', '1', '2026-10-09', '2026-09');
INSERT INTO public.tabla_referencia_dian VALUES (172, 'Retención en la fuente', '2', '2026-10-13', '2026-09');
INSERT INTO public.tabla_referencia_dian VALUES (173, 'Retención en la fuente', '3', '2026-10-14', '2026-09');
INSERT INTO public.tabla_referencia_dian VALUES (174, 'Retención en la fuente', '4', '2026-10-15', '2026-09');
INSERT INTO public.tabla_referencia_dian VALUES (175, 'Retención en la fuente', '5', '2026-10-16', '2026-09');
INSERT INTO public.tabla_referencia_dian VALUES (176, 'Retención en la fuente', '6', '2026-10-19', '2026-09');
INSERT INTO public.tabla_referencia_dian VALUES (177, 'Retención en la fuente', '7', '2026-10-20', '2026-09');
INSERT INTO public.tabla_referencia_dian VALUES (178, 'Retención en la fuente', '8', '2026-10-21', '2026-09');
INSERT INTO public.tabla_referencia_dian VALUES (179, 'Retención en la fuente', '9', '2026-10-22', '2026-09');
INSERT INTO public.tabla_referencia_dian VALUES (180, 'Retención en la fuente', '0', '2026-10-23', '2026-09');
INSERT INTO public.tabla_referencia_dian VALUES (181, 'Retención en la fuente', '1', '2026-11-11', '2026-10');
INSERT INTO public.tabla_referencia_dian VALUES (182, 'Retención en la fuente', '2', '2026-11-12', '2026-10');
INSERT INTO public.tabla_referencia_dian VALUES (183, 'Retención en la fuente', '3', '2026-11-13', '2026-10');
INSERT INTO public.tabla_referencia_dian VALUES (184, 'Retención en la fuente', '4', '2026-11-17', '2026-10');
INSERT INTO public.tabla_referencia_dian VALUES (185, 'Retención en la fuente', '5', '2026-11-18', '2026-10');
INSERT INTO public.tabla_referencia_dian VALUES (186, 'Retención en la fuente', '6', '2026-11-19', '2026-10');
INSERT INTO public.tabla_referencia_dian VALUES (187, 'Retención en la fuente', '7', '2026-11-20', '2026-10');
INSERT INTO public.tabla_referencia_dian VALUES (188, 'Retención en la fuente', '8', '2026-11-23', '2026-10');
INSERT INTO public.tabla_referencia_dian VALUES (189, 'Retención en la fuente', '9', '2026-11-24', '2026-10');
INSERT INTO public.tabla_referencia_dian VALUES (190, 'Retención en la fuente', '0', '2026-11-25', '2026-10');
INSERT INTO public.tabla_referencia_dian VALUES (191, 'Retención en la fuente', '1', '2026-12-10', '2026-11');
INSERT INTO public.tabla_referencia_dian VALUES (192, 'Retención en la fuente', '2', '2026-12-11', '2026-11');
INSERT INTO public.tabla_referencia_dian VALUES (193, 'Retención en la fuente', '3', '2026-12-14', '2026-11');
INSERT INTO public.tabla_referencia_dian VALUES (194, 'Retención en la fuente', '4', '2026-12-15', '2026-11');
INSERT INTO public.tabla_referencia_dian VALUES (195, 'Retención en la fuente', '5', '2026-12-16', '2026-11');
INSERT INTO public.tabla_referencia_dian VALUES (196, 'Retención en la fuente', '6', '2026-12-17', '2026-11');
INSERT INTO public.tabla_referencia_dian VALUES (197, 'Retención en la fuente', '7', '2026-12-18', '2026-11');
INSERT INTO public.tabla_referencia_dian VALUES (198, 'Retención en la fuente', '8', '2026-12-21', '2026-11');
INSERT INTO public.tabla_referencia_dian VALUES (199, 'Retención en la fuente', '9', '2026-12-22', '2026-11');
INSERT INTO public.tabla_referencia_dian VALUES (200, 'Retención en la fuente', '0', '2026-12-23', '2026-11');
INSERT INTO public.tabla_referencia_dian VALUES (201, 'Retención en la fuente', '1', '2027-01-13', '2026-12');
INSERT INTO public.tabla_referencia_dian VALUES (202, 'Retención en la fuente', '2', '2027-01-14', '2026-12');
INSERT INTO public.tabla_referencia_dian VALUES (203, 'Retención en la fuente', '3', '2027-01-15', '2026-12');
INSERT INTO public.tabla_referencia_dian VALUES (204, 'Retención en la fuente', '4', '2027-01-18', '2026-12');
INSERT INTO public.tabla_referencia_dian VALUES (205, 'Retención en la fuente', '5', '2027-01-19', '2026-12');
INSERT INTO public.tabla_referencia_dian VALUES (206, 'Retención en la fuente', '6', '2027-01-20', '2026-12');
INSERT INTO public.tabla_referencia_dian VALUES (207, 'Retención en la fuente', '7', '2027-01-21', '2026-12');
INSERT INTO public.tabla_referencia_dian VALUES (208, 'Retención en la fuente', '8', '2027-01-22', '2026-12');
INSERT INTO public.tabla_referencia_dian VALUES (209, 'Retención en la fuente', '9', '2027-01-25', '2026-12');
INSERT INTO public.tabla_referencia_dian VALUES (210, 'Retención en la fuente', '0', '2027-01-26', '2026-12');
INSERT INTO public.tabla_referencia_dian VALUES (211, 'Renta personas jurídicas', '1', '2026-05-12', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (212, 'Renta personas jurídicas', '2', '2026-05-13', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (213, 'Renta personas jurídicas', '3', '2026-05-14', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (214, 'Renta personas jurídicas', '4', '2026-05-15', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (215, 'Renta personas jurídicas', '5', '2026-05-19', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (216, 'Renta personas jurídicas', '6', '2026-05-20', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (217, 'Renta personas jurídicas', '7', '2026-05-21', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (218, 'Renta personas jurídicas', '8', '2026-05-22', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (219, 'Renta personas jurídicas', '9', '2026-05-25', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (220, 'Renta personas jurídicas', '0', '2026-05-26', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (221, 'Renta personas jurídicas', '1', '2026-07-09', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (222, 'Renta personas jurídicas', '2', '2026-07-10', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (223, 'Renta personas jurídicas', '3', '2026-07-14', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (224, 'Renta personas jurídicas', '4', '2026-07-15', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (225, 'Renta personas jurídicas', '5', '2026-07-16', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (226, 'Renta personas jurídicas', '6', '2026-07-17', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (227, 'Renta personas jurídicas', '7', '2026-07-21', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (228, 'Renta personas jurídicas', '8', '2026-07-22', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (229, 'Renta personas jurídicas', '9', '2026-07-23', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (230, 'Renta personas jurídicas', '0', '2026-07-24', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (231, 'Renta grandes contribuyentes', '1', '2026-02-10', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (232, 'Renta grandes contribuyentes', '2', '2026-02-11', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (233, 'Renta grandes contribuyentes', '3', '2026-02-12', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (234, 'Renta grandes contribuyentes', '4', '2026-02-13', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (235, 'Renta grandes contribuyentes', '5', '2026-02-16', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (236, 'Renta grandes contribuyentes', '6', '2026-02-17', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (237, 'Renta grandes contribuyentes', '7', '2026-02-18', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (238, 'Renta grandes contribuyentes', '8', '2026-02-19', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (239, 'Renta grandes contribuyentes', '9', '2026-02-20', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (240, 'Renta grandes contribuyentes', '0', '2026-02-23', '2026-1C');
INSERT INTO public.tabla_referencia_dian VALUES (241, 'Renta grandes contribuyentes', '1', '2026-04-13', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (242, 'Renta grandes contribuyentes', '2', '2026-04-14', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (243, 'Renta grandes contribuyentes', '3', '2026-04-15', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (244, 'Renta grandes contribuyentes', '4', '2026-04-16', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (245, 'Renta grandes contribuyentes', '5', '2026-04-20', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (246, 'Renta grandes contribuyentes', '6', '2026-04-21', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (247, 'Renta grandes contribuyentes', '7', '2026-04-22', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (248, 'Renta grandes contribuyentes', '8', '2026-04-23', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (249, 'Renta grandes contribuyentes', '9', '2026-04-24', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (250, 'Renta grandes contribuyentes', '0', '2026-04-27', '2026-2C');
INSERT INTO public.tabla_referencia_dian VALUES (251, 'Renta grandes contribuyentes', '1', '2026-06-10', '2026-3C');
INSERT INTO public.tabla_referencia_dian VALUES (252, 'Renta grandes contribuyentes', '2', '2026-06-11', '2026-3C');
INSERT INTO public.tabla_referencia_dian VALUES (253, 'Renta grandes contribuyentes', '3', '2026-06-12', '2026-3C');
INSERT INTO public.tabla_referencia_dian VALUES (254, 'Renta grandes contribuyentes', '4', '2026-06-16', '2026-3C');
INSERT INTO public.tabla_referencia_dian VALUES (255, 'Renta grandes contribuyentes', '5', '2026-06-17', '2026-3C');
INSERT INTO public.tabla_referencia_dian VALUES (256, 'Renta grandes contribuyentes', '6', '2026-06-18', '2026-3C');
INSERT INTO public.tabla_referencia_dian VALUES (257, 'Renta grandes contribuyentes', '7', '2026-06-19', '2026-3C');
INSERT INTO public.tabla_referencia_dian VALUES (258, 'Renta grandes contribuyentes', '8', '2026-06-22', '2026-3C');
INSERT INTO public.tabla_referencia_dian VALUES (259, 'Renta grandes contribuyentes', '9', '2026-06-23', '2026-3C');
INSERT INTO public.tabla_referencia_dian VALUES (260, 'Renta grandes contribuyentes', '0', '2026-06-24', '2026-3C');
INSERT INTO public.tabla_referencia_dian VALUES (261, 'Renta personas naturales', '01', '2026-08-12', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (262, 'Renta personas naturales', '02', '2026-08-12', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (263, 'Renta personas naturales', '03', '2026-08-13', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (264, 'Renta personas naturales', '04', '2026-08-13', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (265, 'Renta personas naturales', '05', '2026-08-14', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (266, 'Renta personas naturales', '06', '2026-08-14', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (267, 'Renta personas naturales', '07', '2026-08-18', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (268, 'Renta personas naturales', '08', '2026-08-18', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (269, 'Renta personas naturales', '09', '2026-08-19', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (270, 'Renta personas naturales', '10', '2026-08-19', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (271, 'Renta personas naturales', '11', '2026-08-20', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (272, 'Renta personas naturales', '12', '2026-08-20', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (273, 'Renta personas naturales', '13', '2026-08-21', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (274, 'Renta personas naturales', '14', '2026-08-21', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (275, 'Renta personas naturales', '15', '2026-08-24', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (276, 'Renta personas naturales', '16', '2026-08-24', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (277, 'Renta personas naturales', '17', '2026-08-25', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (278, 'Renta personas naturales', '18', '2026-08-25', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (279, 'Renta personas naturales', '19', '2026-08-26', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (280, 'Renta personas naturales', '20', '2026-08-26', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (281, 'Renta personas naturales', '21', '2026-08-27', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (282, 'Renta personas naturales', '22', '2026-08-27', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (283, 'Renta personas naturales', '23', '2026-08-28', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (284, 'Renta personas naturales', '24', '2026-08-28', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (285, 'Renta personas naturales', '25', '2026-08-31', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (286, 'Renta personas naturales', '26', '2026-08-31', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (287, 'Renta personas naturales', '27', '2026-09-01', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (288, 'Renta personas naturales', '28', '2026-09-01', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (289, 'Renta personas naturales', '29', '2026-09-02', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (290, 'Renta personas naturales', '30', '2026-09-02', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (291, 'Renta personas naturales', '31', '2026-09-03', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (292, 'Renta personas naturales', '32', '2026-09-03', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (293, 'Renta personas naturales', '33', '2026-09-04', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (294, 'Renta personas naturales', '34', '2026-09-04', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (295, 'Renta personas naturales', '35', '2026-09-07', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (296, 'Renta personas naturales', '36', '2026-09-07', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (297, 'Renta personas naturales', '37', '2026-09-08', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (298, 'Renta personas naturales', '38', '2026-09-08', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (299, 'Renta personas naturales', '39', '2026-09-09', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (300, 'Renta personas naturales', '40', '2026-09-09', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (301, 'Renta personas naturales', '41', '2026-09-10', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (302, 'Renta personas naturales', '42', '2026-09-10', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (303, 'Renta personas naturales', '43', '2026-09-11', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (304, 'Renta personas naturales', '44', '2026-09-11', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (305, 'Renta personas naturales', '45', '2026-09-14', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (306, 'Renta personas naturales', '46', '2026-09-14', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (307, 'Renta personas naturales', '47', '2026-09-15', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (308, 'Renta personas naturales', '48', '2026-09-15', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (309, 'Renta personas naturales', '49', '2026-09-16', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (310, 'Renta personas naturales', '50', '2026-09-16', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (311, 'Renta personas naturales', '51', '2026-09-17', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (312, 'Renta personas naturales', '52', '2026-09-17', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (313, 'Renta personas naturales', '53', '2026-09-18', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (314, 'Renta personas naturales', '54', '2026-09-18', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (315, 'Renta personas naturales', '55', '2026-09-21', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (316, 'Renta personas naturales', '56', '2026-09-21', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (317, 'Renta personas naturales', '57', '2026-09-22', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (318, 'Renta personas naturales', '58', '2026-09-22', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (319, 'Renta personas naturales', '59', '2026-09-23', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (320, 'Renta personas naturales', '60', '2026-09-23', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (321, 'Renta personas naturales', '61', '2026-09-24', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (322, 'Renta personas naturales', '62', '2026-09-24', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (323, 'Renta personas naturales', '63', '2026-09-25', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (324, 'Renta personas naturales', '64', '2026-09-25', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (325, 'Renta personas naturales', '65', '2026-09-28', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (326, 'Renta personas naturales', '66', '2026-09-28', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (327, 'Renta personas naturales', '67', '2026-10-01', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (328, 'Renta personas naturales', '68', '2026-10-01', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (329, 'Renta personas naturales', '69', '2026-10-02', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (330, 'Renta personas naturales', '70', '2026-10-02', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (331, 'Renta personas naturales', '71', '2026-10-05', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (332, 'Renta personas naturales', '72', '2026-10-05', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (333, 'Renta personas naturales', '73', '2026-10-06', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (334, 'Renta personas naturales', '74', '2026-10-06', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (335, 'Renta personas naturales', '75', '2026-10-07', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (336, 'Renta personas naturales', '76', '2026-10-07', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (337, 'Renta personas naturales', '77', '2026-10-08', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (338, 'Renta personas naturales', '78', '2026-10-08', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (339, 'Renta personas naturales', '79', '2026-10-09', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (340, 'Renta personas naturales', '80', '2026-10-09', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (341, 'Renta personas naturales', '81', '2026-10-13', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (342, 'Renta personas naturales', '82', '2026-10-13', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (343, 'Renta personas naturales', '83', '2026-10-14', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (344, 'Renta personas naturales', '84', '2026-10-14', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (345, 'Renta personas naturales', '85', '2026-10-15', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (346, 'Renta personas naturales', '86', '2026-10-15', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (347, 'Renta personas naturales', '87', '2026-10-16', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (348, 'Renta personas naturales', '88', '2026-10-16', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (349, 'Renta personas naturales', '89', '2026-10-19', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (350, 'Renta personas naturales', '90', '2026-10-19', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (351, 'Renta personas naturales', '91', '2026-10-20', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (352, 'Renta personas naturales', '92', '2026-10-20', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (353, 'Renta personas naturales', '93', '2026-10-21', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (354, 'Renta personas naturales', '94', '2026-10-21', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (355, 'Renta personas naturales', '95', '2026-10-22', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (356, 'Renta personas naturales', '96', '2026-10-22', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (357, 'Renta personas naturales', '97', '2026-10-23', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (358, 'Renta personas naturales', '98', '2026-10-23', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (359, 'Renta personas naturales', '99', '2026-10-26', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (360, 'Renta personas naturales', '00', '2026-10-26', '2026');
INSERT INTO public.tabla_referencia_dian VALUES (361, 'RST anticipo bimestral', '1', '2026-05-12', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (362, 'RST anticipo bimestral', '2', '2026-05-13', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (363, 'RST anticipo bimestral', '3', '2026-05-14', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (364, 'RST anticipo bimestral', '4', '2026-05-15', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (365, 'RST anticipo bimestral', '5', '2026-05-19', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (366, 'RST anticipo bimestral', '6', '2026-05-20', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (367, 'RST anticipo bimestral', '7', '2026-05-21', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (368, 'RST anticipo bimestral', '8', '2026-05-22', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (369, 'RST anticipo bimestral', '9', '2026-05-25', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (370, 'RST anticipo bimestral', '0', '2026-05-26', '2026-01');
INSERT INTO public.tabla_referencia_dian VALUES (371, 'RST anticipo bimestral', '1', '2026-06-10', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (372, 'RST anticipo bimestral', '2', '2026-06-11', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (373, 'RST anticipo bimestral', '3', '2026-06-12', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (374, 'RST anticipo bimestral', '4', '2026-06-16', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (375, 'RST anticipo bimestral', '5', '2026-06-17', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (376, 'RST anticipo bimestral', '6', '2026-06-18', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (377, 'RST anticipo bimestral', '7', '2026-06-19', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (378, 'RST anticipo bimestral', '8', '2026-06-22', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (379, 'RST anticipo bimestral', '9', '2026-06-23', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (380, 'RST anticipo bimestral', '0', '2026-06-24', '2026-02');
INSERT INTO public.tabla_referencia_dian VALUES (381, 'RST anticipo bimestral', '1', '2026-07-09', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (382, 'RST anticipo bimestral', '2', '2026-07-10', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (383, 'RST anticipo bimestral', '3', '2026-07-14', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (384, 'RST anticipo bimestral', '4', '2026-07-15', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (385, 'RST anticipo bimestral', '5', '2026-07-16', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (386, 'RST anticipo bimestral', '6', '2026-07-17', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (387, 'RST anticipo bimestral', '7', '2026-07-21', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (388, 'RST anticipo bimestral', '8', '2026-07-22', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (389, 'RST anticipo bimestral', '9', '2026-07-23', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (390, 'RST anticipo bimestral', '0', '2026-07-24', '2026-03');
INSERT INTO public.tabla_referencia_dian VALUES (391, 'RST anticipo bimestral', '1', '2026-09-09', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (392, 'RST anticipo bimestral', '2', '2026-09-10', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (393, 'RST anticipo bimestral', '3', '2026-09-11', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (394, 'RST anticipo bimestral', '4', '2026-09-14', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (395, 'RST anticipo bimestral', '5', '2026-09-15', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (396, 'RST anticipo bimestral', '6', '2026-09-16', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (397, 'RST anticipo bimestral', '7', '2026-09-17', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (398, 'RST anticipo bimestral', '8', '2026-09-18', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (399, 'RST anticipo bimestral', '9', '2026-09-21', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (400, 'RST anticipo bimestral', '0', '2026-09-22', '2026-04');
INSERT INTO public.tabla_referencia_dian VALUES (401, 'RST anticipo bimestral', '1', '2026-11-11', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (402, 'RST anticipo bimestral', '2', '2026-11-12', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (403, 'RST anticipo bimestral', '3', '2026-11-13', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (404, 'RST anticipo bimestral', '4', '2026-11-17', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (405, 'RST anticipo bimestral', '5', '2026-11-18', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (406, 'RST anticipo bimestral', '6', '2026-11-19', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (407, 'RST anticipo bimestral', '7', '2026-11-20', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (408, 'RST anticipo bimestral', '8', '2026-11-23', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (409, 'RST anticipo bimestral', '9', '2026-11-24', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (410, 'RST anticipo bimestral', '0', '2026-11-25', '2026-05');
INSERT INTO public.tabla_referencia_dian VALUES (411, 'RST anticipo bimestral', '1', '2027-01-13', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (412, 'RST anticipo bimestral', '2', '2027-01-14', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (413, 'RST anticipo bimestral', '3', '2027-01-15', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (414, 'RST anticipo bimestral', '4', '2027-01-18', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (415, 'RST anticipo bimestral', '5', '2027-01-19', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (416, 'RST anticipo bimestral', '6', '2027-01-20', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (417, 'RST anticipo bimestral', '7', '2027-01-21', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (418, 'RST anticipo bimestral', '8', '2027-01-22', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (419, 'RST anticipo bimestral', '9', '2027-01-25', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (420, 'RST anticipo bimestral', '0', '2027-01-26', '2026-06');
INSERT INTO public.tabla_referencia_dian VALUES (421, 'RST consolidada anual', '1', '2026-02-16', '2025');
INSERT INTO public.tabla_referencia_dian VALUES (422, 'RST consolidada anual', '2', '2026-02-16', '2025');
INSERT INTO public.tabla_referencia_dian VALUES (423, 'RST consolidada anual', '3', '2026-02-17', '2025');
INSERT INTO public.tabla_referencia_dian VALUES (424, 'RST consolidada anual', '4', '2026-02-17', '2025');
INSERT INTO public.tabla_referencia_dian VALUES (425, 'RST consolidada anual', '5', '2026-02-18', '2025');
INSERT INTO public.tabla_referencia_dian VALUES (426, 'RST consolidada anual', '6', '2026-02-18', '2025');
INSERT INTO public.tabla_referencia_dian VALUES (427, 'RST consolidada anual', '7', '2026-02-19', '2025');
INSERT INTO public.tabla_referencia_dian VALUES (428, 'RST consolidada anual', '8', '2026-02-19', '2025');
INSERT INTO public.tabla_referencia_dian VALUES (429, 'RST consolidada anual', '9', '2026-02-20', '2025');
INSERT INTO public.tabla_referencia_dian VALUES (430, 'RST consolidada anual', '0', '2026-02-20', '2025');
INSERT INTO public.tabla_referencia_dian VALUES (431, 'RST consolidada anual', '1', '2026-04-20', '2026-IVA');
INSERT INTO public.tabla_referencia_dian VALUES (432, 'RST consolidada anual', '2', '2026-04-20', '2026-IVA');
INSERT INTO public.tabla_referencia_dian VALUES (433, 'RST consolidada anual', '3', '2026-04-21', '2026-IVA');
INSERT INTO public.tabla_referencia_dian VALUES (434, 'RST consolidada anual', '4', '2026-04-21', '2026-IVA');
INSERT INTO public.tabla_referencia_dian VALUES (435, 'RST consolidada anual', '5', '2026-04-22', '2026-IVA');
INSERT INTO public.tabla_referencia_dian VALUES (436, 'RST consolidada anual', '6', '2026-04-22', '2026-IVA');
INSERT INTO public.tabla_referencia_dian VALUES (437, 'RST consolidada anual', '7', '2026-04-23', '2026-IVA');
INSERT INTO public.tabla_referencia_dian VALUES (438, 'RST consolidada anual', '8', '2026-04-23', '2026-IVA');
INSERT INTO public.tabla_referencia_dian VALUES (439, 'RST consolidada anual', '9', '2026-04-24', '2026-IVA');
INSERT INTO public.tabla_referencia_dian VALUES (440, 'RST consolidada anual', '0', '2026-04-24', '2026-IVA');


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
-- Name: tabla_referencia_dian_id_referencia_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tabla_referencia_dian_id_referencia_seq', 440, true);


--
-- Name: tipo_servicio_id_tipo_servicio_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tipo_servicio_id_tipo_servicio_seq', 8, true);


--
-- PostgreSQL database dump complete
--

\unrestrict DlhcVzAMlHU3rbBKuu48WtybAsVHO7X4Xz3HfXpoocEw34y33mWaOUJpSjGn8im

