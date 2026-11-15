"""Genera versiones Word (.docx) editables de la documentación, en docs/word/.

Fuentes: docs/fuentes/*.md (E1–E7 y acta) y docs/*.md (informes 01–05, capacidad, manual y guía).
Requiere:  pip install pypandoc_binary python-docx      (Pandoc viene incluido en pypandoc_binary)
Uso:       python scripts/generar_word.py
"""

import re
import statistics
import sys
from pathlib import Path

import pypandoc
from docx import Document
from docx.enum.text import WD_BREAK  # noqa: F401
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _comun as C  # noqa: E402

RAIZ = C.RAIZ
DOCS = C.DOCS
SALIDA = DOCS / "word"
# +hard_line_breaks respeta los renglones escritos; -smart evita cambiar comillas y guiones
FORMATO = "markdown+pipe_tables+hard_line_breaks-smart"

AZUL, AZUL2, GRIS = "16367F", "1F3F94", "5A6478"
ANCHO_TEXTO_CM = 17.0  # A4 (21 cm) con márgenes de 2 cm


# ---------------------------------------------------------------- utilidades XML
def _el(nombre, **attrs):
    e = OxmlElement(nombre)
    for k, v in attrs.items():
        e.set(qn(k.replace("_", ":", 1)), str(v))
    return e


# Orden de los hijos que exige el esquema OOXML (Word rechaza o «repara» documentos con otro orden)
PPR = ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr", "suppressLineNumbers", "pBdr", "shd", "tabs",
       "suppressAutoHyphens", "kinsoku", "wordWrap", "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
       "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc", "textDirection", "textAlignment",
       "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange"]
RPR = ["rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike", "outline", "shadow", "emboss", "imprint", "noProof",
       "snapToGrid", "vanish", "webHidden", "color", "spacing", "w", "kern", "position", "sz", "szCs", "highlight", "u", "effect", "bdr", "shd",
       "fitText", "vertAlign", "rtl", "cs", "em", "lang", "eastAsianLayout", "specVanish", "oMath"]
TBLPR = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize", "tblStyleColBandSize", "tblW", "jc", "tblCellSpacing", "tblInd",
         "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook", "tblCaption", "tblDescription"]
TCPR = ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap", "tcMar", "textDirection", "tcFitText", "vAlign", "hideMark"]


def _local(e):
    return e.tag.split("}")[1]


def insertar(padre, hijo, orden):
    """Inserta `hijo` en `padre` en la posición que corresponde según `orden` (sustituye otro del mismo tipo)."""
    nombre = _local(hijo)
    for viejo in [c for c in padre if _local(c) == nombre]:
        padre.remove(viejo)
    pos = orden.index(nombre)
    for c in padre:
        if _local(c) in orden and orden.index(_local(c)) > pos:
            c.addprevious(hijo)
            return
    padre.append(hijo)


def sombrear(pr, color, orden=None):
    if orden is None:
        orden = {"pPr": PPR, "rPr": RPR, "tcPr": TCPR}[_local(pr)]
    insertar(pr, _el("w:shd", w_val="clear", w_color="auto", w_fill=color), orden)


def borde(pr, lado, color, sz=4, space=0):
    pb = pr.find(qn("w:pBdr"))
    if pb is None:
        pb = _el("w:pBdr")
        insertar(pr, pb, PPR)
    pb.append(_el(f"w:{lado}", w_val="single", w_sz=sz, w_space=space, w_color=color))


def fuente(estilo, nombre="Calibri", tam=None, negrita=None, color=None, cursiva=None):
    f = estilo.font
    f.name = nombre
    rpr = estilo.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = _el("w:rFonts")
        insertar(rpr, rf, RPR)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), nombre)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        rf.attrib.pop(qn(a), None)
    if tam:
        f.size = Pt(tam)
    if negrita is not None:
        f.bold = negrita
    if cursiva is not None:
        f.italic = cursiva
    if color:
        f.color.rgb = RGBColor.from_string(color)


def estilo(doc, nombre):
    try:
        return doc.styles[nombre]
    except KeyError:
        return None


