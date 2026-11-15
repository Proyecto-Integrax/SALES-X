# Auditoría de seguridad — SALES-X

## 0. Ficha del informe

| Campo | Detalle |
|---|---|
| Sistema | SALES-X · gestión de ventas y pedidos (microproyecto de INTEGRAX) |
| Versión auditada | **1.0.0** (línea base, 13 de noviembre de 2026) y **reverificación** de la 1.2.0 (14 de noviembre de 2026) |
| Tipo | Auditoría **interna** de caja blanca: revisión de código, pruebas de seguridad automatizadas, análisis de dependencias y de configuración |
| Auditor | El propio equipo desarrollador (ver la limitación 2.4) |
| Stack real | Python 3.12 · FastAPI · SQLAlchemy 2 · PostgreSQL 16 · interfaz en JavaScript puro · Docker Compose |
| Despliegue previsto | Contenedores Docker (API + PostgreSQL) detrás de un proxy inverso con TLS |
| Metodología | Revisión por capas y OWASP Top 10 (2021); ver `03-Metodologia-y-Evidencias.md` |
| Documentos relacionados | `03-Metodologia-y-Evidencias.md` (cómo se hizo), `04-Estado-de-Remediacion.md` (qué se corrigió), `05-Revision-Lanzamiento-GO-NO-GO.md` (decisión) |

## 1. Resumen ejecutivo

> **Veredicto: apto para demostración y piloto controlado; no apto aún para exponer a Internet** hasta cerrar el hallazgo H-09 (TLS) y repetir las pruebas en el entorno de despliegue. No quedan hallazgos críticos ni altos abiertos.

Se identificaron **14 hallazgos**: 0 críticos, 2 altos, 7 medios, 4 bajos y 1 informativo (cumplimiento). En la línea base (versión 1.0.0) el escenario más grave era que una instalación con los valores de ejemplo permitía a un tercero entrar como administrador (ver 1.3). Durante la auditoría se corrigieron **9 de los 14**, incluidos los dos altos; quedan **4 abiertos**, todos de severidad baja o de configuración de despliegue, y uno de ellos (H-09) es requisito para producción.

### 1.1 Distribución de hallazgos

| Severidad | Total | ✅ Remediados | ⛔ Abiertos | Cumple |
|---|:---:|:---:|:---:|:---:|
| Crítica | 0 | — | — | — |
| Alta | 2 | 2 | 0 | — |
| Media | 7 | 6 | 1 | — |
| Baja | 4 | 1 | 3 | — |
| Informativa | 1 | — | — | 1 |
| **Total** | **14** | **9** | **4** | **1** |

### 1.2 Top 5 acciones inmediatas (antes de exponer la aplicación)

1. **Poner TLS** con un proxy inverso (Nginx o Traefik) y redirigir HTTP a HTTPS. Sin esto la cookie de sesión `Secure` no viaja y las credenciales irían en claro (H-09). *~4–6 h.*
2. **Limitar peticiones y tamaño** de los cuerpos en el proxy (H-10). *~1–2 h.*
3. **Ocultar `/docs`** (Swagger) fuera de la red interna (H-08). *~0,5 h.*
4. **Aplicar `sql/03_rol_aplicacion.sql`** en la base del entorno objetivo y conectar la API con `salesx_app` (H-13, ya verificado en desarrollo). *~0,5 h.*
5. **Repetir la suite, la carga y la restauración de un respaldo** en el servidor real, y definir la rotación de las claves de integración. *~2–3 h.*

### 1.3 Escenario de ataque realista (kill chain) en la línea base 1.0.0

Esto es lo que habría podido hacer una persona con acceso a Internet contra una instalación hecha **sin cambiar los valores de ejemplo**, y por qué cada eslabón está hoy cortado:

