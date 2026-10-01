#!/usr/bin/env python3
"""unicode_scan.py — Varredura de caracteres Unicode suspeitos (auditor-pecas-processuais).

Stdlib pura — nao requer nenhuma dependencia externa. Detecta em texto de peca:

(a) ASCII SMUGGLING — caracteres do bloco Tags U+E0000..U+E007F (usados para
    esconder instrucoes legiveis so por maquina dentro de texto aparentemente normal);
(b) ZERO-WIDTH / INVISIVEIS — U+200B, U+200C, U+200D, U+2060, U+FEFF, U+00AD, U+180E;
(c) CONTROLES BIDIRECIONAIS — U+202A..U+202E e U+2066..U+2069 (podem reordenar o
    texto exibido em relacao ao texto real);
(d) HOMOGLIFOS — confusaveis cirilico/grego que imitam letras latinas; sinaliza
    PALAVRA que MISTURA scripts (latino + outro). Se a lib opcional
    `confusable_homoglyphs` estiver instalada, ela roda como motor adicional.

ENTRADA:
    - arquivo `.txt` / `.md`  (lido como UTF-8)
    - arquivo `.docx`         (texto extraido de word/document.xml via zipfile+regex)
    - arquivo `.pdf`          (texto extraido pagina a pagina via PyMuPDF; sem a lib -> missing_dependency)
    - texto por stdin         (passe `-` como caminho)

CONTRATO / USO:
    python3 scripts/unicode_scan.py <arquivo | -> [--json]

Cada achado traz: codepoint, nome Unicode, contexto (+-20 chars visiveis) e posicao.

PROIBICOES: sem rede; nunca modifica o arquivo; nunca inventa achado.
"""

from __future__ import annotations

import re
import sys
import unicodedata
import zipfile
from typing import Any

import _contrato as C

PARSER = "unicode_scan"

# (b) zero-width e invisiveis
INVISIVEIS = {
    0x200B: "ZERO WIDTH SPACE",
    0x200C: "ZERO WIDTH NON-JOINER",
    0x200D: "ZERO WIDTH JOINER",
    0x2060: "WORD JOINER",
    0xFEFF: "ZERO WIDTH NO-BREAK SPACE (BOM)",
    0x00AD: "SOFT HYPHEN",
    0x180E: "MONGOLIAN VOWEL SEPARATOR",
}

# (c) controles bidirecionais
BIDI = set(range(0x202A, 0x202F)) | set(range(0x2066, 0x206A))  # 202A..202E, 2066..2069

from _homoglifos import HOMOGLIFOS  # noqa: E402  (tabela compartilhada com _padroes)

_RE_WT = re.compile(r"<w:t[^>]*>(.*?)</w:t>", re.DOTALL)
_RE_PALAVRA = re.compile(r"\w+", re.UNICODE)


# ---------------------------------------------------------------------------
# Extracao de texto
# ---------------------------------------------------------------------------


def _texto_de_docx(path: str) -> str:
    """Extrai o texto de runs (<w:t>) de word/document.xml de um .docx."""
    with zipfile.ZipFile(path) as zf:
        try:
            xml = zf.read("word/document.xml").decode("utf-8", "replace")
        except KeyError:
            return ""
    partes = _RE_WT.findall(xml)
    return "".join(partes)


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
    # tenta como texto plano; se for binario, avisa formato
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read(), path
    except (UnicodeDecodeError, OSError):
        return C.envelope(
            PARSER, path, C.STATUS_FORMATO, "stdlib", [],
            extra={"erro": "Formato nao suportado: use .txt, .md, .docx ou passe texto por stdin com '-'."},
        )


# ---------------------------------------------------------------------------
# Deteccao
# ---------------------------------------------------------------------------


def _nome_unicode(ch: str) -> str:
    try:
        return unicodedata.name(ch)
    except ValueError:
        return "SEM NOME UNICODE"


def _contexto(texto: str, i: int, larg: int = 20) -> str:
    """Contexto +-`larg` chars, com invisiveis/controles escapados para leitura."""
    ini = max(0, i - larg)
    fim = min(len(texto), i + larg + 1)
    saida = []
    for j in range(ini, fim):
        ch = texto[j]
        cp = ord(ch)
        if cp in INVISIVEIS or cp in BIDI or (0xE0000 <= cp <= 0xE007F) or not ch.isprintable():
            marca = f"<U+{cp:04X}>"
            saida.append(f"[{marca}]" if j == i else marca)
        else:
            saida.append(ch)
    return "".join(saida)


def _scan_char_a_char(texto: str) -> list[dict[str, Any]]:
    achados: list[dict[str, Any]] = []
    for i, ch in enumerate(texto):
        cp = ord(ch)
        if 0xE0000 <= cp <= 0xE007F:
            achados.append(
                C.achado("tag_ascii_smuggling", "alta",
                         f"U+{cp:04X} {_nome_unicode(ch)} — bloco Tags (ASCII smuggling): «{_contexto(texto, i)}»",
                         f"offset {i}")
            )
        elif cp in INVISIVEIS:
            achados.append(
                C.achado("zero_width_ou_invisivel", "alta",
                         f"U+{cp:04X} {INVISIVEIS[cp]} — «{_contexto(texto, i)}»",
                         f"offset {i}")
            )
        elif cp in BIDI:
            achados.append(
                C.achado("bidi_control", "alta",
                         f"U+{cp:04X} {_nome_unicode(ch)} — controle bidirecional: «{_contexto(texto, i)}»",
                         f"offset {i}")
            )
    return achados