# ---------------------------------------------------------------- estilos
def preparar_estilos(doc):
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2)
    sec.top_margin, sec.bottom_margin = Cm(2), Cm(2)
    sec.header_distance = sec.footer_distance = Cm(1)
    sec._sectPr.find(qn("w:pgMar")).set(qn("w:gutter"), "0")  # atributo obligatorio del esquema

    # idioma del documento (corrector ortográfico)
    rpr_def = doc.styles.element.find(qn("w:docDefaults")).find(qn("w:rPrDefault")).find(qn("w:rPr"))
    insertar(rpr_def, _el("w:lang", w_val="es-CO", w_eastAsia="es-CO", w_bidi="ar-SA"), RPR)

    fuente(doc.styles["Normal"], "Calibri", 10.5, color="1B2333")
    for n in ("Header", "Footer"):  # los números de página (campos) heredan este tamaño
        s = estilo(doc, n)
        if s:
            fuente(s, "Calibri", 8, color=GRIS)
    for n in ("Body Text", "First Paragraph", "Compact"):
        s = estilo(doc, n)
        if s:
            fuente(s, "Calibri", 10.5, color="1B2333")
            s.paragraph_format.space_before = Pt(0)
            s.paragraph_format.space_after = Pt(6 if n != "Compact" else 2)
            s.paragraph_format.line_spacing = 1.12
    medidas = {"Heading 1": (20, AZUL, 0, 8), "Heading 2": (14, AZUL, 16, 6), "Heading 3": (12, AZUL2, 12, 4), "Heading 4": (11, AZUL2, 10, 3)}
    for n, (tam, color, antes, despues) in medidas.items():
        s = estilo(doc, n)
        if s:
            fuente(s, "Calibri", tam, True, color, False)
            pf = s.paragraph_format
            pf.space_before, pf.space_after, pf.keep_with_next = Pt(antes), Pt(despues), True
    h2 = estilo(doc, "Heading 2")
    if h2:
        borde(h2.element.get_or_add_pPr(), "bottom", "DBE3F5", sz=6, space=2)
    cab = estilo(doc, "Codigo")
    if cab:
        fuente(cab, "Calibri", 9, True, "2457D6")
        cab.paragraph_format.space_after = Pt(2)
        borde(cab.element.get_or_add_pPr(), "bottom", "2457D6", sz=12, space=3)
    code = estilo(doc, "Source Code")
    if code:
        fuente(code, "Consolas", 8.5, color="1B2333")
        pf = code.paragraph_format
        pf.space_before, pf.space_after, pf.line_spacing = Pt(2), Pt(6), 1.0
        ppr = code.element.get_or_add_pPr()
        sombrear(ppr, "F4F6FB")
        for lado in ("top", "left", "bottom", "right"):
            borde(ppr, lado, "DBE3F5", sz=4, space=4)
    vc = estilo(doc, "Verbatim Char")
    if vc:
        fuente(vc, "Consolas", 9.5, color="1B2333")
        sombrear(vc.element.get_or_add_rPr(), "F0F3FA")
    bt = estilo(doc, "Block Text")
    if bt:
        fuente(bt, "Calibri", 10, color="5C4510")
        ppr = bt.element.get_or_add_pPr()
        sombrear(ppr, "FFF7E6")
        borde(ppr, "left", "F0B04B", sz=24, space=6)
        bt.paragraph_format.left_indent = Cm(0.3)

    # ---- portada y pie de documento (estilos creados por Pandoc a partir de los `custom-style`)
    def p(nombre, tam, color, negrita=False, antes=0, despues=0, interlineado=1.0):
        s = estilo(doc, nombre)
        if s:
            fuente(s, "Calibri", tam, negrita, color)
            pf = s.paragraph_format
            pf.space_before, pf.space_after, pf.line_spacing = Pt(antes), Pt(despues), interlineado
        return s

    p("PortadaMarca", 30, AZUL, True, 0, 0)
    p("PortadaSub", 12, GRIS, False, 0, 0)
    ev = p("PortadaEv", 10, AZUL, True, 100, 6)
    if ev:
        sombrear(ev.element.get_or_add_pPr(), "E8EEFC")
    p("PortadaTitulo", 27, AZUL, True, 6, 10)
    d = p("PortadaDesc", 11.5, "33405A", False, 0, 22, 1.15)
    if d:
        d.paragraph_format.right_indent = Cm(1.5)
    p("PortadaAut", 9, GRIS, True, 150, 2)
    p("PortadaNombres", 12, "1B2333", True, 0, 6)
    ln = p("PortadaLinea", 9, GRIS, False, 8, 0)
    if ln:
        borde(ln.element.get_or_add_pPr(), "top", "2457D6", sz=12, space=6)
    pd = p("PieDoc", 8.5, GRIS, False, 14, 0)
    if pd:
        borde(pd.element.get_or_add_pPr(), "top", "DBE3F5", sz=4, space=4)


