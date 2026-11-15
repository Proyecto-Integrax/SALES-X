# Revisión de lanzamiento · SALES-X 1.2.0

**Comité de revisión de lanzamiento (simulado por el equipo, con cuatro perspectivas: QA, DevOps, Tech Lead y Product Owner)**
**Aplicación:** SALES-X · gestión de ventas y pedidos (microproyecto de INTEGRAX)
**Fecha:** 14 de noviembre de 2026
**Versión evaluada:** 1.2.0
**Stack real:** Python 3.12 · FastAPI · SQLAlchemy 2 · PostgreSQL 16 · interfaz en JavaScript puro · Docker Compose
**Despliegue real previsto:** Docker Compose en un único host con un proxy inverso con TLS (aún no existe). **No** se usa nube gestionada.
**Evidencia base:** suite de 63 pruebas (Evidencia 7), auditoría de 14 hallazgos y su remediación (documentos 01 y 04), y verificación en Docker en modo producción.

> **Veredicto anticipado: GO para demostración, entrega académica y piloto en red interna; NO-GO para producción expuesta a Internet.** El producto está funcionalmente completo y bien probado, pero faltan elementos de despliegue que no se pueden resolver desde un equipo de desarrollo: TLS, límites de tasa, servidor real, y los servicios reales de Clientes y Productos. El detalle y las condiciones para el GO están al final.

---

# 1. QA Engineer — Control de calidad

## 1.1 Smoke tests (15–20 minutos, obligatorios en cada despliegue)

| ID | Flujo | Pasos | Resultado esperado | Estado en este lanzamiento |
|---|---|---|---|---|
| S-01 | Salud | `GET /health` | `{"status":"ok","database":"ok"}` | ✅ Docker |
| S-02 | Cabeceras de producción | Revisar la respuesta de `/health` | HSTS, CSP, `nosniff` presentes | ✅ Docker |
| S-03 | Primer ingreso | Iniciar sesión con una cuenta nueva | 200; toda la API responde 403 hasta cambiar la contraseña | ✅ Docker |
| S-04 | Cambio de contraseña | Actual + nueva de 10+ con letras y números | 204; la anterior ya no sirve | ✅ |
| S-05 | Pedido | Cliente + 2 productos | 201; subtotal, IVA 19 % y total exactos | ✅ Docker |
| S-06 | Disponibilidad | Pedir más que las existencias | 409 y no se crea el pedido | ✅ Docker |
| S-07 | Estados | Confirmar y luego saltar a «Entregado» | 200 y luego 409 con las transiciones permitidas | ✅ Docker |
| S-08 | Cancelación | Cancelar con motivo; cancelar de nuevo | 200 y luego 409 | ✅ |
| S-09 | Doble clic | Dos cancelaciones simultáneas | Una 200 y una 409; **un solo** registro de auditoría | ✅ PostgreSQL (CP-62) |
| S-10 | Auditoría | Ver la auditoría del pedido | CREAR, CAMBIO_ESTADO… con autor y hora | ✅ |
| S-11 | Reporte | Ventas del mes y CSV | Totales; sin cancelados | ✅ |
| S-12 | Integración | Consultar un pedido con la clave inicial; sin clave | 200; 401 | ✅ Docker |
| S-13 | Solicitud del cliente | Solicitar cancelación por integración | 202; el pedido **no** cambia; queda auditada | ✅ Docker |
| S-14 | Servicio externo caído | Apagar Clientes/Productos y registrar un pedido | 502 y ningún pedido a medias; al volver, se recupera solo | ✅ Docker (REST) |
| S-15 | Rol de BD | `UPDATE` sobre la auditoría como `salesx_app` | *permission denied* | ✅ Docker |
| S-16 | Respaldo | `pg_dump` y `pg_restore --clean` | Datos recuperados y rol sin poder editar la auditoría | ✅ Docker |
| S-17 | Móvil | Abrir el panel a 390 px | Sin desplazamiento horizontal; menú y tarjetas visibles | ✅ (tras DEF-06) |
| S-18 | HTTPS | Acceder por HTTPS y mantener la sesión | Cookie `Secure` enviada | ⛔ **No verificable:** no existe el proxy TLS |

