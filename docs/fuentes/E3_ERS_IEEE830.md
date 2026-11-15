---
codigo: SALESX-E3
evidencia: 3 de 7
titulo: Especificación de Requisitos de Software
descripcion: Documento de requisitos elaborado siguiendo la estructura del estándar IEEE 830. Define qué debe hacer SALES-X y bajo qué condiciones debe funcionar, con requisitos verificables y trazables al software realmente construido.
metadatos:
  - Sistema | SALES-X · Gestión de ventas y pedidos
  - Estándar de referencia | IEEE 830 (estructura de una ERS)
  - Requisitos funcionales | 17
  - Requisitos no funcionales | 27
  - Reglas de negocio | 15
  - Criterios de aceptación | 20
pie: SALES-X · Evidencia 3 de 7 · Especificación de Requisitos de Software (IEEE 830) · 17 requisitos funcionales, 27 no funcionales, 15 reglas de negocio, 20 criterios de aceptación.
---

# 1. Introducción

## 1.1 Propósito

Este documento especifica los requisitos de **SALES-X**, un sistema de gestión de ventas y pedidos que forma parte de INTEGRAX. Está dirigido a:

- El equipo de desarrollo, como contrato de lo que debe construirse.
- El docente evaluador o un revisor externo, para verificar que lo entregado corresponde a lo especificado.
- Un desarrollador futuro que reciba el proyecto, para entender qué hace y por qué.

Responde a la pregunta guía de la evidencia: **¿qué debe hacer exactamente el sistema y bajo qué condiciones debe funcionar?**

## 1.2 Alcance

SALES-X cubre el ciclo de venta de una organización desde que el área de ventas registra un pedido hasta que se entrega o se cancela:

**Cliente → Pedido (con productos) → Estados → Entrega (o Cancelación)**

El sistema ofrece una interfaz web para el personal de ventas y servicios REST para que otros sistemas de INTEGRAX consulten pedidos, verifiquen disponibilidad y registren solicitudes de los clientes.

> **Fuera de alcance.** SALES-X no es un ERP. Quedan expresamente fuera: el maestro de clientes y el de productos/inventario (pertenecen a otros microproyectos, que SALES-X consulta), el descuento real de existencias, la facturación electrónica, la pasarela de pagos y la logística de transporte. Ver la sección 2.5, Restricciones.

## 1.3 Definiciones y abreviaturas

| Término | Significado en este documento |
|---|---|
| INTEGRAX | Conjunto de microproyectos de integración de aplicaciones del curso. SALES-X es uno de ellos. |
| Pedido | Orden de venta de uno o más productos para un cliente. |
| Línea (detalle) | Un producto y su cantidad dentro de un pedido. |
| Estado | Etapa del pedido: Pendiente, Confirmado, En preparación, Enviado, Entregado o Cancelado. |
| Auditoría | Registro inmutable de las operaciones sobre un pedido. |
| Consumidor | Sistema de INTEGRAX autorizado, con su propia clave, para usar los servicios de integración. |
| API REST | Interfaz de servicios sobre HTTP con intercambio de datos en JSON. |
| JWT | Token firmado que identifica la sesión del usuario. |
| CSRF | Ataque que aprovecha la sesión abierta de un usuario; se evita exigiendo un token adicional en las escrituras. |
| IVA | Impuesto sobre las ventas (19 % por defecto, configurable). |
| RBAC | Control de acceso basado en roles. |

## 1.4 Referencias

- IEEE Std 830-1998 — *Recommended Practice for Software Requirements Specifications* (estructura seguida).
- Seguimientos 1 y 2 del curso: términos de referencia, fichas técnicas, requerimientos, casos de uso y diagramas.
- `specs/sales-x/requirements.md`, `design.md` y `tasks.md` — especificación de trabajo del equipo.
- `sql/01_schema.sql` y `app/models.py` — esquema real de la base de datos.
- `tests/` — suite de pruebas que verifica estos requisitos (Evidencia 7).

# 2. Descripción general

