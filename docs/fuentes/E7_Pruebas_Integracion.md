---
codigo: SALESX-E7
evidencia: 7 de 7
titulo: Pruebas de integración
descripcion: Resultados de la suite de integración de SALES-X ejecutada sobre el sistema en funcionamiento, más las pruebas de carga, de Docker y de integración REST. Verifica que las piezas —interfaz, API y base de datos— funcionan juntas y cumplen las reglas de negocio. 63 pruebas, 0 fallos.
metadatos:
  - Sistema | SALES-X · Gestión de ventas y pedidos
  - Tipo de prueba | Integración de extremo a extremo (API + base de datos)
  - Pruebas ejecutadas | 63
  - Aprobadas | 63
  - Fallidas | 0
  - Casos de control documentados | 63 (CP-01 a CP-63)
  - Defectos hallados y corregidos | 7
pie: SALES-X · Evidencia 7 de 7 · Pruebas de integración · 63 pruebas aprobadas, 0 fallidas; 7 defectos hallados y corregidos durante las pruebas.
---

# 1. Objetivo

Demostrar que los componentes de SALES-X funcionan correctamente en conjunto. Responde a la pregunta de la evidencia: **¿cómo comprobamos que los componentes funcionan bien juntos?**

Una prueba unitaria verifica una función aislada; aquí lo que se verifica es el recorrido completo de una operación:

**Usuario (navegador o sistema externo) → petición HTTP → API REST (FastAPI) → reglas de negocio → PostgreSQL → respuesta JSON**

Cada comprobación recorre esa cadena completa y verifica el resultado de negocio, no solo que la llamada responda.

# 2. Alcance

| Se incluye | Se excluye de esta evidencia |
|---|---|
| Ejecución real de la API contra la base de datos (SQLite y PostgreSQL), con datos de demostración. | Pruebas unitarias de funciones aisladas (la cobertura principal del proyecto es de integración). |
| Autenticación, autorización por rol, sesión por cookie, CSRF y bloqueo por intentos. | Pruebas de penetración formales con herramientas dinámicas (ver el informe de auditoría). |
| Todos los módulos: pedidos, estados, auditoría, reportes, catálogo, integración y usuarios. | Pruebas de usabilidad con usuarios reales. |
| Reglas de negocio: precio del catálogo, totales exactos, transiciones válidas, auditoría. | Compatibilidad en todos los navegadores del mercado (se revisó en Edge). |
| Integración REST con Clientes y Productos (servicios simulados), incluidas sus fallas. | Pruebas con los servicios **reales** de Clientes y Productos (aún no existen). |
| Concurrencia: dos usuarios sobre el mismo pedido. | Medición de disponibilidad en operación (RNF-03). |
| Carga, Docker Compose, respaldo/restauración, permisos del rol de base de datos. | Pruebas sobre un servidor Linux de despliegue. |

# 3. Entorno de pruebas

| Elemento | Detalle |
|---|---|
| Sistema bajo prueba | SALES-X versión 1.2.0 |
| Sistema operativo | Windows 11 Pro; contenedores Linux con Docker Desktop 4.99 |
| Lenguaje y marco | Python 3.13 (3.12 en la imagen Docker), FastAPI, SQLAlchemy 2, pytest 9 |
| Bases de datos | SQLite temporal (por defecto) y **PostgreSQL 18.6** local (`salesx_test`); PostgreSQL 16 en Docker |
| Cliente de pruebas | Cliente HTTP de FastAPI (peticiones reales a la API, independientes del navegador) |
| Catálogo de Clientes y Productos | Proveedor simulado interno y, para la integración REST, un servicio HTTP simulado (`mocks/integrax_mock.py`) |
| Datos de entrada | Datos de demostración: 5 clientes y 10 productos (uno agotado); usuarios de prueba creados por cada caso |
| Automatización | `python -m pytest` (desde `sales-x/`); `TEST_DATABASE_URL` para PostgreSQL |

> **Nota sobre la repetibilidad.** Cada ejecución parte de una base limpia: SQLite es temporal y, en PostgreSQL, la suite vacía la base `salesx_test` (se niega a limpiar cualquier base cuyo nombre no termine en `_test`). Cada caso crea sus propios usuarios con identificadores únicos, por lo que puede repetirse sin interferencias.

