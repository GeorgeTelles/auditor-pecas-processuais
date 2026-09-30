#!/usr/bin/env python3
"""metadados.py — Extracao de metadados de peca (DOCX e PDF) para o auditor-pecas-processuais.

Reporta FATOS de metadados como achados INFORMATIVOS — a decisao de relevancia
(o autor real diverge do assinante? o comentario interno importa?) e do LLM/advogado.
O parser so reporta o que existe; nunca conclui fraude nem intencao.

DOCX (via stdlib zipfile):
    - docProps/core.xml : dc:creator, cp:lastModifiedBy, dcterms:created,
                          dcterms:modified, cp:revision;
    - docProps/app.xml  : Company, TotalTime;
    - presenca de word/comments.xml (comentarios internos!);
    - presenca de <w:ins>/<w:del> no document.xml (alteracoes de controle de
      revisao nao aceitas).

PDF:
    - dicionario Info + XMP via pikepdf ou PyMuPDF;
    - fallback (sem lib): raw scan por /Author, /Creator, /Producer, /CreationDate,
      /ModDate no texto plano.

CONTRATO / USO:
    python3 scripts/metadados.py <arquivo.docx | arquivo.pdf> [--json]

PROIBICOES: sem rede; nunca modifica o arquivo; nunca inventa achado.
"""

from __future__ import annotations

import re
import sys
import zipfile
from typing import Any

import _contrato as C

PARSER = "metadados"


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------


def _tag(xml: str, tag: str) -> str | None:
    """Extrai o conteudo textual da primeira ocorrencia de <ns:tag>...</ns:tag>."""
    m = re.search(rf"<[^>]*\b{re.escape(tag)}\b[^>]*>(.*?)</[^>]*\b{re.escape(tag)}\b[^>]*>",
                  xml, re.DOTALL)
    if m:
        return m.group(1).strip()
    # forma self-closing/atributo nao tem conteudo textual
    return None


def _analisar_docx(path: str) -> dict[str, Any]:
    achados: list[dict[str, Any]] = []
    with zipfile.ZipFile(path) as zf:
        nomes = set(zf.namelist())

        core = zf.read("docProps/core.xml").decode("utf-8", "replace") if "docProps/core.xml" in nomes else ""
        app = zf.read("docProps/app.xml").decode("utf-8", "replace") if "docProps/app.xml" in nomes else ""
        document = zf.read("word/document.xml").decode("utf-8", "replace") if "word/document.xml" in nomes else ""

        # --- core.xml ---
        creator = _tag(core, "dc:creator")
        if creator:
            achados.append(C.achado("autor", "media",
                                    f"dc:creator (autor original) = {creator}", "docProps/core.xml"))
        last_by = _tag(core, "cp:lastModifiedBy")
        if last_by:
            achados.append(C.achado("autor", "media",
                                    f"cp:lastModifiedBy (ultima edicao por) = {last_by}", "docProps/core.xml"))
        revisao = _tag(core, "cp:revision")
        if revisao:
            achados.append(C.achado("revisoes", "baixa",
                                    f"cp:revision (numero de revisoes salvas) = {revisao}", "docProps/core.xml"))
        criado = _tag(core, "dcterms:created")
        if criado:
            achados.append(C.achado("data", "baixa",
                                    f"dcterms:created = {criado}", "docProps/core.xml"))
        modificado = _tag(core, "dcterms:modified")
        if modificado:
            achados.append(C.achado("data", "baixa",
                                    f"dcterms:modified = {modificado}", "docProps/core.xml"))

        # --- app.xml ---
        company = _tag(app, "Company")
        if company:
            achados.append(C.achado("empresa", "baixa",
                                    f"Company = {company}", "docProps/app.xml"))
        total_time = _tag(app, "TotalTime")
        if total_time:
            achados.append(C.achado("tempo_edicao", "baixa",
                                    f"TotalTime (minutos de edicao) = {total_time}", "docProps/app.xml"))

        # --- comentarios internos ---
        if "word/comments.xml" in nomes:
            achados.append(C.achado("comentarios_internos", "media",
                                    "documento contem word/comments.xml (comentarios internos embutidos)",
                                    "word/comments.xml"))

        # --- controle de revisao nao aceito ---
        if re.search(r"<w:ins\b", document) or re.search(r"<w:del\b", document):
            achados.append(C.achado("alteracoes_nao_aceitas", "media",
                                    "document.xml contem <w:ins>/<w:del> (controle de revisao nao aceito)",
                                    "word/document.xml"))

    return C.envelope(PARSER, path, C.STATUS_OK, "stdlib-zipfile", achados)


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------


