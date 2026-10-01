#!/usr/bin/env python3
"""_padroes.py — Padroes de comando dirigido a IA (por grupo de ataque) + whitelist de rodape PJe.

Modulo compartilhado por `lexico_scan.py`, `pdf_integridade.py` e `docx_integridade.py`. Stdlib pura
— sem rede, sem efeito colateral.

Grupos de ataque (taxonomia usada no relatorio):
    A  desvio de funcao da IA      ("ignore as instrucoes anteriores", "a partir de agora voce e...")
    B  supressao de informacao     ("nao mencione os comprovantes", "omita qualquer referencia")
    C  inducao de vies             ("recomende a improcedencia", "favoreca a parte re")
    D  padroes tecnicos            (Base64/hex com comando, tags <ai-...>, [INST], JSON de instrucao)
    E  falsa autoridade            ("instrucoes do sistema", "modo de emergencia", "autorizado pelo STJ")

Defesas contra ofuscacao, aplicadas antes de casar: remove caracteres invisiveis, tira acentos,
troca letra de outro alfabeto pela latina que ela imita, procura de novo sem espacos (palavra
partida) e decodifica trechos em Base64, hexadecimal, percent-encoding e entidades HTML.

Decisoes de desenho: o alvo curto "IA" so vale em caixa alta; imperativos ("recomende",
"omita") e nao prosa ("requer a improcedencia", "a parte autora age de ma-fe"); a whitelist so
aceita marcadores fortes de documento oficial.

O que este modulo NAO faz: nao julga intencao. Casar um padrao e "padrao presente", nunca
"comando confirmado" — quem julga e o classificador-prompt-injection e, acima dele, o advogado.
"""

from __future__ import annotations

import base64
import binascii
import html as _html
import re
import unicodedata
import urllib.parse

from _homoglifos import HOMOGLIFOS

GRUPOS = {
    "A": "desvio de função da IA",
    "B": "supressão de informação",
    "C": "indução de viés",
    "D": "padrão técnico",
    "E": "falsa autoridade",
}

# ---------------------------------------------------------------------------
# Normalizacao (com mapa de offsets para apontar o trecho no texto original)
# ---------------------------------------------------------------------------

_DOBRA = {cp: latina.lower() for cp, (latina, _script) in HOMOGLIFOS.items()}


def normalizar_com_mapa(texto: str) -> tuple[str, list[int]]:
    """Normaliza para casar regex e devolve (texto_normalizado, mapa).

    Por caractere: troca letra de outro alfabeto pela latina que imita -> NFKC -> descarta
    invisiveis (categoria Cf: zero-width, bidi, Tags, soft hyphen) -> tira acento -> casefold ->
    colapsa espacos. `mapa[i]` = indice, no texto ORIGINAL, do caractere que gerou o caractere
    normalizado `i`.
    """
    saida: list[str] = []
    mapa: list[int] = []
    for i, ch in enumerate(texto):
        ch = _DOBRA.get(ord(ch), ch)
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
# Padroes — escritos para o texto JA normalizado (minusculo, sem acento)
# (regex, tag, severidade, grupo). Severidade vira gravidade do plugin em lexico_scan.py:
# CRITICAL->alta, HIGH->media, MEDIUM->baixa; trecho oculto ou codificado sempre sobe para alta.
# ---------------------------------------------------------------------------

_PARTE = r"(parte|autor|autora|reu|re|reclamante|reclamad[oa]|requerente|requerid[oa]|apelante|apelad[oa]|agravante|agravad[oa]|exequente|executad[oa]|empresa|cliente)"
_ALVO_PROVA = r"(comprovantes?|documentos?|provas?|recibos?|laudos?|contratos?|anexos?|argumentos?|pagamentos?|testemunhas?|depoimentos?|fatos?|clausulas?|pedidos?|fundamentos?|fls\.?|paginas?)"