| Paso | Acción del atacante | Hallazgo que lo permitía | Estado hoy |
|---|---|---|---|
| 1 | Lee el repositorio público: `.env.example` trae la contraseña del administrador y las claves de ejemplo. | H-01 | ✅ En producción el sistema **se niega a arrancar** con esos valores. |
| 2 | Inicia sesión como administrador con la contraseña de ejemplo; nada le obliga a cambiarla. | H-01, H-07 | ✅ Validación de arranque; cambio de contraseña obligatorio para cuentas nuevas. |
| 3 | Si la contraseña fuera distinta, prueba claves en masa; el contador de intentos vivía en memoria y se reiniciaba o se repartía entre réplicas. | H-04 | ✅ Contador en la base de datos, compartido entre instancias. |
| 4 | Con la sesión, crea o usa la clave de integración única y consulta pedidos de cualquier cliente. | H-06 | ✅ Una clave por consumidor, revocable y con último uso. |
| 5 | Roba el token desde el navegador de una víctima con un script inyectado. | H-05 | ✅ Cookie `HttpOnly` + CSP; el JavaScript no puede leer la sesión. |
| 6 | Altera pedidos y **borra sus propios rastros** de la auditoría, porque la API se conectaba como dueño de la base. | H-13 | ✅ Rol `salesx_app`: la auditoría es de solo-agregar. |
| 7 | Con dos sesiones a la vez, deja un pedido «Enviado» y «Cancelado» para generar inconsistencias. | H-14 | ✅ Bloqueo de fila; CP-61 a CP-63. |

## 2. Alcance, metodología y limitaciones

### 2.1 Alcance

| Dentro del alcance | Fuera del alcance |
|---|---|
| API (`app/`): rutas, servicios, modelos, seguridad, configuración | Los servicios reales de Clientes y Productos (no existen aún) |
| Interfaz web (`app/static/`) | Infraestructura real (servidores, red, firewall): aún no desplegada |
| Scripts SQL, `Dockerfile`, `docker-compose*.yml` | Pruebas de penetración dinámicas con herramientas externas |
| Dependencias de Python y la imagen Docker | Ingeniería social y seguridad física |
| Documentación de seguridad y operación | Auditoría de los otros microproyectos de INTEGRAX |

### 2.2 Método de trabajo (cinco fases)

1. **Reconocimiento:** inventario de archivos, endpoints, tablas y flujos de datos (secciones 3.3 y 3.4).
2. **Revisión estática manual** por capas: entrada → autenticación y autorización → lógica de negocio → persistencia → salida.
3. **Pruebas dirigidas** con la suite automatizada (inyección, tokens alterados, CSRF, límites, configuración insegura) y con pruebas nuevas por cada hallazgo.
4. **Análisis de dependencias y configuración:** `pip-audit` y lectura de los valores por defecto.
5. **Clasificación, corrección y reverificación:** cada hallazgo se clasificó, se corrigió cuando fue posible y se volvió a probar (documento 04).

### 2.3 Herramientas y evidencia

`pytest` (63 pruebas), `pip-audit`, lectura de código, un cliente HTTP para ataques manuales, `psql` y `pg_dump`/`pg_restore` para verificar permisos y restauración, Docker Compose para repetir todo en el entorno de producción. Las huellas SHA-256 de los archivos revisados y los comandos están en `03-Metodologia-y-Evidencias.md`.

### 2.4 Limitaciones (declaración de honestidad)

- **Auditoría interna:** quien revisó el código es quien lo escribió; hay sesgo posible. Es válida como control interno, **no sustituye** una auditoría independiente ni una prueba de penetración antes de una salida a producción con datos reales.
- **No se usaron** escáneres dinámicos (OWASP ZAP, Burp), análisis estático automático (Bandit, Semgrep) ni *fuzzing*.
- **La ausencia de hallazgos** en un área no garantiza la ausencia de vulnerabilidades.
- **No se auditó** el comportamiento real de los servicios de Clientes y Productos, ni un servidor de producción.
- Las cifras de rendimiento son de un equipo de desarrollo.

### 2.5 Declaración sobre las modificaciones

A diferencia de una auditoría de «solo lectura», **el equipo sí modificó el sistema durante la auditoría** para corregir hallazgos. Por eso este informe distingue siempre entre el estado de la línea base (1.0.0) y el actual (1.2.0), y el documento 04 detalla cada cambio con su verificación.

## 3. Contexto: arquitectura y superficie de ataque

### 3.1 Arquitectura observada

