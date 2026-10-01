#!/usr/bin/env python3
"""relatorio_html.py — Gera a versao HTML (com botao "Exportar PDF") de um relatorio em markdown.

Recebe o relatorio final escrito pelas skills (dossie de integridade ou relatorio pre-protocolo)
e produz um HTML autocontido: CSS e icones inline, nenhum recurso externo, abre offline. O botao
"Exportar PDF" chama a impressao do navegador, com folha de estilo A4 propria; o usuario escolhe
"Salvar como PDF" e o texto sai selecionavel, com os links clicaveis.

Tambem garante o credito do autor no proprio .md (acrescenta o rodape uma unica vez).

CONTRATO / USO:
    python3 scripts/relatorio_html.py <relatorio.md> [-o saida.html]

Saida no stdout: JSON com `status`, `arquivo_md`, `arquivo_html`, `credito_md_adicionado` e
`termos_tecnicos`. Com termo tecnico no relatorio, `status` sai `revisar` e o HTML NAO e gerado:
cada item traz o trecho e a troca sugerida. `--forcar` gera mesmo assim (so para teste).

SEGURANCA: o relatorio transcreve texto da peca analisada, que pode trazer HTML ou script
plantado. Todo conteudo e escapado antes de qualquer marcacao; link so aceita http(s) e mailto;
a pagina declara Content-Security-Policy sem recurso externo.

PROIBICOES: sem rede; nunca altera o conteudo do relatorio alem de acrescentar o rodape de credito.
"""

from __future__ import annotations

import datetime as _dt
import html
import json
import os
import re
import sys
from typing import Any

import _marca as M

# ---------------------------------------------------------------------------
# Inline
# ---------------------------------------------------------------------------

_SELOS = {
    "✅": "ok", "⚠️": "aviso", "⚠": "aviso", "🔴": "erro", "⬜": "neutro",
    "🚫": "erro", "📝": "aviso", "🎯": "erro", "❓": "aviso", "📄": "neutro",
}
_RE_SELO = re.compile("(" + "|".join(sorted(map(re.escape, _SELOS), key=len, reverse=True)) + ")")
_RE_CODE = re.compile(r"`([^`]+)`")
_RE_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_RE_BOLD = re.compile(r"\*\*(.+?)\*\*")
_RE_ITAL = re.compile(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])")
_RE_GRAV = re.compile(r"\b(gravidade\s+)(ALTA|M[ÉE]DIA|BAIXA|alta|m[ée]dia|baixa)\b")
_ESQUEMAS_OK = ("http://", "https://", "mailto:")
ICONE_LINK = (
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 14a4.5 4.5 0 0 0 6.4 0l3-3a4.5 4.5 0 0 0-6.4-6.4l-1 1" '
    'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M14 10a4.5 4.5 0 0 0-6.4 0l-3 3'
    'a4.5 4.5 0 0 0 6.4 6.4l1-1" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
)


def _grav_classe(palavra: str) -> str:
    p = palavra.lower().replace("é", "e")
    return {"alta": "alta", "media": "media", "baixa": "baixa"}.get(p, "")


def inline(texto: str) -> str:
    """Markdown inline -> HTML. Escapa TUDO primeiro; so depois aplica a marcacao."""
    guardados: list[str] = []

    def guardar(frag: str) -> str:
        guardados.append(frag)
        return f"\x00{len(guardados) - 1}\x00"

    s = html.escape(texto, quote=True)
    s = _RE_CODE.sub(lambda m: guardar(f"<code>{m.group(1)}</code>"), s)

    def _link(m: re.Match[str]) -> str:
        rotulo, url = m.group(1), m.group(2)
        url_crua = html.unescape(url).strip()
        if url_crua.lower().startswith(_ESQUEMAS_OK) and rotulo.strip() == "🔗":
            site = re.sub(r"^(https?://|mailto:)(www\.)?", "", url_crua, flags=re.I).split("/")[0]
            return guardar(
                f'<a class="link-fonte" href="{html.escape(url_crua, quote=True)}" rel="noopener noreferrer" '
                f'target="_blank" title="Abrir a fonte: {html.escape(site, quote=True)}" '
                f'aria-label="Abrir a fonte: {html.escape(site, quote=True)}">{ICONE_LINK}</a>'
            )
        if url_crua.lower().startswith(_ESQUEMAS_OK):
            return guardar(
                f'<a href="{html.escape(url_crua, quote=True)}" rel="noopener noreferrer" '
                f'target="_blank">{rotulo}</a>'
            )
        return rotulo  # esquema nao permitido (javascript:, data:...): fica so o texto

    s = _RE_LINK.sub(_link, s)
    s = _RE_BOLD.sub(r"<strong>\1</strong>", s)
    s = _RE_ITAL.sub(r"<em>\1</em>", s)
    s = _RE_GRAV.sub(
        lambda m: f'{m.group(1)}<span class="grav grav-{_grav_classe(m.group(2))}">{m.group(2)}</span>', s
    )
    s = _RE_SELO.sub(lambda m: f'<span class="selo selo-{_SELOS[m.group(1)]}">{m.group(1)}</span>', s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: guardados[int(m.group(1))], s)
    return s


