# Requisitos — SALES-X · Gestión de Ventas y Pedidos

**Versión:** 1.0 · **Estado:** implementado y verificado (salvo lo marcado como pendiente) · **Fuente:** seguimientos 1 y 2, `docs/E3_ERS_IEEE830`

## Introducción
SALES-X es el microproyecto de INTEGRAX que permite al área de ventas **registrar, gestionar y reportar pedidos** de venta, asociándolos a clientes y productos que pertenecen a otros microproyectos, y que **expone servicios REST** para integrarse con ellos.

## Glosario
| Término | Significado |
|---|---|
| Usuario de ventas | Persona con rol `vendedor` que opera pedidos. |
| Administrador | Persona con rol `admin`: lo anterior + gestión de usuarios. |
| Cliente | Comprador. Su ficha vive en el microproyecto de Clientes; SALES-X guarda su `cliente_id`. |
| Catálogo | Servicios de Clientes y Productos de INTEGRAX (o el proveedor simulado equivalente). |
| Estado | Etapa del pedido: Pendiente, Confirmado, En preparación, Enviado, Entregado, Cancelado. |
| Auditoría | Registro inmutable de las operaciones sobre un pedido. |

---

## Requisitos funcionales

### REQ-01 · Registrar pedidos *(RF-01, CU-01)*
**Historia:** Como usuario de ventas, quiero registrar un pedido nuevo para dejar constancia de una venta.
**Criterios de aceptación**
1. CUANDO el usuario envía un pedido válido ENTONCES el sistema DEBERÁ crearlo en estado *Pendiente*, con fecha y vendedor responsable, y responder 201 con el pedido completo.
2. CUANDO se crea un pedido ENTONCES el sistema DEBERÁ registrar el evento `CREAR` en la auditoría.
3. SI el usuario no está autenticado ENTONCES el sistema DEBERÁ responder 401.

### REQ-02 · Asociar clientes *(RF-02, CU-02)*
**Historia:** Como usuario de ventas, quiero asociar un cliente al pedido para saber a quién se vende.
1. El `cliente_id` DEBERÁ ser obligatorio.
2. SI el cliente no existe en el catálogo ENTONCES el sistema DEBERÁ rechazar el pedido con 422 y no crear nada.

### REQ-03 · Agregar productos *(RF-03, CU-03)*
**Historia:** Como usuario de ventas, quiero agregar uno o varios productos con su cantidad.
1. El pedido DEBERÁ tener entre 1 y 100 líneas; cada cantidad, un entero entre 1 y 10 000.
2. CUANDO un mismo producto aparece en varias líneas ENTONCES el sistema DEBERÁ consolidarlas sumando cantidades.
3. SI el producto no existe o está inactivo ENTONCES el sistema DEBERÁ responder 422.
4. SI la cantidad supera la disponibilidad ENTONCES el sistema DEBERÁ responder 409 indicando solicitado y disponible.
5. El precio unitario DEBERÁ tomarse **siempre del catálogo**; cualquier precio enviado por el cliente DEBERÁ ignorarse.

### REQ-04 · Modificar pedidos *(RF-04, CU-06)*
**Historia:** Como usuario de ventas, quiero modificar un pedido para atender cambios del cliente.
1. MIENTRAS el pedido esté *Pendiente* o *Confirmado* el sistema DEBERÁ permitir cambiar observaciones y/o reemplazar las líneas.
2. SI está en otro estado ENTONCES el sistema DEBERÁ responder 409.
3. CUANDO se reemplazan líneas ENTONCES el sistema DEBERÁ revalidar disponibilidad, recalcular totales y auditar `MODIFICAR` con el total anterior y el nuevo.
4. SI la petición no trae cambios ENTONCES el sistema DEBERÁ responder 422.

### REQ-05 · Cancelar pedidos *(RF-05, CU-07)*
**Historia:** Como usuario de ventas, quiero cancelar un pedido cuando el cliente desiste.
1. La cancelación DEBERÁ exigir un motivo de al menos 3 caracteres.
2. SOLO DEBERÁ permitirse desde *Pendiente*, *Confirmado* o *En preparación*; en cualquier otro estado, 409.
3. CUANDO se cancela ENTONCES el sistema DEBERÁ auditar `CANCELAR` con el motivo.

### REQ-06 · Consultar pedidos *(RF-06, CU-08)*
**Historia:** Como usuario de ventas, quiero buscar y ver pedidos para atender consultas.
1. El listado DEBERÁ filtrarse por estado, cliente, vendedor y rango de fechas, ordenarse por fecha descendente y paginarse (tamaño máximo 100).
2. SI el pedido no existe ENTONCES el sistema DEBERÁ responder 404; SI el identificador no es un UUID, 422.
3. Las fechas del filtro DEBERÁN interpretarse en la zona horaria de negocio (por defecto America/Bogota).

