"""Contrasta la documentación (docs/fuentes) con el código real.

Uso:  python scripts/verificar_documentacion.py
Sale con código 1 si encuentra diferencias. No modifica nada.

Comprueba:
  1. Cada prueba mapeada en E6 (CP-xx -> función) existe, y cada prueba del código está mapeada.
  2. Numeración CP contigua y total igual al número de pruebas recolectadas por pytest.
  3. Las tablas y columnas del modelo aparecen en E1/E2 y el total de campos coincide.
  4. Los RF/RNF/HU definidos en E3 están en E6, y E6 no cita IDs inexistentes.
  5. Cifras clave (pruebas, operaciones, paquetes, versión) coinciden con el código.
  6. No quedan referencias obsoletas (IT-xx, nombres de otros proyectos, etc.).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FUENTES = RAIZ / "docs" / "fuentes"
FRAG = RAIZ / "docs" / "fragmentos"
sys.path.insert(0, str(RAIZ))

errores: list[str] = []
avisos: list[str] = []
ok: list[str] = []


def leer(nombre: str) -> str:
    return (FUENTES / nombre).read_text(encoding="utf-8")


def todos_los_textos() -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(FUENTES.glob("*.md"))}


def pruebas_recolectadas() -> list[str]:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
    )
    ids = [l.strip() for l in r.stdout.splitlines() if "::" in l and not l.startswith(("=", " "))]
    if not ids:
        errores.append("pytest no recolectó pruebas:\n" + r.stdout[-500:] + r.stderr[-500:])
    return ids


def version_codigo() -> str:
    m = re.search(r'__version__\s*=\s*"([^"]+)"', (RAIZ / "app" / "__init__.py").read_text(encoding="utf-8"))
    return m.group(1)


# ---------------------------------------------------------------- 1 y 2
def verificar_pruebas() -> None:
    ids = pruebas_recolectadas()
    funciones = sorted({re.sub(r"\[.*\]$", "", i.split("::")[-1]) for i in ids})
    e6 = leer("E6_Matriz_Trazabilidad.md")
    # filas de la tabla de correspondencia: | CP-01 | `fn` | CP-33 | `fn` |
    pares = re.findall(r"\|\s*(CP-\d+)\s*\|\s*`([^`]+)`", e6)
    mapa: dict[str, str] = {}
    for cp, fn in pares:
        # una prueba parametrizada puede aparecer con su variante: `fn[caso]`
        base = re.sub(r"\[.*\]$", "", fn)
        if cp in mapa:
            errores.append(f"E6: {cp} aparece mapeado dos veces")
        mapa[cp] = base
    numeros = sorted(int(c[3:]) for c in mapa)
    if numeros != list(range(1, len(numeros) + 1)):
        errores.append(f"E6: la numeración CP no es contigua (hay {len(numeros)} y faltan/sobran números)")
    for cp, fn in mapa.items():
        if fn not in funciones:
            errores.append(f"E6: {cp} apunta a `{fn}`, que no existe en tests/")
    sin_mapa = [f for f in funciones if f not in set(mapa.values())]
    if sin_mapa:
        errores.append("Pruebas del código sin CP en E6: " + ", ".join(sin_mapa))
    if len(mapa) != len(ids):
        errores.append(f"E6 mapea {len(mapa)} pruebas pero pytest recolecta {len(ids)}")
    else:
        ok.append(f"{len(ids)} pruebas recolectadas = {len(mapa)} filas CP en E6, todas existen")
    globals()["TOTAL_PRUEBAS"] = len(ids)


# ---------------------------------------------------------------- 3
def verificar_modelo() -> None:
    from app.database import Base  # noqa: WPS433
    import app.models  # noqa: F401,WPS433

    tablas = Base.metadata.tables
    campos = sum(len(t.columns) for t in tablas.values())
    e1, e2 = leer("E1_Modelo_Entidad_Relacion.md"), leer("E2_Diccionario_de_Datos.md")
    dic = (FRAG / "diccionario_entidades.md").read_text(encoding="utf-8")
    for nombre, t in tablas.items():
        if nombre not in e1:
            errores.append(f"E1 no menciona la tabla `{nombre}`")
        if nombre not in dic:
            errores.append(f"El diccionario generado no incluye la tabla `{nombre}`")
        for c in t.columns:
            if f"`{c.name}`" not in dic:
                errores.append(f"El diccionario no incluye la columna {nombre}.{c.name}")
    for nombre, texto in (("E1", e1), ("E2", e2)):
        if f"{len(tablas)} tablas" not in texto:
            errores.append(f"{nombre}: no dice «{len(tablas)} tablas»")
    if f"{campos} campos" not in e2 and f"{campos} campos" not in e1:
        errores.append(f"E1/E2 no mencionan «{campos} campos»")
    ok.append(f"{len(tablas)} tablas y {campos} campos del modelo presentes en E1/E2")


# ---------------------------------------------------------------- 4
def ids_definidos(texto: str, prefijo: str) -> set[str]:
    return set(re.findall(rf"^\|\s*({prefijo}-\d+)\s*\|", texto, re.M))


def verificar_requisitos() -> None:
    e3, e6 = leer("E3_ERS_IEEE830.md"), leer("E6_Matriz_Trazabilidad.md")
    for pref in ("RF", "RNF"):
        d3 = ids_definidos(e3, pref)
        citados6 = set(re.findall(rf"\b{pref}-\d+\b", e6))
        falta = sorted(d3 - citados6)
        sobra = sorted(citados6 - d3)
        if falta:
            errores.append(f"E6 no traza {pref}: {', '.join(falta)}")
        if sobra:
            errores.append(f"E6 cita {pref} inexistentes en E3: {', '.join(sobra)}")
        ok.append(f"{pref}: {len(d3)} definidos en E3, todos trazados en E6")
    # Historias de usuario: filas de E6
    hus = set(re.findall(r"^\|\s*(HU-\d+)\b", e6, re.M))
    if len(hus) != 17:
        avisos.append(f"E6 tiene {len(hus)} historias (se esperaban 17)")
    # CP citados en cualquier documento no pueden superar el total
    total = globals().get("TOTAL_PRUEBAS", 0)
    for nombre, texto in todos_los_textos().items():
        for n in re.findall(r"\bCP-(\d+)\b", texto):
            if total and not 1 <= int(n) <= total:
                errores.append(f"{nombre}: cita CP-{n}, fuera del rango 1..{total}")
    ok.append("IDs de requisitos y de pruebas coherentes entre E3, E6 y el resto")


# ---------------------------------------------------------------- 5
def verificar_cifras() -> None:
    res = json.loads((FRAG / "_resumen.json").read_text(encoding="utf-8"))
    v = version_codigo()
    textos = todos_los_textos()
    total = globals().get("TOTAL_PRUEBAS", 0)

    # versión
    for nombre in ("E7_Pruebas_Integracion.md", "05-Revision-Lanzamiento-GO-NO-GO.md", "Manual-de-Usuario.md",
                   "Guia-de-Operacion-y-Despliegue.md", "04-Estado-de-Remediacion.md", "capacidad.md"):
        if v not in textos.get(nombre, ""):
            errores.append(f"{nombre}: no menciona la versión {v}")

    # operaciones expuestas
    ops = res["endpoints"]["operaciones"]
    if f"{ops} operaciones" not in textos["01-Informe-Auditoria-Seguridad-SALES-X.md"]:
        errores.append(f"01: no menciona «{ops} operaciones»")
    if "30 operaciones" not in textos["E3_ERS_IEEE830.md"] and f"{ops-1} operaciones" not in textos["E3_ERS_IEEE830.md"]:
        avisos.append(f"E3: revisar el número de operaciones bajo /api/v1 (código: {ops} con /health)")

    # paquetes
    pk = res["licencias"]["paquetes"]
    if f"{pk} paquetes" not in textos["E4_Matriz_Propiedad_Intelectual.md"]:
        errores.append(f"E4: no menciona «{pk} paquetes»")

    # total de pruebas en los documentos que lo citan
    for nombre, texto in textos.items():
        for n in re.findall(r"\b(\d+) pruebas (?:automat|autom|aprob|en total|de integraci)", texto):
            if int(n) not in (total, 60, 3) and total:
                avisos.append(f"{nombre}: dice «{n} pruebas»; el total real es {total}")

    # alineación con el README
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    if f"{total} pruebas" not in readme:
        errores.append(f"README: no menciona «{total} pruebas»")
    ok.append(f"Cifras clave: versión {v}, {total} pruebas, {ops} operaciones, {pk} paquetes")


# ---------------------------------------------------------------- 6
PROHIBIDOS = [
    (r"\bIT-\d+", "referencia antigua IT-xx (ahora CP-xx)"),
    (r"FINAN-?X(?! \(referencia)", None),  # se admite solo la mención de referencia
    (r"Jaramillo|Mayra|V[eé]lez Hern", "nombre de los autores del proyecto de ejemplo"),
    (r"los 7 tablas", "concordancia: «las 7 tablas»"),
]


def verificar_obsoletos() -> None:
    for nombre, texto in todos_los_textos().items():
        for patron, msg in PROHIBIDOS:
            hits = re.findall(patron, texto)
            if hits and msg:
                errores.append(f"{nombre}: {msg} ({len(hits)})")
            elif hits and msg is None:
                avisos.append(f"{nombre}: menciona FINAN-X ({len(hits)}); confirmar que sea solo como referencia")
    # carpetas citadas que deben existir
    for nombre, texto in todos_los_textos().items():
        for ruta in set(re.findall(r"\.\./capturas/([\w\-]+\.png)", texto)):
            if not (RAIZ / "docs" / "capturas" / ruta).exists():
                errores.append(f"{nombre}: falta la captura {ruta}")
        for ruta in set(re.findall(r"\.\./diagramas/([\w\-]+\.(?:png|svg))", texto)):
            if not (RAIZ / "docs" / "diagramas" / ruta).exists():
                errores.append(f"{nombre}: falta el diagrama {ruta}")
        for inc in re.findall(r"\{\{incluir:\s*([^}]+?)\s*\}\}", texto):
            if not (RAIZ / "docs" / inc).exists():
                errores.append(f"{nombre}: el fragmento {inc} no existe (ejecute generar_fragmentos.py)")
    ok.append("Sin referencias obsoletas ni recursos faltantes")


def main() -> int:
    for paso in (verificar_pruebas, verificar_modelo, verificar_requisitos, verificar_cifras, verificar_obsoletos):
        try:
            paso()
        except Exception as exc:  # noqa: BLE001
            errores.append(f"{paso.__name__} falló: {exc!r}")
    print("== Verificación documentación ↔ código ==")
    for m in ok:
        print("  OK   ", m)
    for m in avisos:
        print("  AVISO", m)
    for m in errores:
        print("  ERROR", m)
    print(f"\nResultado: {len(ok)} comprobaciones correctas, {len(avisos)} avisos, {len(errores)} errores.")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
