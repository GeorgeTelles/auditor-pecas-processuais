#!/usr/bin/env python3
"""pdf_integridade.py — Varredura de integridade estrutural de PDF (auditor-pecas-processuais).

Procura DOIS grupos de sinais numa peticao em PDF:

(a) TEXTO OCULTO — texto que existe no arquivo mas o leitor humano nao ve:
    - preenchimento branco / quase-branco (RGB todos >= 0.95, ou cinza >= 0.95);
    - tamanho de fonte < 4pt;
    - modo de renderizacao de texto invisivel (operador `3 Tr`).
    (O caso TRT-8: fonte branca com comando de prompt injection embutido na peca.)

(b) CONTEUDO ATIVO — chaves de acao/execucao no dicionario de objetos:
    /OpenAction, /AA, /JS, /JavaScript, /Launch, /EmbeddedFile.

(c) ZONA + WHITELIST DE RODAPE OFICIAL — nos motores com posicao por span (PyMuPDF,
    pdfplumber) cada achado de texto oculto traz `texto` (trecho literal), `zona`
    (rodape/cabecalho/corpo) e `whitelist`. Fonte < 4pt em rodape/cabecalho que traz marcador
    forte de documento oficial (PJe, ICP-Brasil, OAB...) e NAO casa padrao lexico de comando
    a IA sai `baixa` (era `media`) com `whitelist: true`. Nunca suprime o achado e nunca
    rebaixa fonte branca. Motores pikepdf/raw nao tem posicao por span: sem whitelist (declarado).

CADEIA DE MOTORES (degradacao graciosa, em ordem de preferencia):
    1. PyMuPDF (fitz)   — spans com cor/tamanho + contents por pagina
    2. pikepdf          — modelo de objetos + parse de content stream (pega comprimido)
    3. pdfplumber       — chars com atributos (cor/tamanho)
    4. raw (sem lib)    — regex sobre o arquivo descomprimido

O tier `raw` cobre APENAS streams NAO comprimidos e e DECLARADO como
`motor_usado: "raw"` com aviso. Se nenhum motor existe E o PDF esta comprimido
(`/FlateDecode`), a varredura de texto oculto nao pode rodar de forma confiavel:
o envelope sai com status `missing_dependency` e `dependency_hint` — NUNCA finge
ter varrido.

CONTRATO / USO:
    python3 scripts/pdf_integridade.py <arquivo.pdf> [--json]

PROIBICOES: sem rede; nunca modifica o arquivo; nunca inventa achado.

NOTA DE AMBIENTE: neste repositorio nenhum motor de PDF esta instalado, entao o
caminho exercitado pelo smoke-test e o tier `raw` (a isca e escrita com streams
NAO comprimidos justamente para isso). Os tiers de lib estao escritos contra as
APIs reais de cada biblioteca e assumem a responsabilidade dos PDFs de producao
(inclusive comprimidos) quando as libs forem instaladas via pip.
"""

from __future__ import annotations

import re
import sys
from typing import Any

import _contrato as C
import _padroes as P

PARSER = "pdf_integridade"

# Chaves de conteudo ativo procuradas no dicionario de objetos / no raw.
CHAVES_ATIVAS = ("/OpenAction", "/AA", "/JavaScript", "/JS", "/Launch", "/EmbeddedFile")

# Limiar de "branco / quase-branco": cada componente RGB (ou o cinza) >= 0.95.
LIMIAR_BRANCO = 0.95
# Limiar de fonte minuscula suspeita.
LIMIAR_FONTE_MIN = 4.0


# ---------------------------------------------------------------------------
# Normalizacao de cor (as libs devolvem cor em escalas diferentes)
# ---------------------------------------------------------------------------


def _componentes_para_01(cor: Any) -> list[float] | None:
    """Normaliza uma cor de fonte para lista de floats em [0,1].

    Aceita: float/int (cinza), tupla/lista RGB (0-1 ou 0-255) ou CMYK (len 4).
    Retorna None se nao for interpretavel.
    """
    if cor is None:
        return None
    if isinstance(cor, (int, float)):
        v = float(cor)
        v = v / 255.0 if v > 1.0 else v
        return [v, v, v]
    if isinstance(cor, (list, tuple)):
        try:
            nums = [float(x) for x in cor]
        except (TypeError, ValueError):
            return None
        if not nums:
            return None
        escala = 255.0 if any(n > 1.0 for n in nums) else 1.0
        nums = [n / escala for n in nums]
        if len(nums) == 1:
            return [nums[0]] * 3
        if len(nums) == 3:
            return nums
        if len(nums) == 4:
            # CMYK -> RGB simples: branco = tudo perto de 0
            c, m, y, k = nums
            r = (1 - c) * (1 - k)
            g = (1 - m) * (1 - k)
            b = (1 - y) * (1 - k)
            return [r, g, b]
    return None