**Navegador → proxy TLS (pendiente) → API FastAPI (rol de BD limitado) → PostgreSQL**, con la API consumiendo por HTTP los servicios de Clientes y Productos. La interfaz web la sirve la propia API (sin CDN). Dos puntos de entrada: el navegador (sesión por cookie) y los sistemas de INTEGRAX (clave por consumidor).

### 3.2 Actores y roles

| Actor | Cómo se autentica | Qué puede hacer |
|---|---|---|
| Vendedor | Cookie `HttpOnly` + CSRF, o Bearer | Operar pedidos, catálogo y reportes. Ve **todos** los pedidos (decisión de diseño, no es un IDOR). |
| Administrador | Ídem | Lo anterior + usuarios, restablecer contraseñas, consumidores de integración. |
| Sistema consumidor | `X-API-Key` (una por sistema) | Consultar pedidos, historial, disponibilidad; registrar solicitudes del cliente. |
| Cliente final | No accede a SALES-X | Solo a través de un sistema autorizado. |
| Anónimo | — | Solo `/health`, el inicio de sesión y la página de acceso. |

### 3.3 Inventario de endpoints

Generado desde las rutas reales del programa (`python scripts/generar_fragmentos.py`):

{{incluir: fragmentos/endpoints.md}}

**Lectura:** de 31 operaciones expuestas, solo 4 son públicas (la página de acceso, `/health`, el inicio y el cierre de sesión); 2 requieren sesión incluso con cambio de contraseña pendiente; 21 exigen un usuario autenticado (6 de ellas, administrador) y 4 una clave de integración.

### 3.4 Datos sensibles tratados

| Dato | Dónde vive | Protección |
|---|---|---|
| Contraseña de usuarios | `vendedor.contrasena` | Hash bcrypt (coste 12); nunca se devuelve. |
| Claves de integración | `consumidor_api.clave_hash` | Solo el hash SHA-256; la clave se muestra una vez. |
| Sesión | Cookie `salesx_session` | `HttpOnly`, `SameSite=Strict`, `Secure` en producción; JWT de 8 h. |
| Datos de pedidos y clientes (identificadores) | `pedido`, `detalle_pedido` | Solo el `cliente_id`; la ficha del cliente no se almacena. |
| Correos y nombres de usuarios internos | `vendedor` | Datos personales (Ley 1581): se minimizan. |
| Secretos de configuración | Variables de entorno | Nunca en el código ni en la imagen; validados al arrancar. |

### 3.5 Modelo de amenazas (resumen)

| Amenaza | Vector | Control principal |
|---|---|---|
| Suplantación de un usuario | Contraseña débil o filtrada; fuerza bruta | Política de contraseñas, bloqueo compartido, bcrypt |
| Robo de sesión | XSS, CSRF | CSP, escape de salida, cookie `HttpOnly`, token CSRF |
| Escalada de privilegios | Rol insuficiente | Dependencias `current_user` y `require_admin` |
| Manipulación de importes | Precios o totales enviados por el cliente | El servidor calcula todo (RN-01, RN-02) |
| Repudio | «Yo no cancelé ese pedido» | Auditoría de solo-agregar con autor y fecha |
| Fuga de datos hacia otros sistemas | Clave de integración compartida | Una clave por consumidor, revocable |
| Inconsistencia por concurrencia | Dos usuarios a la vez | Bloqueo de fila |
| Denegación de servicio | Ráfagas de peticiones | Límites en el proxy (H-10, pendiente) |
| Servicio externo malicioso o caído | Respuestas inválidas, lentitud | Adaptador con tiempo máximo, validación y 502 |

## 4. Controles que ya funcionan bien