_PADROES_FONTE: list[tuple[str, str, str, str]] = [
    # ---- A: desvio de funcao da IA (endereco a IA, troca de papel, ignorar instrucoes)
    (r"\batencao\s*[,:!.\-]*\s*(a\s+|ao\s+)?inteligencia\s+artificial", "atencao-ia-pt", "CRITICAL", "A"),
    (r"\batencao\s*[,:!.\-]*\s*(ia|ai|llm|assistente)\b", "atencao-ia-sigla", "CRITICAL", "A"),
    (r"\battention\s*[,:!.\-]*\s*(ai|llm|assistant|model|language\s+model)\b", "attention-ai", "CRITICAL", "A"),
    (r"\bse\s+voce\s+(e|for)\s+(uma?\s+)?(ia|inteligencia\s+artificial|llm|assistente)\b", "se-voce-e-ia-pt", "CRITICAL", "A"),
    (r"\b(if|when)\s+you\s+are\s+(an?\s+)?(ai|llm|language\s+model|artificial|assistant)\b", "if-you-are-ai", "CRITICAL", "A"),
    (r"\b(ignore|disregard|override|forget)\s+(all\s+|any\s+|the\s+|your\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?|context)", "ignore-previous", "CRITICAL", "A"),
    (r"\b(ignore|desconsidere|esqueca)\s+(todas?\s+)?(as\s+|suas\s+)?(instrucoes|regras|ordens|diretrizes|orientacoes)\s+(anteriores|previas|acima|recebidas|originais)", "ignore-anteriores-pt", "CRITICAL", "A"),
    (r"\bignore\s+(all\s+|any\s+)?(instructions|prompts)\b", "ignore-instructions", "CRITICAL", "A"),
    (r"\bignore\s+(qualquer|quaisquer|todas?\s+as?|toda)\s+(instrucao|instrucoes|criterio|criterios|orientacao|orientacoes|regra|regras|diretriz|diretrizes)\b", "ignore-qualquer-instrucao-pt", "CRITICAL", "A"),
    (r"\b(esqueca|desconsidere|abandone|descarte)\s+(suas|as|todas\s+as|quaisquer)\s+(instrucoes|regras|diretrizes|orientacoes|configuracoes)\b", "esqueca-instrucoes-pt", "CRITICAL", "A"),
    (r"\ba\s+partir\s+de\s+agora\s*,?\s*(voce\s+(e|sera|passa\s+a\s+ser|deve|vai|atuara)|atue|aja|comporte-se|seja|considere-se)\b", "papel-novo-pt", "CRITICAL", "A"),
    (r"\b(voce\s+e|voce\s+sera|voce\s+agora\s+e|atue\s+como|aja\s+como|comporte-se\s+como|assuma\s+o\s+papel\s+de)\s+(um|uma|o|a)?\s*(assistente|advogad[oa]|representante|defensor[a]?|aliad[oa]|procurador[a]?)\s+(do|da|de)\s+" + _PARTE, "assistente-da-parte-pt", "CRITICAL", "A"),
    (r"\b(seu|o\s+seu)\s+novo\s+papel\b|\bnovo\s+papel\s*:", "novo-papel-pt", "HIGH", "A"),
    (r"\bsua\s+(analise|resposta|conclusao|avaliacao|decisao|minuta|manifestacao)\s+(deve|devera|precisa|tem\s+que|tera\s+que)\s+(concluir|ser|reconhecer|indicar|apontar|declarar|acolher|rejeitar)", "analise-deve-concluir-pt", "HIGH", "A"),
    (r"\b(you\s+are\s+now|from\s+now\s+on\s*,?\s*you|act\s+as\s+(an?|the)\s+\w+|your\s+new\s+role)\b", "role-change-en", "HIGH", "A"),
    (r"\bjailbreak\b", "jailbreak", "HIGH", "A"),
    (r"\boverride\s+(rules|instructions|system)\b", "override-rules", "HIGH", "A"),
    (r"\bdo\s+not\s+(follow|obey|trust)\s+(the\s+)?(previous|user|operator)", "do-not-follow", "HIGH", "A"),
    (r"\b(system|assistant)\s*:\s*(you\s+(are|must|will|shall)|ignore|do\s+not|always|never|respond|answer)", "role-prefix", "HIGH", "A"),
    (r"\bindependentemente\s+do\s+comando", "indep-comando-pt", "HIGH", "A"),
    (r"\brespond[ae]\s+(somente|apenas|exclusivamente)\s+com\b", "responda-somente-pt", "HIGH", "A"),
    (r"\brespond\s+only\s+with\b", "respond-only-with", "HIGH", "A"),
    (r"\bpriorid(ade)?\s+sobre\s+(o\s+)?(usuario|operador)|\bpriority\s+over\s+(the\s+)?(user|operator)", "priority-over-user", "HIGH", "A"),
    (r"\binstruc(ao|oes)\s+(ao|aos|para\s+o)\s+(sistema|modelo|assistente|agente|ia)\b", "instrucao-ao-sistema-pt", "CRITICAL", "A"),
    (r"\b(sistema|redator|agente|pipeline|automacao|automation)\s*,\s*(ignor|nao\s+(?!obstante)|respond|destaque|faca)", "endereco-sistema-pt", "MEDIUM", "A"),
    # ---- B: supressao de informacao
    (r"\bnao\s+impugne\s+(os\s+)?documentos?", "nao-impugne-pt", "CRITICAL", "B"),
    (r"\bnao\s+(mencione|cite|aborde|comente|reporte|aponte|informe|destaque|registre|examine|leia)\s+(o|a|os|as|nenhum|nenhuma|qualquer|quaisquer|esse|esses|essa|essas|este|estes|esta|estas|seus|suas|\w+s?\s+)?\s*" + _ALVO_PROVA, "nao-mencione-pt", "HIGH", "B"),
    (r"\bnao\s+(cite|mencione|aborde|comente)\s+(argumentos?|provas?|documentos?|precedentes?|jurisprudencia)", "nao-cite-pt", "HIGH", "B"),
    (r"\bomita\s+(qualquer|toda|todas\s+as|quaisquer|a|as|o|os)?\s*(referencia|referencias|mencao|mencoes|informacao|informacoes|dado|dados|trecho|trechos|documento|documentos|prova|provas)\b", "omita-referencia-pt", "HIGH", "B"),
    (r"\bdeixe\s+de\s+(mencionar|citar|analisar|apontar|considerar|informar|registrar)\b", "deixe-de-mencionar-pt", "HIGH", "B"),
    (r"(?<!\bse )(?<!\bque )\bignore\s+(o|os|a|as|este|esse|estes|esses|esta|essa)\s+" + _ALVO_PROVA + r"\b", "ignore-documento-pt", "HIGH", "B"),
    (r"\bnao\s+registr[ea]\s+(esse|este|no|neste)\s+(log|achado|relatorio)", "no-log-pt", "HIGH", "B"),
    (r"\b(do\s+not\s+(mention|cite|include|report|disclose)|omit\s+(any|all)\s+(reference|mention))\b", "supressao-en", "HIGH", "B"),
    # ---- C: inducao de vies
    (r"\bconteste\b.{0,60}\bsuperficial", "conteste-superficial-pt", "CRITICAL", "C"),
    (r"\b(recomende|sugira|indique|opine\s+pela|conclua\s+pela|proponha|declare)\s+(a\s+|pela\s+)?(improcedencia|procedencia|condenacao|absolvicao|extincao|rejeicao|aceitacao|deferimento|indeferimento|nulidade)\b", "recomende-resultado-pt", "HIGH", "C"),
    (r"\bfavoreca\s+(a|o|os|as)\s+" + _PARTE, "favoreca-parte-pt", "HIGH", "C"),
    (r"\bclassifique\s+(o\s+risco\s+|este\s+caso\s+|esse\s+caso\s+|o\s+caso\s+|a\s+demanda\s+|a\s+acao\s+|o\s+pedido\s+)?como\s+(de\s+)?(risco\s+)?(baixo|alto|minimo|nenhum|inexistente|remoto|baixissimo)\b", "classifique-risco-pt", "HIGH", "C"),
    (r"\btrate\s+(a|o)\s+" + _PARTE + r"\s+como\b", "trate-parte-pt", "HIGH", "C"),
    (r"\b(dê|de)\s+provimento\s+integral\b", "de-provimento-pt", "HIGH", "C"),
    (r"\byou\s+(must|shall|should)\s+(contest|reject|refuse|dismiss)\b", "must-contest", "HIGH", "C"),
    (r"\b(recommend\s+(dismissal|rejection|approval|denial)|favor\s+the\s+(plaintiff|defendant))\b", "vies-en", "HIGH", "C"),
    (r"\bresultado\s+esperado\s*[:\-]?\s*(a\s+)?(procedencia|improcedencia|deferimento|indeferimento|provimento|desprovimento)", "resultado-esperado-pt", "HIGH", "C"),
    (r"\bconclusao\s+obrigatoria\s+da\s+analise", "conclusao-obrigatoria-pt", "HIGH", "C"),
    # ---- D: padroes tecnicos (estrutura de prompt)
    (r"<\s*/?\s*ai[\-_][a-z0-9\-_]*[^>]{0,80}>", "tag-ai-xml", "HIGH", "D"),
    (r"<\s*/?\s*(instructions?|system|prompt|assistant|context)s?\s*>", "xml-instruction-tag", "HIGH", "D"),
    (r"\[/?inst\]|<<\s*/?sys\s*>>|<\|\s*(im_start|im_end|system|assistant)\s*\|>", "marcador-chat-template", "HIGH", "D"),
    (r"[\"'](instruction|instructions|system_prompt|system|role|prompt)[\"']\s*:\s*[\"']", "json-instrucao", "HIGH", "D"),
    (r"<!--.{3,300}?-->", "comentario-html", "MEDIUM", "D"),
    # ---- E: falsa autoridade
    (r"\binstruc(ao|oes)\s+(do|de)\s+sistema\b", "instrucoes-do-sistema-pt", "CRITICAL", "E"),
    (r"\bmodo\s+(de\s+)?(emergencia|administrador|desenvolvedor|manutencao|depuracao|debug|supervisor|teste\s+interno)\b", "modo-especial-pt", "HIGH", "E"),
    (r"\bnivel\s+de\s+(acesso|permissao|autorizacao)\s+(superior|administrativo|maximo|privilegiado|elevado|irrestrito|especial)\b", "nivel-acesso-pt", "HIGH", "E"),
    (r"\binstruc(ao|oes)\s+(prioritaria|prioritarias|superior|superiores|de\s+maior\s+prioridade|mestra|absoluta)\b", "instrucao-prioritaria-pt", "HIGH", "E"),
    (r"\b(esta|essa)\s+instrucao\s+(deve|devera|devem)\s+prevalecer", "instrucao-prevalece-pt", "HIGH", "E"),
    (r"\b(este|esse|o\s+presente)\s+(documento|arquivo|peticao|texto|conteudo|relatorio|parecer)\s+(foi\s+|e\s+|esta\s+)?(previamente\s+)?(autorizad|certificad|validad|homologad|aprovad|chancelad)[oa]\s+(pelo|pela)\s+(stj|stf|cnj|tst|tse|trf\d?|tribunal|juizo|corregedoria|oab|ministerio\s+publico|presidencia)", "falsa-autoridade-pt", "HIGH", "E"),
    (r"\b(system\s+override|admin(istrator)?\s+mode|developer\s+mode|emergency\s+mode|priority\s+instruction|elevated\s+access)\b", "autoridade-en", "HIGH", "E"),
]

