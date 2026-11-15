## 3.1. estado_pedido

Catálogo cerrado de estados del ciclo de vida del pedido: Pendiente, Confirmado, En preparación, Enviado, Entregado y Cancelado. Define las etapas que recorre un pedido.

| Campo | Tipo | Long. | PK | FK | Oblig. | Descripción |
|---|---|---|---|---|---|---|
| `estado_id` | UUID | — | Sí | No | Sí | Identificador único del estado. Clave primaria. |
| `nombre` | VARCHAR | 40 | No | No | Sí | Nombre del estado (Pendiente, Confirmado, En preparación, Enviado, Entregado, Cancelado). Único. |
| `descripcion` | VARCHAR | 200 | No | No | No | Explicación breve de lo que significa el estado. |

## 3.2. vendedor

Usuarios internos de SALES-X (vendedores y administradores). Es quien registra y gestiona los pedidos y quien firma cada evento de auditoría.

| Campo | Tipo | Long. | PK | FK | Oblig. | Descripción |
|---|---|---|---|---|---|---|
| `vendedor_id` | UUID | — | Sí | No | Sí | Identificador único del usuario. Clave primaria. |
| `nombre` | VARCHAR | 120 | No | No | Sí | Nombre completo del usuario; es el que aparece en la auditoría. |
| `correo` | VARCHAR | 160 | No | No | Sí | Correo electrónico en minúscula; sirve como nombre de usuario para ingresar. Único. |
| `contrasena` | VARCHAR | 100 | No | No | Sí | Contraseña cifrada con bcrypt (nunca en texto plano ni devuelta por la API). |
| `rol` | VARCHAR | 20 | No | No | Sí | Perfil de autorización: «vendedor» (opera pedidos) o «admin» (además gestiona usuarios e integraciones). |
| `activo` | BOOLEAN | — | No | No | Sí | Si es falso, el usuario no puede ingresar ni operar. Se desactiva en lugar de borrar para conservar la trazabilidad. |
| `debe_cambiar_contrasena` | BOOLEAN | — | No | No | Sí | Verdadero cuando la contraseña la conoce el administrador (usuario nuevo o restablecida): el usuario debe definir una propia antes de operar. |

## 3.3. pedido

Cabecera de una venta: a quién se vende, quién la registró, en qué estado está y cuánto suma. Sus importes los calcula siempre el servidor a partir de los precios del catálogo.

| Campo | Tipo | Long. | PK | FK | Oblig. | Descripción |
|---|---|---|---|---|---|---|
| `pedido_id` | UUID | — | Sí | No | Sí | Identificador único del pedido. Clave primaria. |
| `cliente_id` | UUID | — | No | No | Sí | Cliente al que se vende. Identificador común de INTEGRAX: la ficha del cliente vive en otro microproyecto, por eso no es clave foránea. |
| `estado_id` | UUID | — | No | estado_pedido.estado_id | Sí | Estado actual del pedido. Clave foránea a estado_pedido. |
| `vendedor_id` | UUID | — | No | vendedor.vendedor_id | Sí | Usuario que registró el pedido. Clave foránea a vendedor. |
| `subtotal` | NUMERIC | 14,2 | No | No | Sí | Suma de los subtotales de las líneas, sin impuestos. Lo calcula siempre el servidor. |
| `impuestos` | NUMERIC | 14,2 | No | No | Sí | IVA del pedido: subtotal × tasa configurada (19 %), redondeado a 2 decimales. |
| `descripcion` | VARCHAR | 500 | No | No | No | Observaciones libres sobre el pedido (por ejemplo, instrucciones de entrega). |
| `total` | NUMERIC | 14,2 | No | No | Sí | subtotal + impuestos. Calculado y verificado en el servidor; el navegador nunca envía importes. |
| `fecha_creacion` | TIMESTAMPTZ | — | No | No | Sí | Momento en que se registró el pedido, en UTC. Los reportes lo interpretan en la zona horaria de negocio (America/Bogota). |

## 3.4. detalle_pedido

Líneas del pedido: un registro por producto y cantidad. Resuelve la relación de muchos a muchos entre pedidos y productos y congela el precio aplicado en el momento de la venta.