## 2.1 Perspectiva del producto

SALES-X es un **microproyecto independiente** con base de datos propia. Se compone de cuatro piezas que se comunican por HTTP:

**Navegador → Interfaz web → API REST (FastAPI) → PostgreSQL**  ·  y, hacia los lados, **API REST ⇄ Clientes y Productos (INTEGRAX)**

SALES-X no accede a las bases de datos de los otros microproyectos: solo consume sus servicios REST (o un catálogo simulado con el mismo contrato mientras no existan).

## 2.2 Funciones principales

| Grupo de funciones | Qué incluye |
|---|---|
| Autenticación y seguridad | Inicio de sesión con cookie `HttpOnly`, cierre de sesión, cambio de contraseña (obligatorio en el primer ingreso), bloqueo por intentos fallidos, control por roles. |
| Pedidos | Registro con clientes y productos, cálculo de totales en el servidor, modificación, cancelación, consulta y filtros. |
| Estados | Ciclo de vida con transiciones válidas; auditoría de cada cambio. |
| Catálogo | Consulta de clientes, productos y disponibilidad en vivo (servicios de INTEGRAX). |
| Reportes | Ventas por día o mes, totales, ticket promedio, pedidos por estado, exportación a CSV. |
| Auditoría | Registro inmutable de cada operación sobre un pedido, con autor y fecha. |
| Integración | Servicios REST protegidos con una clave por sistema consumidor; solicitudes del cliente (modificación o cancelación). |
| Administración | Gestión de usuarios y de claves de integración. |

## 2.3 Usuarios del sistema

El sistema distingue cuatro tipos de actor. Los dos primeros usan la interfaz web; los otros dos acceden solo por la API.

| Rol | Quién es | Qué puede hacer | Qué no puede hacer |
|---|---|---|---|
| Administrador | Responsable del sistema | Todo lo del vendedor y, además, crear y desactivar usuarios, restablecer contraseñas y administrar las claves de integración. | Desactivarse a sí mismo ni quitarse el rol. |
| Vendedor | Área de ventas | Registrar, consultar, modificar y cancelar pedidos; cambiar su estado; consultar el catálogo; generar reportes. | Gestionar usuarios ni claves de integración. |
| Cliente | Comprador (externo) | Solicitar la modificación o cancelación de un pedido, a través de un sistema autorizado. | Usar la interfaz web ni cambiar pedidos directamente: su solicitud solo queda registrada para que ventas decida. |
| Sistema consumidor | Otro microproyecto de INTEGRAX | Consultar pedidos, historial de un cliente y disponibilidad; registrar solicitudes del cliente. | Crear o modificar pedidos. Su clave se puede revocar. |

## 2.4 Entorno de operación

- **Servidor:** cualquier equipo con Docker (API y PostgreSQL en contenedores) o con Python 3.12+ (modo local con SQLite para demostración).
- **Cliente:** navegador web actual (Chrome, Edge, Firefox o Safari); la interfaz se adapta a pantallas estrechas. No requiere instalación.
- **Base de datos:** PostgreSQL 14 o superior, con volumen persistente en Docker. SQLite solo en desarrollo.
- **Red:** en producción, detrás de un proxy inverso con HTTPS (la cookie de sesión es `Secure`).

## 2.5 Restricciones de diseño y supuestos

| Tipo | Descripción |
|---|---|
| Tecnológica | Lenguaje **Python**, API con FastAPI, base de datos **PostgreSQL** y servicios **REST/JSON** (decisiones de los seguimientos 1 y 2). La interfaz es JavaScript puro, sin librerías de terceros. |
| De despliegue | Contenedores Docker orquestados con Docker Compose; configuración exclusivamente por variables de entorno, sin secretos por defecto en producción. |
| De integración | SALES-X no es dueño de Clientes ni de Productos: consume sus servicios REST. Mientras no existan, usa un catálogo simulado con el mismo contrato (`mocks/`). Los servicios reales **aún no se han probado** con SALES-X. |
| De alcance | No es un ERP: no incluye inventario propio, facturación, pagos ni logística. |
| De seguridad | No existe recuperación de contraseña por autoservicio: la restablece el administrador. La entrega de correos o mensajes no está implementada. |
| Legal | El software se distribuye bajo licencia de uso; las dependencias de terceros conservan sus licencias (ver Evidencias 4 y 5). |
| Académica | Proyecto de la asignatura Integración de Aplicaciones. |

