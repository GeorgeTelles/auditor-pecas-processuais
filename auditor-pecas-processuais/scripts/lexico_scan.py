#!/usr/bin/env python3
"""lexico_scan.py — Varredura lexica de comando dirigido a IA no texto da peca (auditor-pecas-processuais).

Procura, no texto INTEIRO da peca (visivel ou nao), padroes PT/EN de comando a sistema
de IA: "IA, ignore...", "nao impugne os documentos", "ignore previous instructions" e
similares. Complementa `pdf_integridade.py` (que so ve texto OCULTO): um comando escrito
em fonte preta normal nao dispara nenhum parser de ocultacao, mas dispara este.

ENTRADA:
    - arquivo `.txt` / `.md`  (UTF-8)
    - arquivo `.docx`         (todas as partes: corpo, cabecalho, rodape, notas, comentarios,
                               caixas de texto, propriedades; trecho oculto pela formatacao)
    - arquivo `.pdf`          (paginas + anotacoes, campos de formulario, propriedades e marcadores;
                               PyMuPDF; sem a lib -> status missing_dependency, nunca finge)
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
import _docx as DX
import _padroes as P

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
    quando = "TRECHO OCULTO ou fora do texto impresso" if oculto else "texto visivel"
    grupo = P.grupo_de(tag)
    ev = (f"frase de comando a IA ({P.GRUPOS[grupo]}) presente ({quando}): «{trecho}» — "
          "padrao presente, nao comando confirmado")
    return C.achado(
        "comando_lexico",
        _gravidade(severidade, oculto),
        ev,
        localizacao,
        tag=tag,
        trecho=trecho,
        contexto=contexto,
        visivel=not oculto,
        grupo=grupo,
        grupo_nome=P.GRUPOS[grupo],
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


def _achados_de_docx(path: str) -> dict[str, Any]:
    """Todas as partes do Word, com zona e marca de trecho oculto por formatacao."""
    achados: list[dict[str, Any]] = []
    for z in DX.ler(path):
        vistos: set[tuple[str, int]] = set()
        for tag, sev, trecho, ini, fim, ctx in P.achados_lexicos(z.texto):
            if (tag, ini) in vistos:
                continue
            vistos.add((tag, ini))
            tocados = [f for f in z.faixas if f.ini < fim and f.fim > ini]
            oculto = z.nao_exibida or any(f.motivos for f in tocados)
            achados.append(_achado_lexico(tag, sev, trecho, ctx, z.nome, oculto, zona=z.nome))
    return C.envelope(PARSER, path, C.STATUS_OK, "stdlib", achados, extra={"origem_texto": "docx:todas as partes"})


def _ler_texto(path: str) -> tuple[str, str] | dict[str, Any]:
    """Retorna (texto, origem) ou um envelope de erro/formato ja pronto (dict)."""
    if path == "-":
        return sys.stdin.read(), "stdin"
    baixo = path.lower()
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
            try:  # inclui texto posicionado fora da area visivel da pagina
                info = page.get_text("dict", clip=fitz.INFINITE_RECT())
            except Exception:
                info = page.get_text("dict")
            for bloco in info.get("blocks", []):
                for linha in bloco.get("lines", []):
                    for span in linha.get("spans", []):
                        t = span.get("text") or ""
                        if not t:
                            continue
                        ini = len(texto)
                        texto += t
                        fora = not fitz.Rect(span.get("bbox") or (0, 0, 0, 0)).intersects(page.rect)
                        faixas.append((ini, len(texto), _span_oculto(span) or fora, list(span.get("bbox", []))))
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
            # anotacoes/comentarios e campos de formulario da pagina: fora do texto impresso
            extras: list[tuple[str, str]] = []
            try:
                for an in page.annots() or []:
                    info = an.info or {}
                    t = " ".join(x for x in (info.get("title"), info.get("subject"), info.get("content")) if x)
                    if t.strip():
                        extras.append(("anotação ou comentário", t))
            except Exception:
                pass
            try:
                for wd in page.widgets() or []:
                    t = " ".join(str(x) for x in (wd.field_name, wd.field_value, wd.field_label) if x)
                    if t.strip():
                        extras.append(("campo de formulário", t))
            except Exception:
                pass
            for zona_x, t in extras:
                for tag, sev, trecho, _i, _f, ctx in P.achados_lexicos(t):
                    achados.append(_achado_lexico(tag, sev, trecho, ctx, f"pagina {pno + 1}", True, zona=zona_x))
        # propriedades do arquivo e marcadores (indice lateral)
        meta = doc.metadata or {}
        textos_doc = [("propriedades do arquivo", " ".join(str(v) for v in meta.values() if v))]
        try:
            textos_doc.append(("marcadores do PDF", " ".join(str(item[1]) for item in doc.get_toc())))
        except Exception:
            pass
        for zona_x, t in textos_doc:
            for tag, sev, trecho, _i, _f, ctx in P.achados_lexicos(t):
                achados.append(_achado_lexico(tag, sev, trecho, ctx, "documento", True, zona=zona_x))
    finally:
        doc.close()
    return C.envelope(PARSER, path, C.STATUS_OK, "PyMuPDF", achados)


# ---------------------------------------------------------------------------
# Orquestracao
# ---------------------------------------------------------------------------


def analisar(path: str) -> dict[str, Any]:
    if path != "-":
        with open(path, "rb") as fh:
            cab = fh.read(1024)
        if b"%PDF" in cab:
            return _achados_de_pdf(path)
        if cab.startswith(b"PK"):
            if DX.eh_docx(path):
                return _achados_de_docx(path)
            return C.envelope(PARSER, path, C.STATUS_FORMATO, "stdlib", [],
                              extra={"erro": "Arquivo .docx invalido (nao e um zip OOXML)."})

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