PADROES = [(re.compile(p), tag, sev) for p, tag, sev, _g in _PADROES_FONTE]
GRUPO_DA_TAG: dict[str, str] = {tag: g for _p, tag, _s, g in _PADROES_FONTE}

# Verbo de controle dirigido a um alvo-IA, aplicado ao texto ORIGINAL. So formas IMPERATIVAS.
# Alvo curto ("IA"/"AI"/"LLM") so vale em CAIXA ALTA (em minusculo, "ia" e verbo do portugues).
# Alvos de palavra comum (agente, redator, sistema...) so valem como VOCATIVO ("Redator, ignore...").
_VERBO_CONTROLE = (
    r"(?i:ignore|disregard|desconsidere|conteste|impugne|responda|destaque|omita|esconda|favore[cç]a|"
    r"recomende|reject|dismiss|n[aã]o\s+(?:sig[ao]|obede[cç]a|fa[cç]a|execute|registre|mencione|impugne|conteste|cite))"
)
VERBO_IA_RE = re.compile(
    r"(?:\b(?:IA|AI|LLM)\b.{0,40}?"
    r"|(?i:\bintelig[eê]ncia\s+artificial\b).{0,40}?"
    r"|(?i:\b(?:assistant|assistente|agente|redator|pipeline|sistema)\b)\s*[,:]\s*)"
    + _VERBO_CONTROLE
)
GRUPO_DA_TAG["ia-verbo-controle"] = "A"