**Supuestos:** el equipo dispone de Docker o de Python; el usuario final tiene un navegador moderno; los servicios de Clientes y Productos respetarán el contrato descrito en el diccionario de datos (Evidencia 2, sección 4).

# 3. Requisitos funcionales

Se especifican **17 requisitos funcionales**. Cada uno declara el actor que lo usa, su prioridad, cómo se verifica y su estado. No hay requisitos «pendientes»: todo lo especificado aquí está construido y probado, y lo que no existe figura en el alcance como fuera de alcance en lugar de como requisito incumplido.

La columna «Verificación» enlaza con los casos de prueba de la Evidencia 7 (CP-xx) y con la matriz de trazabilidad de la Evidencia 6.

| ID | Enunciado del requisito | Actor | Prioridad | Verificación | Estado |
|---|---|---|---|---|---|
| RF-01 | El sistema debe permitir registrar un pedido nuevo, que nace en estado *Pendiente* con fecha y vendedor responsable. | Vendedor | Crítica | Prueba CP-10 | Implementado |
| RF-02 | El sistema debe asociar cada pedido a un cliente y rechazar (422) un cliente que no exista en el catálogo. | Vendedor | Alta | Pruebas CP-13, CP-56 | Implementado |
| RF-03 | El sistema debe permitir agregar de 1 a 100 productos con cantidad entera (1–10.000), consolidar líneas repetidas y tomar el precio siempre del catálogo, no de la petición. | Vendedor | Alta | Pruebas CP-11, CP-12, CP-13 | Implementado |
| RF-04 | El sistema debe permitir modificar observaciones y líneas de un pedido solo en *Pendiente* o *Confirmado*, revalidando disponibilidad y recalculando totales. | Vendedor | Alta | Pruebas CP-16, CP-63 | Implementado |
| RF-05 | El sistema debe permitir cancelar un pedido con motivo, solo hasta *En preparación*; un pedido enviado, entregado o ya cancelado no se cancela (409). | Vendedor | Alta | Pruebas CP-19, CP-20, CP-62 | Implementado |
| RF-06 | El sistema debe permitir consultar pedidos con filtros por estado, cliente, vendedor y fechas, paginados, y ver el detalle de un pedido. | Vendedor, Administrador | Alta | Prueba CP-14 | Implementado |
| RF-07 | El sistema debe calcular subtotal, impuestos y total en el servidor, con redondeo half-up a 2 decimales, sin aceptar importes enviados por el navegador. | Sistema | Crítica | Pruebas CP-10, CP-55 | Implementado |
| RF-08 | El sistema debe permitir cambiar el estado de un pedido admitiendo solo las transiciones válidas (409 si no lo son), auditando cada cambio. | Vendedor | Crítica | Pruebas CP-17, CP-18, CP-61 | Implementado |
| RF-09 | El sistema debe mostrar el historial de pedidos de un cliente, con su total comprado (sin contar cancelados). | Vendedor | Media | Prueba CP-15 | Implementado |
| RF-10 | El sistema debe generar el reporte de ventas por rango de fechas y por día o mes, excluyendo cancelados, y exportarlo a CSV. | Vendedor | Alta | Pruebas CP-22, CP-23, CP-30 | Implementado |
| RF-11 | El sistema debe consultar la disponibilidad de un producto en vivo, y la interfaz debe bloquear los productos agotados o inactivos. | Vendedor | Alta | Pruebas CP-09, CP-57 | Implementado |
| RF-12 | El sistema debe exponer servicios de integración autenticados con `X-API-Key`: consultar un pedido, el historial de un cliente, la disponibilidad y registrar una solicitud de modificación o cancelación (que no altera el pedido). | Sistema consumidor | Alta | Pruebas CP-24, CP-25, CP-58 | Implementado |
| RF-13 | El sistema debe permitir al administrador crear usuarios, activarlos o desactivarlos, cambiar roles y contraseñas; no puede desactivarse a sí mismo. | Administrador | Alta | Pruebas CP-07, CP-08 | Implementado |
| RF-14 | El sistema debe bloquear el inicio de sesión tras 5 intentos fallidos en 5 minutos (429), con un contador en la base de datos compartido entre instancias. | Sistema | Alta | Pruebas CP-32, CP-33 | Implementado |
| RF-15 | El sistema debe gestionar una clave por consumidor de integración: mostrarla una sola vez, guardar solo su hash, y permitir revocarla o dejarla expirar. | Administrador | Alta | Pruebas CP-34 a CP-38 | Implementado |
| RF-16 | El sistema debe guardar la sesión en una cookie `HttpOnly` (`SameSite=Strict`, `Secure` en producción) y exigir un token CSRF en las escrituras hechas por cookie. | Sistema | Alta | Pruebas CP-39 a CP-42 | Implementado |
| RF-17 | El sistema debe exigir una contraseña de al menos 10 caracteres con letras y números, permitir cambiarla, y obligar a cambiarla en el primer ingreso o tras un restablecimiento. | Todos los usuarios | Alta | Pruebas CP-43 a CP-46 | Implementado |

