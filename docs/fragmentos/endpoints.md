| Método | Ruta | Autenticación | Rol | Descripción |
|---|---|---|---|---|
| GET | `/` | Ninguna (pública) | — | index |
| POST | `/api/v1/auth/cambiar-contrasena` | Sesión (incluso con cambio de contraseña pendiente) | Cualquier usuario | Cambiar la propia contraseña (REQ-17) |
| POST | `/api/v1/auth/login` | Ninguna (pública) | — | Iniciar sesión |
| POST | `/api/v1/auth/logout` | Ninguna (pública) | — | Cerrar sesión (elimina las cookies) |
| GET | `/api/v1/auth/me` | Sesión (incluso con cambio de contraseña pendiente) | Cualquier usuario | Usuario autenticado |
| GET | `/api/v1/catalogo/clientes` | Sesión (cookie `HttpOnly` o Bearer) | Vendedor o administrador | Consultar clientes |
| GET | `/api/v1/catalogo/productos` | Sesión (cookie `HttpOnly` o Bearer) | Vendedor o administrador | Consultar productos y disponibilidad |
| GET | `/api/v1/catalogo/productos/{producto_id}/disponibilidad` | Sesión (cookie `HttpOnly` o Bearer) | Vendedor o administrador | Disponibilidad de un producto (RF-11) |
| GET | `/api/v1/consumidores` | Sesión (cookie `HttpOnly` o Bearer) | Administrador | Listar consumidores |
| POST | `/api/v1/consumidores` | Sesión (cookie `HttpOnly` o Bearer) | Administrador | Crear consumidor (la clave se muestra una sola vez) |
| PATCH | `/api/v1/consumidores/{consumidor_id}` | Sesión (cookie `HttpOnly` o Bearer) | Administrador | Activar/desactivar o cambiar expiración |
| GET | `/api/v1/estados` | Sesión (cookie `HttpOnly` o Bearer) | Vendedor o administrador | Estados de pedido |
| GET | `/health` | Ninguna (pública) | — | Estado del servicio |
| GET | `/api/v1/integracion/clientes/{cliente_id}/pedidos` | API Key (`X-API-Key`) | Sistema consumidor | Pedidos de un cliente |
| GET | `/api/v1/integracion/disponibilidad/{producto_id}` | API Key (`X-API-Key`) | Sistema consumidor | Disponibilidad de un producto |
| GET | `/api/v1/integracion/pedidos/{pedido_id}` | API Key (`X-API-Key`) | Sistema consumidor | Consultar un pedido |
| POST | `/api/v1/integracion/pedidos/{pedido_id}/solicitudes` | API Key (`X-API-Key`) | Sistema consumidor | Solicitud de modificación o cancelación del cliente (CU-05) |
| GET | `/api/v1/pedidos` | Sesión (cookie `HttpOnly` o Bearer) | Vendedor o administrador | Consultar pedidos (RF-06) |
| POST | `/api/v1/pedidos` | Sesión (cookie `HttpOnly` o Bearer) | Vendedor o administrador | Registrar pedido (RF-01/02/03/07) |
| GET | `/api/v1/pedidos/historial/{cliente_id}` | Sesión (cookie `HttpOnly` o Bearer) | Vendedor o administrador | Historial de pedidos de un cliente (RF-09) |
| GET | `/api/v1/pedidos/solicitudes` | Sesión (cookie `HttpOnly` o Bearer) | Vendedor o administrador | Solicitudes de clientes recibidas (CU-05) |
| GET | `/api/v1/pedidos/{pedido_id}` | Sesión (cookie `HttpOnly` o Bearer) | Vendedor o administrador | Detalle de un pedido |
| PUT | `/api/v1/pedidos/{pedido_id}` | Sesión (cookie `HttpOnly` o Bearer) | Vendedor o administrador | Modificar pedido (RF-04) |
| GET | `/api/v1/pedidos/{pedido_id}/auditoria` | Sesión (cookie `HttpOnly` o Bearer) | Vendedor o administrador | Auditoría del pedido (RNF-05) |
| POST | `/api/v1/pedidos/{pedido_id}/cancelar` | Sesión (cookie `HttpOnly` o Bearer) | Vendedor o administrador | Cancelar pedido (RF-05) |
| PATCH | `/api/v1/pedidos/{pedido_id}/estado` | Sesión (cookie `HttpOnly` o Bearer) | Vendedor o administrador | Gestionar estado del pedido (RF-08) |
| GET | `/api/v1/reportes/ventas` | Sesión (cookie `HttpOnly` o Bearer) | Vendedor o administrador | Reporte de ventas (RF-10) |
| GET | `/api/v1/reportes/ventas.csv` | Sesión (cookie `HttpOnly` o Bearer) | Vendedor o administrador | Reporte de ventas en CSV |
| GET | `/api/v1/vendedores` | Sesión (cookie `HttpOnly` o Bearer) | Administrador | Listar usuarios (admin) |
| POST | `/api/v1/vendedores` | Sesión (cookie `HttpOnly` o Bearer) | Administrador | Crear usuario (admin) |
| PATCH | `/api/v1/vendedores/{vendedor_id}` | Sesión (cookie `HttpOnly` o Bearer) | Administrador | Actualizar usuario (admin) |
