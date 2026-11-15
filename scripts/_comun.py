"""Utilidades compartidas por los generadores de documentación (PDF y Word)."""

import re
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
SISTEMA = "SALES-X"
DESCRIPCION_SISTEMA = "Sistema de gestión de ventas y pedidos"
CURSO = "Proyecto académico · Integración de Aplicaciones · Sexto semestre"


def version() -> str:
    m = re.search(r'__version__\s*=\s*"([^"]+)"', (RAIZ / "app" / "__init__.py").read_text(encoding="utf-8"))
    return m.group(1) if m else "1.0.0"


def fecha_larga(d: date | None = None) -> str:
    d = d or date.today()
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def autores() -> str:
    """Nombres de los autores (una sola vez, en docs/autores.txt). Si no existe, deja un marcador visible."""
    f = DOCS / "autores.txt"
    if f.exists():
        nombres = [x.strip() for x in f.read_text(encoding="utf-8").splitlines() if x.strip() and not x.startswith("#")]
        if nombres:
            return " · ".join(nombres)
    return "[Nombre del estudiante o equipo]"


def linea_proyecto() -> str:
    return f"{CURSO} · {SISTEMA} {version()} · {fecha_larga()}"


def separar_front_matter(texto: str) -> tuple[dict, str]:
    """Lee el bloque `---` inicial. Admite `clave: valor` y listas `metadatos:` con líneas `  - Etiqueta | Valor`."""
    m = re.match(r"^---\n(.*?)\n---\n", texto, re.S)
    if not m:
        return {}, texto
    meta: dict = {}
    clave_lista = None
    for linea in m.group(1).splitlines():
        item = re.match(r"^\s+-\s+(.*)$", linea)
        if item and clave_lista:
            meta[clave_lista].append(item.group(1).strip())
            continue
        kv = re.match(r"^([A-Za-z_]+):\s*(.*)$", linea)
        if kv:
            if kv.group(2) == "":
                clave_lista = kv.group(1)
                meta[clave_lista] = []
            else:
                clave_lista = None
                meta[kv.group(1)] = kv.group(2).strip()
    return meta, texto[m.end():]


def expandir(texto: str, base: Path | None = None) -> str:
    """Sustituye las líneas `{{incluir: ruta}}` por el contenido del archivo (ruta relativa a docs/)."""
    base = base or DOCS

    def reemplazo(m):
        f = base / m.group(1).strip()
        return f.read_text(encoding="utf-8").rstrip() if f.exists() else f"> **Falta el fragmento `{m.group(1).strip()}`:** ejecute `python scripts/generar_fragmentos.py`."

    return re.sub(r"^\{\{incluir:\s*([^}]+)\}\}[ \t]*$", reemplazo, texto, flags=re.M)


def filas_meta(meta: dict) -> list[tuple[str, str]]:
    filas = []
    for it in meta.get("metadatos", []):
        etiqueta, _, valor = it.partition("|")
        filas.append((etiqueta.strip(), valor.strip()))
    return filas