# 4. Requisitos no funcionales

Los requisitos no funcionales describen **cómo** debe comportarse el sistema, no qué hace. Los ocho primeros (RNF-01 a RNF-08) son los definidos en el seguimiento 2; del RNF-09 en adelante se detallan los atributos de seguridad, integridad y resiliencia que la construcción y la auditoría hicieron explícitos.

| ID | Categoría | Requisito | Prioridad | Cómo se verifica |
|---|---|---|---|---|
| RNF-01 | Rendimiento · tiempo de respuesta | Las operaciones responden en menos de 3 segundos (percentil 95) con 20 usuarios concurrentes. | Alta | Prueba de carga (`scripts/carga_basica.py`): p95 = 0,098 s en PostgreSQL y 0,130 s en Docker. |
| RNF-02 | Portabilidad · interfaz | Toda función se ofrece por una API REST/JSON documentada con OpenAPI. | Alta | `/docs`; todas las pruebas ejercitan la API. |
| RNF-03 | Disponibilidad | Disponibilidad mínima del 95 % mensual; punto de salud `/health` y reinicio automático. | Media | `/health` y *healthcheck* de Docker verificados; el porcentaje real solo se mide en operación. |
| RNF-04 | Seguridad · autenticación | Todo endpoint, salvo `/health` y el inicio de sesión, exige sesión o API Key. | Crítica | Pruebas CP-02 a CP-05, CP-24. |
| RNF-05 | Integridad · auditoría | Toda operación sobre un pedido queda auditada con autor y fecha, y los eventos no se pueden modificar ni borrar. | Alta | Prueba CP-21; permisos del rol `salesx_app` verificados en PostgreSQL. |
| RNF-06 | Escalabilidad | API sin estado, paginada e indexada; el bloqueo de login no depende del proceso. | Media | Prueba CP-32; revisión del diseño. |
| RNF-07 | Portabilidad · plataforma | Funciona en Windows y Linux (contenedores), con SQLite o PostgreSQL. | Alta | Pruebas en Windows (SQLite y PostgreSQL) y en contenedores Linux (Docker). |
| RNF-08 | Documentación | Documentación técnica actualizada junto al código. | Media | Esta evidencia y el cruce automático documentación-código. |
| RNF-09 | Seguridad · contraseñas | Las contraseñas se guardan con bcrypt (coste 12); política de ≥ 10 caracteres con letras y números, sin contraseñas comunes ni el usuario. | Crítica | Pruebas CP-43, CP-44; inspección de la columna `vendedor.contrasena`. |
| RNF-10 | Seguridad · sesiones | La sesión viaja en cookie `HttpOnly` y `SameSite=Strict` (`Secure` en producción), firmada con JWT de 8 horas; la interfaz no guarda el token. | Alta | Prueba CP-39; inspección en el navegador (`document.cookie` no muestra la sesión). |
| RNF-11 | Seguridad · CSRF | Las escrituras por cookie exigen el encabezado `X-CSRF-Token` (patrón *double submit*). | Alta | Pruebas CP-40, CP-41. |
| RNF-12 | Seguridad · fuerza bruta | Tras 5 intentos fallidos en 5 minutos la cuenta se bloquea, también al cambiar la contraseña. | Alta | Pruebas CP-06, CP-32, CP-46. |
| RNF-13 | Seguridad · autorización | Cada operación exige el rol adecuado; un rol sin permiso recibe 403. | Crítica | Pruebas CP-07, CP-37. |
| RNF-14 | Seguridad · configuración | En producción el sistema no arranca con claves por defecto, contraseña de administrador débil, SQLite o usuarios de demostración. | Alta | Pruebas CP-28, CP-29. |
| RNF-15 | Seguridad · cabeceras HTTP | Las respuestas incluyen `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options` y HSTS en producción. | Media | Prueba CP-27; verificación en Docker. |
| RNF-16 | Seguridad · inyección y XSS | Consultas parametrizadas (ORM), validación estricta de entradas, escape de toda salida y CSP sin scripts en línea. | Alta | Prueba CP-26; revisión de la interfaz. |
| RNF-17 | Seguridad · claves de integración | Una clave por consumidor, guardada como hash SHA-256, revocable y con expiración opcional. | Alta | Pruebas CP-34 a CP-38. |
| RNF-18 | Seguridad · mínimo privilegio | La API se conecta a la base de datos con un rol que no puede alterar el esquema ni editar la auditoría. | Alta | Comprobación de permisos en PostgreSQL y en Docker (Evidencia 7). |
| RNF-19 | Integridad · concurrencia | Dos usuarios que actúan a la vez sobre el mismo pedido se serializan (bloqueo de fila) y no pueden violar la máquina de estados. | Crítica | Pruebas CP-61 a CP-63 (30 rondas cada una). |
| RNF-20 | Integridad · precisión monetaria | Los importes usan `NUMERIC(14,2)` y se redondean a 2 decimales (half-up) en cada paso. | Alta | Pruebas CP-10, CP-55. |
| RNF-21 | Integridad · atomicidad | Cada operación se confirma en una sola transacción, junto con su auditoría; si falla, no queda nada a medias. | Alta | Prueba CP-59; revisión del código. |
| RNF-22 | Usabilidad | Interfaz en español, importes en COP, fechas en hora de Colombia y adaptable a pantallas estrechas. | Media | Capturas de la Evidencia 7; comprobación de que no hay desbordamiento horizontal a 390 px. |
| RNF-23 | Resiliencia · integración externa | Si Clientes o Productos fallan, tardan o responden mal, SALES-X responde 502, no registra el pedido y se recupera solo. | Alta | Pruebas CP-49 a CP-53, CP-59, CP-60 y apagado de contenedores en Docker. |
| RNF-24 | Mantenibilidad · pruebas | Existe una suite automatizada que verifica los requisitos de punta a punta. | Alta | Ejecución: 63 pruebas (60 en SQLite; 63 en PostgreSQL). |
| RNF-25 | Portabilidad · despliegue | El sistema completo se levanta con un solo comando. | Alta | `iniciar.bat` (local) y `docker compose up` (producción), probados desde cero. |
| RNF-26 | Disponibilidad de datos | Los datos persisten entre reinicios y existe un procedimiento de respaldo y restauración. | Alta | Prueba de `pg_dump` / `pg_restore` en PostgreSQL y en Docker. |
| RNF-27 | Licenciamiento | Todas las dependencias usan licencias permisivas o de copyleft débil; ninguna es copyleft fuerte. | Alta | Evidencia 4: análisis de las 29 dependencias de la imagen. |