def _pdf_via_pikepdf(path: str) -> tuple[list[dict[str, Any]], str] | None:
    try:
        import pikepdf  # type: ignore
    except ImportError:
        return None
    achados: list[dict[str, Any]] = []
    pdf = pikepdf.open(path)
    try:
        info = pdf.docinfo
        for chave in ("/Author", "/Creator", "/Producer", "/CreationDate", "/ModDate", "/Title"):
            if chave in info:
                achados.append(C.achado("metadado_pdf", "baixa",
                                        f"{chave} = {str(info[chave])}", "dicionario Info"))
        try:
            with pdf.open_metadata() as meta:
                for k, v in dict(meta).items():
                    achados.append(C.achado("xmp", "baixa", f"{k} = {v}", "XMP"))
        except Exception:
            pass
        return achados, "pikepdf"
    finally:
        pdf.close()


def _pdf_via_fitz(path: str) -> tuple[list[dict[str, Any]], str] | None:
    try:
        import fitz  # type: ignore
    except ImportError:
        return None
    achados: list[dict[str, Any]] = []
    doc = fitz.open(path)
    try:
        for k, v in (doc.metadata or {}).items():
            if v:
                achados.append(C.achado("metadado_pdf", "baixa", f"{k} = {v}", "dicionario Info"))
        return achados, "PyMuPDF"
    finally:
        doc.close()


_RE_PDF_META = {
    "/Author": re.compile(rb"/Author\s*\(([^)]*)\)"),
    "/Creator": re.compile(rb"/Creator\s*\(([^)]*)\)"),
    "/Producer": re.compile(rb"/Producer\s*\(([^)]*)\)"),
    "/CreationDate": re.compile(rb"/CreationDate\s*\(([^)]*)\)"),
    "/ModDate": re.compile(rb"/ModDate\s*\(([^)]*)\)"),
    "/Title": re.compile(rb"/Title\s*\(([^)]*)\)"),
}


def _pdf_via_raw(path: str) -> tuple[list[dict[str, Any]], str]:
    with open(path, "rb") as fh:
        dados = fh.read()
    achados: list[dict[str, Any]] = []
    for chave, regex in _RE_PDF_META.items():
        m = regex.search(dados)
        if m:
            valor = m.group(1).decode("latin-1", "ignore").strip()
            achados.append(C.achado("metadado_pdf", "baixa",
                                    f"{chave} = {valor}", f"offset {m.start()}"))
    return achados, "raw"


def _analisar_pdf(path: str) -> dict[str, Any]:
    for tier in (_pdf_via_pikepdf, _pdf_via_fitz):
        try:
            resultado = tier(path)
        except Exception as exc:
            print(f"[{PARSER}] {tier.__name__} falhou: {exc}", file=sys.stderr)
            resultado = None
        if resultado is not None:
            achados, motor = resultado
            return C.envelope(PARSER, path, C.STATUS_OK, motor, achados)

    achados, motor = _pdf_via_raw(path)
    return C.envelope(
        PARSER, path, C.STATUS_OK, motor, achados,
        extra={"aviso": "motor 'raw': metadados lidos do texto plano; XMP em stream comprimido nao e coberto"},
    )


# ---------------------------------------------------------------------------
# Deteccao de formato + orquestracao
# ---------------------------------------------------------------------------


def analisar(path: str) -> dict[str, Any]:
    with open(path, "rb") as fh:
        cabecalho = fh.read(8)

    baixo = path.lower()
    if cabecalho[:4] == b"%PDF" or baixo.endswith(".pdf"):
        return _analisar_pdf(path)
    if cabecalho[:2] == b"PK" or baixo.endswith(".docx"):
        try:
            return _analisar_docx(path)
        except zipfile.BadZipFile:
            return C.envelope(PARSER, path, C.STATUS_FORMATO, "n/a", [],
                              extra={"erro": "Arquivo .docx invalido (nao e um zip OOXML)."})

    return C.envelope(PARSER, path, C.STATUS_FORMATO, "n/a", [],
                      extra={"erro": "Formato nao suportado para metadados: use .docx ou .pdf."})


def _main(argv: list[str]) -> int:
    posicionais, _flags = C.separar_argv(argv)
    if not posicionais:
        C.emitir(C.erro(PARSER, "", "USO: python3 metadados.py <arquivo.docx | arquivo.pdf> [--json]"))
        return 0

    path = posicionais[0]
    msg = C.checar_arquivo(PARSER, path)
    if msg:
        C.emitir(C.erro(PARSER, path, msg))
        return 0

    try:
        env = analisar(path)
    except Exception as exc:
        C.emitir(C.erro(PARSER, path, f"Falha inesperada ao ler metadados: {exc}"))
        return 0

    return C.emitir(env)


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