## 1.2 Pruebas de aceptación (UAT) críticas

### UAT-01 · Cálculo de IVA y redondeo
**Datos:** IVA 19 %, redondeo half-up a 2 decimales, importes calculados con el código real (`Pedido.calcular_total`).

| Caso | Subtotal | IVA | Total | Criterio |
|---|---:|---:|---:|---|
| Laptop 2.850.000 × 1 | 2.850.000,00 | 541.500,00 | 3.391.500,00 | Exacto |
| Mouse 55.000 × 3 | 165.000,00 | 31.350,00 | 196.350,00 | Exacto (CP-10) |
| Laptop × 1 + Mouse × 2 | 2.960.000,00 | 562.400,00 | 3.522.400,00 | Suma de líneas |
| 333,33 × 3 | 999,99 | 189,9981 → **190,00** | 1.189,99 | Redondeo hacia arriba |
| 10,05 × 1 | 10,05 | 1,9095 → **1,91** | 11,96 | Sin error binario |
| 45.500,50 × 3 | 136.501,50 | 25.935,285 → **25.935,29** | 162.436,79 | Mitad hacia arriba (CP-55) |
| 0,10 × 3 | 0,30 | 0,057 → **0,06** | 0,36 | Sin acumular error de coma flotante |
| 19.999,99 × 7 | 139.999,93 | 26.599,9867 → **26.599,99** | 166.599,92 | Cifras grandes |
| 0,01 × 1 | 0,01 | 0,0019 → **0,00** | 0,01 | Importe mínimo |

**Debe verificarse además:** que la suma de las líneas coincida con el subtotal del pedido, que la vista previa de la pantalla «Nuevo pedido» coincida con lo que persiste el servidor (ocurre en la prueba manual y en las capturas), y que el redondeo sea **siempre el mismo** (política única en el servidor).

### UAT-02 · Estados y auditoría
- Recorrer *Pendiente → Confirmado → En preparación → Enviado → Entregado*: cada paso añade un evento `CAMBIO_ESTADO` con el estado anterior y el nuevo.
- Intentar saltarse un estado, volver atrás o salir de un estado final: **409** con la lista de transiciones permitidas.
- **Criterio:** la auditoría cuenta exactamente la historia del pedido, sin huecos ni eventos duplicados.

### UAT-03 · Modificación y cancelación
- Modificar un pedido *Pendiente*: se recalculan totales y se audita el total anterior y el nuevo.
- Intentar modificar uno *En preparación*: 409.
- Cancelar con motivo desde *Pendiente*, *Confirmado* o *En preparación*; intentar cancelar uno *Enviado* o *Entregado*: 409.

### UAT-04 · Roles y aislamiento
- El **vendedor** no ve *Usuarios* ni *Integraciones*; la API le responde 403.
- El **administrador** crea un usuario: este debe cambiar su contraseña antes de operar.
- Una **clave de integración revocada** o **expirada** responde 401.
- Un **JWT** no sirve en los servicios de integración, ni una API Key en los de usuario.

### UAT-05 · Reportes
- Rango de fechas en hora de Colombia: un pedido de las 23:48 aparece en su día (no en el siguiente).
- Las ventas **excluyen** los cancelados; el total del reporte coincide con la suma de los pedidos activos del período.
- El CSV abre en Excel (con BOM UTF-8) y respeta el rango.

### UAT-06 · Operación
- Respaldo y restauración en una base nueva: mismas filas, mismo total, misma auditoría.
- Tras restaurar, el rol de la API **sigue sin poder** modificar la auditoría.
- Reinicio de los contenedores: los datos persisten.

## 1.3 Pruebas de concurrencia (obligatorias)

| Escenario | Qué se prueba | Resultado |
|---|---|---|
| «Enviado» y «Cancelar» simultáneos sobre el mismo pedido | Exactamente una prospera; la cadena de estados es válida | ✅ 30 rondas (CP-61). **Antes del bloqueo de fila fallaban 29 de 30.** |
| Dos cancelaciones simultáneas | Una 200, una 409; un solo registro de auditoría | ✅ 30 rondas (CP-62) |
| Modificar y cancelar a la vez | Un pedido cancelado no queda modificado | ✅ 30 rondas (CP-63) |
| 20–50 usuarios concurrentes con mezcla de lectura y escritura | Sin errores; p95 dentro del RNF-01 | ✅ 0 errores en 1.500 peticiones |

