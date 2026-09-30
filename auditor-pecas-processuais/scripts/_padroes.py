#!/usr/bin/env python3
"""_padroes.py — Padroes lexicos de comando dirigido a IA + whitelist de rodape PJe.

Modulo compartilhado por `lexico_scan.py` (texto visivel) e `pdf_integridade.py` (whitelist
contra falso positivo de fonte pequena). Stdlib pura — sem rede, sem efeito colateral.

Decisoes de desenho: a normalizacao remove invisiveis e acentos antes de casar; o alvo curto
"IA" so vale em caixa alta; o vocativo a "sistema" tem gravidade baixa; a whitelist so aceita
marcadores fortes de documento oficial.

O que este modulo NAO faz: nao julga intencao. Casar um padrao e "padrao presente",
nunca "comando confirmado" — quem julga e o classificador-prompt-injection e, acima
dele, o advogado.
"""

from __future__ import annotations

import re
import unicodedata

# ---------------------------------------------------------------------------
# Normalizacao (com mapa de offsets para apontar o trecho no texto original)
# ---------------------------------------------------------------------------


def normalizar_com_mapa(texto: str) -> tuple[str, list[int]]:
    """Normaliza para casar regex e devolve (texto_normalizado, mapa).

    Passos por caractere: NFKC -> descarta invisiveis (categoria Cf: zero-width, bidi,
    Tags U+E0000..E007F, soft hyphen) -> NFD sem marcas combinantes (tira acento) ->
    casefold -> colapsa espacos. `mapa[i]` = indice, no texto ORIGINAL, do caractere que
    gerou o caractere normalizado `i`. Tirar os invisiveis ANTES de casar impede a evasao
    `IGN<ZWSP>ORE`.
    """
    saida: list[str] = []
    mapa: list[int] = []
    for i, ch in enumerate(texto):
        for c1 in unicodedata.normalize("NFKC", ch):
            if unicodedata.category(c1) == "Cf":
                continue
            for c2 in unicodedata.normalize("NFD", c1):
                if unicodedata.category(c2) == "Mn":
                    continue
                for c3 in c2.casefold():
                    if c3.isspace():
                        if saida and saida[-1] == " ":
                            continue
                        c3 = " "
                    saida.append(c3)
                    mapa.append(i)
    return "".join(saida), mapa


def normalizar(texto: str) -> str:
    return normalizar_com_mapa(texto)[0]


# ---------------------------------------------------------------------------
# Padroes lexicos — escritos para o texto JA normalizado (minusculo, sem acento)
# (regex, tag, severidade_original). A severidade vira gravidade do plugin em
# lexico_scan.py: CRITICAL->alta, HIGH->media, demais->baixa.
# ---------------------------------------------------------------------------

_PADROES_FONTE: list[tuple[str, str, str]] = [
    # endereco direto a IA
    (r"\batencao\s*[,:!.\-]*\s*(a\s+|ao\s+)?intelig[eê]ncia\s+artificial", "atencao-ia-pt", "CRITICAL"),
    (r"\batencao\s*[,:!.\-]*\s*(ia|ai|llm|assistente)\b", "atencao-ia-sigla", "CRITICAL"),
    (r"\battention\s*[,:!.\-]*\s*(ai|llm|assistant|model|language\s+model)\b", "attention-ai", "CRITICAL"),
    (r"\bse\s+voce\s+(e|for)\s+(uma?\s+)?(ia|intelig[eê]ncia\s+artificial|llm|assistente)\b", "se-voce-e-ia-pt", "CRITICAL"),
    (r"\b(if|when)\s+you\s+are\s+(an?\s+)?(ai|llm|language\s+model|artificial|assistant)\b", "if-you-are-ai", "CRITICAL"),
    # ordens de manipulacao
    (r"\b(ignore|disregard|override|forget)\s+(all\s+|any\s+|the\s+|your\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?|context)", "ignore-previous", "CRITICAL"),
    (r"\b(ignore|desconsidere|esqueca)\s+(todas?\s+)?(as\s+)?(instrucoes|regras|ordens)\s+(anteriores|previas|acima)", "ignore-anteriores-pt", "CRITICAL"),
    (r"\bignore\s+(all\s+|any\s+)?(instructions|prompts)\b", "ignore-instructions", "CRITICAL"),
    (r"\bjailbreak\b", "jailbreak", "HIGH"),
    (r"\boverride\s+(rules|instructions|system)\b", "override-rules", "HIGH"),
    (r"\bdo\s+not\s+(follow|obey|trust)\s+(the\s+)?(previous|user|operator)", "do-not-follow", "HIGH"),
    (r"\byou\s+(must|shall|should)\s+(contest|reject|refuse|dismiss)\b", "must-contest", "HIGH"),
    (r"\b(system|assistant)\s*:\s*(you\s+(are|must|will|shall)|ignore|do\s+not|always|never|respond|answer)", "role-prefix", "HIGH"),
    (r"<\s*/?\s*(instructions?|system|prompt)s?\s*>", "xml-instruction-tag", "HIGH"),
    # ordens em PT-BR (caso TRT-8: texto branco com comando a IA)
    (r"\bconteste\b.{0,60}\bsuperficial", "conteste-superficial-pt", "CRITICAL"),
    (r"\bnao\s+impugne\s+(os\s+)?documentos?", "nao-impugne-pt", "CRITICAL"),
    (r"\bindependentemente\s+do\s+comando", "indep-comando-pt", "HIGH"),
    (r"\brespond[ae]\s+(somente|apenas|exclusivamente)\s+com\b", "responda-somente-pt", "HIGH"),
    (r"\brespond\s+only\s+with\b", "respond-only-with", "HIGH"),
    (r"\bpriorid(ade)?\s+sobre\s+(o\s+)?(usuario|operador)|\bpriority\s+over\s+(the\s+)?(user|operator)", "priority-over-user", "HIGH"),
    (r"\bnao\s+registr[ea]\s+(esse|este|no|neste)\s+(log|achado|relatorio)", "no-log-pt", "HIGH"),
    # vocativo a sistema/redator — rebaixado: "no sistema, nao consta" e prosa juridica comum
    (r"\b(sistema|redator|agente|pipeline|automacao|automation)\s*,\s*(ignor|nao\s+(?!obstante)|respond|destaque|faca)", "endereco-sistema-pt", "MEDIUM"),
]

