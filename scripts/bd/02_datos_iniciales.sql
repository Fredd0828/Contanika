-- ============================================================================
-- Datos iniciales del sistema Contanika (anexo del entregable 3.1)
-- Catálogos: roles, módulos, reportes, permisos por rol, tipos de servicio,
-- métodos de pago, conceptos facturables, plantillas base con sus campos
-- (simples y repetibles), configuración del despacho y calendario oficial
-- DIAN 2026. No incluye usuarios ni credenciales por seguridad.
-- ============================================================================

--
-- PostgreSQL database dump
--

\restrict DUwTXrkFdnqTrXsRn5JBpFaUmfsOx5f6TdPaldhuHybmj8JW1NiUfqubDT5GT8v

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
-- Data for Name: plantilla; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.plantilla (id_plantilla, nombre_plantilla, texto_predeterminado, tipo_documento) FROM stdin;
1	Certificación de ingresos para independientes	El suscrito contador certifica que {{ cliente }}, identificado con {{ tipo_documento_cliente }} No. {{ identificacion_cliente }}, ejerce la actividad económica de {{ actividad_economica }} de manera independiente.\n\nPara el período {{ periodo }}, se certifica un ingreso de $ {{ valor_del_ingreso_certificado }}, por concepto de {{ concepto }}.\n\nEsta certificación se expide a solicitud del interesado en {{ ciudad_despacho }}, el {{ fecha_expedicion }}.	Certificación de ingresos para independientes
2	Certificado de ingresos y retenciones (Art. 378 ET)	Certificado de ingresos y retenciones - Artículo 378 del Estatuto Tributario, período gravable {{ periodo }}.\n\n{{ nombre_despacho }} certifica, como agente retenedor, que durante el período {{ periodo }} efectuó pagos a {{ nombre_del_asalariado }}, identificado con cédula No. {{ identificacion_del_asalariado }}.\n\nAgente retenedor: {{ cliente }}, NIT {{ identificacion_cliente }}, con dirección {{ direccion_del_agente_retenedor }}.\n\nValor de los pagos o abonos en cuenta: $ {{ valor_de_los_pagos_o_abonos }}, por concepto de {{ concepto }}. Monto de la retención practicada: $ {{ monto_de_la_retencion }}.\n\nLa retención fue consignada en {{ ciudad_donde_se_consigno_la_retencion }}.\n\nSe expide el presente certificado en {{ ciudad_despacho }}, el {{ fecha_expedicion }}.	Certificado de ingresos y retenciones (Art. 378 ET)
3	Certificado de composición accionaria	Se certifica que la composición accionaria de {{ cliente }}, identificada con NIT {{ identificacion_cliente }}, con corte a {{ periodo }}, es la siguiente:\n\n{% for fila in filas_repetibles %}- {{ fila.nombre_del_accionista }}: {{ fila.porcentaje_de_participacion }}%\n{% endfor %}\nSe expide la presente certificación en {{ ciudad_despacho }}, el {{ fecha_expedicion }}.	Certificado de composición accionaria
4	Certificado de patrimonio	Se certifica que, con corte a {{ periodo }}, {{ cliente }}, identificado con {{ tipo_documento_cliente }} No. {{ identificacion_cliente }}, presenta el siguiente patrimonio:\n\nValor del patrimonio: $ {{ valor_del_patrimonio }}\nTotal de activos: $ {{ total_de_activos }}\nTotal de pasivos: $ {{ total_de_pasivos }}\n\nEsta certificación se expide con base en {{ base_de_la_certificacion }}, en {{ ciudad_despacho }}, el {{ fecha_expedicion }}.	Certificado de patrimonio
5	Certificado de dependiente económico	Se certifica que {{ nombre_del_dependiente_economico }}, identificado con cédula No. {{ identificacion_del_dependiente_economico }}, es dependiente económico de {{ cliente }}, identificado con {{ tipo_documento_cliente }} No. {{ identificacion_cliente }}, en calidad de {{ relacion_o_parentesco }}, para el año gravable {{ periodo }}.\n\nSe certifica que el dependiente económico cumple los requisitos establecidos en el Estatuto Tributario para ser considerado como tal.\n\nSe expide la presente certificación en {{ ciudad_despacho }}, el {{ fecha_expedicion }}.	Certificado de dependiente económico
6	Certificación de no obligación a declarar renta	Se certifica que {{ cliente }}, identificado con {{ tipo_documento_cliente }} No. {{ identificacion_cliente }}, para el año gravable {{ periodo }}, no se encuentra obligado a declarar renta, de acuerdo con los siguientes valores:\n\nIngresos brutos: $ {{ ingresos_brutos }}\nPatrimonio bruto: $ {{ patrimonio_bruto }}\nConsignaciones, compras y consumos del período: $ {{ consignaciones_compras_y_consumos_del_periodo }}\n\nSe certifica que estos valores no superan los topes vigentes establecidos por la DIAN para estar obligado a declarar renta.\n\nSe expide la presente certificación en {{ ciudad_despacho }}, el {{ fecha_expedicion }}.	Certificación de no obligación a declarar renta
\.


