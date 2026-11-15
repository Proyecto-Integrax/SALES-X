# Tareas — SALES-X · Gestión de Ventas y Pedidos

**Leyenda:** `[x]` hecha y verificada · `[ ]` pendiente · *(REQ-nn)* requisito que cubre · **Prueba** = evidencia que la verifica.
**Corte:** 14 de noviembre de 2026 · **Resumen:** 51 tareas hechas · 3 pendientes (7.3 TLS, 7.4b servicios reales de INTEGRAX, 7.10b vista móvil/otros navegadores y disponibilidad en operación).

## Fase 1 — Cimientos
- [x] **1.1** Estructura del proyecto, configuración por variables de entorno y `.env.example`. *(REQ-NF-09)*
- [x] **1.2** Modelo de datos ORM (5 tablas, restricciones, índices). *(REQ-01…09)* · Prueba: toda la suite
- [x] **1.3** Scripts SQL PostgreSQL `01_schema.sql` y `02_seed_estados.sql`. · Prueba: suite sobre el esquema creado con el SQL (31/31)
- [x] **1.4** Semilla idempotente de estados y usuarios iniciales. *(REQ-13)*
- [x] **1.5** Zona horaria de negocio (`timeutil`). *(REQ-06, 10)* · Prueba: CP-30, CP-31

## Fase 2 — Seguridad y acceso
- [x] **2.1** Login con JWT y bcrypt; `GET /auth/me`. *(REQ-NF-04)* · CP-02, CP-03
- [x] **2.2** Protección de todos los endpoints; manejo de token inválido. *(REQ-NF-04)* · CP-04, CP-05
- [x] **2.3** Bloqueo tras 5 intentos fallidos. *(REQ-NF-04)* · CP-06
- [x] **2.4** Roles y administración de usuarios (crear, activar/desactivar, contraseña). *(REQ-13)* · CP-07, CP-08
- [x] **2.5** Cabeceras de seguridad y CSP. *(REQ-NF-10)* · CP-27
- [x] **2.6** Validación de arranque en producción y HSTS. *(REQ-NF-09)* · CP-28, CP-29
- [x] **2.7** Registro de errores no controlados sin exponer trazas. *(REQ-NF-04)*

## Fase 3 — Pedidos (núcleo de negocio)
- [x] **3.1** Puerto de catálogo con proveedores simulado y REST. *(REQ-02, 03, 11)* · CP-09
- [x] **3.2** Registrar pedido con consolidación de líneas y precio del catálogo. *(REQ-01, 02, 03)* · CP-10…CP-13
- [x] **3.3** Cálculo de subtotal, impuestos y total. *(REQ-07)* · CP-10, CP-12, CP-16
- [x] **3.4** Consultar, filtrar y paginar pedidos. *(REQ-06)* · CP-14
- [x] **3.5** Historial por cliente. *(REQ-09)* · CP-15
- [x] **3.6** Modificar pedido. *(REQ-04)* · CP-16, CP-19
- [x] **3.7** Máquina de estados y cambio de estado. *(REQ-08)* · CP-17, CP-18
- [x] **3.8** Cancelar pedido con motivo. *(REQ-05)* · CP-19, CP-20
- [x] **3.9** Auditoría de todas las operaciones. *(REQ-NF-05)* · CP-21

## Fase 4 — Reportes e integración
- [x] **4.1** Reporte de ventas por día/mes excluyendo cancelados. *(REQ-10)* · CP-22, CP-23
- [x] **4.2** Exportación CSV. *(REQ-10)* · CP-23
- [x] **4.3** Servicios `/integracion/*` con API Key. *(REQ-12)* · CP-24
- [x] **4.4** Solicitudes del cliente (202, auditadas, sin alterar el pedido). *(REQ-12)* · CP-25
- [x] **4.5** `GET /health`. *(REQ-NF-03)* · CP-01

## Fase 5 — Interfaz web
- [x] **5.1** Inicio de sesión y navegación por rol. *(REQ-NF-04, 13)*
- [x] **5.2** Panel con indicadores, estados y solicitudes. *(REQ-06, 10, 12)*
- [x] **5.3** Lista de pedidos con filtros y paginación. *(REQ-06)*
- [x] **5.4** Nuevo/modificar pedido con vista previa de totales y bloqueo de agotados. *(REQ-01…04, 07, 11)*
- [x] **5.5** Detalle con cambio de estado, cancelación y auditoría. *(REQ-05, 08)*
- [x] **5.6** Reportes con CSV e impresión. *(REQ-10)*
- [x] **5.7** Gestión de usuarios (crear, contraseña, activar). *(REQ-13)*
- [x] **5.8** Recorrido manual con CSP activa, sin errores de consola. *(REQ-NF-10)*

## Fase 6 — Calidad, rendimiento y operación
- [x] **6.1** Suite de 63 pruebas automatizadas (31 base + 15 de endurecimiento + 14 de integración REST + 3 de concurrencia). · SQLite 60/60 (+3 omitidas)
- [x] **6.2** Misma suite sobre **PostgreSQL 18.6** con protección `*_test`. *(REQ-NF-07)* · 63/63; las 46 anteriores también sobre el esquema creado con `sql/01`+`02`
- [x] **6.3** Prueba de carga (SQLite y PostgreSQL). *(REQ-NF-01)* · p95 = 0,092 s (20 usuarios), 0,359 s (50)
- [x] **6.4** Auditoría de dependencias (`pip-audit`). · sin vulnerabilidades conocidas
- [x] **6.5** `Dockerfile`, `docker-compose.yml`, `iniciar.bat`, datos de demostración.
- [x] **6.6** Documentación formal (E1–E7, informes 01–05, capacidad, manuales) y generador de PDF.