def _e_branco(cor: Any) -> bool:
    comp = _componentes_para_01(cor)
    return comp is not None and all(c >= LIMIAR_BRANCO for c in comp)


# ---------------------------------------------------------------------------
# Tier RAW — regex sobre o arquivo descomprimido (sem nenhuma lib)
# ---------------------------------------------------------------------------

_RE_FILL_RGB = re.compile(r"(\d*\.?\d+)\s+(\d*\.?\d+)\s+(\d*\.?\d+)\s+rg\b")
_RE_FILL_GRAY = re.compile(r"(\d*\.?\d+)\s+g\b")
_RE_TR = re.compile(r"\b([0-7])\s+Tr\b")
_RE_TF = re.compile(r"/[A-Za-z0-9]+\s+(\d*\.?\d+)\s+Tf\b")
_RE_SHOW = re.compile(r"\b(?:Tj|TJ)\b")


def _ultimo(regex: re.Pattern[str], janela: str) -> re.Match[str] | None:
    ultimo = None
    for m in regex.finditer(janela):
        ultimo = m
    return ultimo


def _raw_texto_oculto(texto: str) -> list[dict[str, Any]]:
    """Varre operadores de texto e avalia o estado grafico que os governa.

    Para cada operador de exibicao (Tj/TJ), olha para tras (mesma janela) e pega
    o ultimo preenchimento de cor, modo de render e tamanho de fonte definidos.
    """
    achados: list[dict[str, Any]] = []
    vistos: set[tuple[str, str]] = set()

    for show in _RE_SHOW.finditer(texto):
        ini = max(0, show.start() - 400)
        janela = texto[ini:show.start()]

        m_rgb = _ultimo(_RE_FILL_RGB, janela)
        m_gray = _ultimo(_RE_FILL_GRAY, janela)
        m_tr = _ultimo(_RE_TR, janela)
        m_tf = _ultimo(_RE_TF, janela)

        loc = f"offset {show.start()}"

        # ultima cor de preenchimento definida (rgb vence gray se vier depois)
        cor_branca = False
        cor_desc = ""
        pos_rgb = m_rgb.start() if m_rgb else -1
        pos_gray = m_gray.start() if m_gray else -1
        if pos_rgb >= pos_gray and m_rgb:
            comp = [float(m_rgb.group(i)) for i in (1, 2, 3)]
            if all(c >= LIMIAR_BRANCO for c in comp):
                cor_branca = True
                cor_desc = f"rg={comp[0]},{comp[1]},{comp[2]}"
        elif m_gray:
            g = float(m_gray.group(1))
            if g >= LIMIAR_BRANCO:
                cor_branca = True
                cor_desc = f"g={g}"

        if cor_branca:
            ev = f"texto com preenchimento branco/quase-branco ({cor_desc}) antes de operador de exibicao"
            chave = ("texto_oculto", ev)
            if chave not in vistos:
                vistos.add(chave)
                achados.append(C.achado("texto_oculto", "alta", ev, loc))

        if m_tr and int(m_tr.group(1)) == 3:
            ev = "modo de renderizacao de texto invisivel (operador 3 Tr)"
            chave = ("texto_oculto", ev)
            if chave not in vistos:
                vistos.add(chave)
                achados.append(C.achado("texto_oculto", "alta", ev, loc))

        if m_tf:
            tam = float(m_tf.group(1))
            if tam < LIMIAR_FONTE_MIN:
                ev = f"fonte com tamanho {tam}pt (< {LIMIAR_FONTE_MIN}pt)"
                chave = ("texto_oculto", ev)
                if chave not in vistos:
                    vistos.add(chave)
                    achados.append(C.achado("texto_oculto", "media", ev, loc))

    return achados


def _raw_conteudo_ativo(dados: bytes) -> list[dict[str, Any]]:
    """Procura chaves de conteudo ativo em texto plano do arquivo."""
    achados: list[dict[str, Any]] = []
    for chave in CHAVES_ATIVAS:
        pos = dados.find(chave.encode("latin-1"))
        if pos >= 0:
            achados.append(
                C.achado(
                    "conteudo_ativo",
                    "alta",
                    f"chave de conteudo ativo presente: {chave}",
                    f"offset {pos}",
                )
            )
    return achados