# ---------------------------------------------------------------- tablas
def formatear_meta(tabla):
    """Tabla de datos de la portada: sin encabezado, dos columnas, solo líneas finas horizontales."""
    tabla._tbl.remove(tabla.rows[0]._tr)  # fila de encabezado ficticia (__META__)
    tbl = tabla._tbl
    pr = tbl.tblPr
    insertar(pr, _el("w:tblW", w_w=int(15 / 2.54 * 1440), w_type="dxa"), TBLPR)
    b = _el("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideV"):
        b.append(_el(f"w:{lado}", w_val="nil"))
    b.append(_el("w:insideH", w_val="single", w_sz=4, w_space=0, w_color="DBE3F5"))
    insertar(pr, b, TBLPR)
    insertar(pr, _el("w:tblLayout", w_type="fixed"), TBLPR)
    anchos = [int(5.2 / 2.54 * 1440), int(9.8 / 2.54 * 1440)]
    for gc, w in zip(tbl.tblGrid.findall(qn("w:gridCol")), anchos):
        gc.set(qn("w:w"), str(w))
    for fila in tabla.rows:
        for j, celda in enumerate(fila.cells):
            celda.width = Cm(anchos[j] / 1440 * 2.54)
            for par in celda.paragraphs:
                par.paragraph_format.space_after = Pt(0)
                for run in par.runs:
                    run.font.size = Pt(10.5)
                    run.font.bold = j == 1
                    run.font.color.rgb = RGBColor.from_string(GRIS if j == 0 else "1B2333")


