*Fuente del análisis: imagen Docker `sales-x-api` (Linux, lo que se despliega).*

**Dependencias directas** (las que declara `requirements.txt` y se distribuyen):

| Paquete | Versión | Licencia | Para qué se usa |
|---|---|---|---|
| bcrypt | 5.0.0 | Apache-2.0 | Hash de contraseñas |
| fastapi | 0.162.7 | MIT | Framework de la API REST |
| httpx | 0.28.1 | BSD-3-Clause | Cliente HTTP (integración con Clientes y Productos) |
| psycopg2-binary | 2.9.13 | LGPL-3.0 | Conector a PostgreSQL |
| pydantic-settings | 2.16.3 | MIT | Configuración por variables de entorno |
| pyjwt | 2.15.1 | MIT | Tokens de sesión (JWT) |
| sqlalchemy | 2.1.8 | MIT | ORM y acceso a datos |
| tzdata | 2026.6 | Apache-2.0 | Zonas horarias (America/Bogota) en Windows |
| uvicorn | 0.54.0 | BSD-3-Clause | Servidor ASGI |

**Dependencias transitivas** (las que traen las anteriores):

| Paquete | Versión | Licencia | Lo trae |
|---|---|---|---|
| annotated-doc | 0.0.6 | MIT | fastapi |
| annotated-types | 0.8.0 | MIT | pydantic |
| anyio | 4.16.0 | MIT | httpx |
| certifi | 2026.10.23 | MPL-2.0 | httpcore |
| click | 8.5.1 | BSD-3-Clause | uvicorn |
| h11 | 0.16.0 | MIT | httpcore |
| httpcore | 1.0.9 | BSD-3-Clause | httpx |
| httptools | 0.9.0 | MIT | uvicorn |
| idna | 3.20 | BSD-3-Clause | httpx |
| opentelemetry-api | 1.45.2 | Apache-2.0 | fastapi |
| pydantic | 2.14.3 | MIT | pydantic-settings |
| pydantic-core | 2.50.4 | MIT | pydantic |
| python-dotenv | 1.2.4 | BSD-3-Clause | pydantic-settings |
| pyyaml | 6.0.3 | MIT | uvicorn |
| starlette | 1.10.0 | BSD-3-Clause | fastapi |
| typing-inspection | 0.4.5 | MIT | pydantic-settings |
| typing_extensions | 4.16.0 | PSF-2.0 | anyio |
| uvloop | 0.23.0 | MIT / Apache-2.0 | uvicorn |
| watchfiles | 1.3.0 | MIT | uvicorn |
| websockets | 17.4 | BSD-3-Clause | uvicorn |