| Control | Evidencia |
|---|---|
| Contraseñas con bcrypt (coste 12); respuesta uniforme ante usuario inexistente o contraseña errónea, con verificación a tiempo casi constante | `app/security.py`, `app/routers/auth.py`; CP-03 |
| Todo endpoint de negocio exige autenticación; JWT firmado con expiración; un usuario inactivo pierde acceso de inmediato | CP-04, CP-05 |
| Clave de integración comparada por hash; el JWT no sirve en esos servicios | CP-24 |
| Autorización por rol en la administración de usuarios y consumidores | CP-07, CP-37 |
| **Sin inyección SQL:** ORM parametrizado y validación estricta de entradas | CP-26 |
| El precio y los totales los calcula el servidor | CP-11, CP-55 |
| Máquina de estados que impide transiciones indebidas, también con concurrencia | CP-18, CP-61 a CP-63 |
| Auditoría de operaciones, de solo-agregar a nivel de base de datos | CP-21; Evidencia 7 §7.2 |
| Cabeceras de seguridad y CSP estricta (sin scripts ni estilos en línea) | CP-27 |
| Escape de toda salida en la interfaz; el JavaScript no puede leer la sesión | Revisión de `app/static/app.js`; CP-39 |
| Errores internos sin trazas hacia el cliente, pero registrados | `app/main.py` |
| Contenedor sin privilegios de root; base de datos sin puerto publicado | `Dockerfile`, `docker-compose.yml` |
| Configuración de producción validada al arrancar | CP-28, CP-29 |
| Dependencias sin vulnerabilidades conocidas | `pip-audit` (anexo B) |

## 5. Hallazgos

Cada hallazgo indica su **estado actual**. La severidad es la de la línea base (versión 1.0.0).

### 5.1 Hallazgos críticos

Ninguno.

### 5.2 Hallazgos altos

#### H-01 · Secretos por defecto utilizables en producción — ALTA — ✅ Remediado
- **Ubicación:** `app/config.py`, `.env.example`.
- **Descripción:** `SECRET_KEY`, `INTEGRATION_API_KEY` y la contraseña del administrador tenían valores de ejemplo publicados en el repositorio.
- **Impacto:** quien conociera el repositorio podía iniciar sesión como administrador o usar los servicios de integración en una instalación que no hubiera cambiado esos valores.
- **Remediación:** con `ENVIRONMENT=production` el sistema **se niega a iniciar** si detecta claves por defecto o cortas, contraseña de administrador débil, SQLite o usuarios de demostración (`validate_for_production`). `docker-compose.yml` exige definir cada secreto.
- **Verificación:** CP-28, CP-29; arranque en Docker en modo producción.

#### H-14 · Condición de carrera en los cambios de estado — ALTA — ✅ Remediado
- **Ubicación:** `app/services/pedidos.py` y rutas de modificación, estado y cancelación.
- **Descripción:** cada petición leía el pedido, validaba la transición contra ese estado y escribía, **sin bloquear la fila**. Dos usuarios simultáneos validaban contra el mismo estado y ambos escribían.
- **Evidencia:** en 29 de 30 rondas de prueba, «Enviado» y «Cancelar» a la vez respondieron **200 los dos**; el pedido quedó «Enviado» y «Cancelado» a la vez, con una auditoría que registraba transiciones contradictorias.
- **Impacto:** pedidos en estados imposibles, auditoría que no refleja lo ocurrido; un pedido enviado y cancelado generaría discrepancias con otros sistemas.
- **Remediación:** `SELECT … FOR UPDATE` en modificar, cambiar de estado y cancelar. El segundo usuario espera, relee el estado ya cambiado y su transición se valida contra la realidad (409 si ya no procede). El estado se carga después del bloqueo.
- **Verificación:** CP-61, CP-62, CP-63 (30 rondas cada una), estables en 5 ejecuciones seguidas. *Nota:* el bloqueo solo existe en PostgreSQL; SQLite es únicamente para demostración.

### 5.3 Hallazgos medios

#### H-02 · Ausencia de HSTS — MEDIA — ✅ Remediado
- **Descripción:** no se enviaba `Strict-Transport-Security`, lo que permite ataques de degradación a HTTP.
- **Remediación:** la cabecera se añade automáticamente en producción (1 año, subdominios). **Verificación:** observada en Docker en modo producción.

#### H-03 · Errores no controlados sin registro — MEDIA — ✅ Remediado
- **Descripción:** el manejador global ocultaba la traza al cliente pero no la registraba, impidiendo investigar incidentes.
- **Remediación:** `log.error(..., exc_info=exc)` con método y ruta. **Verificación:** 0 errores no explicados en los registros tras las pruebas de carga y de integración.

