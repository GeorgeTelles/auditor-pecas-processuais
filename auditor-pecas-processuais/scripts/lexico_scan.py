#!/usr/bin/env python3
"""lexico_scan.py — Varredura lexica de comando dirigido a IA no texto da peca (auditor-pecas-processuais).

Procura, no texto INTEIRO da peca (visivel ou nao), padroes PT/EN de comando a sistema
de IA: "IA, ignore...", "nao impugne os documentos", "ignore previous instructions" e
similares. Complementa `pdf_integridade.py` (que so ve texto OCULTO): um comando escrito
em fonte preta normal nao dispara nenhum parser de ocultacao, mas dispara este.

ENTRADA:
    - arquivo `.txt` / `.md`  (UTF-8)
    - arquivo `.docx`         (texto de word/document.xml, via zipfile)
    - arquivo `.pdf`          (PyMuPDF; sem a lib -> status missing_dependency, nunca finge)
    - texto por stdin         (passe `-` como caminho)

CONTRATO / USO:
    python3 scripts/lexico_scan.py <arquivo | -> [--json]

Cada achado (`tipo: comando_lexico`) traz: regra (`tag`), trecho casado, contexto, onde
esta (pagina/offset) e `visivel` (False = o trecho caiu em span branco ou < 4pt, o que
sobe a gravidade para `alta`). No PDF traz tambem `zona` (rodape/cabecalho/corpo).

GRAVIDADE: CRITICAL->alta · HIGH->media · demais->baixa · trecho oculto->alta.

LIMITES (declarados, nunca escondidos): so casa os padroes listados em `_padroes.py` —
parafrase nao e pega; achado e "padrao presente", NAO "comando confirmado"; a leitura da
intencao (comando a IA x citacao legitima) e do classificador-prompt-injection. Ausencia de
achado NAO significa peca limpa.

PROIBICOES: sem rede; nunca modifica o arquivo; nunca inventa achado.
"""

from __future__ import annotations

import sys
import zipfile
from typing import Any

import _contrato as C
import _padroes as P
from unicode_scan import _texto_de_docx

PARSER = "lexico_scan"

GRAVIDADE_POR_SEVERIDADE = {"CRITICAL": "alta", "HIGH": "media"}

# mesmos limiares do pdf_integridade (texto "oculto ao leitor humano")
LIMIAR_BRANCO_255 = 242  # 0.95 * 255
LIMIAR_FONTE_MIN = 4.0


def _gravidade(severidade: str, oculto: bool) -> str:
    if oculto:
        return "alta"
    return GRAVIDADE_POR_SEVERIDADE.get(severidade, "baixa")


def _achado_lexico(
    tag: str,
    severidade: str,
    trecho: str,
    contexto: str,
    localizacao: str,
    oculto: bool,
    **extra: Any,
) -> dict[str, Any]:
    quando = "TRECHO OCULTO (branco/fonte minuscula)" if oculto else "texto visivel"
    ev = f"padrao lexico «{tag}» presente ({quando}): «{trecho}» — padrao presente, nao comando confirmado"
    return C.achado(
        "comando_lexico",
        _gravidade(severidade, oculto),
        ev,
        localizacao,
        tag=tag,
        trecho=trecho,
        contexto=contexto,
        visivel=not oculto,
        **extra,
    )


# ---------------------------------------------------------------------------
# Texto corrido (txt/md/docx/stdin)
# ---------------------------------------------------------------------------


def _achados_de_texto(texto: str) -> list[dict[str, Any]]:
    achados = []
    vistos: set[tuple[str, int]] = set()
    for tag, sev, trecho, ini, _fim, ctx in P.achados_lexicos(texto):
        if (tag, ini) in vistos:
            continue
        vistos.add((tag, ini))
        achados.append(_achado_lexico(tag, sev, trecho, ctx, f"offset {ini}", oculto=False))
    return achados