# 4. Procedimiento

1. **Preparar el entorno:** instalar dependencias (`pip install -r requirements.txt`). Para PostgreSQL, crear una base `salesx_test` y definir `TEST_DATABASE_URL`.
2. **Ejecutar la suite:** `python -m pytest -v`. La suite crea sus propios datos, ejecuta los casos y devuelve un código de salida distinto de cero si alguno falla.
3. **Repetirla sobre PostgreSQL**, donde además se ejecutan las pruebas de concurrencia (necesitan bloqueo de filas).
4. **Registrar el resultado:** la salida completa se guarda como anexo de esta evidencia.
5. **Analizar los fallos:** si hay casos fallidos, se revisa la causa, se corrige y se repite la ejecución (ver sección 8).

```
# Secuencia completa
python -m pip install -r requirements.txt
python -m pytest -v                                   # SQLite: 60 aprobadas, 3 omitidas (concurrencia)

set TEST_DATABASE_URL=postgresql+psycopg2://salesx:CLAVE@localhost:5432/salesx_test
python -m pytest -v                                   # PostgreSQL: 63 aprobadas
```

# 5. Resultado de la ejecución

**63** pruebas ejecutadas · **63** aprobadas · **0** fallidas

**Resultado global: TODAS LAS PRUEBAS APROBADAS** (PostgreSQL 18.6). En SQLite se aprueban las 60 que no requieren bloqueo de filas y las 3 de concurrencia se omiten por diseño.

## 5.1 Resultado por bloque

La suite está organizada en bloques temáticos. Este es el recuento de cada uno, leído de la recolección real de pytest:

{{incluir: fragmentos/pruebas_por_bloque.md}}

# 6. Casos de prueba de control

Se documentan **63 casos de control** (CP-01 a CP-63) que cubren todos los requisitos de la Evidencia 3. Cada caso declara sus datos de entrada, el resultado esperado, el resultado obtenido y su estado (PASS o FAIL). El resultado obtenido se comprueba con las aserciones de una prueba realmente ejecutada; la Evidencia 6 (§3) relaciona cada CP con su función de prueba y el anexo A lista la salida completa de la ejecución. Los 63 casos terminaron en **PASS**. Los errores encontrados y su corrección están en la sección 8, y las capturas en la sección 9.