def _celula(texto: str) -> str:
    t = texto.strip()
    classe = _grav_classe(re.sub(r"[*_`]", "", t))
    if classe:
        return f'<span class="grav grav-{classe}">{html.escape(re.sub(r"[*_`]", "", t))}</span>'
    return inline(t)


# ---------------------------------------------------------------------------
# Blocos
# ---------------------------------------------------------------------------

_RE_TITULO = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_RE_HR = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")
_RE_ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
_RE_FICHA = re.compile(r"^\*\*([^*]{1,40}?):\*\*\s*(.+)$")
_RE_SEP_TABELA = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def _linhas_tabela(linha: str) -> list[str]:
    s = linha.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c for c in re.split(r"(?<!\\)\|", s)]


def _tabela(linhas: list[str]) -> str:
    cab = _linhas_tabela(linhas[0])
    corpo = [_linhas_tabela(l) for l in linhas[2:]]
    th = "".join(f"<th>{inline(c.strip())}</th>" for c in cab)
    trs = []
    for linha in corpo:
        linha = (linha + [""] * len(cab))[: max(len(cab), len(linha))]
        trs.append("<tr>" + "".join(f"<td>{_celula(c)}</td>" for c in linha) + "</tr>")
    return f'<div class="tabela"><table><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>'


def _lista(linhas: list[str]) -> str:
    """Lista com aninhamento por indentacao."""
    itens: list[tuple[int, bool, str]] = []
    for l in linhas:
        m = _RE_ITEM.match(l)
        if m:
            itens.append((len(m.group(1).replace("\t", "    ")), m.group(2)[0].isdigit(), m.group(3)))
        elif itens:
            ind, ordenada, txt = itens[-1]
            itens[-1] = (ind, ordenada, txt + " " + l.strip())

    def montar(i: int, nivel: int) -> tuple[str, int]:
        ordenada = itens[i][1]
        tag = "ol" if ordenada else "ul"
        partes = [f"<{tag}>"]
        while i < len(itens) and itens[i][0] >= nivel:
            ind, _, txt = itens[i]
            if ind > nivel:
                sub, i = montar(i, ind)
                partes[-1] = partes[-1][: -len("</li>")] + sub + "</li>" if partes[-1].endswith("</li>") else partes[-1] + sub
                continue
            caixa = re.match(r"^\[( |x|X)\]\s+(.*)$", txt)
            if caixa:
                marcada = caixa.group(1).lower() == "x"
                txt_html = f'<span class="caixa{" marcada" if marcada else ""}">{"✔" if marcada else ""}</span>{inline(caixa.group(2))}'
            else:
                txt_html = inline(txt)
            partes.append(f"<li>{txt_html}</li>")
            i += 1
        partes.append(f"</{tag}>")
        return "".join(partes), i

    saida, _ = montar(0, itens[0][0]) if itens else ("", 0)
    return saida