def _ler_texto(path: str) -> tuple[str, str] | dict[str, Any]:
    """Retorna (texto, origem) ou um envelope de erro/formato ja pronto (dict)."""
    if path == "-":
        return sys.stdin.read(), "stdin"
    baixo = path.lower()
    if baixo.endswith(".docx"):
        try:
            return _texto_de_docx(path), "docx:word/document.xml"
        except zipfile.BadZipFile:
            return C.envelope(
                PARSER, path, C.STATUS_FORMATO, "stdlib", [],
                extra={"erro": "Arquivo .docx invalido (nao e um zip OOXML)."},
            )
    if baixo.endswith((".txt", ".md")):
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read(), path
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read(), path
    except (UnicodeDecodeError, OSError):
        return C.envelope(
            PARSER, path, C.STATUS_FORMATO, "stdlib", [],
            extra={"erro": "Formato nao suportado: use .pdf, .docx, .txt, .md ou passe texto por stdin com '-'."},
        )


# ---------------------------------------------------------------------------
# PDF (PyMuPDF): texto por pagina, com deteccao de trecho oculto e zona
# ---------------------------------------------------------------------------


def _span_oculto(span: dict[str, Any]) -> bool:
    cor = int(span.get("color", 0) or 0)
    r, g, b = (cor >> 16) & 255, (cor >> 8) & 255, cor & 255
    branco = r >= LIMIAR_BRANCO_255 and g >= LIMIAR_BRANCO_255 and b >= LIMIAR_BRANCO_255
    tam = float(span.get("size", 12) or 12)
    return branco or tam < LIMIAR_FONTE_MIN


def _achados_de_pdf(path: str) -> dict[str, Any]:
    try:
        import fitz  # type: ignore  # PyMuPDF
    except ImportError:
        return C.envelope(
            PARSER, path, C.STATUS_DEP, "n/a", [],
            dependency_hint="pip install pymupdf",
            extra={"aviso": "Varredura lexica de PDF nao executada: PyMuPDF ausente."},
        )

    achados: list[dict[str, Any]] = []
    doc = fitz.open(path)
    try:
        for pno in range(doc.page_count):
            page = doc[pno]
            altura = page.rect.height
            texto = ""
            faixas: list[tuple[int, int, bool, list[float]]] = []  # (ini, fim, oculto, bbox)
            for bloco in page.get_text("dict").get("blocks", []):
                for linha in bloco.get("lines", []):
                    for span in linha.get("spans", []):
                        t = span.get("text") or ""
                        if not t:
                            continue
                        ini = len(texto)
                        texto += t
                        faixas.append((ini, len(texto), _span_oculto(span), list(span.get("bbox", []))))
                        texto += " "
                texto += "\n"

            vistos: set[tuple[str, int]] = set()
            for tag, sev, trecho, ini, fim, ctx in P.achados_lexicos(texto):
                if (tag, ini) in vistos:
                    continue
                vistos.add((tag, ini))
                tocados = [f for f in faixas if f[0] < fim and f[1] > ini]
                oculto = any(f[2] for f in tocados)
                bbox = tocados[0][3] if tocados else []
                achados.append(
                    _achado_lexico(
                        tag, sev, trecho, ctx, f"pagina {pno + 1}", oculto,
                        zona=P.classificar_zona(bbox, altura),
                    )
                )
    finally:
        doc.close()
    return C.envelope(PARSER, path, C.STATUS_OK, "PyMuPDF", achados)


# ---------------------------------------------------------------------------
# Orquestracao
# ---------------------------------------------------------------------------


def analisar(path: str) -> dict[str, Any]:
    if path != "-":
        with open(path, "rb") as fh:
            if b"%PDF" in fh.read(1024):
                return _achados_de_pdf(path)

    resultado = _ler_texto(path)
    if isinstance(resultado, dict):
        return resultado
    texto, origem = resultado
    return C.envelope(
        PARSER, path, C.STATUS_OK, "stdlib", _achados_de_texto(texto), extra={"origem_texto": origem}
    )


def _main(argv: list[str]) -> int:
    posicionais, _flags = C.separar_argv(argv)
    if not posicionais:
        C.emitir(C.erro(PARSER, "", "USO: python3 lexico_scan.py <arquivo | -> [--json]"))
        return 0

    path = posicionais[0]
    if path != "-":
        msg = C.checar_arquivo(PARSER, path)
        if msg:
            C.emitir(C.erro(PARSER, path, msg))
            return 0

    try:
        env = analisar(path)
    except Exception as exc:
        C.emitir(C.erro(PARSER, path, f"Falha inesperada na varredura lexica: {exc}"))
        return 0
    return C.emitir(env)


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