| ID | Módulo | Objetivo | Datos de entrada | Resultado esperado | Resultado obtenido | Estado | Requisitos |
|---|---|---|---|---|---|---|---|
| CP-01 | Salud | Comprobar el punto de salud. | `GET /health` sin sesión. | 200 y base de datos «ok». | Coincide con lo esperado | PASS | RNF-03 |
| CP-02 | Autenticación | Iniciar sesión. | Correo y contraseña válidos del vendedor. | 200 con token; `/auth/me` no expone la contraseña. | Coincide con lo esperado | PASS | RNF-04, RNF-09 |
| CP-03 | Autenticación | Rechazar credenciales erróneas. | Contraseña incorrecta. | 401. | Coincide con lo esperado | PASS | RNF-04 |
| CP-04 | Autenticación | Proteger los endpoints sin sesión. | Pedidos, reportes y catálogo sin token. | 401 en todos. | Coincide con lo esperado | PASS | RNF-04, CA-09 |
| CP-05 | Autenticación | Rechazar un token alterado. | `Bearer abc.def.ghi`. | 401. | Coincide con lo esperado | PASS | RNF-04, CA-09 |
| CP-06 | Autenticación | Bloquear tras intentos fallidos. | 5 contraseñas erróneas y un sexto intento. | 429 en el sexto. | Coincide con lo esperado | PASS | RNF-12, CA-10 |
| CP-07 | Usuarios | Restringir la administración al rol admin. | Un vendedor consulta `/vendedores`. | 403. | Coincide con lo esperado | PASS | RF-13, RNF-13 |
| CP-08 | Usuarios | Crear un usuario y detectar duplicados. | Administrador crea un usuario; repite el mismo correo. | 201 y luego 409. | Coincide con lo esperado | PASS | RF-13 |
| CP-09 | Catálogo | Consultar disponibilidad. | Búsqueda «mouse»; producto agotado; producto inexistente. | 1 resultado; disponibilidad 0; 404. | Coincide con lo esperado | PASS | RF-11 |
| CP-10 | Pedidos | Registrar un pedido y calcular sus totales. | Cliente y «Mouse inalámbrico» × 3 (precio 55.000). | 201, *Pendiente*; subtotal 165.000, IVA 31.350, total 196.350. | Coincide con lo esperado | PASS | RF-01, RF-07, CA-01 |
| CP-11 | Pedidos | Tomar el precio del catálogo, no de la petición. | Línea con `precio_unitario` = 1 enviado por el cliente. | Se usa 55.000. | Coincide con lo esperado | PASS | RF-03, RN-01 |
| CP-12 | Pedidos | Consolidar líneas repetidas. | Dos líneas del mismo producto (1 y 4 unidades). | Una línea con cantidad 5. | Coincide con lo esperado | PASS | RF-03 |
| CP-13 | Pedidos | Validar las entradas. | Cantidad 0 o −5; sin líneas; cliente o producto inexistente; agotado; más que las existencias. | 422, 422, 422, 422, 409, 409. | Coincide con lo esperado | PASS | RF-02, RF-03, CA-02 |
| CP-14 | Pedidos | Consultar, filtrar y paginar. | Detalle; filtro por estado y cliente; UUID inválido; `size` = 1000. | 200; 404 si no existe; 422 en los inválidos. | Coincide con lo esperado | PASS | RF-06 |
| CP-15 | Pedidos | Ver el historial de un cliente. | Cliente con pedidos. | Total de pedidos y total comprado. | Coincide con lo esperado | PASS | RF-09 |
| CP-16 | Pedidos | Modificar un pedido. | Cambiar a 10 unidades y observaciones; cuerpo vacío. | 200 con subtotal recalculado; 422 con cuerpo vacío. | Coincide con lo esperado | PASS | RF-04 |
| CP-17 | Estados | Recorrer el ciclo de vida. | Confirmado → En preparación → Enviado → Entregado. | 200 en cada paso. | Coincide con lo esperado | PASS | RF-08 |
| CP-18 | Estados | Rechazar transiciones inválidas. | *Pendiente* → *Entregado*; un estado inexistente. | 409 indicando las permitidas; 422. | Coincide con lo esperado | PASS | RF-08, CA-03 |
| CP-19 | Estados | Cancelar y respetar las reglas posteriores. | Motivo de 1 letra; motivo válido; cancelar de nuevo; modificar; cambiar de estado. | 422, 200, 409, 409, 409. | Coincide con lo esperado | PASS | RF-05, CA-04 |
| CP-20 | Estados | No cancelar un pedido enviado. | Cancelar un pedido en *Enviado*. | 409. | Coincide con lo esperado | PASS | RF-05, CA-05 |
| CP-21 | Auditoría | Registrar cada operación. | Crear, modificar, cambiar de estado y cancelar un pedido. | Auditoría: CREAR, MODIFICAR, CAMBIO_ESTADO, CANCELAR. | Coincide con lo esperado | PASS | RNF-05, CA-06 |
| CP-22 | Reportes | Excluir los cancelados de las ventas. | Un pedido válido de 2 u. y otro de 7 u. que se cancela. | Las ventas suben solo por el válido. | Coincide con lo esperado | PASS | RF-10, CA-07 |
| CP-23 | Reportes | Exportar a CSV y agrupar por mes. | CSV; agrupar por mes; agrupación inválida. | Cabecera correcta; períodos AAAA-MM; 422. | Coincide con lo esperado | PASS | RF-10 |
| CP-24 | Integración | Exigir la API Key. | Sin clave; clave errónea; un JWT en lugar de la clave; clave válida. | 401, 401, 401, 200. | Coincide con lo esperado | PASS | RF-12, CA-13 |
| CP-25 | Integración | Registrar la solicitud de un cliente. | Solicitud de cancelación; tipo inválido. | 202; el pedido no cambia; auditoría «Sistema externo»; 422. | Coincide con lo esperado | PASS | RF-12, CA-14 |
| CP-26 | Seguridad | Resistir la inyección SQL en los filtros. | `estado` = `' OR 1=1; DROP TABLE pedido;--`. | 200, sin datos, tablas intactas. | Coincide con lo esperado | PASS | RNF-16 |
| CP-27 | Seguridad | Enviar cabeceras de seguridad. | `GET /health` y `GET /`. | `nosniff`, `X-Frame-Options: DENY`, CSP. | Coincide con lo esperado | PASS | RNF-15 |
| CP-28 | Configuración | Rechazar la configuración insegura en producción. | Claves por defecto, SQLite y usuarios de demostración. | 5 problemas detectados. | Coincide con lo esperado | PASS | RNF-14, CA-17 |
| CP-29 | Configuración | Aceptar una configuración robusta. | Claves largas, PostgreSQL, sin usuarios demo. | Sin problemas. | Coincide con lo esperado | PASS | RNF-14 |
| CP-30 | Reportes | Asignar el día en hora de Colombia. | Pedido de las 23:48 del 13/nov (04:48 UTC del 14/nov). | Cae en el 13/nov (antes aparecía vacío). | Coincide con lo esperado | PASS | RF-10, CA-08 |
| CP-31 | Reportes | Convertir fechas a hora local. | Fecha UTC sin zona (SQLite). | 13/nov 23:48. | Coincide con lo esperado | PASS | RF-10 |
| CP-32 | Seguridad | Bloqueo de login compartido en la base de datos. | 5 fallos y consulta desde otra sesión de BD. | El bloqueo se ve desde otra sesión; el sexto intento da 429. | Coincide con lo esperado | PASS | RF-14, CA-10 |
| CP-33 | Seguridad | Limpiar los fallos al ingresar bien. | 3 fallos y luego un ingreso correcto. | Los fallos se borran. | Coincide con lo esperado | PASS | RF-14 |
| CP-34 | Integración | Clave de consumidor: una sola vez y su uso. | Crear un consumidor; usar la clave; listar. | Clave `sx_…` solo al crear; el listado no la muestra; queda el último uso y la auditoría nombra al consumidor. | Coincide con lo esperado | PASS | RF-15 |
| CP-35 | Integración | Revocar y reactivar una clave. | Desactivar y volver a activar. | 401 y luego vuelve a autenticar. | Coincide con lo esperado | PASS | RF-15, CA-13 |
| CP-36 | Integración | Rechazar una clave expirada. | Clave con fecha vencida. | 401. | Coincide con lo esperado | PASS | RF-15, CA-13 |
| CP-37 | Integración | Validar y proteger la administración de consumidores. | Un vendedor; expiración pasada; nombre repetido; id inexistente. | 403, 422, 409, 404. | Coincide con lo esperado | PASS | RF-15 |
| CP-38 | Integración | Mensaje genérico y consumidor inicial. | Clave inexistente. | 401 genérico; existe «INTEGRAX-inicial». | Coincide con lo esperado | PASS | RF-15 |
| CP-39 | Sesión | Cookie `HttpOnly` y cookie CSRF legible. | Iniciar sesión. | Sesión `HttpOnly` + `SameSite=Strict`; la cookie CSRF sí es legible. | Coincide con lo esperado | PASS | RF-16, RNF-10 |
| CP-40 | Sesión | Exigir CSRF en las escrituras por cookie. | POST sin cabecera, con cabecera falsa y con la correcta. | 403, 403, 201. | Coincide con lo esperado | PASS | RF-16, RNF-11, CA-12 |
| CP-41 | Sesión | No exigir CSRF a un cliente de API. | POST con `Bearer` y sin cookie. | 201. | Coincide con lo esperado | PASS | RF-16 |
| CP-42 | Sesión | Cerrar sesión. | Cerrar sesión y consultar `/auth/me`. | 204 y luego 401. | Coincide con lo esperado | PASS | RF-16 |
| CP-43 | Contraseñas | Aplicar la política de contraseñas. | Corta; solo letras; solo números; común; con el usuario. | 422 en todas. | Coincide con lo esperado | PASS | RF-17, RNF-09 |
| CP-44 | Contraseñas | Cambio obligatorio en el primer ingreso. | Usuario nuevo; pedidos y catálogo; cambio correcto. | 403 hasta cambiarla; luego opera; la anterior ya no sirve. | Coincide con lo esperado | PASS | RF-17, CA-11 |
| CP-45 | Contraseñas | Cambio obligatorio tras un restablecimiento. | El administrador cambia la contraseña de un usuario. | Vuelve a exigir el cambio. | Coincide con lo esperado | PASS | RF-17 |
| CP-46 | Contraseñas | Bloquear también el cambio de contraseña. | 5 contraseñas actuales erróneas. | 429 en el sexto intento. | Coincide con lo esperado | PASS | RF-17, RNF-12 |
| CP-47 | Integración REST | Listar y obtener clientes y productos. | Servicio HTTP simulado de Clientes y Productos. | 3 clientes y 5 productos; el precio 45.500,5 conserva su exactitud. | Coincide con lo esperado | PASS | RF-02, RF-03, RF-11 |
| CP-48 | Integración REST | Tratar un 404 externo como «no existe». | Cliente o producto inexistente. | «No existe» (sin error). | Coincide con lo esperado | PASS | RF-02, RF-03 |
| CP-49 | Integración REST | Tolerar un servicio caído. | Nadie escucha en el puerto. | 502. | Coincide con lo esperado | PASS | RNF-23 |
| CP-50 | Integración REST | Tolerar un error 500 del servicio. | El servicio responde 500. | 502. | Coincide con lo esperado | PASS | RNF-23 |
| CP-51 | Integración REST | No colgarse con un servicio lento. | Latencia de 1,5 s con tiempo máximo de 0,3 s. | 502 en menos de 1,2 s. | Coincide con lo esperado | PASS | RNF-23, RNF-01 |
| CP-52 | Integración REST | Rechazar un JSON que no cumple el contrato. | Respuesta con otros campos. | 502 (antes: 500, defecto DEF-04). | Coincide con lo esperado | PASS | RNF-23 |
| CP-53 | Integración REST | Rechazar una respuesta que no es JSON. | Página HTML de un proxy. | 502 (antes: 500, defecto DEF-04). | Coincide con lo esperado | PASS | RNF-23 |
| CP-54 | Integración REST | Registrar un pedido con precios del servicio. | Taladro a 289.900 × 2. | Total 689.962 (289.900 × 2 + IVA). | Coincide con lo esperado | PASS | RF-01, RF-07 |
| CP-55 | Integración REST | Calcular decimales exactos. | Destornilladores a 45.500,50 × 3. | Subtotal 136.501,50; total 162.436,79. | Coincide con lo esperado | PASS | RF-07, CA-01 |
| CP-56 | Integración REST | Aplicar las reglas con datos externos. | 4 unidades de un producto con 3 en existencia; agotado; inactivo; cliente y producto inexistentes. | 409, 409, 422, 422, 422. | Coincide con lo esperado | PASS | RF-02, RF-03, CA-02 |
| CP-57 | Integración REST | Leer las existencias en vivo. | Cambiar las existencias en el servicio externo. | SALES-X las ve al instante (sin caché). | Coincide con lo esperado | PASS | RF-11 |
| CP-58 | Integración REST | Reflejar el servicio externo en catálogo e integración. | Listar clientes; `/integracion/disponibilidad`. | Datos del servicio externo. | Coincide con lo esperado | PASS | RF-11, RF-12 |
| CP-59 | Integración REST | No dejar pedidos a medias si el servicio cae. | Falla 500; registrar un pedido. | 502 y el total de pedidos no cambia. | Coincide con lo esperado | PASS | RNF-21, CA-15 |
| CP-60 | Integración REST | Responder 502 ante respuestas inválidas por la API. | Respuesta malformada; listar el catálogo. | 502. | Coincide con lo esperado | PASS | RNF-23 |
| CP-61 | Concurrencia | Enviar y cancelar a la vez. | 30 rondas: «Enviado» y «Cancelar» simultáneos sobre un pedido *En preparación*. | Exactamente una prospera; la cadena de estados auditada es válida. | Coincide con lo esperado | PASS | RNF-19, CA-16 |
| CP-62 | Concurrencia | Cancelar dos veces a la vez. | 30 rondas: dos cancelaciones simultáneas. | Una 200 y una 409; un solo registro CANCELAR. | Coincide con lo esperado | PASS | RNF-19, CA-16 |
| CP-63 | Concurrencia | Modificar y cancelar a la vez. | 30 rondas: editar y cancelar al mismo tiempo. | Un pedido cancelado no queda modificado después. | Coincide con lo esperado | PASS | RNF-19, CA-16 |

