#!/usr/bin/env python3
"""_docx.py — Leitor de DOCX completo, com a formatacao efetiva de cada trecho.

Le todas as partes do arquivo Word que podem carregar texto e devolve, por ZONA (corpo,
cabecalho, rodape, nota de rodape, comentario, caixa de texto, propriedades do arquivo, dados
anexos, texto alternativo de imagem), o texto corrido e as faixas de cada trecho com a sua
formatacao efetiva — cor, tamanho, marca de oculto, realce, sombreamento e cor de fundo —
resolvida na ordem de heranca do Word: padrao do documento -> estilo de paragrafo -> estilo de
caractere -> formatacao direta.

Stdlib pura (zipfile + xml.etree). Sem rede. Nunca modifica o arquivo.
"""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"

LIMIAR_BRANCO = 242       # cada componente RGB >= 242 (0.95)
LIMIAR_FONTE_MIN_PT = 4.0
DIST_COR_FUNDO = 40       # soma das diferencas RGB abaixo disso = "mesma cor do fundo"

_REALCE = {
    "white": "FFFFFF", "black": "000000", "yellow": "FFFF00", "green": "00FF00", "cyan": "00FFFF",
    "magenta": "FF00FF", "blue": "0000FF", "red": "FF0000", "darkBlue": "000080", "darkCyan": "008080",
    "darkGreen": "008000", "darkMagenta": "800080", "darkRed": "800000", "darkYellow": "808000",
    "darkGray": "808080", "lightGray": "C0C0C0",
}
_TEMA_CLARO = {"background1", "bg1", "light1", "lt1"}
_TEMA_ESCURO = {"text1", "tx1", "dark1", "dk1"}


@dataclass
class Props:
    cor: str | None = None          # "RRGGBB"
    tamanho_pt: float | None = None
    oculto: bool = False
    realce: str | None = None       # "RRGGBB"
    sombra: str | None = None       # "RRGGBB"

    def aplicar(self, rpr: ET.Element | None) -> "Props":
        if rpr is None:
            return self
        p = Props(self.cor, self.tamanho_pt, self.oculto, self.realce, self.sombra)
        c = rpr.find(W + "color")
        if c is not None:
            tema = c.get(W + "themeColor")
            val = (c.get(W + "val") or "").upper()
            if tema in _TEMA_CLARO:
                p.cor = "FFFFFF"
            elif tema in _TEMA_ESCURO:
                p.cor = "000000"
            elif re.fullmatch(r"[0-9A-F]{6}", val):
                p.cor = val
            elif val == "AUTO":
                p.cor = None
        s = rpr.find(W + "sz")
        if s is not None and (s.get(W + "val") or "").isdigit():
            p.tamanho_pt = int(s.get(W + "val")) / 2.0
        for tag in ("vanish", "specVanish", "webHidden"):
            v = rpr.find(W + tag)
            if v is not None:
                p.oculto = (v.get(W + "val") or "true").lower() not in ("0", "false", "off")
        h = rpr.find(W + "highlight")
        if h is not None:
            p.realce = _REALCE.get(h.get(W + "val") or "", None)
        sh = rpr.find(W + "shd")
        if sh is not None and re.fullmatch(r"[0-9A-Fa-f]{6}", sh.get(W + "fill") or ""):
            p.sombra = (sh.get(W + "fill") or "").upper()
        return p


@dataclass
class Faixa:
    ini: int
    fim: int
    motivos: list[str] = field(default_factory=list)
    cor: str | None = None
    tamanho_pt: float | None = None


@dataclass
class Zona:
    nome: str
    texto: str = ""
    faixas: list[Faixa] = field(default_factory=list)
    nao_exibida: bool = False      # parte que nao sai no texto impresso (comentario, propriedades...)


def _rgb(h: str) -> tuple[int, int, int]:
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _distancia(a: str, b: str) -> int:
    return sum(abs(x - y) for x, y in zip(_rgb(a), _rgb(b)))