def blocos(md: str) -> list[tuple[str, str, str]]:
    """Converte markdown em blocos (tipo, html, texto_cru)."""
    linhas = md.replace("\r\n", "\n").split("\n")
    out: list[tuple[str, str, str]] = []
    i = 0
    while i < len(linhas):
        l = linhas[i]
        if not l.strip() or l.strip() == M.MARCADOR_RODAPE:
            i += 1
            continue
        if l.strip().startswith("```"):
            j = i + 1
            while j < len(linhas) and not linhas[j].strip().startswith("```"):
                j += 1
            codigo = "\n".join(linhas[i + 1: j])
            out.append(("pre", f"<pre><code>{html.escape(codigo)}</code></pre>", codigo))
            i = j + 1
            continue
        m = _RE_TITULO.match(l)
        if m:
            nivel = len(m.group(1))
            out.append((f"h{nivel}", f"<h{nivel}>{inline(m.group(2))}</h{nivel}>", m.group(2)))
            i += 1
            continue
        if _RE_HR.match(l):
            out.append(("hr", "<hr>", ""))
            i += 1
            continue
        if "|" in l and i + 1 < len(linhas) and _RE_SEP_TABELA.match(linhas[i + 1]):
            j = i + 2
            while j < len(linhas) and linhas[j].strip() and "|" in linhas[j]:
                j += 1
            out.append(("table", _tabela(linhas[i:j]), ""))
            i = j
            continue
        if l.lstrip().startswith(">"):
            j = i
            dentro = []
            while j < len(linhas) and linhas[j].lstrip().startswith(">"):
                dentro.append(re.sub(r"^\s*>\s?", "", linhas[j]))
                j += 1
            interno = "".join(h for _, h, _ in blocos("\n".join(dentro))).replace('<p class="aviso">', "<p>")
            cru = " ".join(dentro)
            classe = "aviso" if ("⚠" in cru or "conferência humana" in cru.lower()) else "nota"
            out.append(("quote", f'<blockquote class="{classe}">{interno}</blockquote>', cru))
            i = j
            continue
        if _RE_ITEM.match(l):
            j = i
            while j < len(linhas) and linhas[j].strip() and (
                _RE_ITEM.match(linhas[j]) or linhas[j].startswith(("  ", "\t"))
            ):
                j += 1
            out.append(("list", _lista(linhas[i:j]), ""))
            i = j
            continue
        j = i
        par = []
        while j < len(linhas) and linhas[j].strip() and not (
            _RE_TITULO.match(linhas[j]) or _RE_HR.match(linhas[j]) or _RE_ITEM.match(linhas[j])
            or linhas[j].lstrip().startswith((">", "```"))
            or ("|" in linhas[j] and j + 1 < len(linhas) and _RE_SEP_TABELA.match(linhas[j + 1]))
        ):
            par.append(linhas[j].strip())
            j += 1
        cru = " ".join(par)
        ficha = [_RE_FICHA.match(p) for p in par]
        if len(par) >= 2 and all(ficha):
            itens = "".join(
                f"<div><dt>{inline(m.group(1))}</dt><dd>{inline(m.group(2))}</dd></div>" for m in ficha if m
            )
            out.append(("ficha", f'<dl class="ficha">{itens}</dl>', cru))
            i = j
            continue
        classe = ' class="aviso"' if ("conferência humana" in cru.lower() and ("aviso" in cru.lower() or "⚠" in cru)) else ""
        # linhas do mesmo paragrafo se juntam com espaco (markdown); quebra forcada so com
        # linha iniciada por **Rotulo:** (capa/metadados) — o resto flui como texto corrido
        partes_html = []
        for k, p in enumerate(par):
            sep = "<br>" if k and _RE_FICHA.match(p) else " "
            partes_html.append((sep if k else "") + inline(p))
        out.append(("p", f"<p{classe}>" + "".join(partes_html) + "</p>", cru))
        i = j
    return out


# ---------------------------------------------------------------------------
# Pagina
# ---------------------------------------------------------------------------

_RE_SECAO = re.compile(r"^\s*([A-D])\s*[.)—–-]\s*")

ICONES = {
    "email": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2.5" y="5" width="19" height="14" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M3.5 7l8.5 6 8.5-6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "linkedin": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2.5" y="2.5" width="19" height="19" rx="4" fill="currentColor"/><rect x="6.2" y="10" width="2.6" height="7.6" fill="#fff"/><circle cx="7.5" cy="7" r="1.6" fill="#fff"/><path d="M11 10h2.5v1.2c.5-.8 1.5-1.4 2.8-1.4 2 0 3 1.3 3 3.6v4.2h-2.6v-3.8c0-1.1-.4-1.8-1.4-1.8s-1.7.7-1.7 1.9v3.7H11z" fill="#fff"/></svg>',
    "whatsapp": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.8a9.1 9.1 0 0 0-7.8 13.8L3 21l4.5-1.2A9.1 9.1 0 1 0 12 2.8z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M8.6 7.6c.3-.3.7-.3.9 0l1.1 1.6c.2.3.1.7-.1.9l-.6.6c.6 1.3 1.6 2.3 2.9 2.9l.6-.6c.2-.2.6-.3.9-.1l1.6 1.1c.3.2.3.6 0 .9l-.8.8c-.6.6-1.6.7-2.4.3-2.1-1-3.9-2.8-4.9-4.9-.4-.8-.3-1.8.3-2.4z" fill="currentColor"/></svg>',
    "pdf": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 2.5h8l4.5 4.5v14.5H6z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M14 2.5V7h4.5M12 10.5v6m0 0l-2.5-2.5M12 16.5l2.5-2.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "escudo": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.5l8 3v6c0 5-3.4 8.6-8 10-4.6-1.4-8-5-8-10v-6z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M8.5 12l2.5 2.5 4.5-5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
}