# 7. Pruebas adicionales sobre el sistema completo

Además de la suite, se ejecutaron estas verificaciones sobre el sistema en funcionamiento.

## 7.1 Prueba de carga (RNF-01)

`python scripts/carga_basica.py` — mezcla del 25 % de cada tipo: consultar pedidos, reportes, catálogo y registrar pedidos. Medida con la versión 1.1; las operaciones de la mezcla no cambian en la 1.2.

| Entorno | Usuarios | Peticiones | Errores | Rendimiento | p95 | Máx. |
|---|---:|---:|---:|---:|---:|---:|
| SQLite (desarrollo) | 20 | 500 | **0** | 185 req/s | 0,242 s | 2,415 s |
| PostgreSQL 18.6 local | 20 | 500 | **0** | 281 req/s | **0,098 s** | 0,147 s |
| PostgreSQL 18.6 local | 50 | 1.000 | **0** | 202 req/s | **0,389 s** | 0,669 s |
| Docker Compose (producción) | 20 | 500 | **0** | 206 req/s | **0,130 s** | 0,164 s |
| Docker Compose (producción) | 50 | 1.000 | **0** | 151 req/s | **0,554 s** | 0,931 s |

**Criterio RNF-01 (p95 < 3 s): cumple** en todos los escenarios. Las cifras son de un equipo de desarrollo, con cliente y servidor en la misma máquina; sirven de referencia, no de garantía para producción.

