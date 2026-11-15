---
codigo: SALESX-E6
evidencia: 6 de 7
titulo: Matriz de trazabilidad
descripcion: Relaciona cada requisito con su origen, su diseño, su implementación y la prueba que lo verifica. Permite responder a dos preguntas clave: si un requisito está construido y si algo construido responde a un requisito.
metadatos:
  - Sistema | SALES-X · Gestión de ventas y pedidos
  - Historias de usuario trazadas | 17
  - Requisitos funcionales | 17
  - Requisitos no funcionales | 27
  - Casos de prueba de control | 63 (Evidencia 7)
  - Pruebas citadas y verificadas | 63 de 63
pie: SALES-X · Evidencia 6 de 7 · Matriz de trazabilidad · 17 historias, 17 requisitos funcionales y 63 pruebas verificadas. Pruebas citadas contrastadas contra el código real.
---

# 1. Para qué sirve la trazabilidad

Un proyecto puede tener buen código y buenos requisitos y, aun así, fallar en lo esencial: que lo uno corresponda a lo otro. La trazabilidad es la herramienta que lo comprueba. Sirve para responder:

- **¿Todo requisito está construido y probado?** Se recorre la matriz de izquierda a derecha: si un requisito no tiene implementación ni prueba, queda a la vista.
- **¿Todo lo construido responde a un requisito?** Se recorre al revés: si aparece una funcionalidad sin requisito, es alcance no deseado o falta documentar.
- **Si algo cambia, ¿qué se ve afectado?** Sabiendo qué requisito toca a qué pantalla, tabla y prueba, se puede medir el impacto de un cambio.

# 2. La cadena de trazabilidad del proyecto

Cada eslabón apunta a un archivo del repositorio o a una prueba de la Evidencia 7. Ejemplo con la historia **HU-05** (gestionar el estado de un pedido):

| Eslabón | Contenido | Referencia |
|---|---|---|
| **Historia de usuario** | «Como vendedor, quiero avanzar el estado del pedido para reflejar su ciclo de vida». | HU-05 |
| ↓ **Requisito funcional** | «Solo transiciones válidas; 409 si no lo son; se audita cada cambio». | RF-08 |
| ↓ **Caso de uso** | Gestionar estados del pedido. | CU-09 |
| ↓ **Diseño de datos** | `pedido.estado_id` → `estado_pedido`; `auditoria_pedido` (Evidencias 1 y 2). | MER |
| ↓ **Implementación** | `PATCH /api/v1/pedidos/{id}/estado` → `app/services/pedidos.py` (`TRANSICIONES`, `cambiar_estado`). Pantalla: detalle del pedido. | `app/` |
| ↓ **Prueba de integración** | «Transición inválida → 409»; «dos acciones simultáneas respetan la máquina de estados». | CP-18, CP-61 |
| ↓ **Requisito no funcional** | Integridad en concurrencia; auditoría; mínimo privilegio. | RNF-19, RNF-05, RNF-18 |

# 3. Matriz principal

Cada fila es una historia de usuario y recorre la cadena completa. La columna «Clase» cita las clases del diagrama de clases (`Pedido`, `DetallePedido`, `EstadoPedido`, `AuditoriaPedido`) y las que se añadieron en la implementación (`Vendedor`, `IntentoLogin`, `ConsumidorApi`, `CatalogoClient`, `Settings`). La columna «Prueba» cita casos de la Evidencia 7, y el generador de verificación contrasta cada uno contra las pruebas realmente definidas en `tests/`.