**Límite:** estas pruebas solo son representativas en PostgreSQL; en SQLite (demostración) el bloqueo de fila no existe y se omiten.

## 1.4 Pruebas que hoy **no existen** y deben añadirse

| Prueba | Por qué falta | Prioridad |
|---|---|---|
| Medición de **disponibilidad** durante semanas (RNF-03) | Requiere el sistema funcionando | Alta, en operación |
| Carga **sostenida** (horas) y de pico | Solo se hicieron ráfagas de 500–1.500 peticiones | Media |
| Integración con los servicios **reales** de Clientes y Productos | No existen todavía | **Alta** |
| Verificación de **TLS**, redirección y cookie `Secure` extremo a extremo | No hay proxy | **Alta** |
| Límites de tasa y de tamaño de petición | Dependen del proxy | Media |
| Prueba **automática** de «un administrador no puede desactivarse a sí mismo» | La regla está en el código, sin prueba | Media |
| Pruebas de **interfaz automatizadas** | La UI se probó con recorridos y capturas, no con una suite | Media |
| Otros navegadores (Chrome, Firefox, Safari) | Solo se revisó Edge | Baja |
| Ejecución en un **servidor Linux** de despliegue | Solo se probó en contenedores sobre Windows | Alta |
| Prueba de fallo de **PostgreSQL** a mitad de una operación | No simulada | Media |

---

# 2. DevOps / Cloud Engineer

## 2.1 Checklist de despliegue (estado real del proyecto)

| Elemento | Estado | Observación |
|---|:---:|---|
| Imagen Docker sin privilegios de root | ✅ | Usuario `salesx` (uid 10001) |
| *Healthcheck* y reinicio automático | ✅ | Verificado: contenedores *healthy* en ≈ 27 s |
| Secretos solo por variables de entorno | ✅ | `.env.docker` generado al azar; no se sube a Git |
| El sistema se niega a arrancar con configuración insegura | ✅ | CP-28, CP-29 |
| Base de datos sin puerto publicado | ✅ | Solo la API accede |
| Rol de BD de mínimo privilegio | ✅ | Se crea al inicializar; **aplicar** en la base real |
| Migraciones | 🟡 | Scripts SQL idempotentes (`sql/04`), pero **sin herramienta de versionado de esquema** (ver Tech Lead) |
| Respaldo y restauración | ✅ | Procedimiento probado; **falta automatizarlo** (cron) y llevarlo fuera del servidor |
| Registros | 🟡 | A salida estándar (`docker compose logs`); sin agregador |
| Monitoreo y alertas | ⛔ | No existe |
| **TLS / proxy inverso** | ⛔ | **Bloqueante** (H-09) |
| Límites de tasa y tamaño, `/docs` oculto | ⛔ | H-10, H-08 |
| CI/CD | ⛔ | No hay integración continua |
| Varias réplicas de la API | 🟡 | El diseño lo permite (sin estado, bloqueo en BD); **no se probó** |
| Plan de retorno (*rollback*) | ✅ | Imagen anterior + respaldo previo (ver 2.2) |

## 2.2 Requisitos mínimos antes de producción

1. Proxy inverso con TLS, HSTS y redirección a HTTPS; límites de tasa y tamaño; `/docs` no público.
2. Aplicar `sql/03_rol_aplicacion.sql` en la base real y usar `salesx_app`.
3. Respaldos automáticos diarios, con una restauración de prueba en el servidor real.
4. Repetir la suite, la carga y la restauración **en el servidor de despliegue** (Linux).
5. Monitoreo mínimo: `/health`, errores 5xx, espacio en disco, y alerta por intentos de acceso fallidos.
6. Revisión de los secretos: ninguno de ejemplo; claves de integración una por sistema.