def _tier_raw(path: str) -> dict[str, Any]:
    """Tier final sem lib. Sempre devolve um envelope (o chamador nao decide mais)."""
    with open(path, "rb") as fh:
        dados = fh.read()

    texto = dados.decode("latin-1", "ignore")
    achados = _raw_conteudo_ativo(dados) + _raw_texto_oculto(texto)

    comprimido = b"/FlateDecode" in dados or b"/Filter" in dados
    if comprimido:
        # streams comprimidos: o raw ve as chaves ativas do dicionario, mas NAO
        # consegue varrer texto oculto dentro do stream. Declara a limitacao.
        return C.envelope(
            PARSER,
            path,
            C.STATUS_DEP,
            "raw",
            achados,
            dependency_hint="pip install pymupdf  (ou: pip install pikepdf / pdfplumber)",
            extra={
                "aviso": (
                    "PDF com streams comprimidos (/FlateDecode) e nenhum motor de PDF "
                    "instalado: a varredura de TEXTO OCULTO nao rodou. As chaves de "
                    "conteudo ativo acima foram lidas do texto plano do arquivo. "
                    "Instale PyMuPDF/pikepdf/pdfplumber para varrer o conteudo dos streams."
                )
            },
        )

    return C.envelope(
        PARSER,
        path,
        C.STATUS_OK,
        "raw",
        achados,
        extra={"aviso": "motor 'raw': cobertura limitada a streams nao comprimidos; sem zona/whitelist de rodape PJe"},
    )


# ---------------------------------------------------------------------------
# Zona + whitelist de rodape oficial (PJe) — rebaixa, NUNCA suprime
# ---------------------------------------------------------------------------

_MAX_TEXTO = 240


def _achado_fonte_pequena(evidencia: str, localizacao: str, texto: str, zona: str) -> dict[str, Any]:
    """Achado de fonte < LIMIAR_FONTE_MIN com zona, texto e whitelist de rodape oficial.

    Rebaixa de `media` para `baixa` SO quando: o trecho esta em rodape/cabecalho, traz
    marcador forte de documento oficial (PJe, ICP-Brasil, OAB...) E nao casa nenhum
    padrao lexico de comando a IA. Se casar, sobe para `alta`. O achado continua na
    lista, com o texto como evidencia.
    """
    legitimo = zona in ("rodape", "cabecalho") and P.eh_marcador_legitimo(texto)
    if P.tem_padrao_lexico(texto):
        # fonte minuscula + padrao de comando a IA no mesmo trecho: nunca rebaixa, sobe
        return C.achado(
            "texto_oculto", "alta",
            evidencia + " — trecho tambem casa padrao lexico de comando a IA (ver lexico_scan)",
            localizacao, texto=texto[:_MAX_TEXTO], zona=zona, whitelist=False,
        )
    if legitimo:
        return C.achado(
            "texto_oculto", "baixa",
            evidencia + " — rodape/cabecalho oficial reconhecido (PJe/ICP/OAB): rebaixado, mantido com evidencia",
            localizacao, texto=texto[:_MAX_TEXTO], zona=zona, whitelist=True,
        )
    return C.achado(
        "texto_oculto", "media", evidencia, localizacao,
        texto=texto[:_MAX_TEXTO], zona=zona, whitelist=False,
    )


# ---------------------------------------------------------------------------
# Tier PyMuPDF (fitz)
# ---------------------------------------------------------------------------