# Frases-chave procuradas no texto normalizado SEM ESPACOS (palavra partida por espacamento de
# caracteres, "I g n o r e"). So frases longas e especificas, para nao casar prosa juridica.
_COMPACTOS_FONTE: list[tuple[str, str, str]] = [
    (r"instruc(ao|oes)(ao|aos|parao)(sistema|modelo|assistente|agente)", "instrucao-ao-sistema-pt", "CRITICAL"),
    (r"instruc(ao|oes)(do|de)sistema", "instrucoes-do-sistema-pt", "CRITICAL"),
    (r"ignore(qualquer|quaisquer|todasas|todaas|toda)(instrucao|instrucoes|criterio|orientacao|regra)", "ignore-qualquer-instrucao-pt", "CRITICAL"),
    (r"(ignore|disregard)(all|any|the|your)?(previous|prior|above)(instructions?|prompts?)", "ignore-previous", "CRITICAL"),
    (r"(ignore|desconsidere|esqueca)(todas)?(as|suas)?(instrucoes|regras)(anteriores|previas)", "ignore-anteriores-pt", "CRITICAL"),
    (r"apartirdeagora,?(voce(e|sera)|atue|aja)", "papel-novo-pt", "CRITICAL"),
    (r"naoimpugne(os)?documentos?", "nao-impugne-pt", "CRITICAL"),
    (r"nao(mencione|cite)(os|as|o|a|nenhum|nenhuma)?(comprovantes?|documentos?|provas?|argumentos?|recibos?|laudos?)", "nao-mencione-pt", "HIGH"),
    (r"omita(qualquer|toda|quaisquer)(referencia|mencao|informacao)", "omita-referencia-pt", "HIGH"),
    (r"favoreca(a|o)(parte|autor|autora|reu|re)", "favoreca-parte-pt", "HIGH"),
    (r"recomende(a)?(improcedencia|procedencia)", "recomende-resultado-pt", "HIGH"),
    (r"atencao[,:!.\-]*(a|ao)?inteligenciaartificial", "atencao-ia-pt", "CRITICAL"),
    (r"conteste.{0,50}superficial", "conteste-superficial-pt", "CRITICAL"),
    (r"(esta|essa)instrucao(deve|devera)prevalecer", "instrucao-prevalece-pt", "HIGH"),
    (r"instrucaoprioritaria", "instrucao-prioritaria-pt", "HIGH"),
    (r"mododeemergencia", "modo-especial-pt", "HIGH"),
    (r"niveldeacesso(superior|administrativo|maximo)", "nivel-acesso-pt", "HIGH"),
    (r"resultadoesperado[:\-]?(procedencia|improcedencia|deferimento|provimento)", "resultado-esperado-pt", "HIGH"),
    (r"independentementedocomando", "indep-comando-pt", "HIGH"),
]
COMPACTOS = [(re.compile(p), tag, sev) for p, tag, sev in _COMPACTOS_FONTE]