## 7.2 Esquema SQL, migración y rol de mínimo privilegio en PostgreSQL

- **Scripts SQL:** `sql/01_schema.sql` y `02_seed_estados.sql` se aplicaron a una base vacía (7 tablas, 6 estados) y la suite se ejecutó **sobre ese esquema** sin que la aplicación creara nada: aprobada. El SQL y el modelo ORM son equivalentes.
- **Migración 1.0 → 1.1:** `sql/04_migracion_v1_1.sql` se aplicó sobre una base con 40 pedidos: los conservó y se puede repetir sin errores.
- **Rol `salesx_app`** (`sql/03_rol_aplicacion.sql`): como ese usuario, `SELECT` e `INSERT` en la auditoría se permiten; `UPDATE`, `DELETE` y `TRUNCATE` se **deniegan**; `CREATE`, `DROP` y `ALTER TABLE` se deniegan. Con la API arrancada con ese rol, 11 de 11 pasos funcionaron (pedido, estados, auditoría, consumidores, API Key, reportes).

## 7.3 Docker Compose en modo producción

Docker Desktop 4.99 sobre Windows 11; imágenes `python:3.12-slim` y `postgres:16-alpine`; secretos aleatorios.

| Verificación | Resultado |
|---|:---:|
| `docker compose up -d --build` desde cero: contenedores *healthy* en ≈ 27 s | ✅ |
| PostgreSQL ejecutó `01_schema.sql`, `02_seed_estados.sql` y el script que crea el rol `salesx_app` | ✅ |
| La API arrancó en producción (su validación de claves, base y usuarios demo pasó) | ✅ |
| Dentro del contenedor, como `salesx_app`: `UPDATE`/`DELETE` en auditoría y `CREATE TABLE` rechazados | ✅ |
| Cabeceras de producción: HSTS, CSP, `nosniff`; cookie `HttpOnly` + `Secure` + `SameSite=Strict` | ✅ |
| Prueba de humo contra la API (pedido, estados, auditoría, reporte, API Key, solicitud, consumidor, usuario con cambio obligatorio) | ✅ 19/19 |
| Persistencia: los datos y el rol sobreviven a `docker compose restart` | ✅ |
| Respaldo (`pg_dump -Fc`) → borrar → restaurar con `pg_restore --clean`: datos recuperados y rol sin poder editar la auditoría (tras corregir DEF-03) | ✅ |
| Carga de 1.500 peticiones sin errores; 0 errores en los registros de la API | ✅ |

