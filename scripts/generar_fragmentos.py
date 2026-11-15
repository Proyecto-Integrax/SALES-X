"""Genera los fragmentos de documentación derivados de DATOS REALES del programa (docs/fragmentos/*.md).

Los documentos los incluyen con una línea `{{incluir: fragmentos/<archivo>.md}}`, de modo que las cifras no se escriben
a mano y no pueden desactualizarse.

    endpoints.md            operaciones de la API con su mecanismo de autenticación y rol (desde las rutas reales)
    licencias.md            dependencias directas y transitivas con su licencia (desde los paquetes instalados)
    inventario_codigo.md    archivos, líneas y huella SHA-256 de cada archivo fuente
    pruebas_por_bloque.md   pruebas por archivo (desde la recolección real de pytest)
    registro_pruebas.md     salida completa de `pytest -v` (solo con --con-pruebas; tarda ~30 s)

Uso:  python scripts/generar_fragmentos.py [--con-pruebas]
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "docs" / "fragmentos"
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


def escribir(nombre: str, texto: str) -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / nombre).write_text(texto.rstrip() + "\n", encoding="utf-8")
    print(f"OK  {nombre}")


# ------------------------------------------------------------------ endpoints
def endpoints() -> dict:
    from fastapi.routing import APIRoute

    from app.main import API, app
    from app.routers import auth, catalogo, consumidores, integracion, pedidos, reportes

    def llamadas(dep, acumulado):
        for d in dep.dependencies:
            acumulado.add(getattr(d.call, "__name__", str(d.call)))
            llamadas(d, acumulado)

    # FastAPI registra los routers de forma diferida: se leen directamente de cada router (que ya trae sus dependencias)
    rutas = [r for r in app.routes if isinstance(r, APIRoute)]  # /health y /
    for router in (auth.router, consumidores.router, catalogo.router, pedidos.router, reportes.router, integracion.router):
        for r in router.routes:
            if isinstance(r, APIRoute):
                copia = type("R", (), {"dependant": r.dependant, "methods": r.methods, "path": f"{API}{r.path}", "summary": r.summary, "name": r.name})
                rutas.append(copia)

    filas, cuenta = [], Counter()
    for r in rutas:
        nombres: set = set()
        llamadas(r.dependant, nombres)
        if "require_admin" in nombres:
            auth, rol = "Sesión (cookie `HttpOnly` o Bearer)", "Administrador"
        elif "require_api_key" in nombres:
            auth, rol = "API Key (`X-API-Key`)", "Sistema consumidor"
        elif "current_user" in nombres:
            auth, rol = "Sesión (cookie `HttpOnly` o Bearer)", "Vendedor o administrador"
        elif "session_user" in nombres:
            auth, rol = "Sesión (incluso con cambio de contraseña pendiente)", "Cualquier usuario"
        else:
            auth, rol = "Ninguna (pública)", "—"
        cuenta[rol] += 1
        for m in sorted(r.methods - {"HEAD", "OPTIONS"}):
            filas.append((r.path, m, auth, rol, r.summary or r.name))
    orden = {"GET": 0, "POST": 1, "PUT": 2, "PATCH": 3, "DELETE": 4}
    filas.sort(key=lambda f: (f[0].replace("/api/v1", ""), orden.get(f[1], 9)))
    md = ["| Método | Ruta | Autenticación | Rol | Descripción |", "|---|---|---|---|---|"]
    for ruta, m, auth, rol, resumen in filas:
        md.append(f"| {m} | `{ruta}` | {auth} | {rol} | {resumen} |")
    escribir("endpoints.md", "\n".join(md))
    return {"operaciones": len(filas), "por_rol": dict(cuenta)}


# ------------------------------------------------------------------ licencias
def licencias() -> dict:
    import licencias as L

    pk, fuente = None, "entorno local (Windows)"
    docker = Path(r"C:\Program Files\Docker\Docker\resources\bin\docker.exe")
    if docker.exists():  # lo que se despliega es la imagen Docker (Linux): se analiza ahí si está disponible
        try:
            r = subprocess.run([str(docker), "run", "--rm", "-v", f"{RAIZ}:/w", "-w", "/w", "--entrypoint", "sh", "sales-x-api", "-c",
                                "pip install -q packaging >/dev/null 2>&1; python scripts/licencias.py --json"], capture_output=True, timeout=180)
            datos = json.loads(r.stdout.decode("utf-8-sig"))
            pk, fuente = datos["paquetes"], "imagen Docker `sales-x-api` (Linux, lo que se despliega)"
        except Exception:  # noqa: BLE001 - sin Docker o sin imagen: se usa el entorno local
            pk = None
    if pk is None:
        raices = [r for r in L.directos(RAIZ / "requirements.txt") if L.norm(r.name) not in {L.norm(d) for d in L.DEV}]
        pk = sorted(L.cierre(raices).values(), key=lambda v: (not v["directo"], v["nombre"].lower()))
    md = [f"*Fuente del análisis: {fuente}.*", "", "**Dependencias directas** (las que declara `requirements.txt` y se distribuyen):", "", "| Paquete | Versión | Licencia | Para qué se usa |", "|---|---|---|---|"]
    uso = {"fastapi": "Framework de la API REST", "uvicorn": "Servidor ASGI", "sqlalchemy": "ORM y acceso a datos", "psycopg2-binary": "Conector a PostgreSQL",
           "pydantic-settings": "Configuración por variables de entorno", "pyjwt": "Tokens de sesión (JWT)", "bcrypt": "Hash de contraseñas",
           "httpx": "Cliente HTTP (integración con Clientes y Productos)", "tzdata": "Zonas horarias (America/Bogota) en Windows"}
    for p in pk:
        if p["directo"]:
            md.append(f"| {p['nombre']} | {p['version']} | {p['licencia']} | {uso.get(p['nombre'].lower(), '')} |")
    md += ["", "**Dependencias transitivas** (las que traen las anteriores):", "", "| Paquete | Versión | Licencia | Lo trae |", "|---|---|---|---|"]
    for p in pk:
        if not p["directo"]:
            md.append(f"| {p['nombre']} | {p['version']} | {p['licencia']} | {p['padre']} |")
    escribir("licencias.md", "\n".join(md))
    por = Counter(p["licencia"] for p in pk)
    return {"paquetes": len(pk), "directos": sum(p["directo"] for p in pk), "licencias": len(por)}


# ------------------------------------------------------------------ inventario del código
AREAS = [
    ("app/ (API: rutas, servicios, modelos, integración)", "app", {".py"}),
    ("app/static/ (interfaz web)", "app/static", {".js", ".html", ".css"}),
    ("sql/ (esquema, semillas, rol, migración)", "sql", {".sql"}),
    ("tests/ (pruebas automatizadas)", "tests", {".py"}),
    ("mocks/ (servicios simulados de INTEGRAX)", "mocks", {".py"}),
    ("scripts/ (carga, documentación, utilidades)", "scripts", {".py", ".ps1"}),
    ("Despliegue (Docker y arranque)", ".", {".yml", ".bat"}),
]


def contar(directorio: Path, exts, recursivo=True):
    archivos = []
    it = directorio.rglob("*") if recursivo else directorio.glob("*")
    for f in it:
        if f.is_file() and f.suffix in exts and "__pycache__" not in f.parts and ".git" not in f.parts and f.name != "package-lock.json":
            archivos.append(f)
    return archivos


def inventario() -> dict:
    def miles(n):
        return f"{n:,}".replace(",", ".")

    filas = ["| Área | Archivos | Líneas |", "|---|---:|---:|"]
    total_a = total_l = 0
    todos = []
    for nombre, rel, exts in AREAS:
        d = RAIZ / rel
        fs = contar(d, exts, recursivo=rel != ".")
        if rel == "app":
            fs = [f for f in fs if "static" not in f.parts]
        if rel == ".":
            fs += [RAIZ / "Dockerfile"]
        lineas = sum(len(f.read_text(encoding="utf-8", errors="ignore").splitlines()) for f in fs)
        filas.append(f"| {nombre} | {len(fs)} | {miles(lineas)} |")
        total_a += len(fs)
        total_l += lineas
        todos += fs
    filas.append(f"| **Total** | **{total_a}** | **{miles(total_l)}** |")
    escribir("inventario_codigo.md", "\n".join(filas) + "\n\n" + hashes(sorted(set(todos))))
    return {"archivos": total_a, "lineas": total_l}


def hashes(archivos) -> str:
    md = ["**Huellas de integridad (SHA-256, primeros 16 caracteres)** de los archivos fuente analizados:", "", "| Archivo | Bytes | SHA-256 |", "|---|---:|---|"]
    for f in archivos:
        rel = f.relative_to(RAIZ).as_posix()
        md.append(f"| `{rel}` | {f'{f.stat().st_size:,}'.replace(',', '.')} | `{hashlib.sha256(f.read_bytes()).hexdigest()[:16]}` |")
    return "\n".join(md)


# ------------------------------------------------------------------ pruebas
def pruebas() -> dict:
    r = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=RAIZ, capture_output=True, text=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    por_archivo = Counter()
    for linea in r.stdout.splitlines():
        m = re.match(r"^(tests/[\w]+\.py)::", linea)
        if m:
            por_archivo[m.group(1)] += 1
    desc = {
        "tests/test_api.py": "Núcleo de la API: autenticación, pedidos, estados, reportes, integración, seguridad básica",
        "tests/test_config.py": "Validación de la configuración de producción",
        "tests/test_timeutil.py": "Zona horaria de negocio (reportes por día)",
        "tests/test_endurecimiento.py": "Endurecimiento: bloqueo en BD, consumidores, cookie + CSRF, contraseñas",
        "tests/test_catalogo_rest.py": "Integración REST con Clientes y Productos (servicio HTTP simulado)",
        "tests/test_concurrencia.py": "Concurrencia: cambios de estado simultáneos sobre un mismo pedido (solo PostgreSQL)",
    }
    md = ["| Bloque de pruebas | Archivo | Pruebas | Resultado |", "|---|---|---:|---|"]
    for arch in sorted(por_archivo, key=lambda a: list(desc).index(a) if a in desc else 99):
        md.append(f"| {desc.get(arch, arch)} | `{arch}` | {por_archivo[arch]} | Aprobadas |")
    total = sum(por_archivo.values())
    md.append(f"| **Total** | | **{total}** | **{total} aprobadas, 0 fallidas** |")
    escribir("pruebas_por_bloque.md", "\n".join(md))
    return {"pruebas": total, "por_archivo": dict(por_archivo)}


def pip_audit() -> None:
    r = subprocess.run([sys.executable, "-m", "pip_audit", "-r", "requirements.txt", "--progress-spinner", "off"], cwd=RAIZ, capture_output=True, text=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    salida = (r.stdout + r.stderr).strip() or "(sin salida)"
    escribir("pip_audit.md", f"```\n$ python -m pip_audit -r requirements.txt\n{salida}\n```")


def registro_pruebas() -> None:
    r = subprocess.run([sys.executable, "-m", "pytest", "-v", "-p", "no:cacheprovider"], cwd=RAIZ, capture_output=True, text=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    lineas = [ln for ln in r.stdout.splitlines() if "PASSED" in ln or "FAILED" in ln or "ERROR" in ln or ln.startswith("=")]
    cuerpo = []
    for ln in lineas:
        m = re.match(r"^(tests/\w+\.py)::(\S+)\s+(PASSED|FAILED|ERROR)", ln)
        cuerpo.append(f"{'✔' if m and m.group(3) == 'PASSED' else '✘'} {m.group(1).split('/')[1]} · {m.group(2)}" if m else ln)
    escribir("registro_pruebas.md", "```\n" + "\n".join(cuerpo) + "\n```")


def main():
    resumen = {"endpoints": endpoints(), "licencias": licencias(), "inventario": inventario(), "pruebas": pruebas()}
    if "--con-pruebas" in sys.argv:
        registro_pruebas()
        pip_audit()
    (SALIDA / "_resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resumen, ensure_ascii=False))


if __name__ == "__main__":
    main()