**Plan de retorno:** conservar la imagen y el respaldo anteriores. Si `/health` falla o aparecen errores 5xx sostenidos tras desplegar, volver a la imagen previa y restaurar la base solo si hubo cambios de esquema. Los cambios de esquema futuros deben ser compatibles hacia atrás (agregar, no eliminar).

---

# 3. Tech Lead — Código y arquitectura

## 3.1 Concurrencia y duplicados
**Resuelto.** El defecto más serio de la línea base (H-14) fue la carrera en los cambios de estado: ahora las operaciones que modifican un pedido toman un bloqueo de fila. **Riesgo restante:** el bloqueo se mantiene mientras se consulta el catálogo externo al modificar un pedido (hasta el tiempo máximo de 5 s por llamada), de modo que otro usuario que edite *el mismo pedido* esperaría. Es aceptable por la baja contención por pedido, pero conviene consultar el catálogo **antes** de tomar el bloqueo.

## 3.2 Precisión del dinero
Sin riesgo: `NUMERIC(14,2)` en base de datos, `Decimal` en el código, redondeo half-up en cada paso, verificado con casos de la UAT-01. Los precios se leen del catálogo como texto para no pasar por coma flotante.

## 3.3 Inmutabilidad de los datos históricos
- La **auditoría** es de solo-agregar a nivel de PostgreSQL y el precio de cada línea se **congela** en el momento de la venta.
- Los pedidos **sí son modificables** mientras están en *Pendiente* o *Confirmado*, con la modificación auditada (total anterior y nuevo).
- No hay endpoint de borrado: los usuarios se desactivan y los pedidos se cancelan.
- **Riesgo restante:** la auditoría vive en la misma base que los datos; un administrador de base de datos con privilegios podría alterarla. La mitigación sería enviar la auditoría a un registro externo (Fase 2 del informe 01).

## 3.4 Integración con servicios externos
- Cada pedido consulta 1 vez al cliente y 1 vez por producto, **en serie** (≈ 1 ms por consulta con el cliente HTTP persistente; 200 ms el `POST /pedidos` completo en Docker). Con muchos productos por pedido o servicios reales lentos esto crecerá: la mejora sería paralelizar o pedir por lotes.
- No hay caché (decisión deliberada: las existencias deben ser en vivo).
- Un servicio caído produce 502 y no deja datos a medias; se recupera solo.

## 3.5 Otros riesgos técnicos

| Riesgo | Detalle | Mitigación sugerida |
|---|---|---|
| **Migraciones sin herramienta de versionado** | El esquema se crea con `create_all` y scripts SQL manuales; un cambio de modelo exige un script nuevo y disciplina. | Adoptar Alembic antes de la siguiente versión. |
| Reportes calculados en memoria | Se leen todos los pedidos del rango y se agrupan en Python. | Pasar a `GROUP BY` en SQL si el volumen crece (ver `capacidad.md`). |
| Un solo proceso de la API | Uvicorn sin varios *workers*. | Varias réplicas o `--workers`; el diseño ya es sin estado. |
| Contador de login en la base | Cada intento fallido escribe una fila. | Aceptable; complementar con límite de tasa en el proxy. |
| SQLite en el modo de demostración | No tiene bloqueo de fila ni concurrencia real de escritura. | Documentado: solo para demostración. |
| Sin identificador legible de pedido | La interfaz muestra los 8 primeros caracteres de un UUID. | Añadir un número correlativo (ver Product Owner). |

---

# 4. Product Owner — Negocio y cumplimiento

## 4.1 Riesgos de experiencia de usuario
- **No hay recuperación de contraseña por autoservicio:** quien la olvida depende del administrador.
- Los pedidos se identifican con un **código corto de 8 caracteres** (parte de un UUID), poco amigable para dictar por teléfono: falta un **número de pedido correlativo**.
- No hay **búsqueda por texto** de pedidos (solo filtros por estado, cliente y fechas).
- El panel muestra solo los últimos 8 pedidos y no tiene notificaciones.
- El diseño se adapta a móvil, pero no se probó con usuarios reales ni en todos los navegadores.

## 4.2 Cumplimiento normativo (Colombia)