def _motivos(p: Props, fundo: str | None) -> list[str]:
    m: list[str] = []
    cor = p.cor or "000000"
    fundo_efetivo = p.sombra or p.realce or fundo or "FFFFFF"
    r, g, b = _rgb(cor)
    if r >= LIMIAR_BRANCO and g >= LIMIAR_BRANCO and b >= LIMIAR_BRANCO and _distancia(fundo_efetivo, "FFFFFF") < DIST_COR_FUNDO * 3:
        m.append("letra branca sobre fundo branco")
    elif _distancia(cor, fundo_efetivo) < DIST_COR_FUNDO:
        m.append("letra da mesma cor do fundo")
    if p.tamanho_pt is not None and p.tamanho_pt < LIMIAR_FONTE_MIN_PT:
        m.append(f"letra de tamanho {p.tamanho_pt:g} ponto(s)")
    if p.oculto:
        m.append("texto marcado como oculto no Word")
    return m


class _Estilos:
    def __init__(self, xml: bytes | None):
        self.padrao = Props()
        self.rpr: dict[str, ET.Element | None] = {}
        self.base: dict[str, str] = {}
        if not xml:
            return
        raiz = ET.fromstring(xml)
        d = raiz.find(f"{W}docDefaults/{W}rPrDefault/{W}rPr")
        self.padrao = Props().aplicar(d)
        for st in raiz.findall(W + "style"):
            sid = st.get(W + "styleId") or ""
            self.rpr[sid] = st.find(W + "rPr")
            b = st.find(W + "basedOn")
            if b is not None:
                self.base[sid] = b.get(W + "val") or ""

    def props(self, sid: str | None, base: Props) -> Props:
        cadeia: list[str] = []
        while sid and sid not in cadeia and len(cadeia) < 20:
            cadeia.append(sid)
            sid = self.base.get(sid)
        p = base
        for s in reversed(cadeia):
            p = p.aplicar(self.rpr.get(s))
        return p


def _nome_zona(parte: str) -> str:
    if parte == "word/document.xml":
        return "corpo"
    if re.match(r"word/header\d*\.xml$", parte):
        return "cabeçalho"
    if re.match(r"word/footer\d*\.xml$", parte):
        return "rodapé"
    if parte == "word/footnotes.xml":
        return "nota de rodapé"
    if parte == "word/endnotes.xml":
        return "nota de fim"
    if parte == "word/comments.xml":
        return "comentário"
    return parte


def _texto_de_run(r: ET.Element) -> str:
    partes = []
    for el in r:
        if el.tag == W + "t":
            partes.append(el.text or "")
        elif el.tag in (W + "tab", W + "ptab"):
            partes.append(" ")
        elif el.tag in (W + "br", W + "cr"):
            partes.append("\n")
        elif el.tag == W + "noBreakHyphen":
            partes.append("-")
    return "".join(partes)


def _percorrer_parte(raiz: ET.Element, nome: str, est: _Estilos, fundo_pagina: str | None,
                     zonas: dict[str, Zona], nao_exibida: bool = False) -> None:
    def zona(n: str) -> Zona:
        if n not in zonas:
            zonas[n] = Zona(n, nao_exibida=nao_exibida)
        return zonas[n]

    def visitar(el: ET.Element, nome_zona: str, fundo: str | None, estilo_par: Props) -> None:
        tag = el.tag
        if tag == W + "tc":
            tcpr = el.find(W + "tcPr")
            sh = tcpr.find(W + "shd") if tcpr is not None else None
            fill = (sh.get(W + "fill") if sh is not None else None) or ""
            if re.fullmatch(r"[0-9A-Fa-f]{6}", fill):
                fundo = fill.upper()
        if tag == W + "txbxContent":
            nome_zona = "caixa de texto" if nome_zona == "corpo" else f"caixa de texto ({nome_zona})"
        if tag == W + "p":
            ppr = el.find(W + "pPr")
            ps = ppr.find(W + "pStyle") if ppr is not None else None
            estilo_par = est.props(ps.get(W + "val") if ps is not None else None, est.padrao)
            z = zona(nome_zona)
            if z.texto and not z.texto.endswith("\n"):
                z.texto += "\n"
        if tag == W + "r":
            rpr = el.find(W + "rPr")
            rs = rpr.find(W + "rStyle") if rpr is not None else None
            p = est.props(rs.get(W + "val") if rs is not None else None, estilo_par).aplicar(rpr)
            t = _texto_de_run(el)
            if t:
                z = zona(nome_zona)
                ini = len(z.texto)
                z.texto += t
                z.faixas.append(Faixa(ini, len(z.texto), _motivos(p, fundo or fundo_pagina), p.cor, p.tamanho_pt))
        if tag == WP + "docPr":
            alt = " ".join(x for x in (el.get("title"), el.get("descr")) if x)
            if alt.strip():
                z = zona("texto alternativo de imagem")
                z.nao_exibida = True
                if z.texto:
                    z.texto += "\n"
                ini = len(z.texto)
                z.texto += alt
                z.faixas.append(Faixa(ini, len(z.texto), []))
        for filho in el:
            if filho.tag == W + "delText":
                continue
            visitar(filho, nome_zona, fundo, estilo_par)

    visitar(raiz, nome, None, est.padrao)