| Historia | Épica | Requisitos | Caso de uso | Clase | Endpoint (API) | Pantalla | Entidades | Prueba | RNF |
|---|---|---|---|---|---|---|---|---|---|
| HU-01 Registrar un pedido | Pedidos | RF-01, RF-02, RF-03, RF-07 | CU-01, CU-02, CU-03, CU-04 | `Pedido`, `DetallePedido`, `EstadoPedido` | `POST /pedidos` | Nuevo pedido | `pedido`, `detalle_pedido`, `estado_pedido` | CP-10, CP-11, CP-12, CP-13 | RNF-20, RNF-21 |
| HU-02 Modificar un pedido | Pedidos | RF-04 | CU-06 | `Pedido`, `DetallePedido` | `PUT /pedidos/{id}` | Detalle → Modificar | `pedido`, `detalle_pedido`, `auditoria_pedido` | CP-16, CP-63 | RNF-19 |
| HU-03 Cancelar un pedido | Pedidos | RF-05 | CU-07 | `Pedido`, `AuditoriaPedido` | `POST /pedidos/{id}/cancelar` | Detalle → Cancelar | `pedido`, `auditoria_pedido` | CP-19, CP-20, CP-62 | RNF-19 |
| HU-04 Consultar pedidos | Pedidos | RF-06 | CU-08 | `Pedido` | `GET /pedidos`, `GET /pedidos/{id}` | Pedidos, Panel | `pedido` | CP-14 | RNF-01 |
| HU-05 Gestionar el estado | Pedidos | RF-08 | CU-09 | `Pedido`, `EstadoPedido`, `AuditoriaPedido` | `PATCH /pedidos/{id}/estado`, `GET /estados` | Detalle | `pedido`, `estado_pedido`, `auditoria_pedido` | CP-17, CP-18, CP-61 | RNF-19 |
| HU-06 Ver el historial de un cliente | Pedidos | RF-09 | CU-10 | `Pedido` | `GET /pedidos/historial/{cliente_id}` | Pedidos (filtro por cliente) | `pedido` | CP-15 | — |
| HU-07 Generar el reporte de ventas | Reportes | RF-10 | CU-12 | `Pedido` | `GET /reportes/ventas`, `/ventas.csv` | Reportes | `pedido` | CP-22, CP-23, CP-30, CP-31 | RNF-01, RNF-15 |
| HU-08 Consultar disponibilidad | Catálogo | RF-11 | CU-11 | `CatalogoClient` | `GET /catalogo/productos/{id}/disponibilidad` | Nuevo pedido | (servicio externo) | CP-09, CP-57, CP-58 | RNF-23 |
| HU-09 Atender sistemas externos | Integración | RF-12 | CU-13, CU-05 | `AuditoriaPedido`, `ConsumidorApi` | `GET/POST /integracion/*` | Panel (solicitudes) | `auditoria_pedido`, `consumidor_api` | CP-24, CP-25, CP-58 | RNF-04 |
| HU-10 Administrar usuarios | Administración | RF-13 | — | `Vendedor` | `GET/POST/PATCH /vendedores` | Usuarios | `vendedor` | CP-07, CP-08 | RNF-13 |
| HU-11 Resistir intentos de acceso | Seguridad | RF-14 | — | `IntentoLogin` | `POST /auth/login` | Inicio de sesión | `intento_login` | CP-06, CP-32, CP-33 | RNF-12 |
| HU-12 Dar una clave a cada sistema | Integración | RF-15 | CU-13 | `ConsumidorApi` | `GET/POST/PATCH /consumidores` | Integraciones | `consumidor_api` | CP-34 a CP-38 | RNF-17 |
| HU-13 Proteger la sesión | Seguridad | RF-16 | — | `Vendedor` | `POST /auth/login`, `/auth/logout` | Inicio de sesión | — | CP-39 a CP-42 | RNF-10, RNF-11 |
| HU-14 Gestionar mi contraseña | Seguridad | RF-17 | — | `Vendedor` | `POST /auth/cambiar-contrasena` | Cambio de contraseña | `vendedor` | CP-43 a CP-46 | RNF-09 |
| HU-15 Seguir funcionando si Clientes o Productos fallan | Integración | RF-02, RF-03, RF-11 | CU-02, CU-03, CU-11 | `CatalogoClient` | (adaptador interno) | — | — | CP-47 a CP-60 | RNF-21, RNF-23 |
| HU-16 Conservar una auditoría inmutable | Seguridad | RF-08 (auditoría) | — | `AuditoriaPedido` | `GET /pedidos/{id}/auditoria` | Detalle | `auditoria_pedido` | CP-21 y permisos del rol (Evid. 7 §7.2) | RNF-05, RNF-18 |
| HU-17 Operar con seguridad en producción | Seguridad | — | — | `Settings` | arranque de la aplicación | — | — | CP-26, CP-27, CP-28, CP-29 | RNF-14, RNF-15, RNF-16 |

**Correspondencia entre casos de control y pruebas ejecutadas.** Cada caso de control de la Evidencia 7 corresponde a una función de prueba de `tests/`:

