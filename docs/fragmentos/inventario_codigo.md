| Área | Archivos | Líneas |
|---|---:|---:|
| app/ (API: rutas, servicios, modelos, integración) | 23 | 1.720 |
| app/static/ (interfaz web) | 3 | 550 |
| sql/ (esquema, semillas, rol, migración) | 5 | 808 |
| tests/ (pruebas automatizadas) | 7 | 855 |
| mocks/ (servicios simulados de INTEGRAX) | 2 | 142 |
| scripts/ (carga, documentación, utilidades) | 12 | 1.787 |
| Despliegue (Docker y arranque) | 5 | 200 |
| **Total** | **57** | **6.062** |

**Huellas de integridad (SHA-256, primeros 16 caracteres)** de los archivos fuente analizados:

| Archivo | Bytes | SHA-256 |
|---|---:|---|
| `app/__init__.py` | 97 | `e43055aa7393ed17` |
| `app/config.py` | 2.267 | `e30fd0160b6e036a` |
| `app/database.py` | 892 | `4a425a91573d7016` |
| `app/demo.py` | 2.762 | `83d6e2fd9187445e` |
| `app/deps.py` | 2.770 | `8a85215362c49e04` |
| `app/integration/__init__.py` | 0 | `e3b0c44298fc1c14` |
| `app/integration/catalogo.py` | 7.259 | `16b300cd5a22aa5f` |
| `app/main.py` | 3.417 | `ce61c595bcf6a194` |
| `app/models.py` | 6.981 | `d1816ef91544bb62` |
| `app/routers/__init__.py` | 0 | `e3b0c44298fc1c14` |
| `app/routers/auth.py` | 5.537 | `aaaa2a8daed004e5` |
| `app/routers/catalogo.py` | 1.314 | `5647de19153f2697` |
| `app/routers/consumidores.py` | 2.187 | `b8144b3be851498c` |
| `app/routers/integracion.py` | 2.848 | `b80eb5b33f4e6382` |
| `app/routers/pedidos.py` | 5.366 | `3f18760954f2ee06` |
| `app/routers/reportes.py` | 3.374 | `3fbc7e33b87eb55d` |
| `app/schemas.py` | 5.724 | `4427a3fc20ec285e` |
| `app/security.py` | 2.265 | `a06d2ca39a1efc78` |
| `app/seed.py` | 1.308 | `092f7c6dd3fc0d3d` |
| `app/services/__init__.py` | 0 | `e3b0c44298fc1c14` |
| `app/services/login_throttle.py` | 1.047 | `012852149ce67d28` |
| `app/services/pedidos.py` | 7.385 | `36d0528b750d62e1` |
| `app/static/app.js` | 29.159 | `e6b2c35628c88d1d` |
| `app/static/index.html` | 2.717 | `395fdead950d5ddb` |
| `app/static/styles.css` | 7.398 | `bea3e4fb22196195` |
| `app/timeutil.py` | 1.077 | `ddb178154e2155c8` |
| `docker-compose.mock.yml` | 1.137 | `023c00fadfd159d3` |
| `docker-compose.yml` | 2.057 | `0d2502ad4223cb0f` |
| `Dockerfile` | 615 | `3984fc5c18edbe3c` |
| `iniciar-docker.bat` | 2.094 | `f03ea1daa5709c8c` |
| `iniciar.bat` | 1.583 | `9c78c6237b267ec3` |
| `mocks/__init__.py` | 0 | `e3b0c44298fc1c14` |
| `mocks/integrax_mock.py` | 4.412 | `4c32c5630c51a284` |
| `scripts/_comun.py` | 2.914 | `dee416a6866f5233` |
| `scripts/armar_entrega.py` | 4.313 | `4ebc6bf31f0fd837` |
| `scripts/capturas.py` | 5.994 | `ad58b6ef7081541f` |
| `scripts/carga_basica.py` | 3.157 | `658fce5ad239d5dc` |
| `scripts/generar_diccionario.py` | 9.989 | `38d2ba4c94aba63b` |
| `scripts/generar_env_docker.ps1` | 1.096 | `dbc60138f4fe4c16` |
| `scripts/generar_fragmentos.py` | 11.568 | `0814e665426eddb0` |
| `scripts/generar_mer.py` | 8.488 | `a7d35e06efdb3fa1` |
| `scripts/generar_pdf.py` | 6.929 | `a6aa634e29b5ef5a` |
| `scripts/generar_word.py` | 17.376 | `82c34ebb621655d5` |
| `scripts/licencias.py` | 4.805 | `8e26120c58bfccdd` |
| `scripts/verificar_documentacion.py` | 10.486 | `dca70e3a5436ab2f` |
| `sql/01_schema.sql` | 4.165 | `c4dbcdee25ac09ec` |
| `sql/02_seed_estados.sql` | 625 | `1a9e77feef6277a9` |
| `sql/03_rol_aplicacion.sql` | 3.032 | `1741b9878ae1e726` |
| `sql/04_migracion_v1_1.sql` | 1.759 | `30b5b89e1bb8ba9c` |
| `sql/salesx_demo.sql` | 55.398 | `8b0d2a69a44be6b7` |
| `tests/conftest.py` | 2.622 | `0fbf7cab97451029` |
| `tests/test_api.py` | 13.652 | `e51ea96ba46f8573` |
| `tests/test_catalogo_rest.py` | 9.591 | `71e25efb284d82a1` |
| `tests/test_concurrencia.py` | 4.641 | `1c809254f033faab` |
| `tests/test_config.py` | 886 | `32b35e3e3e892271` |
| `tests/test_endurecimiento.py` | 10.863 | `85c9cc2196aebcc5` |
| `tests/test_timeutil.py` | 640 | `e32f968280f9dd2f` |