# 5. Interfaces

| Interfaz | Descripción |
|---|---|
| Interfaz de usuario | Aplicación web de una sola página, servida por la propia API, en español: panel, pedidos, nuevo pedido, reportes, usuarios e integraciones. Sin librerías de terceros ni CDN. |
| Interfaz de programación (API) | API REST con JSON bajo `/api/v1` (30 operaciones). Sesión por cookie `HttpOnly` + `X-CSRF-Token`, o `Authorization: Bearer <JWT>` para clientes de API; integración con `X-API-Key`. Los errores devuelven `{"detail": "mensaje"}`. Documentada con OpenAPI en `/docs`. |
| Interfaz de datos | PostgreSQL 14+ con consultas parametrizadas mediante SQLAlchemy. La API usa el rol `salesx_app` (sin permisos de esquema). |
| Interfaz de integración | Consume `GET /api/clientes[/{id}]` y `GET /api/productos[/{id}]` de INTEGRAX (contrato en la Evidencia 2). Un cliente HTTP persistente, con tiempo máximo de 5 s. |
| Interfaz de notificaciones | No aplica: SALES-X no envía correos ni mensajes. |
| Interfaz de hardware | No aplica: se usa un navegador estándar en un equipo convencional. |

# 6. Reglas de negocio

Las reglas de negocio son las invariantes del sistema: condiciones que deben cumplirse siempre, independientemente de quién ejecute la operación o desde dónde. Se aplican en el servidor y en la base de datos, no solo en la interfaz.