#### H-04 · Bloqueo de intentos de login solo en memoria — MEDIA — ✅ Remediado
- **Descripción:** el contador vivía en el proceso: se reiniciaba con la aplicación y no se compartía entre réplicas, por lo que un atacante repartido multiplicaba sus intentos.
- **Remediación:** los fallos se guardan en la tabla `intento_login`; 5 fallos en 5 minutos bloquean (429) y un ingreso correcto los borra.
- **Verificación:** CP-32, CP-33. *Complemento recomendado:* límite de tasa por IP en el proxy (H-10).

#### H-05 · Token de sesión en `sessionStorage` — MEDIA — ✅ Remediado
- **Descripción:** si existiera un XSS, un script podría leer el JWT.
- **Remediación:** la sesión viaja en una cookie `HttpOnly` + `SameSite=Strict` (`Secure` en producción); las escrituras por cookie exigen `X-CSRF-Token`; la interfaz ya no guarda el token y borra el resto de la versión anterior.
- **Verificación:** CP-39 a CP-42 y recorrido en el navegador: `document.cookie` solo muestra la cookie CSRF; un POST sin CSRF devuelve 403.
- **Riesgo residual:** un XSS aún podría *actuar* con la sesión del usuario (no robarla); lo limitan la CSP y el escape de toda salida.

#### H-06 · Clave de integración única y compartida — MEDIA — ✅ Remediado
- **Descripción:** todos los sistemas de INTEGRAX usaban la misma clave: sin trazabilidad por consumidor, sin rotación simple, y un compromiso afectaba a todos.
- **Remediación:** una clave por consumidor, guardada como hash SHA-256 y mostrada una sola vez; expiración opcional, revocación, último uso y el nombre del consumidor en la auditoría.
- **Verificación:** CP-34 a CP-38; pantalla *Integraciones*.

#### H-09 · TLS no terminado por la aplicación — MEDIA — ⛔ Abierto
- **Descripción:** Uvicorn sirve HTTP. Sin un proxy inverso con TLS, credenciales y cookies viajarían en claro; además, la cookie `Secure` no se enviaría fuera de `localhost`, de modo que **el inicio de sesión por la interfaz no se mantendría** desde otra máquina.
- **Evidencia:** comprobado en Docker (modo producción): la cookie `Secure` no se reenvía por HTTP plano.
- **Recomendación:** Nginx o Traefik con certificado válido, redirección HTTP→HTTPS y HSTS. *Requisito para producción.*

#### H-13 · La inmutabilidad de la auditoría dependía de la base de datos — MEDIA — ✅ Remediado
- **Descripción:** la aplicación nunca actualiza ni borra auditoría, pero si se conectaba como dueño de la base esa garantía no era técnica.
- **Remediación:** `sql/03_rol_aplicacion.sql` crea el rol `salesx_app` (sin superusuario, sin crear objetos, sin `UPDATE`/`DELETE`/`TRUNCATE` sobre la auditoría); la API se ejecuta con ese rol. `docker-compose.yml` lo crea y usa automáticamente.
- **Verificación (Evidencia 7 §7.2 y §7.3):** como `salesx_app`, `UPDATE`/`DELETE` en la auditoría y `CREATE/DROP/ALTER TABLE` se rechazan; la API completa funciona con ese rol.
- **Hallazgo durante la verificación (DEF-03):** la primera versión del script daba permisos por defecto sobre tablas futuras y, tras **restaurar un respaldo**, el rol recuperaba `UPDATE`/`DELETE` sobre la auditoría. Se corrigió (sin permisos por defecto) y se repitió la restauración con el resultado correcto.
- **Pendiente (operación):** aplicar el script en la base del entorno objetivo y reejecutarlo después de crear tablas nuevas.

### 5.4 Hallazgos bajos (endurecimiento)

