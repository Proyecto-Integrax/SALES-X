---
codigo: SALESX-E4
evidencia: 4 de 7
titulo: Matriz de propiedad intelectual
descripcion: Inventario de todo lo que compone SALES-X — qué es propio del equipo, qué es de terceros y bajo qué licencia se utiliza. Las licencias se verificaron en el árbol de dependencias real de la imagen que se despliega, no se supusieron.
metadatos:
  - Sistema | SALES-X · Gestión de ventas y pedidos
  - Paquetes analizados | 29 (árbol completo de la imagen Docker)
  - Dependencias directas | 9
  - Componentes que no son paquetes | 9
  - Licencias distintas encontradas | 7
  - Licencias copyleft fuerte | 0 (copyleft débil: psycopg2 con LGPL y certifi con MPL)
pie: SALES-X · Evidencia 4 de 7 · Matriz de propiedad intelectual · 29 paquetes analizados, 7 licencias distintas, ninguna copyleft fuerte.
---

# 1. Para qué sirve esta matriz

Un sistema no es solo el código que escribió el equipo: se apoya en decenas de componentes ajenos, cada uno con su licencia. Esta matriz responde a tres preguntas:

- **¿Qué es nuestro?** Es decir, sobre qué podemos decidir cómo licenciar (Evidencia 5).
- **¿Qué es de terceros y bajo qué condiciones lo usamos?** Algunas licencias exigen conservar avisos; otras, liberar modificaciones.
- **¿Hay algún riesgo legal?** Sobre todo, licencias de copyleft fuerte (GPL/AGPL) que obligarían a liberar el código propio.

El análisis se hizo sobre el árbol **completo** de dependencias (directas y transitivas), leyendo las licencias que declara cada paquete instalado, y sobre la **imagen Docker** que se despliega, no solo en el equipo de desarrollo.

# 2. Lo que es propio del equipo

| Activo | Ubicación | Titular | Licenciamiento | Observaciones |
|---|---|---|---|---|
| Código de la API | `app/` | Equipo desarrollador | Licencia de uso definida en el contrato (Evidencia 5) | Derechos morales irrenunciables (Ley 23 de 1982). |
| Interfaz web (HTML, CSS, JavaScript) | `app/static/` | Equipo desarrollador | Ídem | **Sin librerías de terceros ni CDN**: código 100 % propio. El ícono de la pestaña es un SVG propio. |
| Scripts SQL | `sql/` | Equipo desarrollador | Ídem | — |
| Pruebas, servicios simulados y scripts | `tests/`, `mocks/`, `scripts/` | Equipo desarrollador | Ídem | — |
| Despliegue | `Dockerfile`, `docker-compose*.yml`, `*.bat` | Equipo desarrollador | Ídem | — |
| Documentación (Evidencias 1 a 7, informes, manuales) | `docs/`, `specs/` | Equipo desarrollador | Ídem | Los nombres de los entregables siguen la estructura del proyecto de referencia FINAN-X; el **contenido es original** de SALES-X. |
| Diagramas | `docs/diagramas/` | Equipo desarrollador | Ídem | El MER se genera desde el código; los de casos de uso y clases se hicieron en draw.io (formato abierto). |
| Capturas de pantalla | `docs/capturas/` | Equipo desarrollador | Ídem | Tomadas de la propia aplicación con datos de demostración. |
| Nombre «SALES-X» | — | Equipo desarrollador | Uso académico | No registrado como marca. |

# 3. Componentes de terceros que forman parte del software

Son los paquetes de Python que SALES-X necesita para ejecutarse. Se listan los **directos** (los que declara `requirements.txt`) y, en la sección 6, los transitivos.

{{incluir: fragmentos/licencias.md}}

# 4. Componentes de terceros que NO son paquetes

| Componente | Versión | Licencia | Cómo se usa | Se distribuye con el software |
|---|---|---|---|---|
| Python | 3.12 (imagen) / 3.13 (desarrollo) | PSF License | Lenguaje de ejecución | Sí, dentro de la imagen Docker |
| PostgreSQL | 16 (imagen) / 18 (desarrollo) | PostgreSQL License (tipo MIT/BSD) | Base de datos | Sí, en la imagen `postgres:16-alpine` |
| Imagen `python:3.12-slim` | — | Mezcla (Debian, PSF y utilidades GPL del sistema) | Base del contenedor de la API | Sí; aplica a la imagen, no al código propio |
| Imagen `postgres:16-alpine` | — | PostgreSQL License + Alpine (MIT y GPL de utilidades) | Contenedor de la base de datos | Sí |
| Docker Desktop / Compose | 4.99 / v5.7 | Términos de Docker | Ejecutar los contenedores | No (herramienta de quien despliega) |
| Microsoft Edge | — | Propietaria | Generar PDF y capturas (modo *headless*) | No |
| draw.io (diagrams.net) | — | Apache-2.0 | Diagramas de casos de uso y clases | No (solo las imágenes resultantes) |
| Pandoc (vía `pypandoc_binary`) | 3.9 | GPL-2.0 o posterior | Convertir la documentación a Word | **No**: es una herramienta de construcción de documentos; no forma parte del software |
| Playwright | — | Apache-2.0 | Capturas de la interfaz | No |

# 5. Resumen de licencias encontradas

Sobre los **29 paquetes** de la imagen de producción:

| Licencia | Paquetes | Tipo | Qué exige |
|---|---:|---|---|
| MIT | 14 | Permisiva | Conservar el aviso de copyright y de licencia. |
| BSD-3-Clause | 8 | Permisiva | Conservar el aviso; no usar el nombre de los autores para promocionar el producto. |
| Apache-2.0 | 3 | Permisiva | Conservar el aviso y el archivo NOTICE si existe; indicar los cambios si se modifica. |
| MPL-2.0 | 1 (`certifi`) | **Copyleft débil** (a nivel de archivo) | Si se modifican los archivos de ese paquete, publicar esas modificaciones. Sin cambios, solo conservar el aviso. |
| LGPL-3.0 | 1 (`psycopg2-binary`) | **Copyleft débil** | Permitido en software propietario si se usa como librería **sin modificar**; permitir su reemplazo; conservar el aviso. |
| PSF-2.0 | 1 (`typing_extensions`) | Permisiva | Conservar el aviso. |
| MIT / Apache-2.0 | 1 (`uvloop`) | Permisiva (doble licencia) | Se puede elegir una de las dos. |

**No hay ningún componente de copyleft fuerte (GPL o AGPL) enlazado con el código de SALES-X**, por lo que no se impone la obligación de liberar el código fuente propio.

# 6. Dependencias transitivas

De los 29 paquetes, **20 son transitivos**: los traen los nueve directos (por ejemplo, `starlette`, `pydantic` y `anyio` vienen con FastAPI; `httpcore`, `certifi` y `idna`, con httpx; `uvloop` y `httptools`, con `uvicorn[standard]`). Todos están en la tabla de la sección 3, con la columna «Lo trae» que indica de quién dependen.

Hay **una diferencia entre plataformas**: en Windows (desarrollo) son 28 paquetes y en la imagen Linux 29, porque `uvloop` solo existe en Linux. Por eso el análisis oficial es el de la imagen.

# 7. Obligaciones que asume el equipo

| # | Obligación | Origen | Estado |
|---|---|---|---|
| 1 | Conservar los avisos de copyright y licencia de los componentes de terceros al distribuir el software. | MIT, BSD, Apache, PSF | Pendiente: incluir un archivo `NOTICE`/`LICENSE` con los avisos antes de entregar a un tercero. |
| 2 | Usar `psycopg2-binary` y `certifi` **sin modificarlos**. | LGPL-3.0 y MPL-2.0 | Cumplido: no se modifican. |
| 3 | Mantener esta matriz al día cuando cambie `requirements.txt`. | Gestión | Continuo: `python scripts/licencias.py`. |
| 4 | Definir con el docente u organización la licencia del código propio. | Contrato (Evidencia 5) | Pendiente de decisión. |
| 5 | Tratar los datos personales conforme a la Ley 1581 de 2012: SALES-X solo guarda el correo y el nombre de los usuarios internos (contraseña como hash) y el `cliente_id` de los clientes. | Normativa colombiana | Cumplido por diseño (minimización de datos). |

# 8. Riesgos detectados y medidas

| Riesgo | Detalle | Medida |
|---|---|---|
| Copyleft débil en el conector de PostgreSQL | `psycopg2-binary` es LGPL-3.0. | Uso como dependencia sin modificar y enlazada dinámicamente: permitido en software propietario. Alternativa si se quisiera evitar: `psycopg` 3 (también LGPL) o `pg8000` (BSD). |
| Paquete con MPL-2.0 | `certifi` (lista de certificados raíz). | Sin modificaciones, solo se conserva el aviso. |
| Imágenes base de Docker con licencias mixtas | Incluyen utilidades GPL del sistema operativo. | Aplican a la imagen y no al código propio; no se modifican. |
| Metadatos de licencia declarados por los propios paquetes | Un paquete puede declarar mal su licencia. | Se contrastaron `License-Expression`, `License` y los clasificadores; los paquetes directos se conocen y son proyectos de uso masivo. |
| Herramientas con licencias GPL usadas solo para construir | Pandoc (GPL) convierte los documentos a Word. | No se distribuye con el software ni toca el código; solo produce los `.docx`. |
| Dependencias de desarrollo | `pytest`, `pip-audit`, `playwright`, etc. | No se instalan en la imagen de producción. |

# 9. Cómo se verificó

1. **Árbol real:** `python scripts/licencias.py` parte de `requirements.txt`, resuelve las dependencias de forma transitiva (incluidos los extras de `uvicorn[standard]` y los marcadores de plataforma) y lee los metadatos de cada paquete instalado.
2. **Imagen que se despliega:** el mismo script se ejecuta dentro de la imagen `sales-x-api` (Linux), que es lo que realmente llega a producción; de ahí salen los 29 paquetes y las 7 licencias de este documento.
3. **Normalización:** `License-Expression`, `License` y los clasificadores se reducen a nombres estándar (MIT, BSD-3-Clause, Apache-2.0, etc.); si aparece LGPL no se cuenta además como GPL.
4. **Vulnerabilidades:** `pip-audit` no reporta vulnerabilidades conocidas (Evidencia 7, anexo B).
5. **Límites:** no es un dictamen jurídico; no se revisó el texto completo de cada licencia ni los archivos `NOTICE`; la información depende de lo que cada paquete declare.