## 7.4 Integración REST con Clientes y Productos (servicios simulados)

Con `docker-compose.mock.yml` se levantaron tres contenedores (API, PostgreSQL y el servicio simulado) comunicados por la red de Docker: **14 de 14 comprobaciones correctas**.

| Comprobación | Resultado |
|---|:---:|
| El catálogo y los clientes vienen del otro contenedor | ✅ |
| Pedido con el precio del servicio externo (689.962 = 289.900 × 2 + IVA); más que las existencias externas → 409; cliente inexistente → 422 | ✅ |
| Las existencias que cambian en el servicio se ven al instante | ✅ |
| Latencia de `POST /pedidos` con catálogo REST: media 200 ms, p95 217 ms | ✅ |
| **Se apaga el contenedor externo:** registrar pedido → 502, catálogo → 502, ningún pedido a medias, SALES-X sigue sano | ✅ |
| **Se enciende de nuevo:** SALES-X se recupera solo, sin reiniciar | ✅ |
| Respuesta malformada del servicio → 502 (no 500) | ✅ |

> **Alcance:** valida el adaptador y la tolerancia a fallos contra un servicio que cumple *nuestro* contrato. **No** demuestra que los servicios reales de INTEGRAX lo cumplirán: eso se comprueba al conectarlos.