--
-- Data for Name: campo_plantilla; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.campo_plantilla (id_campo, nombre_campo, tipo_campo, es_repetible, id_plantilla) FROM stdin;
1	Actividad económica	Simple	f	1
2	Valor del ingreso certificado	Simple	f	1
3	Concepto	Simple	f	1
4	Ciudad donde se consignó la retención	Simple	f	2
5	Nombre del asalariado	Simple	f	2
6	Identificación del asalariado	Simple	f	2
7	Dirección del agente retenedor	Simple	f	2
8	Valor de los pagos o abonos	Simple	f	2
9	Concepto	Simple	f	2
10	Monto de la retención	Simple	f	2
11	Nombre del accionista	Repetible	t	3
12	Porcentaje de participación	Repetible	t	3
13	Valor del patrimonio	Simple	f	4
14	Total de activos	Simple	f	4
15	Total de pasivos	Simple	f	4
16	Base de la certificación	Simple	f	4
17	Nombre del dependiente económico	Simple	f	5
18	Identificación del dependiente económico	Simple	f	5
19	Relación o parentesco	Simple	f	5
20	Ingresos brutos	Simple	f	6
21	Patrimonio bruto	Simple	f	6
22	Consignaciones, compras y consumos del período	Simple	f	6
\.


--
-- Data for Name: concepto_facturable; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.concepto_facturable (id_concepto, nombre_concepto, valor_sugerido) FROM stdin;
1	Contabilidad mensual	0.00
2	Nómina	0.00
3	Declaración de renta	0.00
4	Declaración de IVA	0.00
5	Revisoría fiscal	0.00
\.


--
-- Data for Name: configuracion_despacho; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.configuracion_despacho (id_configuracion, nombre_despacho, nit_despacho, membrete, ciudad, direccion, telefono, correo) FROM stdin;
1	Befrec Y Asociados SAS			Bogotá D.C.			
\.


--
-- Data for Name: metodo_pago; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.metodo_pago (id_metodo_pago, nombre_metodo) FROM stdin;
1	Transferencia
2	Consignación
3	Efectivo
4	Nequi
5	Daviplata
\.


--
-- Data for Name: modulo; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.modulo (id_modulo, nombre_modulo, codigo_modulo) FROM stdin;
11	Gestión de clientes	MOD01
12	Calendario	MOD02
13	Tablero de tareas Kanban	MOD03
14	Expedición de documentos y certificados	MOD04
15	Hallazgos y revisiones	MOD05
16	Honorarios, cartera y cuentas de cobro	MOD06
17	Comunicaciones integradas	MOD07
18	Gestión de equipo y roles	MOD08
19	Expediente y bitácora por cliente	MOD09
20	Reportes y análisis	MOD10
\.


--
-- Data for Name: reporte; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.reporte (id_reporte, nombre_reporte, modulo_origen) FROM stdin;
3	Clientes	Gestión de clientes
4	Vencimientos tributarios	Calendario
5	Cartera	Honorarios y cartera
6	Cuentas de cobro	Honorarios y cartera
7	Tareas del Kanban	Tablero Kanban
8	Ingresos mensuales del despacho	Honorarios y cartera
\.


--
-- Data for Name: rol; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.rol (id_rol, nombre_rol) FROM stdin;
4	Administrador
5	Contador Senior
6	Contador Junior
\.


--
-- Data for Name: permiso_reporte_rol; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.permiso_reporte_rol (id_permiso_reporte, habilitado, id_reporte, id_rol) FROM stdin;
1	t	3	4
2	t	4	4
3	t	5	4
4	t	6	4
5	t	7	4
6	t	8	4
7	t	3	5
8	t	4	5
9	t	5	5
10	t	6	5
11	t	7	5
12	t	8	5
13	t	3	6
14	t	4	6
15	t	5	6
16	t	6	6
17	t	7	6
18	t	8	6
\.


--
-- Data for Name: permiso_rol_modulo; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.permiso_rol_modulo (id_permiso, habilitado, id_modulo, id_rol) FROM stdin;
1	t	11	4
2	t	12	4
3	t	13	4
4	t	14	4
5	t	15	4
6	t	16	4
7	t	17	4
8	t	18	4
9	t	19	4
10	t	20	4
11	t	11	5
12	t	12	5
13	t	13	5
14	t	14	5
15	t	15	5
16	t	16	5
17	t	17	5
18	t	18	5
19	t	19	5
20	t	20	5
21	t	11	6
22	t	12	6
23	t	13	6
24	t	14	6
25	t	15	6
26	t	16	6
27	t	17	6
28	t	18	6
29	t	19	6
30	t	20	6
\.