def _tier_fitz(path: str) -> tuple[list[dict[str, Any]], str] | None:
    try:
        import fitz  # type: ignore  # PyMuPDF
    except ImportError:
        return None

    achados: list[dict[str, Any]] = []
    doc = fitz.open(path)
    try:
        # conteudo ativo: varre a definicao textual de cada objeto
        vistos: set[str] = set()
        for xref in range(1, doc.xref_length()):
            try:
                obj = doc.xref_object(xref, compressed=False)
            except Exception:
                continue
            for chave in CHAVES_ATIVAS:
                if chave in obj and chave not in vistos:
                    vistos.add(chave)
                    achados.append(
                        C.achado("conteudo_ativo", "alta",
                                 f"chave de conteudo ativo presente: {chave}",
                                 f"objeto xref {xref}")
                    )

        # texto oculto: spans (cor/tamanho) + contents por pagina (3 Tr)
        for pno in range(doc.page_count):
            page = doc[pno]
            altura = page.rect.height
            try:  # le tambem o que esta fora da area visivel da pagina
                info = page.get_text("dict", clip=fitz.INFINITE_RECT())
            except Exception:
                info = page.get_text("dict")
            for bloco in info.get("blocks", []):
                for linha in bloco.get("lines", []):
                    for span in linha.get("spans", []):
                        texto_span = (span.get("text") or "").strip()
                        zona = P.classificar_zona(span.get("bbox"), altura)
                        bb = span.get("bbox")
                        if texto_span and bb and not fitz.Rect(bb).intersects(page.rect):
                            achados.append(
                                C.achado("texto_oculto", "alta" if P.tem_padrao_lexico(texto_span) else "media",
                                         "texto posicionado fora da area visivel da pagina",
                                         f"pagina {pno + 1}", texto=texto_span[:_MAX_TEXTO],
                                         zona="fora da página", whitelist=False)
                            )
                            continue
                        cor_int = span.get("color", 0)
                        r = (cor_int >> 16) & 255
                        g = (cor_int >> 8) & 255
                        b = cor_int & 255
                        if r >= 242 and g >= 242 and b >= 242:
                            # fonte branca NUNCA e rebaixada pela whitelist
                            achados.append(
                                C.achado("texto_oculto", "alta",
                                         f"span com cor branca/quase-branca (rgb={r},{g},{b})",
                                         f"pagina {pno + 1}",
                                         texto=texto_span[:_MAX_TEXTO], zona=zona, whitelist=False)
                            )
                        tam = float(span.get("size", 12) or 12)
                        if tam < LIMIAR_FONTE_MIN:
                            achados.append(_achado_fonte_pequena(
                                f"span com fonte {tam}pt (< {LIMIAR_FONTE_MIN}pt)",
                                f"pagina {pno + 1}", texto_span, zona))
            try:
                raw = page.read_contents().decode("latin-1", "ignore")
                if _RE_TR.search(raw) and any(int(m.group(1)) == 3 for m in _RE_TR.finditer(raw)):
                    achados.append(
                        C.achado("texto_oculto", "alta",
                                 "modo de renderizacao de texto invisivel (3 Tr)",
                                 f"pagina {pno + 1}")
                    )
            except Exception:
                pass
        return achados, "PyMuPDF"
    finally:
        doc.close()


# ---------------------------------------------------------------------------
# Tier pikepdf (pega streams comprimidos)
# ---------------------------------------------------------------------------


def _tier_pikepdf(path: str) -> tuple[list[dict[str, Any]], str] | None:
    try:
        import pikepdf  # type: ignore
        from pikepdf import parse_content_stream  # type: ignore
    except ImportError:
        return None

    achados: list[dict[str, Any]] = []
    pdf = pikepdf.open(path)
    try:
        vistos: set[str] = set()
        for obj in pdf.objects:
            try:
                if isinstance(obj, pikepdf.Dictionary):
                    chaves = set(obj.keys())
                    for chave in CHAVES_ATIVAS:
                        if chave in chaves and chave not in vistos:
                            vistos.add(chave)
                            achados.append(
                                C.achado("conteudo_ativo", "alta",
                                         f"chave de conteudo ativo presente: {chave}",
                                         "dicionario de objeto")
                            )
            except Exception:
                continue

        for pno, page in enumerate(pdf.pages):
            fill = None
            gray = None
            tr = 0
            size = None
            try:
                instrucoes = parse_content_stream(page)
            except Exception:
                continue
            for operandos, operador in instrucoes:
                op = str(operador)
                try:
                    if op == "rg":
                        fill = [float(o) for o in operandos]
                    elif op == "g":
                        gray = float(operandos[0])
                    elif op == "Tr":
                        tr = int(operandos[0])
                    elif op == "Tf":
                        size = float(operandos[1])
                    elif op in ("Tj", "TJ", "'", '"'):
                        if fill and all(c >= LIMIAR_BRANCO for c in fill):
                            achados.append(
                                C.achado("texto_oculto", "alta",
                                         f"texto com preenchimento branco (rg={fill})",
                                         f"pagina {pno + 1}")
                            )
                        elif gray is not None and gray >= LIMIAR_BRANCO:
                            achados.append(
                                C.achado("texto_oculto", "alta",
                                         f"texto com preenchimento cinza claro (g={gray})",
                                         f"pagina {pno + 1}")
                            )
                        if tr == 3:
                            achados.append(
                                C.achado("texto_oculto", "alta",
                                         "modo de renderizacao de texto invisivel (3 Tr)",
                                         f"pagina {pno + 1}")
                            )
                        if size is not None and size < LIMIAR_FONTE_MIN:
                            achados.append(
                                C.achado("texto_oculto", "media",
                                         f"texto com fonte {size}pt (< {LIMIAR_FONTE_MIN}pt)",
                                         f"pagina {pno + 1}")
                            )
                except Exception:
                    continue
        return achados, "pikepdf"
    finally:
        pdf.close()