| Campo | Tipo | Long. | PK | FK | Oblig. | Descripción |
|---|---|---|---|---|---|---|
| `detalle_pedido_id` | UUID | — | Sí | No | Sí | Identificador único de la línea. Clave primaria. |
| `pedido_id` | UUID | — | No | pedido.pedido_id | Sí | Pedido al que pertenece la línea. Clave foránea a pedido, con borrado en cascada. |
| `producto_id` | UUID | — | No | No | Sí | Producto vendido. Identificador común de INTEGRAX (el catálogo de productos vive en otro microproyecto; no es clave foránea). |
| `cantidad` | INTEGER | — | No | No | Sí | Unidades vendidas; entero mayor que cero (la API admite de 1 a 10.000). |
| `precio_unitario` | NUMERIC | 14,2 | No | No | Sí | Precio vigente del catálogo al registrar el pedido. Se conserva como dato histórico aunque el catálogo cambie después. |
| `subtotal` | NUMERIC | 14,2 | No | No | Sí | cantidad × precio_unitario, redondeado a 2 decimales. |

## 3.5. auditoria_pedido

Bitácora de solo-agregar de todo lo que ocurre sobre un pedido (crear, modificar, cambiar de estado, cancelar, solicitudes del cliente). El rol de base de datos de la API no puede modificarla ni borrarla.

| Campo | Tipo | Long. | PK | FK | Oblig. | Descripción |
|---|---|---|---|---|---|---|
| `auditoria_id` | UUID | — | Sí | No | Sí | Identificador único del evento. Clave primaria. |
| `pedido_id` | UUID | — | No | pedido.pedido_id | Sí | Pedido sobre el que ocurrió el evento. Clave foránea a pedido, con borrado en cascada. |
| `vendedor_id` | UUID | — | No | vendedor.vendedor_id | No | Usuario que realizó la acción. Admite NULL: las solicitudes del cliente llegan por integración, sin usuario interno. |
| `fecha` | TIMESTAMPTZ | — | No | No | Sí | Momento del evento, en UTC. |
| `descripcion` | TEXT | — | No | No | No | Detalle legible del evento (por ejemplo «Pendiente -> Confirmado. Motivo…» o el total anterior y el nuevo). |
| `accion` | VARCHAR | 40 | No | No | Sí | Tipo de evento: CREAR, MODIFICAR, CAMBIO_ESTADO, CANCELAR, SOLICITUD_MODIFICACION o SOLICITUD_CANCELACION. |

## 3.6. intento_login

Fallos de inicio de sesión (y de cambio de contraseña) usados para bloquear temporalmente a quien se equivoca 5 veces en 5 minutos. Vive en la base de datos para que el bloqueo valga entre varias instancias y tras reinicios.

| Campo | Tipo | Long. | PK | FK | Oblig. | Descripción |
|---|---|---|---|---|---|---|
| `intento_id` | UUID | — | Sí | No | Sí | Identificador único del intento fallido. Clave primaria. |
| `clave` | VARCHAR | 170 | No | No | Sí | Correo en minúscula (o «pw:» + correo cuando el fallo fue al cambiar la contraseña). Con ella se cuenta cuántos fallos lleva cada cuenta. |
| `fecha` | TIMESTAMPTZ | — | No | No | Sí | Momento del fallo, en UTC. Solo cuentan los de los últimos 5 minutos; los de más de 10 se borran solos. |

## 3.7. consumidor_api

Sistemas de INTEGRAX que consumen los servicios de integración de SALES-X. Cada uno tiene su propia clave, que se guarda como huella (hash) y se puede revocar o dejar expirar.

| Campo | Tipo | Long. | PK | FK | Oblig. | Descripción |
|---|---|---|---|---|---|---|
| `consumidor_id` | UUID | — | Sí | No | Sí | Identificador único del consumidor. Clave primaria. |
| `nombre` | VARCHAR | 80 | No | No | Sí | Nombre del sistema consumidor (por ejemplo «INTEGRAX-inicial»). Único. |
| `clave_hash` | VARCHAR | 64 | No | No | Sí | Huella SHA-256 de la clave. La clave en claro se muestra una sola vez al crearla y no se guarda. Única. |
| `activo` | BOOLEAN | — | No | No | Sí | Si es falso, la clave está revocada y deja de autenticar. |
| `expira` | TIMESTAMPTZ | — | No | No | No | Fecha de expiración opcional; pasada esa fecha la clave deja de valer. |
| `creado` | TIMESTAMPTZ | — | No | No | Sí | Fecha de creación del consumidor. |
| `ultimo_uso` | TIMESTAMPTZ | — | No | No | No | Última vez que la clave autenticó una petición (sirve para detectar claves en desuso). |
