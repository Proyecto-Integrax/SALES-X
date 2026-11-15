| Entidad | Qué representa | Campos | Clave primaria | FK | Oblig. |
|---|---|---:|---|---:|---:|
| `estado_pedido` | Catálogo cerrado de estados del ciclo de vida del pedido: Pendiente, Confirmado, En preparación, Enviado, Entregado y Cancelado. | 3 | `estado_id` | 0 | 2 |
| `vendedor` | Usuarios internos de SALES-X (vendedores y administradores). | 7 | `vendedor_id` | 0 | 7 |
| `pedido` | Cabecera de una venta: a quién se vende, quién la registró, en qué estado está y cuánto suma. | 9 | `pedido_id` | 2 | 8 |
| `detalle_pedido` | Líneas del pedido: un registro por producto y cantidad. | 6 | `detalle_pedido_id` | 1 | 6 |
| `auditoria_pedido` | Bitácora de solo-agregar de todo lo que ocurre sobre un pedido (crear, modificar, cambiar de estado, cancelar, solicitudes del cliente). | 6 | `auditoria_id` | 2 | 4 |
| `intento_login` | Fallos de inicio de sesión (y de cambio de contraseña) usados para bloquear temporalmente a quien se equivoca 5 veces en 5 minutos. | 3 | `intento_id` | 0 | 3 |
| `consumidor_api` | Sistemas de INTEGRAX que consumen los servicios de integración de SALES-X. | 7 | `consumidor_id` | 0 | 5 |

*Total: 7 tablas y 41 campos.*