### REQ-07 · Calcular subtotal, impuestos y total *(RF-07, CU-04)*
**Historia:** Como usuario de ventas, quiero que el sistema calcule los valores para evitar errores manuales.
1. `subtotal = Σ cantidad × precio_unitario`; `impuestos = subtotal × IVA` (19 % configurable); `total = subtotal + impuestos`.
2. Los importes DEBERÁN redondearse a 2 decimales (half-up) y calcularse **solo en el servidor**.
3. La interfaz DEBERÁ mostrar una vista previa de los totales antes de guardar, coherente con la del servidor.

### REQ-08 · Gestionar estados *(RF-08, CU-09)*
**Historia:** Como usuario de ventas, quiero avanzar el estado del pedido para reflejar su ciclo de vida.
1. SOLO DEBERÁN permitirse estas transiciones: Pendiente → Confirmado | Cancelado · Confirmado → En preparación | Cancelado · En preparación → Enviado | Cancelado · Enviado → Entregado. *Entregado* y *Cancelado* son finales.
2. SI la transición no es válida ENTONCES el sistema DEBERÁ responder 409 listando las permitidas; SI el estado no existe, 422.
3. CUANDO cambia el estado ENTONCES el sistema DEBERÁ auditar `CAMBIO_ESTADO` («anterior → nuevo» y comentario).

### REQ-09 · Historial de pedidos *(RF-09, CU-10)*
**Historia:** Como usuario de ventas, quiero ver todo lo que ha comprado un cliente.
1. El sistema DEBERÁ devolver los pedidos del cliente, su cantidad y el total comprado **excluyendo cancelados**.

### REQ-10 · Reporte de ventas *(RF-10, CU-12)*
**Historia:** Como usuario de ventas, quiero un reporte por período para medir las ventas.
1. El reporte DEBERÁ aceptar rango de fechas y agrupación por día o mes, y devolver totales, ticket promedio, pedidos por estado y la serie por período.
2. Las ventas DEBERÁN **excluir los pedidos cancelados**.
3. El sistema DEBERÁ ofrecer la exportación a CSV (compatible con Excel).
4. SI la agrupación no es `dia` ni `mes` ENTONCES el sistema DEBERÁ responder 422.

### REQ-11 · Disponibilidad de productos *(RF-11, CU-11)*
**Historia:** Como usuario de ventas, quiero saber si hay existencias antes de ofrecer un producto.
1. El sistema DEBERÁ devolver existencias y si el producto está activo; SI no existe, 404.
2. La interfaz DEBERÁ bloquear la selección de productos agotados o inactivos.

### REQ-12 · Servicios de integración *(RF-12, CU-13, CU-05)*
**Historia:** Como sistema de INTEGRAX, quiero consultar pedidos y registrar solicitudes de clientes.
1. Los servicios `/integracion/*` DEBERÁN autenticarse **solo con `X-API-Key`**; sin clave, con clave errónea o con un JWT, 401.
2. DEBERÁN ofrecer: consultar un pedido, pedidos de un cliente, disponibilidad de un producto y registrar una solicitud de modificación o cancelación.
3. CUANDO llega una solicitud ENTONCES el sistema DEBERÁ responder 202, auditarla como `SOLICITUD_*` con autor «Sistema externo» y **no modificar el pedido**.
4. Las solicitudes recibidas DEBERÁN ser visibles para el área de ventas.

### REQ-13 · Administrar usuarios *(RF-13)*
**Historia:** Como administrador, quiero crear, activar/desactivar usuarios y cambiar contraseñas y roles.
1. SOLO el rol `admin` DEBERÁ acceder a estas funciones (403 para otros).
2. SI el correo ya existe ENTONCES 409. El administrador no DEBERÁ poder desactivarse ni quitarse el rol a sí mismo.
3. Los usuarios NO DEBERÁN borrarse (se desactivan) para conservar la trazabilidad.

---

### REQ-14 · Bloqueo de login compartido *(H-04)*
**Historia:** Como administrador, quiero que el bloqueo por intentos fallidos funcione con varias instancias y sobreviva a reinicios.
1. Los intentos fallidos DEBERÁN registrarse en la base de datos por correo.
2. SI hay 5 o más fallos en los últimos 5 minutos ENTONCES el sistema DEBERÁ responder 429, sin importar qué instancia atienda.
3. CUANDO el ingreso es correcto ENTONCES el sistema DEBERÁ borrar los fallos de ese correo.

### REQ-15 · Claves de integración por consumidor *(H-06)*
**Historia:** Como administrador, quiero una clave distinta por cada sistema consumidor para poder revocarla y rastrear su uso.
1. SOLO el rol `admin` DEBERÁ crear, listar y activar/desactivar consumidores, y definir su fecha de expiración.
2. CUANDO se crea un consumidor ENTONCES el sistema DEBERÁ mostrar la clave **una sola vez** y guardar únicamente su hash SHA-256.
3. SI la clave no existe, está inactiva o expirada ENTONCES el sistema DEBERÁ responder 401 con un mensaje genérico.
4. CUANDO una clave se usa ENTONCES el sistema DEBERÁ registrar la fecha de último uso, y las solicitudes auditadas DEBERÁN indicar el consumidor.
5. CUANDO el sistema inicia sin consumidores ENTONCES DEBERÁ crear uno inicial («INTEGRAX-inicial») con `INTEGRATION_API_KEY`.