## 7.5 Auditoría de dependencias

`pip-audit` sobre `requirements.txt`: **«No known vulnerabilities found»** (resultado bruto en el anexo B).

# 8. Errores encontrados y corregidos

Las pruebas no solo comprueban: **encuentran defectos**. Estos siete se hallaron durante la ejecución y se corrigieron; cada uno quedó cubierto por una prueba para que no reaparezca.

| ID | Descripción | Causa | Corrección | Verificación |
|---|---|---|---|---|
| DEF-01 | El reporte y el panel salían **vacíos** para pedidos hechos de noche. | Los filtros por fecha se interpretaban en UTC; las 23:48 en Colombia ya son «mañana» en UTC. | Zona horaria de negocio configurable (`BUSINESS_TZ`) en filtros y agrupación. | CP-30, CP-31 |
| DEF-02 | El cambio obligatorio de contraseña se quedaba detenido tras pulsar «Guardar». | Los diálogos esperaban solo el evento `close`, que el navegador de pruebas no disparaba. | Los diálogos también se resuelven al enviar el formulario. | Recorrido completo en el navegador |
| DEF-03 | **Tras restaurar un respaldo, el rol de la API recuperaba `UPDATE` y `DELETE` sobre la auditoría.** | `sql/03` daba permisos por defecto sobre tablas futuras; al recrearse las tablas en la restauración se aplicaban antes que los del respaldo. | Se eliminaron los permisos por defecto (falla cerrada) y el script limpia los de la versión anterior. | Restauración repetida en Docker y en PostgreSQL local: `actualizar=false`, `borrar=false` |
| DEF-04 | Una respuesta del servicio externo que no cumplía el contrato producía un **error interno 500**. | El adaptador REST suponía que la respuesta siempre era válida. | Toda respuesta inválida (no JSON, campos faltantes, UUID o precio inválidos) se convierte en 502. | CP-52, CP-53, CP-60 (fallaban antes) |
| DEF-05 | Cada consulta al catálogo REST tardaba **≈ 185 ms**: un pedido de 5 productos, más de un segundo solo en consultas. | `httpx.get()` creaba un cliente HTTP —con su contexto TLS— en cada llamada. | Un cliente HTTP persistente y compartido. | Medición: 185 ms → **0,9 ms** por consulta |
| DEF-06 | **En el móvil (390 px) la página se salía por la derecha:** tarjetas cortadas, menú truncado, botones fuera de la pantalla. | Los hijos de la rejilla CSS no se encogían por debajo del ancho de su contenido (una tabla ancha empujaba toda la página). | `min-width: 0` en rejilla y tarjetas, rejilla `minmax(0, 1fr)` y un diseño de una columna en pantallas estrechas. | Captura de la sección 9 y comprobación automática de que `scrollWidth` ≤ 390 px en 4 pantallas |
| DEF-07 | **Dos usuarios sobre el mismo pedido violaban la máquina de estados:** en 29 de 30 rondas ambas peticiones respondían 200 y un pedido quedaba «Enviado» y «Cancelado», con auditoría contradictoria. | Cada petición leía el estado, validaba la transición y escribía sin bloquear la fila. | Bloqueo de fila (`SELECT … FOR UPDATE`) en modificar, cambiar de estado y cancelar; el estado se carga después del bloqueo. | CP-61, CP-62, CP-63: 30 rondas cada una, estables en 5 ejecuciones seguidas |