| Norma | Aplicación a SALES-X | Estado |
|---|---|---|
| Ley 1581 de 2012 (protección de datos personales) | Solo se guardan nombre, correo y hash de contraseña de usuarios internos, y el identificador de los clientes; minimización de datos. | Cumple por diseño. Falta la política de tratamiento y el aviso de privacidad de la organización usuaria. |
| Ley 1273 de 2009 (delitos informáticos) | Trazabilidad de operaciones y de accesos. | Cumple en lo técnico. |
| Ley 23 de 1982 y Decisión Andina 351 (derechos de autor) | Titularidad y licencias de terceros. | Evidencias 4 y 5; **falta definir la licencia final y el archivo `NOTICE`**. |
| Facturación electrónica (DIAN) | SALES-X **no factura**; los pedidos no son documentos fiscales. | No aplica; queda fuera de alcance. |

## 4.3 Tres métricas para medir desde el día 1
1. **Tiempo de respuesta p95** de la API (objetivo: < 3 s; medido: 0,10–0,13 s en pruebas).
2. **Tasa de errores 5xx** y de respuestas 502 por fallo de servicios externos.
3. **Pedidos envejecidos:** cuántos pedidos llevan más de 24 h en *Pendiente* o más de 3 días en *En preparación* (indicador de negocio que hoy no se calcula).

---

# 5. Conclusión del comité: **GO condicionado** (demostración y piloto interno) / **NO-GO para producción expuesta**

## 5.1 Criterios y estado

| Criterio | Estado |
|---|:---:|
| Requisitos funcionales implementados (17 de 17) | ✅ |
| Pruebas automáticas en verde (63; SQLite y PostgreSQL) | ✅ |
| Sin defectos funcionales abiertos | ✅ |
| Sin hallazgos de seguridad críticos o altos abiertos | ✅ |
| Dependencias sin vulnerabilidades conocidas | ✅ |
| Rendimiento dentro del RNF-01 | ✅ |
| Funciona en Docker en modo producción, con respaldo y restauración | ✅ |
| Revisión visual en escritorio y móvil | ✅ |
| Documentación completa y contrastada con el código | ✅ |
| Rol de BD de mínimo privilegio verificado | ✅ (aplicar en la base real) |
| **TLS, límites de tasa y `/docs` oculto** | ⛔ |
| **Servicios reales de Clientes y Productos** | ⛔ |
| **Verificación en el servidor de despliegue (Linux)** | ⛔ |
| Monitoreo, alertas y respaldos automáticos | ⛔ |
| Licencia final y archivo `NOTICE` | ⛔ |
| Usuarios de demostración eliminados y acta firmada | ⛔ (solo aplica en producción) |

## 5.2 Bloqueantes obligatorios para el GO a producción

1. Proxy con TLS, límites de tasa y tamaño, y `/docs` oculto (H-09, H-10, H-08).
2. Repetir suite, carga y restauración en el servidor real.
3. Conectar y probar los servicios reales de Clientes y Productos.
4. Aplicar el rol `salesx_app` en la base real y automatizar los respaldos.
5. Definir la licencia, incluir `NOTICE` y firmar el acta de usuarios.

## 5.3 Lo que sí está listo (no rehacer)

La lógica de pedidos, el cálculo exacto de importes, la máquina de estados con bloqueo de fila, la auditoría inmutable, el control de acceso (cookie, CSRF, roles, bloqueo, contraseñas), las claves de integración por consumidor, el adaptador REST tolerante a fallos, la interfaz responsiva, el despliegue con Docker, los respaldos, la documentación y las pruebas.

## 5.4 Recomendación del comité

**Aprobar para demostración, entrega académica y piloto controlado en red interna.** Para producción expuesta, ejecutar primero la Fase 0 del informe de auditoría (~8 h) y repetir la verificación en el servidor real; contratar una revisión de seguridad **independiente** antes de operar con datos reales.

## 5.5 Aprobaciones

| Rol | Nombre | Decisión | Firma y fecha |
|---|---|---|---|
| Desarrollo (full stack) | Julio Cesar Velasquez Arango | ☐ GO ☐ NO-GO | |
| Docente / evaluador | [ ] | ☐ GO ☐ NO-GO | |
| Responsable de operaciones | [ ] | ☐ GO ☐ NO-GO | |
