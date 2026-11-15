"""Analiza el árbol REAL de dependencias de Python de SALES-X y sus licencias (insumo de la Evidencia 4).

Resuelve requirements.txt de forma transitiva a partir de los paquetes instalados.
Uso:  python scripts/licencias.py            → informe en pantalla
      python scripts/licencias.py --json     → datos en JSON
"""

import json
import re
import sys
from importlib.metadata import PackageNotFoundError, metadata, requires, version
from pathlib import Path

from packaging.requirements import Requirement

RAIZ = Path(__file__).resolve().parent.parent
DEV = {"pytest", "pip-audit", "markdown", "pypandoc-binary", "python-docx", "pymupdf", "playwright"}  # no se distribuyen
CANON = [
    (r"\bMIT\b", "MIT"),
    (r"Apache", "Apache-2.0"),
    (r"BSD", "BSD-3-Clause"),
    (r"LGPL|Lesser", "LGPL-3.0"),
    (r"\bGPL|General Public", "GPL"),
    (r"PSF|Python Software", "PSF-2.0"),
    (r"MPL|Mozilla", "MPL-2.0"),
    (r"ISC", "ISC"),
    (r"Unlicense|Public Domain", "Dominio público"),
]
COPYLEFT_FUERTE = {"GPL"}
COPYLEFT_DEBIL = {"LGPL-3.0", "MPL-2.0"}


def norm(nombre: str) -> str:
    return re.sub(r"[-_.]+", "-", nombre).lower()


def licencia(pkg: str) -> str:
    m = metadata(pkg)
    expr = m.get("License-Expression") or ""
    clas = [c.split("::")[-1].strip() for c in (m.get_all("Classifier") or []) if c.startswith("License")]
    texto = " ".join([expr, m.get("License") or "" if len(m.get("License") or "") < 80 else "", *clas])
    encontradas = []
    for patron, nombre in CANON:
        if re.search(patron, texto, re.I) and nombre not in encontradas:
            encontradas.append(nombre)
    if "LGPL-3.0" in encontradas and "GPL" in encontradas:
        encontradas.remove("GPL")  # «Lesser General Public License» no es la GPL completa
    if not encontradas:
        return "(ver metadatos)"
    # "BSD" y "Apache" juntos son frecuentes (doble licencia): se informan ambas
    return " / ".join(encontradas)


def directos(archivo: Path) -> list[str]:
    nombres = []
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        linea = linea.split("#")[0].strip()
        if linea:
            nombres.append(Requirement(linea))
    return nombres


def cierre(raices: list[Requirement]) -> dict[str, dict]:
    vistos: dict[str, dict] = {}
    pila = [(r, None) for r in raices]
    while pila:
        req, padre = pila.pop()
        n = norm(req.name)
        if n in vistos:
            continue
        try:
            version(req.name)
        except PackageNotFoundError:
            continue
        vistos[n] = {"nombre": req.name, "version": version(req.name), "licencia": licencia(req.name), "directo": padre is None, "padre": padre, "extras": sorted(req.extras)}
        for dep in requires(req.name) or []:
            r = Requirement(dep)
            extras = req.extras or {""}
            if r.marker and not any(r.marker.evaluate({"extra": e}) for e in extras):
                continue
            pila.append((r, req.name))
    return vistos


def main():
    raices = [r for r in directos(RAIZ / "requirements.txt") if norm(r.name) not in {norm(d) for d in DEV}]
    todo = cierre(raices)
    runtime = {k: v for k, v in todo.items() if norm(k) not in {norm(d) for d in DEV}}
    por_lic: dict[str, list[str]] = {}
    for v in runtime.values():
        por_lic.setdefault(v["licencia"], []).append(v["nombre"])
    datos = {
        "paquetes_analizados": len(runtime),
        "dependencias_directas": sum(1 for v in runtime.values() if v["directo"]),
        "licencias_distintas": len(por_lic),
        "copyleft_fuerte": sorted(n for lic, ns in por_lic.items() for n in ns if re.search(r"(?<!L)GPL", lic)),  # LGPL no cuenta
        "copyleft_debil": sorted(n for lic, ns in por_lic.items() for n in ns if any(c in lic for c in COPYLEFT_DEBIL)),
        "por_licencia": {k: sorted(v) for k, v in sorted(por_lic.items(), key=lambda kv: -len(kv[1]))},
        "paquetes": sorted(runtime.values(), key=lambda v: (not v["directo"], v["nombre"].lower())),
    }
    if "--json" in sys.argv:
        print(json.dumps(datos, ensure_ascii=False, indent=2))
        return
    print(f"Paquetes analizados (runtime, transitivo): {datos['paquetes_analizados']} · directos: {datos['dependencias_directas']} · licencias distintas: {datos['licencias_distintas']}")
    print("Copyleft fuerte:", datos["copyleft_fuerte"] or "ninguno", "| copyleft débil:", datos["copyleft_debil"] or "ninguno")
    print("\nPor licencia:")
    for lic, ns in datos["por_licencia"].items():
        print(f"  {lic:28} {len(ns):>3}  {', '.join(ns)}")
    print("\nDirectos:")
    for p in datos["paquetes"]:
        if p["directo"]:
            print(f"  {p['nombre']:20} {p['version']:10} {p['licencia']}")


if __name__ == "__main__":
    main()
