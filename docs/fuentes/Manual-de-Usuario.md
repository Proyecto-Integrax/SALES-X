# Manual de Usuario — SALES-X

Dirigido al **usuario de ventas** y al **administrador**. Versión 1.2.0 · 14 de noviembre de 2026. Las capturas de pantalla están en la Evidencia 7 (§7.4).

## 1. Ingreso
1. Abra la dirección del sistema en su navegador (en modo local: `http://localhost:8000`).
2. Escriba su **correo** y **contraseña** y pulse *Ingresar*.
3. **Primer ingreso:** si el administrador le creó la cuenta (o le restableció la contraseña), el sistema le pedirá definir una **contraseña propia** antes de continuar: escriba la actual, la nueva (mínimo 10 caracteres, con letras y números, que no sea común ni contenga su usuario) y repítala.
4. Tras 5 intentos fallidos se bloquea el acceso durante 5 minutos.
5. Para cambiar su contraseña más adelante use **Cambiar contraseña**; para salir, **Cerrar sesión** (ambos abajo a la izquierda). La sesión dura 8 horas y se cierra al pulsar *Cerrar sesión*.

## 2. Panel
Muestra el resumen del mes: ventas, número de pedidos, ticket promedio y cancelados; los últimos pedidos; los pedidos por estado y las **solicitudes de clientes** (modificación/cancelación) que esperan atención. Haga clic en un pedido para abrirlo.

## 3. Registrar un pedido
1. Menú **Nuevo pedido**.
2. Elija el **cliente**.
3. Elija un **producto** (se muestra el precio y la disponibilidad; los agotados aparecen bloqueados), indique la **cantidad** y pulse *Agregar*. Repita para más productos.
4. Ajuste cantidades o use *Quitar* si es necesario. El resumen muestra **subtotal, IVA y total** al instante.
5. Escriba observaciones si lo desea y pulse **Registrar pedido**.

Notas: el precio lo toma el sistema del catálogo; si otro usuario agotó el producto, el sistema lo avisa al guardar. Si dos personas actúan sobre el mismo pedido a la vez (por ejemplo, una lo envía y otra lo cancela), el sistema las atiende **una tras otra**: la segunda recibe un aviso de transición no permitida y debe recargar el pedido.

## 4. Consultar pedidos
Menú **Pedidos**: filtre por estado, cliente y rango de fechas; use *Anterior/Siguiente* para paginar. Para ver el historial de un cliente, filtre por ese cliente.

## 5. Detalle, estados, modificación y cancelación
Al abrir un pedido verá sus productos, totales y la **auditoría** (quién hizo qué y cuándo).

| Acción | Cómo |
|---|---|
| Cambiar estado | Botón «Pasar a …». Orden: Pendiente → Confirmado → En preparación → Enviado → Entregado. Puede añadir un comentario. |
| Modificar | Botón **Modificar** (solo en *Pendiente* o *Confirmado*): cambie productos, cantidades u observaciones. |
| Cancelar | Botón **Cancelar pedido** (hasta *En preparación*): escriba el motivo. Un pedido *Enviado* o *Entregado* ya no puede cancelarse. |

## 6. Solicitudes de clientes
Cuando un cliente solicita modificar o cancelar un pedido (por los servicios de integración), la solicitud aparece en el **Panel** y en la auditoría del pedido. **No cambia el pedido por sí sola:** revísela y use *Modificar* o *Cancelar*.

## 7. Reportes
Menú **Reportes**: elija *Desde*, *Hasta* y agrupar por **día** o **mes** y pulse *Generar*. Verá ventas totales, subtotal, impuestos, ticket promedio y la tabla por período. Las ventas **no incluyen pedidos cancelados**. Use **Descargar CSV** (abre en Excel) o **Imprimir**.

## 8. Administración de usuarios (solo administrador)
Menú **Usuarios**: cree usuarios (nombre, correo, contraseña inicial de al menos 10 caracteres con letras y números, rol), **cambie contraseñas** y **active/desactive** cuentas. La contraseña que usted asigna es **temporal**: la persona deberá cambiarla en su próximo ingreso. No puede desactivarse a sí mismo. Los usuarios no se borran para conservar la trazabilidad.

## 8.1 Integraciones: claves de otros sistemas (solo administrador)
Menú **Integraciones**: cada sistema de INTEGRAX que consulta SALES-X usa **su propia clave**.
1. Escriba el nombre del sistema (y, si quiere, una fecha de expiración) y pulse **Generar clave**.
2. **Copie la clave en ese momento:** no se vuelve a mostrar (el sistema solo guarda una huella).
3. Entregue la clave al responsable del otro sistema por un canal seguro; la usará en la cabecera `X-API-Key`.
4. Para **revocar** una clave use *Revocar*; para **rotarla**, cree una nueva, configure el otro sistema y revoque la anterior. La tabla muestra la fecha del último uso de cada clave.

## 9. Mensajes frecuentes

| Mensaje | Qué significa / qué hacer |
|---|---|
| «Disponibilidad insuficiente…» | Reduzca la cantidad o elija otro producto. |
| «Transición no permitida…» | El estado elegido no es el siguiente válido; el mensaje indica los permitidos. |
| «No se puede modificar un pedido en estado…» | Solo se modifica en Pendiente/Confirmado. |
| «Sesión expirada» | Ingrese de nuevo. |
| «Debe cambiar su contraseña antes de continuar» | Defina una contraseña propia en la pantalla que aparece al ingresar. |
| «La contraseña actual es incorrecta» | Revise la contraseña actual; tras 5 fallos se bloquea el cambio 5 minutos. |
| «Token CSRF inválido o ausente» | Recargue la página e ingrese de nuevo. |
| «Demasiados intentos fallidos» | Espere 5 minutos. |
| Error 502 al registrar (servicio de Clientes/Productos) | El servicio externo no responde; no se creó ningún pedido. Intente de nuevo en unos minutos o avise al administrador. |

## 10. Uso en teléfono
La interfaz se adapta a pantallas estrechas: el menú pasa a la parte superior, las tarjetas se apilan y las tablas se desplazan dentro de su recuadro, sin mover toda la página.