# ---------------------------------------------------------------------------
# Conteudo codificado (grupo D): decodifica e procura comando dentro
# ---------------------------------------------------------------------------

_RE_B64 = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{20,}={0,2}(?![A-Za-z0-9+/=])")
_RE_HEX = re.compile(r"(?<![0-9A-Fa-f])(?:[0-9A-Fa-f]{2}[\s:]?){12,}(?![0-9A-Fa-f])")
_RE_PCT = re.compile(r"(?:%[0-9A-Fa-f]{2}[^%\s]{0,3}){6,}")
_RE_ENT = re.compile(r"(?:&#x?[0-9A-Fa-f]{2,6};\s?){6,}")


def _legivel(t: str) -> bool:
    if len(t) < 8:
        return False
    imprimiveis = sum(1 for c in t if c.isprintable() and (c.isalnum() or c.isspace() or c in ".,;:!?-()'\"/"))
    letras = sum(1 for c in t if c.isalpha())
    return imprimiveis / len(t) >= 0.9 and letras / len(t) >= 0.5 and " " in t


def _decodificacoes(texto: str) -> list[tuple[str, int, int, str]]:
    """Trechos codificados que decodificam para texto legivel: (codificacao, ini, fim, decodificado)."""
    saida: list[tuple[str, int, int, str]] = []

    def tentar(nome: str, m: re.Match[str], fn) -> None:
        try:
            dec = fn(m.group(0))
        except (ValueError, binascii.Error, UnicodeDecodeError):
            return
        if dec and _legivel(dec):
            saida.append((nome, m.start(), m.end(), dec))

    def _b64(s: str) -> str:
        s2 = s + "=" * (-len(s) % 4)
        return base64.b64decode(s2, validate=True).decode("utf-8")

    def _hex(s: str) -> str:
        return bytes.fromhex(re.sub(r"[\s:]", "", s)).decode("utf-8")

    for m in _RE_B64.finditer(texto):
        if re.fullmatch(r"[0-9A-Fa-f]+", m.group(0)):  # hash hexadecimal nao e Base64
            continue
        tentar("Base64", m, _b64)
    for m in _RE_HEX.finditer(texto):
        tentar("hexadecimal", m, _hex)
    for m in _RE_PCT.finditer(texto):
        tentar("percent-encoding", m, lambda s: urllib.parse.unquote(s, errors="strict"))
    for m in _RE_ENT.finditer(texto):
        tentar("entidades HTML", m, _html.unescape)
    return saida