def _scan_homoglifos_embutido(texto: str) -> list[dict[str, Any]]:
    """Sinaliza PALAVRA que mistura latino + confusavel de outro script."""
    achados: list[dict[str, Any]] = []
    for m in _RE_PALAVRA.finditer(texto):
        palavra = m.group(0)
        tem_latino_ascii = any("a" <= c.lower() <= "z" for c in palavra)
        confusaveis = [(k, c) for k, c in enumerate(palavra) if ord(c) in HOMOGLIFOS]
        if tem_latino_ascii and confusaveis:
            for offset_local, c in confusaveis:
                cp = ord(c)
                latina, script = HOMOGLIFOS[cp]
                pos = m.start() + offset_local
                achados.append(
                    C.achado(
                        "homoglifo", "alta",
                        f"U+{cp:04X} {_nome_unicode(c)} ({script}) imita a latina '{latina}' "
                        f"na palavra que mistura scripts «{palavra}»",
                        f"offset {pos}",
                    )
                )
    return achados


def _scan_homoglifos_lib(texto: str) -> list[dict[str, Any]]:
    """Motor adicional OPCIONAL via confusable_homoglyphs (nunca obrigatorio)."""
    try:
        from confusable_homoglyphs import confusables  # type: ignore
    except ImportError:
        return None  # type: ignore[return-value]
    achados: list[dict[str, Any]] = []
    try:
        resultado = confusables.is_dangerous(texto)
    except Exception:
        return []
    if resultado:
        achados.append(
            C.achado("homoglifo_lib", "media",
                     "confusable_homoglyphs.is_dangerous() sinalizou mistura de scripts no texto",
                     "documento")
        )
    return achados


AVISO_PDF = (
    "Em PDF, caracteres invisiveis so aparecem se o arquivo os guardar no texto; o Word costuma "
    "descarta-los ao gerar o PDF. Letras de outro alfabeto sao preservadas."
)


def analisar_pdf(path: str) -> dict[str, Any]:
    """Extrai o texto do PDF pagina a pagina e roda a mesma varredura de texto."""
    try:
        import fitz  # type: ignore  # PyMuPDF
    except ImportError:
        return C.envelope(
            PARSER, path, C.STATUS_DEP, "n/a", [],
            dependency_hint="pip install pymupdf",
            extra={"aviso": "Varredura de caracteres em PDF nao executada: PyMuPDF ausente."},
        )
    achados: list[dict[str, Any]] = []
    doc = fitz.open(path)
    try:
        for pno in range(doc.page_count):
            texto = doc[pno].get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
            for a in _scan_char_a_char(texto) + _scan_homoglifos_embutido(texto):
                a["localizacao"] = f"pagina {pno + 1}, {a['localizacao']}"
                achados.append(a)
    finally:
        doc.close()
    return C.envelope(PARSER, path, C.STATUS_OK, "PyMuPDF", achados,
                      extra={"origem_texto": "pdf:texto extraido", "aviso": AVISO_PDF})


def analisar_docx(path: str) -> dict[str, Any]:
    """Varre todas as partes do Word (corpo, cabecalho, rodape, notas, comentarios...)."""
    import _docx
    achados: list[dict[str, Any]] = []
    for z in _docx.ler(path):
        for a in _scan_char_a_char(z.texto) + _scan_homoglifos_embutido(z.texto):
            a["localizacao"] = f"{z.nome}, {a['localizacao']}"
            a["zona"] = z.nome
            achados.append(a)
    return C.envelope(PARSER, path, C.STATUS_OK, "stdlib", achados,
                      extra={"origem_texto": "docx:todas as partes"})


def analisar(path: str) -> dict[str, Any]:
    """Ponto de entrada unico (usado tambem pela avaliacao do corpus)."""
    import _docx
    with open(path, "rb") as fh:
        cab = fh.read(1024)
    if b"%PDF" in cab:
        return analisar_pdf(path)
    if cab.startswith(b"PK") and _docx.eh_docx(path):
        return analisar_docx(path)
    resultado = _ler_texto(path)
    if isinstance(resultado, dict):
        return resultado
    texto, origem = resultado
    return analisar_texto(texto, path, origem)


def analisar_texto(texto: str, path: str, origem: str) -> dict[str, Any]:
    achados = _scan_char_a_char(texto) + _scan_homoglifos_embutido(texto)

    motor = "stdlib"
    extra_lib = _scan_homoglifos_lib(texto)
    if extra_lib is not None:
        achados += extra_lib
        if extra_lib:
            motor = "stdlib+confusable_homoglyphs"

    return C.envelope(PARSER, path, C.STATUS_OK, motor, achados, extra={"origem_texto": origem})


def _main(argv: list[str]) -> int:
    posicionais, _flags = C.separar_argv(argv)
    if not posicionais:
        C.emitir(C.erro(PARSER, "", "USO: python3 unicode_scan.py <arquivo | -> [--json]"))
        return 0

    path = posicionais[0]
    if path != "-":
        msg = C.checar_arquivo(PARSER, path)
        if msg:
            C.emitir(C.erro(PARSER, path, msg))
            return 0

    if path != "-":
        try:
            return C.emitir(analisar(path))
        except Exception as exc:
            C.emitir(C.erro(PARSER, path, f"Falha ao ler o arquivo: {exc}"))
            return 0

    try:
        resultado = _ler_texto(path)
    except Exception as exc:
        C.emitir(C.erro(PARSER, path, f"Falha ao ler a entrada: {exc}"))
        return 0

    if isinstance(resultado, dict):  # ja e um envelope de erro/formato
        return C.emitir(resultado)

    texto, origem = resultado
    try:
        env = analisar_texto(texto, path, origem)
    except Exception as exc:
        C.emitir(C.erro(PARSER, path, f"Falha inesperada na varredura: {exc}"))
        return 0

    return C.emitir(env)


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