| Caso | Prueba | Caso | Prueba |
|---|---|---|---|
| CP-01 | `test_health` | CP-33 | `test_login_correcto_borra_los_fallos` |
| CP-02 | `test_login_ok_y_me` | CP-34 | `test_consumidor_clave_se_muestra_una_vez_y_se_usa` |
| CP-03 | `test_login_incorrecto` | CP-35 | `test_consumidor_desactivado_y_reactivado` |
| CP-04 | `test_endpoints_protegidos_sin_token` | CP-36 | `test_consumidor_expirado_no_autentica` |
| CP-05 | `test_token_manipulado` | CP-37 | `test_consumidores_validaciones_y_permisos` |
| CP-06 | `test_bloqueo_por_intentos_fallidos` | CP-38 | `test_clave_invalida_da_mensaje_generico_y_existe_el_consumidor_inicial` |
| CP-07 | `test_vendedor_no_administra_usuarios` | CP-39 | `test_login_fija_cookie_httponly_y_cookie_csrf_legible` |
| CP-08 | `test_admin_crea_usuario` | CP-40 | `test_con_cookie_las_escrituras_exigen_csrf` |
| CP-09 | `test_catalogo_y_disponibilidad` | CP-41 | `test_bearer_no_necesita_csrf` |
| CP-10 | `test_crear_pedido_calcula_totales` | CP-42 | `test_logout_elimina_la_sesion` |
| CP-11 | `test_precio_se_toma_del_catalogo_no_del_cliente` | CP-43 | `test_politica_de_contrasenas` |
| CP-12 | `test_lineas_repetidas_se_consolidan` | CP-44 | `test_usuario_nuevo_debe_cambiar_su_contrasena` |
| CP-13 | `test_validaciones_de_entrada` | CP-45 | `test_admin_que_restablece_la_clave_obliga_a_cambiarla` |
| CP-14 | `test_consultar_y_filtrar` | CP-46 | `test_cambio_de_contrasena_tambien_se_bloquea_por_intentos` |
| CP-15 | `test_historial_cliente` | CP-47 | `test_lista_y_obtiene_clientes_y_productos` |
| CP-16 | `test_modificar_pedido` | CP-48 | `test_inexistente_devuelve_none` |
| CP-17 | `test_flujo_de_estados_valido` | CP-49 | `test_servicio_caido_da_502` |
| CP-18 | `test_transiciones_invalidas` | CP-50 | `test_error_500_del_servicio_da_502` |
| CP-19 | `test_cancelar_y_reglas_posteriores` | CP-51 | `test_timeout_da_502_y_no_se_cuelga` |
| CP-20 | `test_no_cancela_pedido_enviado` | CP-52 | `test_respuesta_invalida_da_502_y_no_error_interno[malformado]` |
| CP-21 | `test_auditoria_registra_cada_operacion` | CP-53 | `test_respuesta_invalida_da_502_y_no_error_interno[no_json]` |
| CP-22 | `test_reporte_ventas_excluye_cancelados` | CP-54 | `test_pedido_con_precios_y_existencias_del_servicio_externo` |
| CP-23 | `test_reporte_csv_y_agrupacion_mensual` | CP-55 | `test_precio_con_decimales_se_calcula_exacto` |
| CP-24 | `test_integracion_requiere_api_key` | CP-56 | `test_reglas_de_negocio_con_datos_externos` |
| CP-25 | `test_solicitud_del_cliente_queda_auditada` | CP-57 | `test_las_existencias_se_leen_en_vivo_sin_cache` |
| CP-26 | `test_sql_injection_en_filtros_no_rompe` | CP-58 | `test_catalogo_y_integracion_reflejan_el_servicio_externo` |
| CP-27 | `test_cabeceras_de_seguridad` | CP-59 | `test_servicio_externo_caido_no_crea_pedidos_y_responde_502` |
| CP-28 | `test_produccion_rechaza_configuracion_insegura` | CP-60 | `test_respuesta_invalida_del_servicio_da_502_en_la_api` |
| CP-29 | `test_produccion_acepta_configuracion_robusta` | CP-61 | `test_enviar_y_cancelar_a_la_vez_no_rompen_la_maquina_de_estados` |
| CP-30 | `test_rango_diario_en_zona_de_negocio_colombia` | CP-62 | `test_dos_cancelaciones_simultaneas_solo_una_prospera` |
| CP-31 | `test_to_local_acepta_fecha_sin_zona_de_sqlite` | CP-63 | `test_modificar_y_cancelar_a_la_vez_no_deja_un_pedido_cancelado_modificado` |
| CP-32 | `test_fallos_de_login_quedan_en_la_bd_y_bloquean` | | |

# 4. Trazabilidad inversa: requisitos sin historia de usuario directa

Los requisitos no funcionales no nacen de una historia concreta sino de atributos de calidad; esta sección evita que parezcan «huérfanos». RNF-02 (API REST), RNF-03 (disponibilidad), RNF-06 (escalabilidad), RNF-07 (portabilidad de plataforma), RNF-08 (documentación), RNF-22 (usabilidad), RNF-24 a RNF-27 (pruebas, despliegue, respaldo y licencias) son transversales: se verifican en la tabla de la sección 5, no en una historia.

Además, **no existe funcionalidad sin requisito**: cada endpoint del inventario del informe de auditoría (30 operaciones) aparece en la columna «Endpoint» de la matriz, y cada tabla del MER aparece en «Entidades».

# 5. Trazabilidad de requisitos no funcionales