| ID | Regla | Dónde se aplica |
|---|---|---|
| RN-01 | El precio de cada línea es el del catálogo; nunca el que envíe quien llama a la API. | `_construir_detalles`; los esquemas de entrada ignoran el precio enviado. |
| RN-02 | Los importes de un pedido los calcula siempre el servidor. | `Pedido.calcular_total`. El navegador solo muestra una vista previa. |
| RN-03 | No se acepta una línea que supere la disponibilidad del producto, ni un producto inactivo. | Validación contra el catálogo → 409 / 422. |
| RN-04 | Un pedido solo cambia de estado por transiciones válidas. | Diccionario `TRANSICIONES` → 409 con las permitidas. |
| RN-05 | Un pedido solo se modifica en *Pendiente* o *Confirmado*. | `MODIFICABLES` → 409. |
| RN-06 | Cancelar exige motivo y solo se permite hasta *En preparación*. | Servicio de pedidos → 409 / 422. |
| RN-07 | Las ventas de un período excluyen los pedidos cancelados. | Servicio de reportes. |
| RN-08 | Los eventos de auditoría no se modifican ni se borran. | Rol de base de datos `salesx_app` sin `UPDATE`/`DELETE`/`TRUNCATE`. |
| RN-09 | Una solicitud del cliente solo queda registrada: no altera el pedido. | Router de integración → 202 y auditoría `SOLICITUD_*`. |
| RN-10 | Un usuario nuevo, o con la contraseña restablecida, debe cambiarla antes de operar. | Dependencia `current_user` → 403 hasta cambiarla. |
| RN-11 | Los usuarios no se borran: se desactivan, para conservar la trazabilidad. | No existe endpoint de borrado; campo `activo`. |
| RN-12 | La clave de integración se muestra una sola vez y solo se guarda su hash. | Router de consumidores. |
| RN-13 | Si el servicio externo falla, el pedido no se registra. | Adaptador REST → 502; transacción única. |
| RN-14 | Dos usuarios sobre el mismo pedido se serializan. | `SELECT … FOR UPDATE` en modificar, cambiar de estado y cancelar. |
| RN-15 | Las fechas se guardan en UTC y se interpretan en la zona de negocio (America/Bogota). | `app/timeutil.py`. |

# 7. Criterios de aceptación