def tem_verbo_ia(texto_original: str) -> bool:
    return bool(VERBO_IA_RE.search(texto_original or ""))


def _casar(texto_original: str) -> list[tuple[str, str, str, int, int, str]]:
    norm, mapa = normalizar_com_mapa(texto_original)
    saida = []
    for rx, tag, sev in PADROES:
        for m in rx.finditer(norm):
            ini = mapa[m.start()]
            fim = mapa[m.end() - 1] + 1
            ctx = norm[max(0, m.start() - 60): min(len(norm), m.end() + 60)]
            saida.append((tag, sev, m.group(0)[:200], ini, fim, ctx[:300]))
    for m in VERBO_IA_RE.finditer(texto_original):
        trecho = normalizar(m.group(0))[:200]
        ctx = normalizar(texto_original[max(0, m.start() - 60): m.end() + 60])[:300]
        saida.append(("ia-verbo-controle", "HIGH", trecho, m.start(), m.end(), ctx))

    # passada sem espacos (palavra partida). So entra o que nao sobrepoe achado ja feito.
    compacto_chars = [(c, mapa[k]) for k, c in enumerate(norm) if c != " "]
    compacto = "".join(c for c, _ in compacto_chars)
    for rx, tag, sev in COMPACTOS:
        for m in rx.finditer(compacto):
            ini = compacto_chars[m.start()][1]
            fim = compacto_chars[m.end() - 1][1] + 1
            if any(a[3] < fim and a[4] > ini for a in saida):
                continue
            trecho = normalizar(texto_original[ini:fim])[:200]
            ctx = normalizar(texto_original[max(0, ini - 60): fim + 60])[:300]
            saida.append((tag, sev, trecho, ini, fim, ctx))
    return saida


def achados_lexicos(texto_original: str) -> list[tuple[str, str, str, int, int, str]]:
    """Casa os padroes no texto e devolve tuplas
    (tag, severidade, trecho, ini_orig, fim_orig, contexto).

    Inclui comando escondido em conteudo codificado: tag `comando-codificado-<codificacao>`,
    severidade CRITICAL, trecho = texto decodificado.
    """
    saida = _casar(texto_original)
    for nome, ini, fim, dec in _decodificacoes(texto_original):
        internos = _casar(dec)
        if internos:
            regras = ", ".join(sorted({t for t, *_ in internos}))
            saida.append((
                "comando-codificado-" + nome.lower().replace(" ", "-"), "CRITICAL",
                f"{nome} decodificado: «{dec[:160]}» (regras: {regras})", ini, fim,
                normalizar(texto_original[max(0, ini - 40): fim + 40])[:300],
            ))
    return saida


def grupo_de(tag: str) -> str:
    if tag.startswith("comando-codificado"):
        return "D"
    return GRUPO_DA_TAG.get(tag, "A")


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
