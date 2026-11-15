"""Arma el paquete de entrega en <proyecto final>/ENTREGA.

Uso:  python scripts/armar_entrega.py [--sin-regenerar]

Con los mismos 13 nombres del proyecto de referencia:
  E1..E7 y Acta -> PDF · 01, 03, 04, 05 y capacidad -> Markdown (con los fragmentos ya expandidos)
  Word/   -> versiones .docx editables de todos
  Extras/ -> Manual de usuario y Guía de operación (PDF y Markdown)
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _comun as C  # noqa: E402

RAIZ = C.RAIZ
DESTINO = RAIZ.parent / "ENTREGA"
FUENTES = C.DOCS / "fuentes"

PDFS = [
    "E1_Modelo_Entidad_Relacion", "E2_Diccionario_de_Datos", "E3_ERS_IEEE830", "E4_Matriz_Propiedad_Intelectual",
    "E5_Contrato_Licencia_Software", "E6_Matriz_Trazabilidad", "E7_Pruebas_Integracion", "Acta-Usuarios-Primer-Ingreso",
]
MARKDOWNS = [
    "01-Informe-Auditoria-Seguridad-SALES-X", "03-Metodologia-y-Evidencias", "04-Estado-de-Remediacion",
    "05-Revision-Lanzamiento-GO-NO-GO", "capacidad",
]
EXTRAS = ["Manual-de-Usuario", "Guia-de-Operacion-y-Despliegue"]


def ejecutar(script: str) -> None:
    r = subprocess.run([sys.executable, str(RAIZ / "scripts" / script)], cwd=RAIZ, text=True, capture_output=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"{script} falló:\n{r.stdout[-800:]}\n{r.stderr[-800:]}")
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else f"{script} OK")


def markdown_expandido(nombre: str) -> str:
    """Cuerpo en Markdown con los fragmentos incluidos y sin la cabecera de portada."""
    meta, cuerpo = C.separar_front_matter((FUENTES / f"{nombre}.md").read_text(encoding="utf-8"))
    return C.expandir(cuerpo).strip() + "\n"


def main() -> None:
    if "--sin-regenerar" not in sys.argv:
        print("Regenerando PDF y Word…")
        ejecutar("generar_pdf.py")
        ejecutar("generar_word.py")

    if DESTINO.exists():
        shutil.rmtree(DESTINO)
    (DESTINO / "Word").mkdir(parents=True)
    (DESTINO / "Extras").mkdir()
    (DESTINO / "Diagramas").mkdir()

    for n in PDFS:
        shutil.copy2(C.DOCS / f"{n}.pdf", DESTINO / f"{n}.pdf")
    for n in MARKDOWNS:
        (DESTINO / f"{n}.md").write_text(markdown_expandido(n), encoding="utf-8")
    for n in PDFS + MARKDOWNS:
        shutil.copy2(C.DOCS / "word" / f"{n}.docx", DESTINO / "Word" / f"{n}.docx")
    for n in EXTRAS:
        shutil.copy2(C.DOCS / f"{n}.pdf", DESTINO / "Extras" / f"{n}.pdf")
        (DESTINO / "Extras" / f"{n}.md").write_text(markdown_expandido(n), encoding="utf-8")
        shutil.copy2(C.DOCS / "word" / f"{n}.docx", DESTINO / "Extras" / f"{n}.docx")

    for d in ("casos-de-uso.png", "diagrama-de-clases.png", "modelo-de-datos.png", "mer-salesx.png"):
        shutil.copy2(C.DOCS / "diagramas" / d, DESTINO / "Diagramas" / d)

    v = C.version()
    (DESTINO / "LEEME.txt").write_text(
        f"""SALES-X {v} · Gestión de ventas y pedidos · Paquete de entrega
================================================================

Documentos principales (13, con los mismos nombres del proyecto de referencia)
  E1  Modelo entidad-relación            E5  Contrato de licencia de software
  E2  Diccionario de datos               E6  Matriz de trazabilidad
  E3  ERS (IEEE 830)                     E7  Pruebas de integración
  E4  Matriz de propiedad intelectual    Acta de usuarios y primer ingreso (PDF)
  01 Informe de auditoría · 03 Metodología y evidencias · 04 Estado de remediación
  05 Revisión de lanzamiento (GO/NO-GO) · capacidad   (Markdown)

Word\\    Versión editable (.docx) de cada documento.
Diagramas\\  UML (casos de uso y clases), modelo de datos y MER.
Extras\\  Manual de usuario y Guía de operación y despliegue (PDF, Markdown y Word).
Código    SALES-X_entrega.zip (en la carpeta superior): aplicación, pruebas, Docker y specs.

Antes de entregar: escriba los nombres del equipo en docs/autores.txt (y regenere con
python scripts/armar_entrega.py) y complete las firmas de los documentos E5, Acta y 05.
""",
        encoding="utf-8",
    )
    total = sum(1 for p in DESTINO.rglob("*") if p.is_file())
    print(f"Entrega armada en {DESTINO} ({total} archivos)")


if __name__ == "__main__":
    main()