| RNF | Atributo | Mecanismo que lo cumple | Dónde se verifica |
|---|---|---|---|
| RNF-01 | Rendimiento | Consultas indexadas, paginación, cliente HTTP persistente | Prueba de carga · Evidencia 7 §7.1 |
| RNF-02 | Portabilidad | API REST/JSON con OpenAPI | `/docs` · todas las pruebas |
| RNF-03 | Disponibilidad | `/health`, `restart: unless-stopped`, *healthcheck* | CP-01 · Evidencia 7 §7.3 (la medición real es en operación) |
| RNF-04 | Seguridad | Autenticación obligatoria en cada endpoint | CP-02 a CP-05, CP-24 |
| RNF-05 | Integridad | Tabla de auditoría de solo-agregar | CP-21 · permisos del rol |
| RNF-06 | Escalabilidad | API sin estado; bloqueo de login en la BD | CP-32 |
| RNF-07 | Portabilidad | Python + ORM + Docker | Evidencia 7 §3 y §7.3 |
| RNF-08 | Documentación | Evidencias 1 a 7 y verificación documentación-código | Script `verificar_documentacion.py` |
| RNF-09 | Seguridad | bcrypt (coste 12) y política de contraseñas | CP-43, CP-44 |
| RNF-10 | Seguridad | Cookie `HttpOnly`, `SameSite=Strict`, `Secure` | CP-39 |
| RNF-11 | Seguridad | CSRF *double submit* | CP-40, CP-41 |
| RNF-12 | Seguridad | Contador de fallos en la BD, ventana de 5 minutos | CP-06, CP-32, CP-46 |
| RNF-13 | Seguridad | Dependencias `current_user` y `require_admin` | CP-07, CP-37 |
| RNF-14 | Seguridad | `validate_for_production` al arrancar | CP-28, CP-29 |
| RNF-15 | Seguridad | Middleware de cabeceras (CSP, HSTS, `nosniff`) | CP-27 |
| RNF-16 | Seguridad | ORM parametrizado, Pydantic, escape de salida | CP-26 |
| RNF-17 | Seguridad | Hash SHA-256 de claves, revocación y expiración | CP-34 a CP-38 |
| RNF-18 | Seguridad | Rol de BD `salesx_app` | Evidencia 7 §7.2 |
| RNF-19 | Integridad | `SELECT … FOR UPDATE` en operaciones que modifican | CP-61 a CP-63 |
| RNF-20 | Precisión | `NUMERIC(14,2)` y redondeo half-up | CP-10, CP-55 |
| RNF-21 | Integridad | Transacción única por operación, incluida la auditoría | CP-59 |
| RNF-22 | Usabilidad | Español, COP, hora de Colombia, diseño adaptable | Capturas · Evidencia 7 §9 |
| RNF-23 | Resiliencia | Adaptador REST con 502, tiempo máximo y recuperación | CP-49 a CP-53, CP-59, CP-60 |
| RNF-24 | Mantenibilidad | Suite de pruebas ejecutable | Evidencia 7 completa |
| RNF-25 | Portabilidad | `iniciar.bat` y `docker compose up` | Evidencia 7 §7.3 |
| RNF-26 | Datos | `pg_dump` / `pg_restore` documentados | Evidencia 7 §7.3 |
| RNF-27 | Licenciamiento | Análisis de licencias de las dependencias | Evidencia 4 |

# 6. Cobertura

**17** historias trazadas · **17** requisitos funcionales · **63** pruebas ejecutadas · **63** aprobadas · **0** fallidas

**Cobertura de la trazabilidad**

- **17 de 17** historias de usuario están trazadas hasta una prueba ejecutada.
- Los **17 requisitos funcionales** están implementados y cubiertos por la suite de integración.
- **No existe funcionalidad sin requisito:** el sistema no implementa nada que no esté especificado en la Evidencia 3, y lo que no se implementó figura allí como fuera de alcance.
- Toda la cadena es verificable por un tercero: cada eslabón apunta a un archivo del repositorio o a una prueba de la Evidencia 7.
- **Límite declarado:** el RNF-03 (disponibilidad ≥ 95 %) solo puede medirse con el sistema funcionando un tiempo; las pruebas verifican los mecanismos (salud, reinicio, persistencia), no el porcentaje.

# 7. Cómo mantener esta matriz

- Si se añade un requisito, se añade su fila aquí y su caso de prueba en la suite.
- Si se añade una prueba, se cita en la tabla de correspondencia; el script de verificación **avisa si una prueba citada no existe o si existe una prueba que ningún caso cita**, de modo que la matriz no puede desactualizarse en silencio.
- Si se cambia una tabla, hay que revisar las filas que la mencionan y regenerar las Evidencias 1 y 2.

```
# Verificar que la documentación coincide con el programa
python scripts/verificar_documentacion.py

# Regenerar los fragmentos y los documentos
python scripts/generar_diccionario.py
python scripts/generar_fragmentos.py --con-pruebas
python scripts/generar_pdf.py
python scripts/generar_word.py
```