#### H-07 · Gestión de contraseñas limitada — BAJA — ✅ Remediado
- **Descripción:** política mínima de 8 caracteres sin complejidad; sin cambio obligatorio en el primer ingreso ni cambio por el propio usuario.
- **Remediación:** política de ≥ 10 caracteres con letras y números, sin contraseñas comunes ni el usuario; `POST /auth/cambiar-contrasena` (con la actual y bloqueo por intentos); cambio **obligatorio** en el primer ingreso y tras un restablecimiento. **Verificación:** CP-43 a CP-46.

#### H-08 · Documentación OpenAPI (`/docs`) expuesta — BAJA — ⛔ Abierto
- **Descripción:** Swagger está disponible sin autenticación y revela la superficie de la API.
- **Recomendación:** ocultarlo o restringirlo por red en producción.

#### H-10 · Sin límites de tasa ni de tamaño de petición — BAJA — ⛔ Abierto
- **Descripción:** un cliente podría saturar el servicio con muchas peticiones o cuerpos grandes.
- **Recomendación:** límites en el proxy (`limit_req`, `client_max_body_size`).

#### H-12 · Los tokens no se revocan al cerrar sesión — BAJA — ⛔ Abierto
- **Descripción:** cerrar sesión borra las cookies, pero un JWT copiado seguiría válido hasta expirar (8 h). Un usuario desactivado sí queda bloqueado al instante.
- **Recomendación:** tokens de 15–30 minutos con renovación revocable.

### 5.5 Falsos positivos descartados (y por qué)

| Sospecha | Por qué se descartó |
|---|---|
| «Inyección SQL en los filtros de pedidos» | Todas las consultas pasan por el ORM con parámetros; la prueba CP-26 con `' OR 1=1; DROP TABLE pedido;--` devolvió 200 sin datos y con las tablas intactas. |
| «El JWT admite el algoritmo `none`» | `jwt.decode` se invoca con `algorithms=["HS256"]` fijo; un token alterado da 401 (CP-05). |
| «IDOR: un vendedor ve pedidos de otro vendedor» | Es una decisión de diseño: el área de ventas gestiona todos los pedidos y atiende las solicitudes de cualquier cliente. La autorización relevante es por rol. |
| «CORS abierto» | No hay middleware CORS salvo que se configure `CORS_ORIGINS`; por defecto solo se acepta el mismo origen. |
| «XSS almacenado en las observaciones del pedido» | Toda salida dinámica pasa por `esc()` y la CSP prohíbe scripts en línea; no se pudo ejecutar código. |
| «CSRF en los servicios de integración» | No aplica: usan `X-API-Key`, que el navegador no envía solo (no hay cookies). El CSRF solo se exige a la sesión por cookie. |
| «Contraseñas en texto plano en el acta» | Son las de la cuenta de **demostración**, públicas a propósito; en producción el sistema se niega a arrancar con ellas. |

## 6. Tabla resumen de hallazgos

| ID | Severidad | Hallazgo | Estado | Evidencia |
|---|:---:|---|:---:|---|
| H-01 | Alta | Secretos por defecto en producción | ✅ | CP-28, CP-29 |
| H-14 | Alta | Carrera en cambios de estado | ✅ | CP-61 a CP-63 |
| H-02 | Media | Sin HSTS | ✅ | Docker (producción) |
| H-03 | Media | Errores sin registro | ✅ | Registros de la API |
| H-04 | Media | Bloqueo de login en memoria | ✅ | CP-32, CP-33 |
| H-05 | Media | Token en `sessionStorage` | ✅ | CP-39 a CP-42 |
| H-06 | Media | Clave de integración única | ✅ | CP-34 a CP-38 |
| H-13 | Media | Auditoría no inmutable en BD | ✅ | Evidencia 7 §7.2, §7.3 |
| H-09 | Media | Sin TLS propio | ⛔ | Docker: cookie `Secure` |
| H-07 | Baja | Gestión de contraseñas | ✅ | CP-43 a CP-46 |
| H-08 | Baja | `/docs` público | ⛔ | — |
| H-10 | Baja | Sin límites de tasa/tamaño | ⛔ | — |
| H-12 | Baja | Sin revocación de tokens | ⛔ | — |
| H-11 | Info | Dependencias sin vulnerabilidades | ✅ | `pip-audit` (anexo B) |