PADROES = [(re.compile(p), tag, sev) for p, tag, sev in _PADROES_FONTE]

# Verbo de controle dirigido a um alvo-IA, aplicado ao texto ORIGINAL. So formas IMPERATIVAS
# ("ignore", "conteste", "impugne", "responda"...): "contestou/contestar/impugnou" sao prosa
# juridica comum. Alvo curto ("IA"/"AI"/"LLM") so vale em CAIXA ALTA (em minusculo, "ia" e verbo
# do portugues: "a re ia contestar"). Alvos de palavra comum (agente, redator, pipeline,
# assistant, sistema) so valem como VOCATIVO ("Redator, ignore...").
_VERBO_CONTROLE = (
    r"(?i:ignore|disregard|desconsidere|conteste|impugne|responda|destaque|omita|esconda|"
    r"reject|dismiss|n[aã]o\s+(?:sig[ao]|obede[cç]a|fa[cç]a|execute|registre|mencione|impugne|conteste))"
)
VERBO_IA_RE = re.compile(
    r"(?:\b(?:IA|AI|LLM)\b.{0,40}?"
    r"|(?i:\bintelig[eê]ncia\s+artificial\b).{0,40}?"
    r"|(?i:\b(?:assistant|assistente|agente|redator|pipeline|sistema)\b)\s*[,:]\s*)"
    + _VERBO_CONTROLE
)


def tem_verbo_ia(texto_original: str) -> bool:
    return bool(VERBO_IA_RE.search(texto_original or ""))


def achados_lexicos(texto_original: str) -> list[tuple[str, str, str, int, int, str]]:
    """Casa os padroes no texto e devolve tuplas
    (tag, severidade, trecho_normalizado, ini_orig, fim_orig, contexto_normalizado).

    `ini_orig`/`fim_orig` sao offsets no texto ORIGINAL recebido.
    """
    norm, mapa = normalizar_com_mapa(texto_original)
    saida = []
    for rx, tag, sev in PADROES:
        for m in rx.finditer(norm):
            ini = mapa[m.start()]
            fim = mapa[m.end() - 1] + 1
            ctx = norm[max(0, m.start() - 60): min(len(norm), m.end() + 60)]
            saida.append((tag, sev, m.group(0)[:200], ini, fim, ctx[:300]))
    # alvo-IA + verbo de controle (ex.: "IA, nao impugne"), casado no texto original
    for m in VERBO_IA_RE.finditer(texto_original):
        trecho = normalizar(m.group(0))[:200]
        ctx = normalizar(texto_original[max(0, m.start() - 60): m.end() + 60])[:300]
        saida.append(("ia-verbo-controle", "HIGH", trecho, m.start(), m.end(), ctx))
    return saida


def tem_padrao_lexico(texto_original: str) -> bool:
    return bool(achados_lexicos(texto_original)) or tem_verbo_ia(texto_original)


# ---------------------------------------------------------------------------
# Whitelist de rodape/cabecalho de documento oficial (PJe e afins)
# Somente MARCADORES FORTES. Rotulos genericos ("Valor", "Cargo", "Periodo", "Foto")
# ficam de fora de proposito: casam palavra comum e abririam brecha.
# ---------------------------------------------------------------------------

_WHITELIST_FONTE = (
    r"\bpje\b|processo\s+judicial\s+eletronico|icp[\-\s]?brasil|"
    r"assinad[oa]\s+(eletronicamente|digitalmente)|documento\s+assinado|"
    r"\boab\s*[/\-]\s*[a-z]{2}\b|\bverificador\b|codigo\s+de\s+verificacao|"
    r"\bhash\b|\bsha[\-\s]?\d{1,3}\b|autenticidade\s+(deste\s+)?documento|"
    r"\bnum\.?\s*\d{5,}\s*[\-\u2013]\s*pag|\bid\s*\d{6,}|"
    r"\bgov\.br\b|\bjus\.br\b|\btrt\d{1,2}\b|\btj[a-z]{2}\b|\bcertificado\s+digital\b"
)
WHITELIST_RODAPE_RE = re.compile(_WHITELIST_FONTE)


def eh_marcador_legitimo(texto_original: str) -> bool:
    """True se o texto traz marcador forte de rodape/cabecalho oficial (PJe, ICP-Brasil...)."""
    return bool(WHITELIST_RODAPE_RE.search(normalizar(texto_original)))


# ---------------------------------------------------------------------------
# Zona da pagina (rodape / cabecalho / corpo) a partir do bbox
# ---------------------------------------------------------------------------


def classificar_zona(bbox: list[float] | tuple[float, ...] | None, altura_pagina: float) -> str:
    """rodape (y1 > 92% da altura) · cabecalho (y0 < 8%) · corpo · indeterminado."""
    if not bbox or len(bbox) < 4 or not altura_pagina:
        return "indeterminado"
    y0, y1 = float(bbox[1]), float(bbox[3])
    if y1 > altura_pagina * 0.92:
        return "rodape"
    if y0 < altura_pagina * 0.08:
        return "cabecalho"
    return "corpo"