# ---------------------------------------------------------------------------
# Tier pdfplumber (chars com atributos; conteudo ativo por raw byte scan)
# ---------------------------------------------------------------------------


def _tier_pdfplumber(path: str) -> tuple[list[dict[str, Any]], str] | None:
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        return None

    achados: list[dict[str, Any]] = []
    with open(path, "rb") as fh:
        achados += _raw_conteudo_ativo(fh.read())

    with pdfplumber.open(path) as pdf:
        for pno, page in enumerate(pdf.pages):
            altura = float(page.height or 0)
            try:
                palavras = page.extract_words(extra_attrs=["size", "non_stroking_color"])
            except Exception:
                palavras = []
            brancas = [w for w in palavras if _e_branco(w.get("non_stroking_color"))]
            pequenas = []
            for w in palavras:
                try:
                    if float(w.get("size", 12)) < LIMIAR_FONTE_MIN:
                        pequenas.append(w)
                except (TypeError, ValueError):
                    pass

            def _bbox(ws: list[dict[str, Any]]) -> list[float]:
                return [0.0, min(float(w["top"]) for w in ws), 0.0, max(float(w["bottom"]) for w in ws)]

            if brancas:
                txt = " ".join(str(w.get("text", "")) for w in brancas)
                achados.append(
                    C.achado("texto_oculto", "alta",
                             "caractere(s) com cor branca/quase-branca na pagina",
                             f"pagina {pno + 1}",
                             texto=txt[:_MAX_TEXTO], zona=P.classificar_zona(_bbox(brancas), altura),
                             whitelist=False)
                )
            if pequenas:
                txt = " ".join(str(w.get("text", "")) for w in pequenas)
                achados.append(_achado_fonte_pequena(
                    f"caractere(s) com fonte < {LIMIAR_FONTE_MIN}pt na pagina",
                    f"pagina {pno + 1}", txt, P.classificar_zona(_bbox(pequenas), altura)))
    return achados, "pdfplumber"


# ---------------------------------------------------------------------------
# Orquestracao da cadeia
# ---------------------------------------------------------------------------


def analisar(path: str) -> dict[str, Any]:
    with open(path, "rb") as fh:
        cabecalho = fh.read(1024)
    if cabecalho.startswith(b"PK"):
        import _docx
        if _docx.eh_docx(path):  # Word: verificacao propria, com as mesmas regras de gravidade
            import docx_integridade
            return docx_integridade.analisar(path)
    if b"%PDF" not in cabecalho:
        return C.envelope(
            PARSER, path, C.STATUS_FORMATO, "n/a", [],
            extra={"erro": "Arquivo nao parece ser um PDF (assinatura %PDF ausente no cabecalho)."},
        )

    for tier in (_tier_fitz, _tier_pikepdf, _tier_pdfplumber):
        try:
            resultado = tier(path)
        except Exception as exc:  # lib presente mas falhou: cai pro proximo tier
            print(f"[{PARSER}] {tier.__name__} falhou: {exc}", file=sys.stderr)
            resultado = None
        if resultado is not None:
            achados, motor = resultado
            extra = None
            if motor == "pikepdf":
                extra = {"aviso": "motor 'pikepdf': sem bbox/texto por span — zona e whitelist de rodape PJe "
                                  "NAO foram aplicadas; achados de fonte pequena nao foram rebaixados."}
            return C.envelope(PARSER, path, C.STATUS_OK, motor, achados, extra=extra)

    # nenhuma lib disponivel -> tier raw (decide ok x missing_dependency sozinho)
    return _tier_raw(path)


def _main(argv: list[str]) -> int:
    posicionais, _flags = C.separar_argv(argv)
    if not posicionais:
        C.emitir(C.erro(PARSER, "", "USO: python3 pdf_integridade.py <arquivo.pdf> [--json]"))
        return 0

    path = posicionais[0]
    msg = C.checar_arquivo(PARSER, path)
    if msg:
        C.emitir(C.erro(PARSER, path, msg))
        return 0

    try:
        env = analisar(path)
    except Exception as exc:
        C.emitir(C.erro(PARSER, path, f"Falha inesperada ao analisar o PDF: {exc}"))
        return 0

    return C.emitir(env)


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