## 7. Plan de remediación priorizado

### Fase 0 — Contención inmediata (antes de exponer, ~8 h)
| Acción | Hallazgo | Responsable | Esfuerzo | Criterio de cierre |
|---|---|---|---|---|
| Proxy inverso con TLS y redirección a HTTPS | H-09 | Operaciones | 4–6 h | `curl -I http://…` redirige a HTTPS; HSTS presente; la sesión se mantiene |
| Límites de tasa y de tamaño de cuerpo | H-10 | Operaciones | 1–2 h | Una ráfaga devuelve 429/413 |
| Ocultar o proteger `/docs` | H-08 | Operaciones | 0,5 h | `/docs` responde 404/403 desde fuera |
| Aplicar `sql/03` en la base real y usar `salesx_app` | H-13 | Operaciones / DBA | 0,5 h | `UPDATE auditoria_pedido` con el rol de la API → *permission denied* |

### Fase 1 — Correcciones de fondo (1–2 semanas, ~15 h)
| Acción | Hallazgo | Esfuerzo | Criterio de cierre |
|---|---|---|---|
| Tokens cortos con renovación revocable | H-12 | 6–8 h | Cerrar sesión invalida el token en el servidor |
| Repetir las pruebas, la carga y la restauración en el servidor real | — | 3 h | Suite en verde; restauración sin perder permisos |
| Pruebas con los servicios reales de Clientes y Productos | — | 3–4 h | Contrato verificado; ajustes si difiere |

### Fase 2 — Madurez y operación (30–90 días)
- Auditoría **independiente** o prueba de penetración externa.
- Integración continua con pruebas y `pip-audit` en cada cambio; análisis estático (Bandit).
- Monitoreo y alertas (disponibilidad, errores 5xx, intentos de acceso fallidos); rotación semestral de `SECRET_KEY` y de las claves de integración.
- Registro centralizado de la auditoría fuera de la base de datos.

**Esfuerzo total estimado:** ~25 h de trabajo, de las cuales ~8 h son bloqueantes para producción.

## 8. Checklist de verificación posterior (para el equipo)

☐ `python -m pytest` en verde en SQLite y en PostgreSQL (63 pruebas).
☐ `docker compose up` desde cero: contenedores *healthy* y `/health` correcto.
☐ Como `salesx_app`, `UPDATE`/`DELETE` sobre `auditoria_pedido` responde *permission denied*.
☐ Tras restaurar un respaldo con `--clean`, el punto anterior sigue cumpliéndose.
☐ Detrás del proxy: HTTPS forzado, HSTS, cookie `Secure` enviada y sesión estable.
☐ `/docs` no es accesible desde Internet.
☐ Límites de tasa y tamaño activos (ráfaga → 429/413).
☐ `pip-audit` sin vulnerabilidades; secretos de producción distintos de los de ejemplo.
☐ Claves de integración: una por sistema; «INTEGRAX-inicial» revocada cuando ya no se use.

## 9. Cumplimiento y buenas prácticas

| Categoría OWASP Top 10 (2021) | Resultado | Hallazgos |
|---|---|---|
| A01 Control de acceso roto | Autorización por rol correcta; todos los vendedores ven todos los pedidos **por diseño** | — |
| A02 Fallas criptográficas | bcrypt, JWT HS256, hash SHA-256 de claves; TLS depende del despliegue | H-09 |
| A03 Inyección | ORM parametrizado, validación estricta, escape y CSP | — |
| A04 Diseño inseguro | Precios y totales en el servidor; máquina de estados; bloqueo de fila | H-14 ✅ |
| A05 Configuración de seguridad incorrecta | Validación de producción; Swagger público | H-01 ✅, H-08, H-10 |
| A06 Componentes vulnerables | `pip-audit` limpio | H-11 |
| A07 Fallas de identificación y autenticación | Bloqueo compartido, política, cookie `HttpOnly`; sin revocación de tokens | H-04 ✅, H-05 ✅, H-07 ✅, H-12 |
| A08 Fallas de integridad de software y datos | Auditoría inmutable por permisos de BD; sin CI aún | H-13 ✅ |
| A09 Fallas de registro y monitoreo | Auditoría de negocio y registro de errores; sin monitoreo centralizado | H-03 ✅ |
| A10 SSRF | Las URL de servicios externos vienen solo de configuración | — |