def formatear_tabla(tabla):
    if tabla.rows and tabla.rows[0].cells[0].text.strip() == "__META__":
        return formatear_meta(tabla)
    tbl = tabla._tbl
    pr = tbl.tblPr
    insertar(pr, _el("w:tblW", w_w=5000, w_type="pct"), TBLPR)
    b = _el("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b.append(_el(f"w:{lado}", w_val="single", w_sz=4, w_space=0, w_color="C9D4EF"))
    insertar(pr, b, TBLPR)
    insertar(pr, _el("w:tblLayout", w_type="fixed"), TBLPR)
    m = _el("w:tblCellMar")
    for lado, v in (("top", 40), ("left", 80), ("bottom", 40), ("right", 80)):
        m.append(_el(f"w:{lado}", w_w=v, w_type="dxa"))
    insertar(pr, m, TBLPR)

    filas = tabla.rows
    ncols = len(filas[0].cells)
    tam = 8.5 if ncols >= 5 else 9

    # anchos proporcionales al contenido (Pandoc los reparte por igual)
    pesos = []
    for j in range(ncols):
        largos = [len(fila.cells[j].text.strip()) for fila in filas if j < len(fila.cells)]
        medio = statistics.mean(largos) if largos else 8
        palabra = max((len(w) for fila in filas for w in fila.cells[j].text.split()), default=4)
        pesos.append(max(8, min(70, medio), min(palabra, 22) * 1.1))
    total_dxa = int(ANCHO_TEXTO_CM / 2.54 * 1440)
    minimo = int(1.5 / 2.54 * 1440)
    # mínimo por columna: que la palabra más larga del encabezado (en negrita) no se parta
    minimos = []
    for j in range(ncols):
        w_enc = max((len(x) for x in filas[0].cells[j].text.split()), default=4)  # el encabezado va en negrita
        w_cuerpo = max((min(len(x), 16) for fila in filas[1:] for x in fila.cells[j].text.split()), default=4)  # nombres largos pueden partirse
        minimos.append(max(minimo, int((0.17 * w_enc + 0.45) / 2.54 * 1440), int((0.15 * w_cuerpo + 0.45) / 2.54 * 1440)))
    ancho = [max(minimos[j], int(total_dxa * p / sum(pesos))) for j, p in enumerate(pesos)]
    if sum(ancho) > total_dxa:  # muchas columnas: los mínimos no caben, se reducen todos en proporción
        factor = total_dxa / sum(ancho)
        ancho = [max(int(0.9 / 2.54 * 1440), int(a * factor)) for a in ancho]
    exceso = sum(ancho) - total_dxa
    ancho[ancho.index(max(ancho))] -= exceso  # el total debe coincidir con el ancho del texto

    grid = tbl.tblGrid
    for gc, w in zip(grid.findall(qn("w:gridCol")), ancho):
        gc.set(qn("w:w"), str(w))
    for i, fila in enumerate(filas):
        trpr = fila._tr.get_or_add_trPr()
        trpr.append(_el("w:cantSplit"))
        if i == 0:
            trpr.append(_el("w:tblHeader"))
        for j, celda in enumerate(fila.cells):
            if j < len(ancho):
                celda.width = Cm(ancho[j] / 1440 * 2.54)
            if i == 0:
                sombrear(celda._tc.get_or_add_tcPr(), "E8EEFC")
            for par in celda.paragraphs:
                if i == 0:
                    par.paragraph_format.keep_with_next = True  # el encabezado no queda solo al final de una página
                par.paragraph_format.space_after = Pt(0)
                par.paragraph_format.space_before = Pt(0)
                par.paragraph_format.line_spacing = 1.05
                for run in par.runs:
                    run.font.size = Pt(tam)
                    if i == 0:
                        run.font.bold = True
                        run.font.color.rgb = RGBColor.from_string(AZUL)


# ---------------------------------------------------------------- pie de página
def campo(parrafo, instruccion, tam):
    """Campo complejo (PAGE/NUMPAGES): cada parte lleva su propio formato, que Word respeta al actualizarlo."""

    def corrida():
        r = _el("w:r")
        rpr = _el("w:rPr")
        rpr.append(_el("w:color", w_val=GRIS))
        rpr.append(_el("w:sz", w_val=int(tam * 2)))
        rpr.append(_el("w:szCs", w_val=int(tam * 2)))
        r.append(rpr)
        return r

    partes = []
    r = corrida(); r.append(_el("w:fldChar", w_fldCharType="begin")); partes.append(r)
    r = corrida(); it = _el("w:instrText"); it.set("{http://www.w3.org/XML/1998/namespace}space", "preserve"); it.text = f" {instruccion} "; r.append(it); partes.append(r)
    r = corrida(); r.append(_el("w:fldChar", w_fldCharType="separate")); partes.append(r)
    r = corrida(); t = _el("w:t"); t.text = "1"; r.append(t); partes.append(r)
    r = corrida(); r.append(_el("w:fldChar", w_fldCharType="end")); partes.append(r)
    for p in partes:
        parrafo._p.append(p)


def pie_y_cabecera(doc, titulo):
    sec = doc.sections[0]
    p = sec.header.paragraphs[0]
    p.text = ""
    r = p.add_run("SALES-X · Integración de Aplicaciones")
    r.font.size, r.font.color.rgb = Pt(8), RGBColor.from_string(GRIS)
    pf = sec.footer.paragraphs[0]
    pf.text = ""
    r = pf.add_run(f"{titulo[:80]}   ·   Página ")
    r.font.size, r.font.color.rgb = Pt(8), RGBColor.from_string(GRIS)
    campo(pf, "PAGE", 8)
    r = pf.add_run(" de ")
    r.font.size, r.font.color.rgb = Pt(8), RGBColor.from_string(GRIS)
    campo(pf, "NUMPAGES", 8)


# ---------------------------------------------------------------- conversión
def bloque(estilo_nombre, texto):
    return f'::: {{custom-style="{estilo_nombre}"}}\n{texto}\n:::\n\n'


SALTO_PAGINA = '```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```\n\n'


def portada_md(meta, md: Path) -> str:
    if meta.get("evidencia"):  # portada de evidencia (como los ejemplos FINAN-X)
        tabla = "| __META__ | |\n|---|---|\n" + "".join(f"| {a.replace('|', '/')} | {v.replace('|', '/')} |\n" for a, v in C.filas_meta(meta)) + "\n"
        return (
            bloque("PortadaMarca", C.SISTEMA.replace("-", "·"))
            + bloque("PortadaSub", C.DESCRIPCION_SISTEMA)
            + bloque("PortadaEv", f"Evidencia {meta['evidencia']}")
            + bloque("PortadaTitulo", meta.get("titulo", md.stem))
            + bloque("PortadaDesc", meta.get("descripcion", ""))
            + tabla
            + bloque("PortadaAut", "AUTORES")
            + bloque("PortadaNombres", C.autores())
            + bloque("PortadaLinea", C.linea_proyecto())
            + SALTO_PAGINA
        )
    codigo = meta.get("codigo", "SALES-X")
    return bloque("Codigo", f"{codigo} · SALES-X · Integración de Aplicaciones")


def convertir(md: Path):
    meta, cuerpo = C.separar_front_matter(md.read_text(encoding="utf-8"))
    cuerpo = C.expandir(cuerpo)
    pie = bloque("PieDoc", meta["pie"]) if meta.get("pie") else ""
    salida = SALIDA / f"{md.stem}.docx"
    pypandoc.convert_text(portada_md(meta, md) + cuerpo + "\n\n" + pie, "docx", format=FORMATO, outputfile=str(salida), extra_args=["--resource-path", str(md.parent), "--columns=200"])

    doc = Document(str(salida))
    preparar_estilos(doc)
    for tabla in doc.tables:
        formatear_tabla(tabla)
    for forma in doc.inline_shapes:
        max_w = Cm(ANCHO_TEXTO_CM)
        if forma.width > max_w:
            forma.height = int(forma.height * max_w / forma.width)
            forma.width = max_w
    titulo = meta.get("titulo") or next((p.text for p in doc.paragraphs if p.style.name == "Heading 1"), md.stem)
    pie_y_cabecera(doc, titulo)
    cp = doc.core_properties
    cp.title, cp.author, cp.subject, cp.language = titulo, "SALES-X", "Integración de Aplicaciones", "es-CO"
    doc.save(str(salida))
    return salida


def main():
    SALIDA.mkdir(exist_ok=True)
    fuentes = sorted((DOCS / "fuentes").glob("*.md")) + sorted(DOCS.glob("*.md"))
    for md in fuentes:
        out = convertir(md)
        print(f"OK  {out.name}  ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