## Fase 7 — Pendientes para producción
> Origen: `docs/02-Plan-de-Remediacion.md` y `docs/05-Revision-Lanzamiento-GO-NO-GO.md`. **P0** bloquea producción.

- [x] **7.1 (P0)** Ejecutar `docker compose up --build` y verificar `/health`. *(REQ-NF-07)* · Hecho (14/11/2026) con Docker Desktop 4.99 en modo producción: arranque desde cero *healthy* en ≈ 27 s, rol creado por `docker/03_aplicar_rol_app.sh`, humo 19/19, carga sin errores (p95 = 0,13 s con 20 usuarios), persistencia y restauración (E7 §5.7). **Repetir en el servidor de despliegue.**
- [x] **7.1b** Corregir `sql/03` (DEF-03): sin permisos por defecto sobre tablas futuras, para que `pg_restore --clean` no devuelva `UPDATE`/`DELETE` sobre la auditoría. · Detectado y verificado en Docker; la migración 04 concede permisos solo a sus tablas nuevas.
- [x] **7.2 (P0)** Aplicar `sql/03_rol_aplicacion.sql` y conectar la API con el rol `salesx_app`; comprobar que `UPDATE auditoria_pedido` es denegado. *(REQ-NF-05, H-13)* · Hecho en desarrollo (14/11/2026): 9/9 permisos correctos y 11/11 pasos de la API con ese rol; `.env` usa `salesx_app`. **Aplicar en el entorno objetivo** (con `docker-compose` lo hace `docker/03_aplicar_rol_app.sh`, aún sin ejecutar).
- [ ] **7.3 (P0)** Publicar detrás de proxy inverso con TLS y verificar HSTS. *(REQ-NF-04, H-09)*
- [x] **7.4a** Servicios simulados de Clientes y Productos (`mocks/integrax_mock.py`, `docker-compose.mock.yml`) y pruebas del adaptador REST. *(REQ-02, 03, 11, 12)* · 14 pruebas (CP-47…CP-60) y 14/14 en Docker con tres contenedores, apagado/encendido del servicio externo incluidos.
- [x] **7.4a2** Correcciones halladas por esas pruebas: respuestas inválidas del servicio → 502 y no 500 (DEF-04); cliente HTTP persistente, de 185 ms a 0,9 ms por consulta (DEF-05).
- [ ] **7.4b (P0)** Conectar y probar con los servicios **reales** de Clientes y Productos cuando existan (`CATALOGO_PROVIDER=rest`); ajustar el contrato si difiere. *(REQ-02, 03, 11)*
- [x] **7.5 (P0)** Probar la restauración de una copia de seguridad (`pg_dump`/`pg_restore`). *(REQ-NF-03)* · Hecho en desarrollo (14/11/2026): respaldo de `salesx` restaurado en otra base; 7 tablas con las mismas filas, mismo total de pedidos y mismas huellas MD5. **Repetir en el entorno objetivo.**
- [x] **7.6 (P1)** Bloqueo de login compartido en la BD (tabla `intento_login`). *(REQ-14 · H-04)* · `test_fallos_de_login_quedan_en_la_bd_y_bloquean`, `test_login_correcto_borra_los_fallos`
- [x] **7.7 (P1)** Claves de integración por consumidor, con hash, expiración, revocación y último uso; endpoints `/consumidores` y pantalla *Integraciones*. *(REQ-15 · H-06)* · 5 pruebas en `test_endurecimiento.py`
- [x] **7.8 (P1)** Sesión en cookie `HttpOnly; SameSite=Strict` (`Secure` en producción) + CSRF *double-submit*; la interfaz ya no guarda el token. *(REQ-16 · H-05)* · 4 pruebas + recorrido en navegador
- [x] **7.9 (P1)** Política de contraseñas, cambio por el propio usuario y cambio obligatorio en primer ingreso/restablecimiento. *(REQ-17 · H-07)* · 4 pruebas + recorrido en navegador
- [x] **7.9b** Migración `sql/04_migracion_v1_1.sql` para bases v1.0. · Probada sobre una base con 40 pedidos: se conservan y es idempotente.
- [x] **7.10a** Revisión visual de la interfaz en escritorio, servida por Docker. · Hecha por el usuario el 14/11/2026: conforme.
- [ ] **7.10b (P2)** Revisión visual de la interfaz (responsive/oscuro) en los navegadores objetivo y medición de disponibilidad en operación. *(REQ-NF-03)*

## Cómo se actualiza este archivo
Al terminar una tarea: marque `[x]`, anote la prueba que la verifica y actualice el resumen y, si cambia el estado de un requisito, `requirements.md` y `docs/E6`.
- [x] **8.1** Bloqueo de fila (SELECT … FOR UPDATE) en modificar, cambiar de estado y cancelar. *(H-14, DEF-07, REQ-05, 08)* · CP-61…CP-63 (30 rondas cada una sobre PostgreSQL; antes del arreglo fallaban 29 de 30).
- [x] **8.2** Interfaz sin desbordamiento horizontal en móvil. *(DEF-06)* · Verificado a 390 px en 4 páginas.
- [x] **8.3** Documentación en el formato del proyecto de referencia (E1–E7, acta, 01, 03, 04, 05, capacidad) generada con scripts desde el código. · scripts/verificar_documentacion.py.