**Normativa colombiana:** Ley 1581 de 2012 (datos personales): minimización — solo nombre, correo y hash de contraseña de usuarios internos, e identificador de clientes. Ley 1273 de 2009 (delitos informáticos): el sistema deja trazabilidad de accesos y operaciones. Ley 23 de 1982 y Decisión Andina 351 (derechos de autor): ver Evidencias 4 y 5.

## 10. Conclusión

SALES-X llegó a la auditoría con una base sólida —ORM parametrizado, bcrypt, cálculo de importes en el servidor, auditoría de negocio— y con debilidades típicas de un primer lanzamiento: valores de ejemplo utilizables, sesión legible por scripts, claves de integración compartidas, bloqueo de intentos en memoria y una auditoría protegida solo por la buena conducta de la aplicación. Además, las pruebas de concurrencia revelaron un defecto de integridad que ninguna revisión de código había visto (H-14).

**Nueve de los catorce hallazgos están corregidos y verificados.** Los cuatro restantes son de configuración de despliegue o de severidad baja, y solo H-09 (TLS) bloquea una salida a producción. El sistema es apto para demostración y piloto en red interna; antes de exponerlo debe ejecutarse la Fase 0, repetirse la verificación en el servidor real y contratarse una revisión independiente.

**Riesgo residual:** bajo-medio, dominado por la ausencia de TLS y de límites de tasa.

## Anexo A — Comandos y evidencias de la revisión

Todos reproducibles desde la carpeta `sales-x`:

```
# Pruebas (SQLite y PostgreSQL)
python -m pytest -v
set TEST_DATABASE_URL=postgresql+psycopg2://salesx:CLAVE@localhost:5432/salesx_test
python -m pytest -v

# Dependencias
python -m pip_audit -r requirements.txt

# Inventario de endpoints, tablas y huellas
python scripts/generar_fragmentos.py

# Permisos del rol de la API (debe responder "permission denied")
psql -U salesx_app -d salesx -c "UPDATE auditoria_pedido SET accion = accion;"

# Docker en modo producción
docker compose --env-file .env.docker up -d --build
curl http://localhost:8000/health
```

## Anexo B — Detalle de dependencias y avisos

Resultado bruto de `pip-audit` (14 de noviembre de 2026):

{{incluir: fragmentos/pip_audit.md}}

El análisis de licencias de las 29 dependencias de la imagen está en la Evidencia 4.

## Anexo C — Fragmentos de referencia para las correcciones

**H-01 · Validación de arranque en producción** (`app/config.py`):

```python
def validate_for_production(s: Settings) -> list[str]:
    problems = []
    if s.secret_key in INSECURE_DEFAULTS or len(s.secret_key) < 32:
        problems.append("SECRET_KEY debe tener al menos 32 caracteres y no ser el valor por defecto")
    if s.database_url.startswith("sqlite"):
        problems.append("En producción debe usarse PostgreSQL (DATABASE_URL), no SQLite")
    if s.seed_demo_users:
        problems.append("SEED_DEMO_USERS debe ser false en producción")
    return problems   # si no está vacía, la aplicación no arranca
```

**H-14 · Bloqueo de fila** (`app/services/pedidos.py`):

```python
consulta = select(Pedido).where(Pedido.pedido_id == pedido_id)
if bloquear:
    # el estado se carga DESPUÉS del bloqueo (carga diferida), no con un JOIN
    consulta = consulta.options(lazyload(Pedido.estado)).with_for_update()
```

**H-13 · Auditoría de solo-agregar** (`sql/03_rol_aplicacion.sql`):

```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO salesx_app;
REVOKE UPDATE, DELETE, TRUNCATE ON auditoria_pedido FROM salesx_app;
ALTER DEFAULT PRIVILEGES FOR ROLE :"owner" IN SCHEMA public REVOKE ALL ON TABLES FROM salesx_app;
```
