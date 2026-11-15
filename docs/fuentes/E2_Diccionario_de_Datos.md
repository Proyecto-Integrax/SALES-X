---
codigo: SALESX-E2
evidencia: 2 de 7
titulo: Diccionario de datos
descripcion: Qué significa exactamente cada dato que guarda SALES-X. Los datos técnicos —tipo, longitud, claves y obligatoriedad— se leen de las tablas del programa; las descripciones de negocio se validan contra ellas, de modo que no puede existir un campo sin documentar.
metadatos:
  - Sistema | SALES-X · Gestión de ventas y pedidos
  - Entidades (tablas) | 7
  - Campos documentados | 41 de 41
  - Claves foráneas | 5
  - Valores de dominio descritos | 4 (estados, roles, acciones de auditoría, agrupaciones)
pie: SALES-X · Evidencia 2 de 7 · Diccionario de datos · 7 tablas y 41 campos, todos documentados. Generado a partir del esquema real.
---

# 1. Propósito y método

Este diccionario define cada campo que utiliza SALES-X. Responde a la pregunta de la evidencia: **¿qué significa exactamente cada dato que guardamos?**

Los datos técnicos —tipo, longitud, clave primaria, clave foránea y obligatoriedad— no se han escrito a mano: se leen del modelo de datos del programa (`app/models.py`, que a su vez coincide con `sql/01_schema.sql`). Las descripciones de negocio se mantienen en `scripts/generar_diccionario.py` y se validan contra el esquema: **si alguien añade una columna y no la describe, el generador falla**, y tampoco admite una descripción que hable de un campo inexistente.

### Convenciones de este documento

- **Tipo:** tipo real en PostgreSQL. `NUMERIC(14,2)` es un decimal con 14 dígitos, 2 de ellos decimales.
- **Long.:** longitud máxima. Para `NUMERIC` se indica precisión y escala.
- **PK:** forma parte de la clave primaria. **FK:** es clave foránea; se indica a qué campo apunta.
- **Oblig.:** si el campo admite NULL (No) o no (Sí).
- Los identificadores son **UUID** generados por la aplicación (no secuencias): no revelan cuántos pedidos existen ni se pueden adivinar.
- Las fechas son `TIMESTAMPTZ` (con zona horaria) y se guardan en UTC.

# 2. Panorama de las entidades

{{incluir: fragmentos/diccionario_panorama.md}}

# 3. Diccionario por entidad

{{incluir: fragmentos/diccionario_entidades.md}}

# 4. Valores de dominio

Algunos campos de texto solo admiten un conjunto cerrado de valores. Se describen aquí porque la interfaz y la API dependen de ellos.

### Estados del pedido (`estado_pedido.nombre`)

| Estado | Significado | Puede pasar a |
|---|---|---|
| Pendiente | Registrado, sin confirmar con el cliente. Se puede modificar. | Confirmado, Cancelado |
| Confirmado | Confirmado con el cliente. Se puede modificar. | En preparación, Cancelado |
| En preparación | En alistamiento. Ya no se modifica. | Enviado, Cancelado |
| Enviado | Despachado al cliente. | Entregado |
| Entregado | Recibido por el cliente. **Estado final.** | — |
| Cancelado | Cancelado con motivo. **Estado final.** | — |

### Roles (`vendedor.rol`)

| Rol | Qué puede hacer |
|---|---|
| `vendedor` | Registrar, consultar, modificar, cancelar pedidos y cambiar su estado; consultar el catálogo; generar reportes. |
| `admin` | Todo lo anterior y, además, crear/desactivar usuarios, restablecer contraseñas y administrar las claves de integración. |

### Acciones de auditoría (`auditoria_pedido.accion`)

| Acción | Cuándo se registra | Qué guarda `descripcion` |
|---|---|---|
| `CREAR` | Al registrar el pedido | Número de productos y total |
| `MODIFICAR` | Al cambiar observaciones o líneas | Cambios realizados y total anterior → nuevo |
| `CAMBIO_ESTADO` | Al pasar de un estado a otro | «anterior -> nuevo» y comentario opcional |
| `CANCELAR` | Al cancelar | «estado -> Cancelado» y el motivo |
| `SOLICITUD_MODIFICACION` / `SOLICITUD_CANCELACION` | Cuando un sistema externo registra la solicitud del cliente | Detalle, solicitante y consumidor que la envió |

### Otros valores

| Concepto | Valores |
|---|---|
| Agrupación de reportes | `dia`, `mes` |
| Moneda y redondeo | COP, 2 decimales, redondeo half-up |
| Zona horaria de negocio | `America/Bogota` (configurable con `BUSINESS_TZ`) |

# 5. Reglas de integridad asociadas a los campos

| Regla | Dónde se aplica |
|---|---|
| El correo de un usuario y el nombre de un estado o consumidor no se repiten. | Restricción `UNIQUE` en la base de datos. |
| `rol` solo admite «admin» o «vendedor»; `cantidad` > 0; `precio_unitario` y `total` ≥ 0. | Restricción `CHECK` en la base de datos. |
| Los importes de un pedido los calcula siempre el servidor; el navegador nunca los envía. | Servicio de pedidos (`calcular_total`) y esquemas de entrada, que ignoran importes enviados. |
| El `precio_unitario` se toma del catálogo, nunca de la petición. | `app/services/pedidos.py` (`_construir_detalles`). |
| La contraseña nunca se guarda en texto plano: solo su hash bcrypt (coste 12). | `app/security.py`. |
| La clave de integración nunca se guarda: solo su hash SHA-256; se muestra una sola vez. | `app/routers/consumidores.py`. |
| Los eventos de auditoría no se modifican ni se borran. | El rol de base de datos `salesx_app` no tiene `UPDATE` ni `DELETE` sobre `auditoria_pedido` (`sql/03_rol_aplicacion.sql`). |
| Un pedido solo puede modificarse en *Pendiente* o *Confirmado*, y solo con transiciones válidas. | Servicio de pedidos, con bloqueo de fila para evitar condiciones de carrera. |
| Las fechas se guardan en UTC y se interpretan en la zona de negocio al reportar. | `app/timeutil.py`. |