### REQ-16 · Sesión en cookie `HttpOnly` con protección CSRF *(H-05)*
**Historia:** Como usuario, quiero que mi sesión no pueda ser leída por scripts de la página.
1. CUANDO el usuario inicia sesión ENTONCES el sistema DEBERÁ emitir el token en una cookie `HttpOnly`, `SameSite=Strict` (y `Secure` en producción), y una cookie legible con el token CSRF.
2. MIENTRAS la sesión llegue por cookie, toda petición que modifique datos (POST, PUT, PATCH, DELETE) DEBERÁ incluir la cabecera `X-CSRF-Token` igual a la cookie; si no, 403.
3. Las peticiones con cabecera `Authorization: Bearer` (clientes de API) NO DEBERÁN requerir CSRF.
4. CUANDO el usuario cierra sesión ENTONCES el sistema DEBERÁ eliminar ambas cookies.
5. La interfaz NO DEBERÁ guardar el token en `sessionStorage` ni `localStorage`.

### REQ-17 · Gestión de contraseñas *(H-07)*
**Historia:** Como usuario, quiero cambiar mi propia contraseña, y como administrador, quiero que las contraseñas iniciales no queden en uso.
1. Toda contraseña nueva DEBERÁ tener al menos 10 caracteres, letras y números, no ser una contraseña común ni contener la parte local del correo.
2. CUANDO el administrador crea un usuario o restablece su contraseña ENTONCES el sistema DEBERÁ exigir el cambio en el siguiente ingreso.
3. MIENTRAS el cambio sea obligatorio el sistema DEBERÁ responder 403 a todo excepto consultar el perfil, cambiar la contraseña y cerrar sesión.
4. El cambio DEBERÁ exigir la contraseña actual, aplicar el bloqueo por intentos fallidos y rechazar una nueva igual a la actual.

> **Verificación de REQ-14…17:** `tests/test_endurecimiento.py` (15 pruebas, en SQLite y PostgreSQL) y recorrido manual en el navegador. ✅

## Requisitos no funcionales

| ID | Requisito (EARS) | Verificación |
|---|---|---|
| **REQ-NF-01** *(RNF-01)* | El sistema DEBERÁ responder en menos de 3 s en el percentil 95 con 20 usuarios concurrentes. | `scripts/carga_basica.py` — ✅ p95 = 0,092 s (PostgreSQL) |
| **REQ-NF-02** *(RNF-02)* | Toda función DEBERÁ ofrecerse por una API REST/JSON documentada con OpenAPI. | `/docs` — ✅ |
| **REQ-NF-03** *(RNF-03)* | El sistema DEBERÁ tener disponibilidad ≥ 95 % mensual y exponer `/health`. | ⏳ se mide en operación |
| **REQ-NF-04** *(RNF-04)* | Todo endpoint, salvo `/health` y `/auth/login`, DEBERÁ exigir JWT o API Key; las contraseñas DEBERÁN guardarse con bcrypt; tras 5 intentos fallidos en 5 min DEBERÁ bloquearse el ingreso (429). | ✅ pruebas CP-02…CP-08, CP-24…CP-29 |
| **REQ-NF-05** *(RNF-05)* | Toda creación, modificación, cambio de estado, cancelación y solicitud externa DEBERÁ quedar auditada con autor y fecha, y la base de datos DEBERÁ impedir a la API modificar o borrar esos eventos (rol `salesx_app`). | ✅ pruebas + permisos verificados en PostgreSQL |
| **REQ-NF-06** *(RNF-06)* | La API DEBERÁ ser sin estado, paginada e indexada para escalar horizontalmente. | ✅ el bloqueo de login ya es compartido (REQ-14) |
| **REQ-NF-07** *(RNF-07)* | El sistema DEBERÁ ejecutarse en Windows y Linux, con SQLite (desarrollo) y PostgreSQL (producción), y en contenedor. | ✅ Windows con SQLite/PostgreSQL y contenedores Linux con Docker Compose; pendiente anfitrión Linux |
| **REQ-NF-08** *(RNF-08)* | La documentación técnica DEBERÁ mantenerse actualizada junto con el código. | ✅ `docs/` y `specs/` |
| **REQ-NF-09** | CUANDO `ENVIRONMENT=production` el sistema DEBERÁ negarse a iniciar con claves por defecto, SQLite o usuarios demo. | ✅ CP-28/29 |
| **REQ-NF-10** | La interfaz DEBERÁ funcionar bajo una CSP estricta (sin scripts ni estilos en línea) y escapar todo dato dinámico. | ✅ CP-27 + recorrido manual |

## Fuera de alcance
Maestro de clientes y de productos/inventario, facturación electrónica, pasarela de pagos, logística de transporte y descuento real de existencias (SALES-X solo las consulta).
