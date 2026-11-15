---
codigo: SALESX-ACTA
titulo: Acta de entrega de cuentas iniciales y primer ingreso
---

**Proyecto:** SALES-X · Gestión de ventas y pedidos
**Versión:** 1.2.0
**Fecha:** 14 de noviembre de 2026
**Responsables:** Julio Cesar Velasquez Arango

# 1. Objeto

Dejar constancia de las cuentas creadas para el primer ingreso a la aplicación, de su rol y de la obligación de cambiar la contraseña temporal antes de usar el sistema.

> **Este documento puede contener claves temporales en texto plano.** Las de la tabla de **demostración** son públicas (están en el README) y solo sirven en el entorno local. Las del entorno de **producción** se entregan por un canal seguro y aparte, **no se escriben en esta acta**, y la acta con claves debe destruirse cuando todas las cuentas hayan cambiado su contraseña.

# 2. Cuentas creadas

## 2.1 Entorno de demostración (`iniciar.bat`, datos de ejemplo)

| # | Nombre | Cargo | Rol | Usuario (correo) | Clave temporal | ¿Debe cambiarla? |
|---|---|---|---|---|---|---|
| 1 | Administrador SALES-X | Administrador | `admin` | admin@salesx.local | `Admin2026*` | No (cuenta de demostración) |
| 2 | Vendedor Demo | Vendedor | `vendedor` | vendedor@salesx.local | `Ventas2026*` | No (cuenta de demostración) |

## 2.2 Entorno de producción (se completa al instalar)

| # | Nombre | Cargo | Rol | Usuario (correo) | Clave temporal | ¿Debe cambiarla? |
|---|---|---|---|---|---|---|
| 1 | ____________________ | Administrador | `admin` | ____________________ | *(canal seguro)* | Ya la definió el instalador |
| 2 | ____________________ | ____________ | `vendedor` | ____________________ | *(canal seguro)* | **Sí**, en el primer ingreso |
| 3 | ____________________ | ____________ | `vendedor` | ____________________ | *(canal seguro)* | **Sí**, en el primer ingreso |
| 4 | ____________________ | ____________ | ______ | ____________________ | *(canal seguro)* | **Sí**, en el primer ingreso |

# 3. Primer ingreso

1. Abrir la aplicación en la dirección indicada (en modo local: `http://localhost:8000`).
2. Ingresar con el correo y la clave temporal de la tabla.
3. Para las cuentas que la administradora creó, la aplicación abre automáticamente la pantalla **«Debe cambiar su contraseña»** y no muestra nada más hasta completarla.
4. Escribir la clave temporal, la nueva y su confirmación.
5. Al guardar, el sistema entra con la clave definitiva. La clave temporal deja de servir.
6. Verificar que el menú muestra solo las opciones de su rol (el menú *Usuarios* e *Integraciones* es solo del administrador).

# 4. Reglas de la contraseña

- Mínimo **10 caracteres**, con **letras y números** (se recomiendan 12 o más).
- No puede ser una contraseña común (por ejemplo, «Password123») ni contener la parte del correo anterior a la arroba.
- Debe ser **distinta** de la actual.
- Se guarda **cifrada con bcrypt** (coste 12): ni el administrador ni el equipo pueden leerla.
- No se debe compartir ni reutilizar la de otros sistemas.

# 5. Bloqueos y recuperación

- **Bloqueo:** tras **5 intentos fallidos en 5 minutos** la cuenta se bloquea temporalmente (el sistema responde «Demasiados intentos fallidos»); basta esperar 5 minutos. El mismo límite protege el cambio de contraseña. El contador vive en la base de datos, de modo que vale aunque haya varias instancias.
- **Recuperación:** en esta versión **no existe recuperación de contraseña por autoservicio** (no se envían correos ni mensajes). Si una persona olvida su contraseña, **el administrador se la restablece** desde *Usuarios → Cambiar contraseña*; el sistema vuelve a exigirle definir una propia en su siguiente ingreso.
- **Cuenta comprometida:** el administrador puede **desactivarla** de inmediato; un usuario inactivo pierde el acceso en su siguiente petición.
- **Último administrador:** un administrador no puede desactivarse a sí mismo ni quitarse el rol, para no quedarse sin acceso de administración.

# 6. Creación de las cuentas (reproducible)

Las cuentas no se crean a mano: salen de la configuración, de modo que el procedimiento se puede repetir.

```
# Administrador inicial (se crea una sola vez, al arrancar, a partir de estas variables de entorno)
ADMIN_EMAIL=correo-del-administrador
ADMIN_PASSWORD=contraseña-de-al-menos-10-caracteres-con-letras-y-números

# Vendedor de demostración: solo si SEED_DEMO_USERS=true (nunca en producción)
python -m app.demo          # crea la base local con usuarios y 40 pedidos de ejemplo

# Usuarios adicionales: pantalla Usuarios (administrador) o POST /api/v1/vendedores
```

En producción (`ENVIRONMENT=production`) el sistema **se niega a iniciar** con la contraseña de administrador de ejemplo, con claves por defecto o con `SEED_DEMO_USERS=true`.

# 7. Custodia

- Esta acta **no se publica** ni se guarda en el repositorio con claves reales.
- Las claves temporales se entregan **por separado** a cada persona (no por el mismo canal que la acta).
- Se registra quién recibió cada cuenta y cuándo (sección 8). Cuando todas las cuentas de producción hayan cambiado su clave, **se destruye la copia con claves**.
- Se recomienda guardar la contraseña del administrador en un gestor de contraseñas.

## Verificación del administrador

☐ Contraseña del administrador cambiada y guardada en un gestor de contraseñas.
☐ `SECRET_KEY` e `INTEGRATION_API_KEY` generadas aleatoriamente (no las de ejemplo).
☐ Usuarios de demostración eliminados o desactivados.
☐ Claves de integración: una por sistema consumidor (pantalla *Integraciones*); revocada «INTEGRAX-inicial» cuando ya no se use.
☐ Acceso mediante HTTPS comprobado.
☐ Copia de seguridad inicial de la base de datos realizada.

# 8. Firmas

| Entrega (Administrador) | Recibe (Responsable del área de ventas) |
|---|---|
| Nombre: ____________________ | Nombre: ____________________ |
| Firma: _____________________ | Firma: _____________________ |
| Fecha: _____________________ | Fecha: _____________________ |