# 9. Evidencia visual

Capturas reales de la aplicación, tomadas con Edge sobre datos de demostración (`python scripts/capturas.py`).

![Inicio de sesión](../capturas/01-inicio-de-sesion.png)

*Figura 1. Inicio de sesión.*

![Panel de ventas](../capturas/02-panel.png)

*Figura 2. Panel de ventas: indicadores del mes, últimos pedidos, pedidos por estado y solicitudes de clientes.*

![Lista de pedidos](../capturas/03-pedidos.png)

*Figura 3. Lista de pedidos con filtros por estado, cliente y fechas (CP-14).*

![Nuevo pedido](../capturas/04-nuevo-pedido.png)

*Figura 4. Nuevo pedido: vista previa de subtotal, IVA y total antes de guardar (CP-10).*

![Detalle de un pedido y su auditoría](../capturas/05-detalle-y-auditoria.png)

*Figura 5. Detalle del pedido: productos, totales, acciones permitidas según el estado y la auditoría con autor y hora (CP-17, CP-21).*

![Reporte de ventas](../capturas/06-reporte-de-ventas.png)

*Figura 6. Reporte de ventas por período, con exportación a CSV (CP-22, CP-23).*

![Gestión de usuarios](../capturas/08-usuarios.png)

*Figura 7. Gestión de usuarios (solo administrador).*

![Claves de integración](../capturas/09-integraciones.png)

*Figura 8. Claves de integración por consumidor (solo administrador; CP-34).*

![Cambio obligatorio de contraseña](../capturas/10-cambio-obligatorio-de-contrasena.png)

*Figura 9. Cambio obligatorio de contraseña en el primer ingreso (CP-44).*

![Vista móvil](../capturas/07-vista-movil.png)

*Figura 10. Vista en móvil (390 px de ancho) después de corregir el defecto DEF-06.*

# 10. Conclusiones

- La suite verifica los **17 requisitos funcionales** y los criterios de aceptación de la Evidencia 3 con **63 pruebas aprobadas y 0 fallidas**, en SQLite y en PostgreSQL.
- Las pruebas **encontraron 7 defectos reales**, entre ellos dos de gravedad alta que ninguna revisión manual había detectado: la violación de la máquina de estados por concurrencia (DEF-07) y la pérdida de la inmutabilidad de la auditoría tras restaurar un respaldo (DEF-03). Ambos están corregidos y cubiertos.
- El sistema se comporta correctamente en Docker en modo producción, con carga (p95 de 0,13 s con 20 usuarios), con respaldo y restauración, y frente a fallas del servicio externo.
- **Límites declarados:** no se probó contra los servicios reales de Clientes y Productos, ni en un servidor Linux de despliegue, ni se midió la disponibilidad en operación; la revisión visual se hizo en Edge de escritorio y móvil, no en otros navegadores.

# Anexo A. Registro completo de la ejecución

Salida de `python -m pytest -v` sobre PostgreSQL (63 pruebas):

{{incluir: fragmentos/registro_pruebas.md}}

# Anexo B. Resultado bruto de la auditoría de dependencias

{{incluir: fragmentos/pip_audit.md}}