CSS = r"""
:root{--tinta:#1c2433;--suave:#5b6577;--linha:#e3e6ec;--fundo:#f4f5f8;--papel:#fff;--marca:#1f3a5f;--marca2:#2c5282;--ouro:#b8893b;
--a:#b42318;--a-bg:#fdecea;--b:#1f5fa8;--b-bg:#e8f1fb;--c:#8a5a00;--c-bg:#fdf3e1;--d:#5b3fa6;--d-bg:#f0ecfa;
--ok:#1e7a46;--ok-bg:#e5f4ec;--av:#9a6200;--av-bg:#fdf1dc;--er:#b42318;--er-bg:#fdecea;--ne:#5b6577;--ne-bg:#eef0f4}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--fundo);color:var(--tinta);font:15px/1.6 "Segoe UI",system-ui,-apple-system,Roboto,"Helvetica Neue",Arial,sans-serif}
.barra{position:sticky;top:0;z-index:5;display:flex;justify-content:space-between;align-items:center;gap:12px;padding:10px 20px;background:rgba(255,255,255,.92);backdrop-filter:blur(6px);border-bottom:1px solid var(--linha)}
.barra .prod{display:flex;align-items:center;gap:8px;font-weight:600;color:var(--marca);font-size:14px}
.barra .prod svg{width:20px;height:20px}
.btn{display:inline-flex;align-items:center;gap:8px;border:0;border-radius:8px;padding:9px 16px;background:var(--marca);color:#fff;font:600 14px/1 inherit;cursor:pointer;box-shadow:0 1px 2px rgba(0,0,0,.12)}
.btn:hover{background:var(--marca2)}
.btn svg{width:18px;height:18px}
main{max-width:980px;margin:0 auto;padding:24px 16px 8px}
.hero{background:linear-gradient(135deg,var(--marca),#15263f);color:#fff;border-radius:14px;padding:28px 30px 24px;margin-bottom:18px;position:relative;overflow:hidden}
.hero:after{content:"";position:absolute;right:-60px;top:-60px;width:220px;height:220px;border-radius:50%;background:radial-gradient(circle at 35% 65%,rgba(232,190,96,.95),rgba(201,152,58,.85) 55%,rgba(166,120,38,.75));box-shadow:0 0 40px rgba(212,166,74,.45)}
.hero>*{position:relative;z-index:1}
.hero .rotulo{text-transform:uppercase;letter-spacing:.12em;font-size:11.5px;color:#e9d3a8;font-weight:600}
.hero h1{margin:6px 0 4px;font:600 26px/1.25 Georgia,"Times New Roman",serif}
.hero .gerado{font-size:12.5px;color:#c9d3e3}
.card{background:var(--papel);border:1px solid var(--linha);border-radius:12px;padding:20px 24px;margin:0 0 16px;box-shadow:0 1px 2px rgba(16,24,40,.04)}
.card>h2:first-child{margin-top:0}
.secao{border-left:5px solid var(--cor,var(--marca))}
.secao>h2{display:flex;align-items:center;gap:10px}
.letra{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:7px;background:var(--cor);color:#fff;font:700 15px/1 inherit;flex:none}
.secao-a{--cor:var(--a)}.secao-b{--cor:var(--b)}.secao-c{--cor:var(--c)}.secao-d{--cor:var(--d)}
h2{font:600 19px/1.3 Georgia,"Times New Roman",serif;color:var(--marca);margin:22px 0 10px}
h3{font-size:15.5px;margin:18px 0 8px;color:var(--tinta)}
h4{font-size:14.5px;margin:14px 0 6px;color:var(--suave)}
p{margin:8px 0}
a{color:var(--marca2)}
code{font:12.5px/1.4 Consolas,"SFMono-Regular",Menlo,monospace;background:#f1f3f7;border:1px solid var(--linha);border-radius:5px;padding:1px 5px;word-break:break-word}
pre{background:#0f172a;color:#e2e8f0;border-radius:10px;padding:14px 16px;overflow:auto}
pre code{background:none;border:0;color:inherit;padding:0}
hr{border:0;border-top:1px solid var(--linha);margin:18px 0}
ul,ol{padding-left:22px;margin:8px 0}
li{margin:3px 0}
blockquote{margin:12px 0;padding:10px 16px;border-radius:8px;background:#f7f8fb;border-left:4px solid var(--marca2);color:#2d3748}
blockquote p{margin:4px 0}
.aviso{background:var(--av-bg)!important;border-left:4px solid var(--ouro)!important;border-radius:8px;padding:12px 16px!important}
.tabela{overflow-x:auto;margin:10px 0;border:1px solid var(--linha);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th{background:#f1f3f7;text-align:left;font-weight:600;color:var(--marca);padding:9px 12px;border-bottom:1px solid var(--linha);white-space:nowrap}
td{padding:9px 12px;border-bottom:1px solid var(--linha);vertical-align:top}
tr:last-child td{border-bottom:0}
tbody tr:nth-child(even) td{background:#fafbfc}
.selo{display:inline-block;border-radius:6px;padding:0 4px;margin-right:2px;line-height:1.5}
.selo-ok{background:var(--ok-bg)}.selo-aviso{background:var(--av-bg)}.selo-erro{background:var(--er-bg)}.selo-neutro{background:var(--ne-bg)}
.grav{display:inline-block;border-radius:999px;padding:1px 10px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em}
.grav-alta{background:var(--er-bg);color:var(--er)}.grav-media{background:var(--av-bg);color:var(--av)}.grav-baixa{background:var(--ne-bg);color:var(--ne)}
.caixa{display:inline-flex;align-items:center;justify-content:center;width:16px;height:16px;border:1.5px solid var(--suave);border-radius:4px;margin-right:8px;font-size:11px;vertical-align:-2px}
.caixa.marcada{background:var(--ok);border-color:var(--ok);color:#fff}
.link-fonte{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:7px;background:#eef3fb;color:var(--marca2);border:1px solid #d6e2f3}
.link-fonte:hover{background:var(--marca2);color:#fff}
.link-fonte svg{width:16px;height:16px}
.achado{border:1px solid var(--linha);border-left:5px solid var(--ne);border-radius:10px;padding:14px 18px 10px;margin:14px 0;background:#fff}
.achado-alta{border-left-color:var(--er)}.achado-media{border-left-color:var(--ouro)}.achado-baixa{border-left-color:var(--ne)}
.achado>h3{margin:0 0 10px;font-size:15.5px;color:var(--marca)}
.campo{margin:8px 0}
.campo .rotulo{display:block;font-size:11.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--suave);font-weight:700;margin-bottom:2px}
.campo>div{margin:0}
blockquote.trecho{background:none;border:0;padding:0;margin:6px 0 10px}
blockquote.trecho p{background:#fff6d6;border-left:4px solid #e0a800;border-radius:6px;padding:8px 12px;margin:6px 0;font-family:Georgia,"Times New Roman",serif;font-style:italic;color:#3d2f00}
.ficha{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin:4px 0 12px}
.ficha div{background:#f7f8fb;border:1px solid var(--linha);border-radius:10px;padding:10px 14px}
.ficha dt{font-size:11.5px;text-transform:uppercase;letter-spacing:.08em;color:var(--suave);font-weight:600;margin-bottom:2px}
.ficha dd{margin:0;font-weight:600;color:var(--tinta)}
.credito{max-width:980px;margin:6px auto 30px;padding:0 16px}
.credito .caixa-cred{background:var(--papel);border:1px solid var(--linha);border-top:4px solid var(--ouro);border-radius:12px;padding:18px 24px;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:14px}
.credito .frase{font:italic 15px/1.4 Georgia,"Times New Roman",serif;color:var(--marca)}
.contatos{display:flex;flex-wrap:wrap;gap:10px}
.contatos a{display:inline-flex;align-items:center;gap:7px;text-decoration:none;color:var(--marca);border:1px solid var(--linha);border-radius:999px;padding:6px 12px;font-size:13px;background:#fafbfc}
.contatos a:hover{border-color:var(--marca2);background:#fff}
.contatos svg{width:18px;height:18px;flex:none}
.contatos .ic-whatsapp{color:#1f8a4c}.contatos .ic-linkedin{color:#0a66c2}.contatos .ic-email{color:var(--marca)}
@media (max-width:640px){.hero{padding:22px 18px}.hero h1{font-size:21px}.card{padding:16px}.barra{padding:8px 12px}.barra .prod span{display:none}}
@page{size:A4;margin:12mm 0 12mm}
@page:first{margin-top:0}
@media print{
 body{background:#fff;font-size:11pt;-webkit-print-color-adjust:exact;print-color-adjust:exact}
 .barra{display:none}
 main{max-width:none;padding:0 9mm}
 .hero{border-radius:0;margin:0 -9mm 12px;padding:20px 9mm 18px}
 .card{box-shadow:none;border-radius:8px;padding:12px 16px;margin-bottom:10px}
 tr,.caixa-cred,.ficha,blockquote.aviso,.campo,blockquote.trecho p{break-inside:avoid;page-break-inside:avoid}
 .achado>h3{break-after:avoid;page-break-after:avoid}
 blockquote p{break-inside:avoid}
 h3,h4{break-after:avoid;page-break-after:avoid}
 h2,h3{break-after:avoid;page-break-after:avoid}
 .tabela{overflow:visible}
 th{white-space:normal}
 a{color:var(--marca2);text-decoration:none}
 .credito{max-width:none;padding:0 9mm;margin:10px 0 0}
}
"""