--
-- Data for Name: tabla_referencia_dian; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tabla_referencia_dian (id_referencia, tipo_obligacion, grupo_nit, fecha_vencimiento, periodo_gravable) FROM stdin;
1	IVA bimestral	1	2026-03-10	2026-01
2	IVA bimestral	2	2026-03-11	2026-01
3	IVA bimestral	3	2026-03-12	2026-01
4	IVA bimestral	4	2026-03-13	2026-01
5	IVA bimestral	5	2026-03-16	2026-01
6	IVA bimestral	6	2026-03-17	2026-01
7	IVA bimestral	7	2026-03-18	2026-01
8	IVA bimestral	8	2026-03-19	2026-01
9	IVA bimestral	9	2026-03-20	2026-01
10	IVA bimestral	0	2026-03-24	2026-01
11	IVA bimestral	1	2026-05-12	2026-02
12	IVA bimestral	2	2026-05-13	2026-02
13	IVA bimestral	3	2026-05-14	2026-02
14	IVA bimestral	4	2026-05-15	2026-02
15	IVA bimestral	5	2026-05-19	2026-02
16	IVA bimestral	6	2026-05-20	2026-02
17	IVA bimestral	7	2026-05-21	2026-02
18	IVA bimestral	8	2026-05-22	2026-02
19	IVA bimestral	9	2026-05-25	2026-02
20	IVA bimestral	0	2026-05-26	2026-02
21	IVA bimestral	1	2026-07-09	2026-03
22	IVA bimestral	2	2026-07-10	2026-03
23	IVA bimestral	3	2026-07-14	2026-03
24	IVA bimestral	4	2026-07-15	2026-03
25	IVA bimestral	5	2026-07-16	2026-03
26	IVA bimestral	6	2026-07-17	2026-03
27	IVA bimestral	7	2026-07-21	2026-03
28	IVA bimestral	8	2026-07-22	2026-03
29	IVA bimestral	9	2026-07-23	2026-03
30	IVA bimestral	0	2026-07-24	2026-03
31	IVA bimestral	1	2026-09-09	2026-04
32	IVA bimestral	2	2026-09-10	2026-04
33	IVA bimestral	3	2026-09-11	2026-04
34	IVA bimestral	4	2026-09-14	2026-04
35	IVA bimestral	5	2026-09-15	2026-04
36	IVA bimestral	6	2026-09-16	2026-04
37	IVA bimestral	7	2026-09-17	2026-04
38	IVA bimestral	8	2026-09-18	2026-04
39	IVA bimestral	9	2026-09-21	2026-04
40	IVA bimestral	0	2026-09-22	2026-04
41	IVA bimestral	1	2026-11-11	2026-05
42	IVA bimestral	2	2026-11-12	2026-05
43	IVA bimestral	3	2026-11-13	2026-05
44	IVA bimestral	4	2026-11-17	2026-05
45	IVA bimestral	5	2026-11-18	2026-05
46	IVA bimestral	6	2026-11-19	2026-05
47	IVA bimestral	7	2026-11-20	2026-05
48	IVA bimestral	8	2026-11-23	2026-05
49	IVA bimestral	9	2026-11-24	2026-05
50	IVA bimestral	0	2026-11-25	2026-05
51	IVA bimestral	1	2027-01-13	2026-06
52	IVA bimestral	2	2027-01-14	2026-06
53	IVA bimestral	3	2027-01-15	2026-06
54	IVA bimestral	4	2027-01-18	2026-06
55	IVA bimestral	5	2027-01-19	2026-06
56	IVA bimestral	6	2027-01-20	2026-06
57	IVA bimestral	7	2027-01-21	2026-06
58	IVA bimestral	8	2027-01-22	2026-06
59	IVA bimestral	9	2027-01-25	2026-06
60	IVA bimestral	0	2027-01-26	2026-06
61	IVA cuatrimestral	1	2026-05-12	2026-C1
62	IVA cuatrimestral	2	2026-05-13	2026-C1
63	IVA cuatrimestral	3	2026-05-14	2026-C1
64	IVA cuatrimestral	4	2026-05-15	2026-C1
65	IVA cuatrimestral	5	2026-05-19	2026-C1
66	IVA cuatrimestral	6	2026-05-20	2026-C1
67	IVA cuatrimestral	7	2026-05-21	2026-C1
68	IVA cuatrimestral	8	2026-05-22	2026-C1
69	IVA cuatrimestral	9	2026-05-25	2026-C1
70	IVA cuatrimestral	0	2026-05-26	2026-C1
71	IVA cuatrimestral	1	2026-09-09	2026-C2
72	IVA cuatrimestral	2	2026-09-10	2026-C2
73	IVA cuatrimestral	3	2026-09-11	2026-C2
74	IVA cuatrimestral	4	2026-09-14	2026-C2
75	IVA cuatrimestral	5	2026-09-15	2026-C2
76	IVA cuatrimestral	6	2026-09-16	2026-C2
77	IVA cuatrimestral	7	2026-09-17	2026-C2
78	IVA cuatrimestral	8	2026-09-18	2026-C2
79	IVA cuatrimestral	9	2026-09-21	2026-C2
80	IVA cuatrimestral	0	2026-09-22	2026-C2
81	IVA cuatrimestral	1	2027-01-13	2026-C3
82	IVA cuatrimestral	2	2027-01-14	2026-C3
83	IVA cuatrimestral	3	2027-01-15	2026-C3
84	IVA cuatrimestral	4	2027-01-18	2026-C3
85	IVA cuatrimestral	5	2027-01-19	2026-C3
86	IVA cuatrimestral	6	2027-01-20	2026-C3
87	IVA cuatrimestral	7	2027-01-21	2026-C3
88	IVA cuatrimestral	8	2027-01-22	2026-C3
89	IVA cuatrimestral	9	2027-01-25	2026-C3
90	IVA cuatrimestral	0	2027-01-26	2026-C3
91	Retención en la fuente	1	2026-02-10	2026-01
92	Retención en la fuente	2	2026-02-11	2026-01
93	Retención en la fuente	3	2026-02-12	2026-01
94	Retención en la fuente	4	2026-02-13	2026-01
95	Retención en la fuente	5	2026-02-16	2026-01
96	Retención en la fuente	6	2026-02-17	2026-01
97	Retención en la fuente	7	2026-02-18	2026-01
98	Retención en la fuente	8	2026-02-19	2026-01
99	Retención en la fuente	9	2026-02-20	2026-01
100	Retención en la fuente	0	2026-02-23	2026-01
101	Retención en la fuente	1	2026-03-10	2026-02
102	Retención en la fuente	2	2026-03-11	2026-02
103	Retención en la fuente	3	2026-03-12	2026-02
104	Retención en la fuente	4	2026-03-13	2026-02
105	Retención en la fuente	5	2026-03-16	2026-02
106	Retención en la fuente	6	2026-03-17	2026-02
107	Retención en la fuente	7	2026-03-18	2026-02
108	Retención en la fuente	8	2026-03-19	2026-02
109	Retención en la fuente	9	2026-03-20	2026-02
110	Retención en la fuente	0	2026-03-24	2026-02
111	Retención en la fuente	1	2026-04-13	2026-03
112	Retención en la fuente	2	2026-04-14	2026-03
113	Retención en la fuente	3	2026-04-15	2026-03
114	Retención en la fuente	4	2026-04-16	2026-03
115	Retención en la fuente	5	2026-04-20	2026-03
116	Retención en la fuente	6	2026-04-21	2026-03
117	Retención en la fuente	7	2026-04-22	2026-03
118	Retención en la fuente	8	2026-04-23	2026-03
119	Retención en la fuente	9	2026-04-24	2026-03
120	Retención en la fuente	0	2026-04-27	2026-03
121	Retención en la fuente	1	2026-05-12	2026-04
122	Retención en la fuente	2	2026-05-13	2026-04
123	Retención en la fuente	3	2026-05-14	2026-04
124	Retención en la fuente	4	2026-05-15	2026-04
125	Retención en la fuente	5	2026-05-19	2026-04
126	Retención en la fuente	6	2026-05-20	2026-04
127	Retención en la fuente	7	2026-05-21	2026-04
128	Retención en la fuente	8	2026-05-22	2026-04
129	Retención en la fuente	9	2026-05-25	2026-04
130	Retención en la fuente	0	2026-05-26	2026-04
131	Retención en la fuente	1	2026-06-10	2026-05
132	Retención en la fuente	2	2026-06-11	2026-05
133	Retención en la fuente	3	2026-06-12	2026-05
134	Retención en la fuente	4	2026-06-16	2026-05
135	Retención en la fuente	5	2026-06-17	2026-05
136	Retención en la fuente	6	2026-06-18	2026-05
137	Retención en la fuente	7	2026-06-19	2026-05
138	Retención en la fuente	8	2026-06-22	2026-05
139	Retención en la fuente	9	2026-06-23	2026-05
140	Retención en la fuente	0	2026-06-24	2026-05
141	Retención en la fuente	1	2026-07-09	2026-06
142	Retención en la fuente	2	2026-07-10	2026-06
143	Retención en la fuente	3	2026-07-14	2026-06
144	Retención en la fuente	4	2026-07-15	2026-06
145	Retención en la fuente	5	2026-07-16	2026-06
146	Retención en la fuente	6	2026-07-17	2026-06
147	Retención en la fuente	7	2026-07-21	2026-06
148	Retención en la fuente	8	2026-07-22	2026-06
149	Retención en la fuente	9	2026-07-23	2026-06
150	Retención en la fuente	0	2026-07-24	2026-06
151	Retención en la fuente	1	2026-08-12	2026-07
152	Retención en la fuente	2	2026-08-13	2026-07
153	Retención en la fuente	3	2026-08-14	2026-07
154	Retención en la fuente	4	2026-08-18	2026-07
155	Retención en la fuente	5	2026-08-19	2026-07
156	Retención en la fuente	6	2026-08-20	2026-07
157	Retención en la fuente	7	2026-08-21	2026-07
158	Retención en la fuente	8	2026-08-24	2026-07
159	Retención en la fuente	9	2026-08-25	2026-07
160	Retención en la fuente	0	2026-08-26	2026-07
161	Retención en la fuente	1	2026-09-09	2026-08
162	Retención en la fuente	2	2026-09-10	2026-08
163	Retención en la fuente	3	2026-09-11	2026-08
164	Retención en la fuente	4	2026-09-14	2026-08
165	Retención en la fuente	5	2026-09-15	2026-08
166	Retención en la fuente	6	2026-09-16	2026-08
167	Retención en la fuente	7	2026-09-17	2026-08
168	Retención en la fuente	8	2026-09-18	2026-08
169	Retención en la fuente	9	2026-09-21	2026-08
170	Retención en la fuente	0	2026-09-22	2026-08
171	Retención en la fuente	1	2026-10-09	2026-09
172	Retención en la fuente	2	2026-10-13	2026-09
173	Retención en la fuente	3	2026-10-14	2026-09
174	Retención en la fuente	4	2026-10-15	2026-09
175	Retención en la fuente	5	2026-10-16	2026-09
176	Retención en la fuente	6	2026-10-19	2026-09
177	Retención en la fuente	7	2026-10-20	2026-09
178	Retención en la fuente	8	2026-10-21	2026-09
179	Retención en la fuente	9	2026-10-22	2026-09
180	Retención en la fuente	0	2026-10-23	2026-09
181	Retención en la fuente	1	2026-11-11	2026-10
182	Retención en la fuente	2	2026-11-12	2026-10
183	Retención en la fuente	3	2026-11-13	2026-10
184	Retención en la fuente	4	2026-11-17	2026-10
185	Retención en la fuente	5	2026-11-18	2026-10
186	Retención en la fuente	6	2026-11-19	2026-10
187	Retención en la fuente	7	2026-11-20	2026-10
188	Retención en la fuente	8	2026-11-23	2026-10
189	Retención en la fuente	9	2026-11-24	2026-10
190	Retención en la fuente	0	2026-11-25	2026-10
191	Retención en la fuente	1	2026-12-10	2026-11
192	Retención en la fuente	2	2026-12-11	2026-11
193	Retención en la fuente	3	2026-12-14	2026-11
194	Retención en la fuente	4	2026-12-15	2026-11
195	Retención en la fuente	5	2026-12-16	2026-11
196	Retención en la fuente	6	2026-12-17	2026-11
197	Retención en la fuente	7	2026-12-18	2026-11
198	Retención en la fuente	8	2026-12-21	2026-11
199	Retención en la fuente	9	2026-12-22	2026-11
200	Retención en la fuente	0	2026-12-23	2026-11
201	Retención en la fuente	1	2027-01-13	2026-12
202	Retención en la fuente	2	2027-01-14	2026-12
203	Retención en la fuente	3	2027-01-15	2026-12
204	Retención en la fuente	4	2027-01-18	2026-12
205	Retención en la fuente	5	2027-01-19	2026-12
206	Retención en la fuente	6	2027-01-20	2026-12
207	Retención en la fuente	7	2027-01-21	2026-12
208	Retención en la fuente	8	2027-01-22	2026-12
209	Retención en la fuente	9	2027-01-25	2026-12
210	Retención en la fuente	0	2027-01-26	2026-12
211	Renta personas jurídicas	1	2026-05-12	2026-1C
212	Renta personas jurídicas	2	2026-05-13	2026-1C
213	Renta personas jurídicas	3	2026-05-14	2026-1C
214	Renta personas jurídicas	4	2026-05-15	2026-1C
215	Renta personas jurídicas	5	2026-05-19	2026-1C
216	Renta personas jurídicas	6	2026-05-20	2026-1C
217	Renta personas jurídicas	7	2026-05-21	2026-1C
218	Renta personas jurídicas	8	2026-05-22	2026-1C
219	Renta personas jurídicas	9	2026-05-25	2026-1C
220	Renta personas jurídicas	0	2026-05-26	2026-1C
221	Renta personas jurídicas	1	2026-07-09	2026-2C
222	Renta personas jurídicas	2	2026-07-10	2026-2C
223	Renta personas jurídicas	3	2026-07-14	2026-2C
224	Renta personas jurídicas	4	2026-07-15	2026-2C
225	Renta personas jurídicas	5	2026-07-16	2026-2C
226	Renta personas jurídicas	6	2026-07-17	2026-2C
227	Renta personas jurídicas	7	2026-07-21	2026-2C
228	Renta personas jurídicas	8	2026-07-22	2026-2C
229	Renta personas jurídicas	9	2026-07-23	2026-2C
230	Renta personas jurídicas	0	2026-07-24	2026-2C
231	Renta grandes contribuyentes	1	2026-02-10	2026-1C
232	Renta grandes contribuyentes	2	2026-02-11	2026-1C
233	Renta grandes contribuyentes	3	2026-02-12	2026-1C
234	Renta grandes contribuyentes	4	2026-02-13	2026-1C
235	Renta grandes contribuyentes	5	2026-02-16	2026-1C
236	Renta grandes contribuyentes	6	2026-02-17	2026-1C
237	Renta grandes contribuyentes	7	2026-02-18	2026-1C
238	Renta grandes contribuyentes	8	2026-02-19	2026-1C
239	Renta grandes contribuyentes	9	2026-02-20	2026-1C
240	Renta grandes contribuyentes	0	2026-02-23	2026-1C
241	Renta grandes contribuyentes	1	2026-04-13	2026-2C
242	Renta grandes contribuyentes	2	2026-04-14	2026-2C
243	Renta grandes contribuyentes	3	2026-04-15	2026-2C
244	Renta grandes contribuyentes	4	2026-04-16	2026-2C
245	Renta grandes contribuyentes	5	2026-04-20	2026-2C
246	Renta grandes contribuyentes	6	2026-04-21	2026-2C
247	Renta grandes contribuyentes	7	2026-04-22	2026-2C
248	Renta grandes contribuyentes	8	2026-04-23	2026-2C
249	Renta grandes contribuyentes	9	2026-04-24	2026-2C
250	Renta grandes contribuyentes	0	2026-04-27	2026-2C
251	Renta grandes contribuyentes	1	2026-06-10	2026-3C
252	Renta grandes contribuyentes	2	2026-06-11	2026-3C
253	Renta grandes contribuyentes	3	2026-06-12	2026-3C
254	Renta grandes contribuyentes	4	2026-06-16	2026-3C
255	Renta grandes contribuyentes	5	2026-06-17	2026-3C
256	Renta grandes contribuyentes	6	2026-06-18	2026-3C
257	Renta grandes contribuyentes	7	2026-06-19	2026-3C
258	Renta grandes contribuyentes	8	2026-06-22	2026-3C
259	Renta grandes contribuyentes	9	2026-06-23	2026-3C
260	Renta grandes contribuyentes	0	2026-06-24	2026-3C
261	Renta personas naturales	01	2026-08-12	2026
262	Renta personas naturales	02	2026-08-12	2026
263	Renta personas naturales	03	2026-08-13	2026
264	Renta personas naturales	04	2026-08-13	2026
265	Renta personas naturales	05	2026-08-14	2026
266	Renta personas naturales	06	2026-08-14	2026
267	Renta personas naturales	07	2026-08-18	2026
268	Renta personas naturales	08	2026-08-18	2026
269	Renta personas naturales	09	2026-08-19	2026
270	Renta personas naturales	10	2026-08-19	2026
271	Renta personas naturales	11	2026-08-20	2026
272	Renta personas naturales	12	2026-08-20	2026
273	Renta personas naturales	13	2026-08-21	2026
274	Renta personas naturales	14	2026-08-21	2026
275	Renta personas naturales	15	2026-08-24	2026
276	Renta personas naturales	16	2026-08-24	2026
277	Renta personas naturales	17	2026-08-25	2026
278	Renta personas naturales	18	2026-08-25	2026
279	Renta personas naturales	19	2026-08-26	2026
280	Renta personas naturales	20	2026-08-26	2026
281	Renta personas naturales	21	2026-08-27	2026
282	Renta personas naturales	22	2026-08-27	2026
283	Renta personas naturales	23	2026-08-28	2026
284	Renta personas naturales	24	2026-08-28	2026
285	Renta personas naturales	25	2026-08-31	2026
286	Renta personas naturales	26	2026-08-31	2026
287	Renta personas naturales	27	2026-09-01	2026
288	Renta personas naturales	28	2026-09-01	2026
289	Renta personas naturales	29	2026-09-02	2026
290	Renta personas naturales	30	2026-09-02	2026
291	Renta personas naturales	31	2026-09-03	2026
292	Renta personas naturales	32	2026-09-03	2026
293	Renta personas naturales	33	2026-09-04	2026
294	Renta personas naturales	34	2026-09-04	2026
295	Renta personas naturales	35	2026-09-07	2026
296	Renta personas naturales	36	2026-09-07	2026
297	Renta personas naturales	37	2026-09-08	2026
298	Renta personas naturales	38	2026-09-08	2026
299	Renta personas naturales	39	2026-09-09	2026
300	Renta personas naturales	40	2026-09-09	2026
301	Renta personas naturales	41	2026-09-10	2026
302	Renta personas naturales	42	2026-09-10	2026
303	Renta personas naturales	43	2026-09-11	2026
304	Renta personas naturales	44	2026-09-11	2026
305	Renta personas naturales	45	2026-09-14	2026
306	Renta personas naturales	46	2026-09-14	2026
307	Renta personas naturales	47	2026-09-15	2026
308	Renta personas naturales	48	2026-09-15	2026
309	Renta personas naturales	49	2026-09-16	2026
310	Renta personas naturales	50	2026-09-16	2026
311	Renta personas naturales	51	2026-09-17	2026
312	Renta personas naturales	52	2026-09-17	2026
313	Renta personas naturales	53	2026-09-18	2026
314	Renta personas naturales	54	2026-09-18	2026
315	Renta personas naturales	55	2026-09-21	2026
316	Renta personas naturales	56	2026-09-21	2026
317	Renta personas naturales	57	2026-09-22	2026
318	Renta personas naturales	58	2026-09-22	2026
319	Renta personas naturales	59	2026-09-23	2026
320	Renta personas naturales	60	2026-09-23	2026
321	Renta personas naturales	61	2026-09-24	2026
322	Renta personas naturales	62	2026-09-24	2026
323	Renta personas naturales	63	2026-09-25	2026
324	Renta personas naturales	64	2026-09-25	2026
325	Renta personas naturales	65	2026-09-28	2026
326	Renta personas naturales	66	2026-09-28	2026
327	Renta personas naturales	67	2026-10-01	2026
328	Renta personas naturales	68	2026-10-01	2026
329	Renta personas naturales	69	2026-10-02	2026
330	Renta personas naturales	70	2026-10-02	2026
331	Renta personas naturales	71	2026-10-05	2026
332	Renta personas naturales	72	2026-10-05	2026
333	Renta personas naturales	73	2026-10-06	2026
334	Renta personas naturales	74	2026-10-06	2026
335	Renta personas naturales	75	2026-10-07	2026
336	Renta personas naturales	76	2026-10-07	2026
337	Renta personas naturales	77	2026-10-08	2026
338	Renta personas naturales	78	2026-10-08	2026
339	Renta personas naturales	79	2026-10-09	2026
340	Renta personas naturales	80	2026-10-09	2026
341	Renta personas naturales	81	2026-10-13	2026
342	Renta personas naturales	82	2026-10-13	2026
343	Renta personas naturales	83	2026-10-14	2026
344	Renta personas naturales	84	2026-10-14	2026
345	Renta personas naturales	85	2026-10-15	2026
346	Renta personas naturales	86	2026-10-15	2026
347	Renta personas naturales	87	2026-10-16	2026
348	Renta personas naturales	88	2026-10-16	2026
349	Renta personas naturales	89	2026-10-19	2026
350	Renta personas naturales	90	2026-10-19	2026
351	Renta personas naturales	91	2026-10-20	2026
352	Renta personas naturales	92	2026-10-20	2026
353	Renta personas naturales	93	2026-10-21	2026
354	Renta personas naturales	94	2026-10-21	2026
355	Renta personas naturales	95	2026-10-22	2026
356	Renta personas naturales	96	2026-10-22	2026
357	Renta personas naturales	97	2026-10-23	2026
358	Renta personas naturales	98	2026-10-23	2026
359	Renta personas naturales	99	2026-10-26	2026
360	Renta personas naturales	00	2026-10-26	2026
361	RST anticipo bimestral	1	2026-05-12	2026-01
362	RST anticipo bimestral	2	2026-05-13	2026-01
363	RST anticipo bimestral	3	2026-05-14	2026-01
364	RST anticipo bimestral	4	2026-05-15	2026-01
365	RST anticipo bimestral	5	2026-05-19	2026-01
366	RST anticipo bimestral	6	2026-05-20	2026-01
367	RST anticipo bimestral	7	2026-05-21	2026-01
368	RST anticipo bimestral	8	2026-05-22	2026-01
369	RST anticipo bimestral	9	2026-05-25	2026-01
370	RST anticipo bimestral	0	2026-05-26	2026-01
371	RST anticipo bimestral	1	2026-06-10	2026-02
372	RST anticipo bimestral	2	2026-06-11	2026-02
373	RST anticipo bimestral	3	2026-06-12	2026-02
374	RST anticipo bimestral	4	2026-06-16	2026-02
375	RST anticipo bimestral	5	2026-06-17	2026-02
376	RST anticipo bimestral	6	2026-06-18	2026-02
377	RST anticipo bimestral	7	2026-06-19	2026-02
378	RST anticipo bimestral	8	2026-06-22	2026-02
379	RST anticipo bimestral	9	2026-06-23	2026-02
380	RST anticipo bimestral	0	2026-06-24	2026-02
381	RST anticipo bimestral	1	2026-07-09	2026-03
382	RST anticipo bimestral	2	2026-07-10	2026-03
383	RST anticipo bimestral	3	2026-07-14	2026-03
384	RST anticipo bimestral	4	2026-07-15	2026-03
385	RST anticipo bimestral	5	2026-07-16	2026-03
386	RST anticipo bimestral	6	2026-07-17	2026-03
387	RST anticipo bimestral	7	2026-07-21	2026-03
388	RST anticipo bimestral	8	2026-07-22	2026-03
389	RST anticipo bimestral	9	2026-07-23	2026-03
390	RST anticipo bimestral	0	2026-07-24	2026-03
391	RST anticipo bimestral	1	2026-09-09	2026-04
392	RST anticipo bimestral	2	2026-09-10	2026-04
393	RST anticipo bimestral	3	2026-09-11	2026-04
394	RST anticipo bimestral	4	2026-09-14	2026-04
395	RST anticipo bimestral	5	2026-09-15	2026-04
396	RST anticipo bimestral	6	2026-09-16	2026-04
397	RST anticipo bimestral	7	2026-09-17	2026-04
398	RST anticipo bimestral	8	2026-09-18	2026-04
399	RST anticipo bimestral	9	2026-09-21	2026-04
400	RST anticipo bimestral	0	2026-09-22	2026-04
401	RST anticipo bimestral	1	2026-11-11	2026-05
402	RST anticipo bimestral	2	2026-11-12	2026-05
403	RST anticipo bimestral	3	2026-11-13	2026-05
404	RST anticipo bimestral	4	2026-11-17	2026-05
405	RST anticipo bimestral	5	2026-11-18	2026-05
406	RST anticipo bimestral	6	2026-11-19	2026-05
407	RST anticipo bimestral	7	2026-11-20	2026-05
408	RST anticipo bimestral	8	2026-11-23	2026-05
409	RST anticipo bimestral	9	2026-11-24	2026-05
410	RST anticipo bimestral	0	2026-11-25	2026-05
411	RST anticipo bimestral	1	2027-01-13	2026-06
412	RST anticipo bimestral	2	2027-01-14	2026-06
413	RST anticipo bimestral	3	2027-01-15	2026-06
414	RST anticipo bimestral	4	2027-01-18	2026-06
415	RST anticipo bimestral	5	2027-01-19	2026-06
416	RST anticipo bimestral	6	2027-01-20	2026-06
417	RST anticipo bimestral	7	2027-01-21	2026-06
418	RST anticipo bimestral	8	2027-01-22	2026-06
419	RST anticipo bimestral	9	2027-01-25	2026-06
420	RST anticipo bimestral	0	2027-01-26	2026-06
421	RST consolidada anual	1	2026-02-16	2025
422	RST consolidada anual	2	2026-02-16	2025
423	RST consolidada anual	3	2026-02-17	2025
424	RST consolidada anual	4	2026-02-17	2025
425	RST consolidada anual	5	2026-02-18	2025
426	RST consolidada anual	6	2026-02-18	2025
427	RST consolidada anual	7	2026-02-19	2025
428	RST consolidada anual	8	2026-02-19	2025
429	RST consolidada anual	9	2026-02-20	2025
430	RST consolidada anual	0	2026-02-20	2025
431	RST consolidada anual	1	2026-04-20	2026-IVA
432	RST consolidada anual	2	2026-04-20	2026-IVA
433	RST consolidada anual	3	2026-04-21	2026-IVA
434	RST consolidada anual	4	2026-04-21	2026-IVA
435	RST consolidada anual	5	2026-04-22	2026-IVA
436	RST consolidada anual	6	2026-04-22	2026-IVA
437	RST consolidada anual	7	2026-04-23	2026-IVA
438	RST consolidada anual	8	2026-04-23	2026-IVA
439	RST consolidada anual	9	2026-04-24	2026-IVA
440	RST consolidada anual	0	2026-04-24	2026-IVA
\.


--
-- Data for Name: tipo_servicio; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tipo_servicio (id_tipo_servicio, nombre_servicio) FROM stdin;
1	Declaración de renta
2	Declaración de IVA
3	Retención en la fuente
4	Contabilidad mensual
5	Nómina
6	Información exógena
7	Medios magnéticos
8	Industria y comercio (ICA)
9	Asesoría
\.


--
-- Name: campo_plantilla_id_campo_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.campo_plantilla_id_campo_seq', 22, true);


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

SELECT pg_catalog.setval('public.tipo_servicio_id_tipo_servicio_seq', 9, true);


--
-- PostgreSQL database dump complete
--

\unrestrict DUwTXrkFdnqTrXsRn5JBpFaUmfsOx5f6TdPaldhuHybmj8JW1NiUfqubDT5GT8v