def _texto_xml_plano(xml: bytes) -> str:
    try:
        raiz = ET.fromstring(xml)
    except ET.ParseError:
        return ""
    return "\n".join(t.strip() for t in raiz.itertext() if t and t.strip())


def ler(path: str) -> list[Zona]:
    """Le o DOCX e devolve as zonas com texto. Levanta zipfile.BadZipFile se nao for DOCX."""
    zonas: dict[str, Zona] = {}
    with zipfile.ZipFile(path) as zf:
        nomes = zf.namelist()
        est = _Estilos(zf.read("word/styles.xml") if "word/styles.xml" in nomes else None)
        fundo_pagina = None
        if "word/document.xml" in nomes:
            doc = ET.fromstring(zf.read("word/document.xml"))
            bg = doc.find(W + "background")
            if bg is not None and re.fullmatch(r"[0-9A-Fa-f]{6}", bg.get(W + "color") or ""):
                fundo_pagina = (bg.get(W + "color") or "").upper()
        ordem = ["word/document.xml"] + sorted(n for n in nomes if re.match(r"word/(header|footer)\d*\.xml$", n)) + \
            [n for n in ("word/footnotes.xml", "word/endnotes.xml", "word/comments.xml") if n in nomes]
        for parte in ordem:
            if parte not in nomes:
                continue
            try:
                raiz = ET.fromstring(zf.read(parte))
            except ET.ParseError:
                continue
            _percorrer_parte(raiz, _nome_zona(parte), est, fundo_pagina, zonas,
                             nao_exibida=(parte == "word/comments.xml"))
        # propriedades do arquivo e dados anexos: texto puro, nunca exibido na peca
        props = [n for n in ("docProps/core.xml", "docProps/app.xml", "docProps/custom.xml") if n in nomes]
        txt = "\n".join(_texto_xml_plano(zf.read(n)) for n in props).strip()
        if txt:
            zonas["propriedades do arquivo"] = Zona("propriedades do arquivo", txt, [Faixa(0, len(txt))], True)
        anexos = [n for n in nomes if re.match(r"customXml/item\d*\.xml$", n)]
        txt = "\n".join(_texto_xml_plano(zf.read(n)) for n in anexos).strip()
        if txt:
            zonas["dados anexos ao arquivo"] = Zona("dados anexos ao arquivo", txt, [Faixa(0, len(txt))], True)
    return [z for z in zonas.values() if z.texto.strip()]


def eh_docx(path: str) -> bool:
    try:
        with zipfile.ZipFile(path) as zf:
            return "word/document.xml" in zf.namelist()
    except (zipfile.BadZipFile, OSError):
        return False


def blocos_ocultos(z: Zona) -> list[tuple[int, int, list[str], str]]:
    """Agrupa faixas ocultas vizinhas (so espaco entre elas) em blocos (ini, fim, motivos, texto)."""
    blocos: list[list] = []
    for f in z.faixas:
        if not f.motivos or not z.texto[f.ini:f.fim].strip():
            continue
        if blocos and not z.texto[blocos[-1][1]:f.ini].strip():
            blocos[-1][1] = f.fim
            for m in f.motivos:
                if m not in blocos[-1][2]:
                    blocos[-1][2].append(m)
        else:
            blocos.append([f.ini, f.fim, list(f.motivos)])
    return [(a, b, m, z.texto[a:b].strip()) for a, b, m in blocos]