def _sem_credito_md(md: str) -> str:
    """Tira do markdown o bloco de credito: no HTML ele vira o rodape proprio, com icones."""
    if M.MARCADOR_RODAPE in md:
        md = md.split(M.MARCADOR_RODAPE)[0]
    linhas = [
        l for l in md.split("\n")
        if M.CREDITO not in l and not (M.EMAIL in l and "wa.me" in l)
    ]
    return "\n".join(linhas).rstrip().rstrip("-").rstrip()


def montar_pagina(md: str) -> str:
    bl = blocos(_sem_credito_md(md))
    titulo = "Relatório de auditoria"
    for i, (tipo, _h, cru) in enumerate(bl):
        if tipo == "h1":
            titulo = cru
            bl = bl[:i] + bl[i + 1:]
            break
    titulo_txt = re.sub(r"[*_`]", "", titulo)

    corpo: list[str] = []
    aberto = False
    achado_aberto = False
    letra_atual = ""
    corpo.append('<section class="card capa">')
    aberto = True

    def fechar_achado() -> None:
        nonlocal achado_aberto
        if achado_aberto:
            corpo.append("</div>")
            achado_aberto = False

    for tipo, h, cru in bl:
        if tipo == "h2":
            fechar_achado()
            if aberto:
                corpo.append("</section>")
            m = _RE_SECAO.match(re.sub(r"[*_`]", "", cru))
            if m:
                letra = m.group(1)
                letra_atual = letra
                resto = inline(_RE_SECAO.sub("", cru, count=1))
                corpo.append(f'<section class="card secao secao-{letra.lower()}"><h2><span class="letra">{letra}</span>{resto}</h2>')
            else:
                letra_atual = ""
                corpo.append(f'<section class="card">{h}')
            aberto = True
            continue
        if tipo == "hr":
            continue  # separadores do markdown viram o espaco entre os cartoes
        if tipo == "h3" and letra_atual == "B":
            # cada achado da secao B vira um cartao proprio, com a cor da gravidade
            fechar_achado()
            g = re.search(r"\b(ALTA|M[ÉE]DIA|BAIXA)\b", cru, re.IGNORECASE)
            grav = _grav_classe(g.group(1)) if g else "neutra"
            corpo.append(f'<div class="achado achado-{grav}">{h}')
            achado_aberto = True
            continue
        if achado_aberto and tipo == "p" and re.match(r"^\W*nada\s+encontrado", cru, re.IGNORECASE):
            fechar_achado()  # linha de resumo "Nada encontrado: ..." fica fora do cartao
        if achado_aberto:
            # "**Rotulo:** texto" vira campo com rotulo em destaque; citacao vira trecho literal
            mc = re.match(r"^<p><strong>([^<]{1,40}?):</strong>\s*(.*)</p>$", h, re.DOTALL)
            if mc:
                valor = mc.group(2).strip()
                valor = re.sub(r"^((?:<[^>]+>)*)([a-zà-ú])", lambda x: x.group(1) + x.group(2).upper(), valor, count=1)
                h = (f'<div class="campo"><span class="rotulo">{mc.group(1)}</span>'
                     + (f"<div>{valor}</div>" if valor else "") + "</div>")
            elif tipo == "quote" and 'class="aviso"' not in h:
                h = h.replace('<blockquote class="nota">', '<blockquote class="trecho">', 1)
        corpo.append(h)
    fechar_achado()
    if aberto:
        corpo.append("</section>")
    corpo_html = "\n".join(c for c in corpo if c != '<section class="card capa"></section>')
    corpo_html = corpo_html.replace('<section class="card capa">\n</section>', "")

    contatos = "".join(
        f'<a class="ic-{icone}" href="{html.escape(url, quote=True)}" rel="noopener noreferrer" target="_blank" '
        f'title="{html.escape(rotulo)}">{ICONES[icone]}<span>{html.escape(texto)}</span></a>'
        for rotulo, texto, url, icone in M.CONTATOS
    )
    gerado = _dt.datetime.now().strftime("%d/%m/%Y %H:%M")
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:">
<meta name="author" content="{html.escape(M.AUTOR)}">
<title>{html.escape(titulo_txt)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="barra">
  <div class="prod">{ICONES["escudo"]}<span>{html.escape(M.PRODUTO)}</span></div>
  <button class="btn" id="exportar" type="button">{ICONES["pdf"]}Exportar PDF</button>
</div>
<main>
<header class="hero">
  <div class="rotulo">{html.escape(M.PRODUTO)}</div>
  <h1>{inline(titulo)}</h1>
  <div class="gerado">Gerado em {gerado}</div>
</header>
{corpo_html}
</main>
<footer class="credito">
  <div class="caixa-cred">
    <div class="frase">{html.escape(M.CREDITO)}</div>
    <div class="contatos">{contatos}</div>
  </div>
</footer>
<script>document.getElementById("exportar").addEventListener("click",function(){{window.print();}});</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


# Jargao que nao deve chegar ao advogado (ver a tabela de linguagem em estilo-e-fronteiras).
# O script so APONTA: quem reescreve o trecho e a skill, e roda o script de novo.
# Jargao que nao pode chegar ao advogado (ver a tabela de linguagem em estilo-e-fronteiras).
# (regex, termo, troque por). O script BLOQUEIA a geracao do HTML enquanto houver termo: quem
# reescreve e a skill, e roda o script de novo.
_JARGAO: list[tuple[str, str, str]] = [
    (r"\bparsers?\b", "parser", "a verificação automática do arquivo"),
    (r"\b(web)?fetch\b", "fetch", "consulta ao site oficial"),
    (r"\bbbox\b|\bcoordenadas?\b", "bbox/coordenadas", "posição na página (\"no alto da página 7\")"),
    (r"\bspans?\b", "span", "trecho"),
    (r"\brgb\b", "rgb", "letra branca, igual ao fundo"),
    (r"#[0-9a-f]{6}\b|\bcor\s+0x[0-9a-f]+", "código de cor", "o nome da cor (branca, cinza claro...)"),
    (r"\bpymupdf\b|\bpikepdf\b|\bpdfplumber\b|\bfitz\b|\bstdlib\b", "nome de biblioteca", "não citar"),
    (r"\b(pdf_integridade|docx_integridade|unicode_scan|lexico_scan|metadados_?py|hash_check|paginas_pdf|relatorio_html)\b|\b[a-z_]+\.py\b",
     "nome de programa", "não citar o programa; diga o que foi verificado"),
    (r"\bsha-?(1|256|512)\b|\bhash\b", "hash", "não citar (só se o advogado pediu a comparação)"),
    (r"missing_dependency|formato_nao_suportado|\bstatus\s*[:=]?\s*(ok|error)\b", "status interno", "\"esta verificação não pôde ser feita\" + como resolver"),
    (r"\bvisivel\s*[:=]\s*(true|false)\b|\b(true|false)\b", "campo interno", "\"texto visível\" ou \"texto escondido\""),
    (r"\bcodepoints?\b|\bU\+[0-9A-F]{4,5}\b", "codepoint", "caractere invisível / letra de outro alfabeto"),
    (r"\bunicode\b", "unicode", "caracteres invisíveis"),
    (r"\bhom[oó]glifos?\b", "homóglifo", "letra de outro alfabeto que imita letra comum"),
    (r"\bmetadados?\b|\bauthor\b|\bcreator\b|\bproducer\b|\bmoddate\b|\bcreationdate\b", "metadados", "dados gravados no arquivo (autor, datas, programa)"),
    (r"/(js|javascript|openaction|launch|aa|embeddedfile)\b|\bpdf\s+ativo\b|\bconte[uú]do\s+ativo\b", "código de PDF", "\"código ou programa embutido no PDF\""),
    (r"\bwhitelist\b|\blista\s+branca\b", "whitelist", "\"rodapé oficial reconhecido (PJe)\""),
    (r"\brobots\.txt\b|\bcrawler\b|\banti-?bot\b|\bhttp\s*\d{3}\b|\b(403|404)\b", "detalhe de site", "\"o site oficial não abriu\" ou \"bloqueou a consulta automática\""),
    (r"\b\d[\d.,]*\s*(bytes|kb|mb)\b", "tamanho do arquivo", "não citar"),
    (r"\([+-]\d{2}:\d{2}\)|\s[+-]\d{2}:\d{2}\b", "fuso horário", "só a data e a hora"),
    (r"\bmotor\s+(pymupdf|pikepdf|pdfplumber|raw|de\s+pdf|l[eé]xico)\b", "motor", "não citar"),
    (r"\b(json|regex|xref|achados\[\]|envelope)\b", "termo de programação", "não citar"),
    (r"\bG[1-8]\b.{0,40}(✔|✓)|\bchecklist\s+de\s+qa\b", "checklist interno", "não incluir no relatório"),
    (r"\bo\s+que\s+rodou\b|\bn[aã]o\s+rodou\b|\brodou\b", "\"o que rodou\"", "não listar; o que não foi verificado vai para \"Limites desta análise\""),
    (r"\bn[aã]o\s+solicitad[oa]\b", "seção não solicitada", "omitir a seção inteira"),
]


def termos_tecnicos(md: str) -> list[dict[str, str]]:
    """Cada termo tecnico encontrado, com o trecho onde aparece e a troca sugerida."""
    texto = _sem_credito_md(md)
    texto = re.sub(r"\]\([^)]*\)", "]", texto)  # endereco de link nao conta
    achados = []
    for rx, termo, troca in _JARGAO:
        m = re.search(rx, texto, re.IGNORECASE)
        if m:
            ini = texto.rfind("\n", 0, m.start()) + 1
            fim = texto.find("\n", m.end())
            linha = texto[ini: fim if fim != -1 else len(texto)].strip()
            achados.append({"termo": termo, "trecho": linha[:160], "troque_por": troca})
    return achados


def _emitir(d: dict[str, Any]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass
    print(json.dumps(d, ensure_ascii=False, indent=2))
    return 0


def _main(argv: list[str]) -> int:
    pos = [a for a in argv if not a.startswith("-")]
    saida = None
    if "-o" in argv:
        k = argv.index("-o")
        if k + 1 < len(argv):
            saida = argv[k + 1]
            pos = [a for a in pos if a != saida]
    if not pos:
        return _emitir({"status": "error", "erro": "USO: python3 relatorio_html.py <relatorio.md> [-o saida.html]"})
    md_path = pos[0]
    if not os.path.isfile(md_path):
        return _emitir({"status": "error", "erro": f"Arquivo nao encontrado: {md_path}"})
    try:
        with open(md_path, encoding="utf-8") as fh:
            md = fh.read()
        adicionado = False
        if M.MARCADOR_RODAPE not in md and M.CREDITO not in md:
            md = md.rstrip() + M.rodape_md()
            with open(md_path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(md)
            adicionado = True
        termos = termos_tecnicos(md)
        if termos and "--forcar" not in argv:
            return _emitir({
                "status": "revisar", "arquivo_md": md_path, "arquivo_html": None,
                "credito_md_adicionado": adicionado, "termos_tecnicos": termos,
                "aviso": "HTML NAO gerado: o relatorio tem termo tecnico. Reescreva cada trecho listado "
                         "em linguagem de advogado (campo troque_por) e rode o script de novo.",
            })
        html_path = saida or os.path.splitext(md_path)[0] + ".html"
        with open(html_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(montar_pagina(md))
    except Exception as exc:
        return _emitir({"status": "error", "arquivo_md": md_path, "erro": f"Falha ao gerar o HTML: {exc}"})
    return _emitir({
        "status": "ok", "arquivo_md": md_path, "arquivo_html": html_path,
        "credito_md_adicionado": adicionado, "termos_tecnicos": termos, "aviso": "",
    })


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