Un requisito está cumplido cuando se puede comprobar de forma objetiva. Estos son los criterios de aceptación del sistema; cada uno se verifica con un caso de prueba concreto de la Evidencia 7.

| ID | Criterio de aceptación | Se verifica con |
|---|---|---|
| CA-01 | Los totales de un pedido coinciden exactamente con la aritmética calculada sobre los precios del catálogo (p. ej. 3 × 45.500,50 → total 162.436,79). | CP-10, CP-55 |
| CA-02 | Una cantidad superior a las existencias se rechaza con 409 y no se crea el pedido. | CP-13, CP-56 |
| CA-03 | Una transición de estado inválida se rechaza con 409 e indica las permitidas. | CP-18 |
| CA-04 | Un pedido cancelado no se puede volver a cancelar, modificar ni cambiar de estado. | CP-19 |
| CA-05 | Un pedido enviado no se puede cancelar. | CP-20 |
| CA-06 | La auditoría registra exactamente CREAR, MODIFICAR, CAMBIO_ESTADO y CANCELAR, en ese orden, con su autor. | CP-21 |
| CA-07 | El reporte de ventas excluye los pedidos cancelados. | CP-22 |
| CA-08 | Un pedido registrado a las 23:48 hora de Colombia aparece en el reporte de ese día. | CP-30 |
| CA-09 | Sin sesión, o con un token alterado, cualquier endpoint protegido responde 401. | CP-04, CP-05 |
| CA-10 | Cinco intentos fallidos de ingreso producen 429, también desde otra instancia. | CP-06, CP-32 |
| CA-11 | Un usuario nuevo recibe 403 en toda la API hasta cambiar su contraseña. | CP-44 |
| CA-12 | Una escritura por cookie sin el token CSRF correcto se rechaza con 403. | CP-40 |
| CA-13 | Una clave de integración ausente, revocada o expirada responde 401. | CP-24, CP-35, CP-36 |
| CA-14 | La solicitud de un cliente responde 202, queda auditada y **no** cambia el pedido. | CP-25 |
| CA-15 | Con el servicio externo caído, registrar un pedido responde 502 y no deja pedidos a medias. | CP-59 |
| CA-16 | Dos acciones simultáneas sobre el mismo pedido no violan la máquina de estados. | CP-61, CP-62, CP-63 |
| CA-17 | En producción el sistema no arranca con claves por defecto o con SQLite. | CP-28 |
| CA-18 | Con el rol limitado de la API, `UPDATE` y `DELETE` sobre la auditoría son rechazados por PostgreSQL. | Evidencia 7 §6 (permisos del rol) |
| CA-19 | El sistema se levanta con un solo comando y queda sano. | Evidencia 7 §7 (Docker) |
| CA-20 | La suite de pruebas finaliza con 0 fallos. | Todas |

# 8. Trazabilidad

Este documento no es un elemento aislado: se enlaza con el resto de la documentación.

**REQUISITOS (esta ERS) → CASOS DE USO (especificación de trabajo) → MER y DICCIONARIO (Evidencias 1 y 2) → IMPLEMENTACIÓN (`app/`) → PRUEBAS (Evidencia 7) → LICENCIAMIENTO (Evidencias 4 y 5)**

Como ejemplo, el requisito **RF-08** («solo transiciones de estado válidas») se puede seguir por toda la cadena:

- Especificado aquí como RF-08, con prioridad Crítica y criterio de aceptación CA-03 y CA-16.
- Implementado en `app/services/pedidos.py` (`TRANSICIONES`, `cambiar_estado`).
- Apoyado en la tabla `estado_pedido` y la columna `pedido.estado_id` (Evidencias 1 y 2).
- Expuesto en `PATCH /api/v1/pedidos/{pedido_id}/estado`.
- Visible en la pantalla de detalle del pedido, con el botón «Pasar a …» (capturas de la Evidencia 7).
- Verificado por los casos de prueba CP-17, CP-18 y CP-61 de la Evidencia 7.
