#!/usr/bin/env bash
#
# smoke_test.sh — Controle POSITIVO e NEGATIVO dos parsers de integridade.
#
# Disciplina "verificar com isca antes de confiar no silencio": um parser que nao
# acha nada so vale depois de provar, num controle negativo, que ele acharia se
# houvesse. Este smoke roda gerar_isca.py, depois cada parser contra a isca (deve
# ACHAR) e contra o controle limpo (deve dar total_achados 0).
#
# USO (a partir da raiz do plugin OU de qualquer lugar):
#     bash scripts/smoke_test.sh
#
# Sai com 0 se todos os checks passarem; 1 se qualquer um falhar.

set -u

# raiz do plugin = pasta-mae do diretorio deste script
AQUI="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$(cd "$AQUI/.." && pwd)"
cd "$RAIZ"

PY="${PY:-python3}"   # no Windows: PY=python bash scripts/smoke_test.sh
SCR="scripts"
FIX="scripts/fixtures"
OUT="$(mktemp -d)"
FAILS=0

trap 'rm -rf "$OUT"' EXIT

echo "== auditor-pecas-processuais :: smoke dos parsers =="
echo "raiz: $RAIZ"
echo

# ---------------------------------------------------------------------------
# 0. gerar as fixtures
# ---------------------------------------------------------------------------
if ! $PY "$SCR/gerar_isca.py" > "$OUT/gerar.log" 2>&1; then
    echo "FAIL: gerar_isca.py nao rodou"
    cat "$OUT/gerar.log"
    exit 1
fi
echo "PASS: gerar_isca.py gerou as fixtures"

# helpers -------------------------------------------------------------------
run() {  # run <parser.py> <arquivo> <nome_saida> [args...]
    local parser="$1"; local arq="$2"; local nome="$3"; shift 3
    $PY "$SCR/$parser" "$arq" "$@" > "$OUT/$nome" 2> "$OUT/$nome.err"
}

assert_contem() {  # assert_contem <desc> <nome_saida> <padrao>
    if grep -qF "$3" "$OUT/$2"; then
        echo "PASS: $1"
    else
        echo "FAIL: $1  (esperava conter: $3)"
        echo "      --- saida ($2) ---"
        sed 's/^/      /' "$OUT/$2"
        FAILS=$((FAILS + 1))
    fi
}

# ---------------------------------------------------------------------------
# 1. isca.pdf -> pdf_integridade deve achar TEXTO BRANCO/OCULTO e CONTEUDO ATIVO
# ---------------------------------------------------------------------------
run "pdf_integridade.py" "$FIX/isca.pdf" "pdf_isca.json"
assert_contem "isca.pdf: pdf_integridade status ok"       "pdf_isca.json" '"status": "ok"'
assert_contem "isca.pdf: acha texto oculto"                "pdf_isca.json" '"tipo": "texto_oculto"'
assert_contem "isca.pdf: acha conteudo ativo (/OpenAction/JS)" "pdf_isca.json" '"tipo": "conteudo_ativo"'

# ---------------------------------------------------------------------------
# 2. isca.docx -> unicode_scan acha os 3 plantados; metadados acha autor+comentario
# ---------------------------------------------------------------------------
run "unicode_scan.py" "$FIX/isca.docx" "uni_isca.json"
assert_contem "isca.docx: unicode_scan acha zero-width/invisivel" "uni_isca.json" '"tipo": "zero_width_ou_invisivel"'
assert_contem "isca.docx: unicode_scan acha Tags (ASCII smuggling)" "uni_isca.json" '"tipo": "tag_ascii_smuggling"'
assert_contem "isca.docx: unicode_scan acha homoglifo"            "uni_isca.json" '"tipo": "homoglifo"'

run "metadados.py" "$FIX/isca.docx" "meta_isca.json"
assert_contem "isca.docx: metadados acha autor interno"           "meta_isca.json" '"tipo": "autor"'
assert_contem "isca.docx: metadados acha comentarios internos"    "meta_isca.json" '"tipo": "comentarios_internos"'

# ---------------------------------------------------------------------------
# 3. CONTROLES LIMPOS -> total_achados 0 (unicode / oculto)
# ---------------------------------------------------------------------------
run "unicode_scan.py" "$FIX/controle_limpo.txt" "uni_ctrl_txt.json"
assert_contem "controle.txt: unicode_scan total_achados 0"        "uni_ctrl_txt.json" '"total_achados": 0'

run "unicode_scan.py" "$FIX/controle_limpo.docx" "uni_ctrl_docx.json"
assert_contem "controle.docx: unicode_scan total_achados 0"       "uni_ctrl_docx.json" '"total_achados": 0'

run "pdf_integridade.py" "$FIX/controle_limpo.pdf" "pdf_ctrl.json"
assert_contem "controle.pdf: pdf_integridade status ok"           "pdf_ctrl.json" '"status": "ok"'
assert_contem "controle.pdf: pdf_integridade total_achados 0"     "pdf_ctrl.json" '"total_achados": 0'

# ---------------------------------------------------------------------------
# 4. hash_check basico + divergencia declarada
# ---------------------------------------------------------------------------
run "hash_check.py" "$FIX/isca.pdf" "hash_isca.json"
assert_contem "isca.pdf: hash_check emite sha256"                 "hash_isca.json" '"tipo": "hash"'

$PY "$SCR/hash_check.py" "$FIX/isca.pdf" --declarado deadbeef > "$OUT/hash_div.json" 2>&1
assert_contem "hash divergente vira ALERTA (nao fraude)"          "hash_div.json" '"tipo": "hash_divergente"'

# ---------------------------------------------------------------------------
# 5. arquivo inexistente -> JSON de erro limpo (sem traceback), status error
# ---------------------------------------------------------------------------
$PY "$SCR/pdf_integridade.py" "$FIX/nao_existe.pdf" > "$OUT/err_pdf.json" 2>&1
assert_contem "arquivo inexistente: status error limpo"          "err_pdf.json" '"status": "error"'
if grep -qF "Traceback" "$OUT/err_pdf.json"; then
    echo "FAIL: arquivo inexistente vazou traceback cru"
    FAILS=$((FAILS + 1))
else
    echo "PASS: arquivo inexistente nao vazou traceback"
fi

# ---------------------------------------------------------------------------
# 6. Varredura LEXICA (comando a IA em texto visivel) + WHITELIST de rodape PJe
# ---------------------------------------------------------------------------

assert_json() {  # assert_json <desc> <nome_saida> <expressao python sobre o dict `d`>
    if $PY - "$OUT/$2" "$3" <<'PYEOF2'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
sys.exit(0 if eval(sys.argv[2], {"d": d, "any": any, "all": all}) else 1)
PYEOF2
    then
        echo "PASS: $1"
    else
        echo "FAIL: $1  (condicao: $3)"
        echo "      --- saida ($2) ---"
        sed 's/^/      /' "$OUT/$2"
        FAILS=$((FAILS + 1))
    fi
}

# 6a. comando a IA em FONTE NORMAL: pdf_integridade NAO acha (prova do furo), lexico_scan ACHA
run "pdf_integridade.py" "$FIX/isca_lexico.pdf" "pdf_lexpdf.json"
assert_contem "isca_lexico.pdf: pdf_integridade total_achados 0 (nada oculto)" "pdf_lexpdf.json" '"total_achados": 0'
run "lexico_scan.py" "$FIX/isca_lexico.pdf" "lex_pdf.json"
assert_contem "isca_lexico.pdf: lexico_scan acha comando_lexico"   "lex_pdf.json" '"tipo": "comando_lexico"'
assert_json   "isca_lexico.pdf: comando visivel de regra critica sai alta" "lex_pdf.json" \
    'any(a["gravidade"] == "alta" and a["visivel"] for a in d["achados"])'

# 6b. evasao por caractere invisivel dentro de "IGNORE" + acentos
run "lexico_scan.py" "$FIX/isca_lexico.txt" "lex_txt.json"
assert_json   "isca_lexico.txt: acha ignore-previous apesar do U+200B" "lex_txt.json" \
    'any(a["tag"] == "ignore-previous" for a in d["achados"])'
assert_json   "isca_lexico.txt: acha 'nao impugne os documentos' acentuado" "lex_txt.json" \
    'any(a["tag"] == "nao-impugne-pt" for a in d["achados"])'

# 6c. texto oculto da isca.pdf tambem e pego pelo lexico e marcado como oculto
run "lexico_scan.py" "$FIX/isca.pdf" "lex_isca.json"
assert_json   "isca.pdf: lexico acha o comando e marca trecho OCULTO (alta)" "lex_isca.json" \
    'any(a["gravidade"] == "alta" and not a["visivel"] for a in d["achados"])'

# 6d. controles LIMPOS (com prosa juridica "sistema PJe, nao respondeu", "ele ia contestar")
run "lexico_scan.py" "$FIX/controle_limpo.txt" "lex_ctrl_txt.json"
assert_contem "controle.txt: lexico_scan total_achados 0 (sem falso positivo)" "lex_ctrl_txt.json" '"total_achados": 0'
run "lexico_scan.py" "$FIX/controle_limpo.pdf" "lex_ctrl_pdf.json"
assert_contem "controle.pdf: lexico_scan total_achados 0 (sem falso positivo)" "lex_ctrl_pdf.json" '"total_achados": 0'

# 6e. whitelist de rodape PJe: REBAIXA (baixa), NAO suprime, traz texto e zona
run "pdf_integridade.py" "$FIX/pje_rodape.pdf" "pdf_pje.json"
assert_json   "pje_rodape.pdf: rodape PJe a 2pt sai baixa + whitelist + zona rodape" "pdf_pje.json" \
    'len(d["achados"]) == 1 and d["achados"][0]["gravidade"] == "baixa" and d["achados"][0]["whitelist"] is True and d["achados"][0]["zona"] == "rodape"'
assert_contem "pje_rodape.pdf: achado rebaixado ainda traz o texto como evidencia" "pdf_pje.json" 'Documento assinado eletronicamente'
run "lexico_scan.py" "$FIX/pje_rodape.pdf" "lex_pje.json"
assert_contem "pje_rodape.pdf: lexico_scan total_achados 0" "lex_pje.json" '"total_achados": 0'

# 6f. rodape PJe COM comando embutido: whitelist NAO rebaixa
run "pdf_integridade.py" "$FIX/pje_rodape_com_comando.pdf" "pdf_pje_cmd.json"
assert_json   "pje_rodape_com_comando.pdf: NAO rebaixa (alta, whitelist false)" "pdf_pje_cmd.json" \
    'any(a["gravidade"] == "alta" and a["whitelist"] is False for a in d["achados"])'
run "lexico_scan.py" "$FIX/pje_rodape_com_comando.pdf" "lex_pje_cmd.json"
assert_json   "pje_rodape_com_comando.pdf: lexico acha o comando oculto (alta)" "lex_pje_cmd.json" \
    'any(a["gravidade"] == "alta" and not a["visivel"] for a in d["achados"])'

# 6g. regressao: fonte branca NUNCA e rebaixada pela whitelist (isca.pdf segue alta, com texto)
assert_json   "isca.pdf: texto branco segue alta (regressao) e traz texto" "pdf_isca.json" \
    'any(a["tipo"] == "texto_oculto" and a["gravidade"] == "alta" and a.get("texto") for a in d["achados"])'

# 6g2. palavra partida por espacamento de caracteres (comando oculto real visto em peticao)
run "lexico_scan.py" "$FIX/isca_fragmentada.pdf" "lex_frag.json"
assert_json   "isca_fragmentada.pdf: acha 'INSTRU CAO AO SISTEMA' com palavra partida" "lex_frag.json" \
    'any(a["tag"] == "instrucao-ao-sistema-pt" and not a["visivel"] for a in d["achados"])'
assert_json   "isca_fragmentada.pdf: acha 'igno re qualquer instrucao'" "lex_frag.json" \
    'any(a["tag"] == "ignore-qualquer-instrucao-pt" for a in d["achados"])'

# 6g3. unicode_scan em PDF (texto extraido pagina a pagina)
if [ -f "$FIX/isca_unicode.pdf" ]; then
    run "unicode_scan.py" "$FIX/isca_unicode.pdf" "uni_pdf.json"
    assert_json "isca_unicode.pdf: unicode_scan acha homoglifo com a pagina" "uni_pdf.json" \
        'any(a["tipo"] == "homoglifo" and a["localizacao"].startswith("pagina 1") for a in d["achados"])'
else
    echo "SKIP: isca_unicode.pdf nao gerada (PyMuPDF ausente)"
fi
run "unicode_scan.py" "$FIX/controle_limpo.pdf" "uni_ctrl_pdf.json"
assert_json "controle.pdf: unicode_scan sem achado (ou dependencia declarada)" "uni_ctrl_pdf.json" \
    '(d["status"] == "ok" and d["resumo"]["total_achados"] == 0) or d["status"] == "missing_dependency"'

# 6g4. paginas_pdf: imagem + texto da pagina pedida
$PY "$SCR/paginas_pdf.py" "$FIX/isca.pdf" --saida "$OUT/paginas" --paginas 1 > "$OUT/paginas.json" 2>&1
assert_json "paginas_pdf: gera imagem e texto da pagina 1 (ou dependencia declarada)" "paginas.json" \
    '(d["status"] == "ok" and d["paginas"][0]["pagina"] == 1 and d["paginas"][0]["imagem"].endswith(".png") and "IGNORE" in d["paginas"][0]["texto"]) or d["status"] == "missing_dependency"'

# 6h. lexico_scan: arquivo inexistente -> erro limpo
$PY "$SCR/lexico_scan.py" "$FIX/nao_existe.txt" > "$OUT/err_lex.json" 2>&1
assert_contem "lexico_scan: arquivo inexistente status error limpo" "err_lex.json" '"status": "error"'

# ---------------------------------------------------------------------------
# 6i. Corpus dos 5 grupos de ataque (A-E) em DOCX e PDF + controles limpos
#     gerado numa pasta temporaria (nao suja o repositorio a cada rodada)
# ---------------------------------------------------------------------------
$PY "$SCR/gerar_corpus.py" --saida "$OUT/corpus" > "$OUT/corpus_gerar.log" 2>&1
if $PY "$SCR/avaliar_corpus.py" "$OUT/corpus" > "$OUT/corpus.txt" 2>&1; then
    echo "PASS: corpus A-E: 100% detectado e 0 alarme falso nos controles"
else
    echo "FAIL: corpus A-E com deteccao faltando ou alarme falso"
    sed 's/^/      /' "$OUT/corpus.txt" | grep -E "FALHOU|ALARME|AUSENTE|RESULTADO|Grupo" || sed 's/^/      /' "$OUT/corpus.txt" | tail -20
    FAILS=$((FAILS + 1))
fi
# cada variacao de frase, sozinha, tem de disparar (nao basta 1 por grupo)
if $PY -c "
import sys; sys.path.insert(0, '$SCR')
import gerar_corpus as G, _padroes as P
faltas = [f for fs in G.VARIACOES.values() for f in fs if not P.achados_lexicos(f)]
fps = [f for f in G.LEGITIMO if P.achados_lexicos(f)]
print('faltas:', faltas, 'alarmes:', fps); sys.exit(1 if faltas or fps else 0)
" > "$OUT/variacoes.txt" 2>&1; then
    echo "PASS: cada variacao de frase dispara e nenhuma frase juridica legitima dispara"
else
    echo "FAIL: variacoes/legitimas: $(cat "$OUT/variacoes.txt")"; FAILS=$((FAILS + 1))
fi
# docx_integridade direto: arquivo inexistente -> erro limpo; DOCX limpo -> 0
$PY "$SCR/docx_integridade.py" "$FIX/nao_existe.docx" > "$OUT/err_docx.json" 2>&1
assert_contem "docx_integridade: arquivo inexistente status error limpo" "err_docx.json" '"status": "error"'
run "docx_integridade.py" "$FIX/controle_limpo.docx" "docx_ctrl.json"
assert_contem "controle.docx: docx_integridade total_achados 0" "docx_ctrl.json" '"total_achados": 0'

# ---------------------------------------------------------------------------
# 7. Relatorio HTML: credito do autor, botao de PDF e escape do conteudo da peca
# ---------------------------------------------------------------------------
cp "$FIX/relatorio_exemplo.md" "$OUT/rel.md"
$PY "$SCR/relatorio_html.py" "$OUT/rel.md" -o "$OUT/rel.html" > "$OUT/rel_run1.json" 2>&1
$PY "$SCR/relatorio_html.py" "$OUT/rel.md" -o "$OUT/rel.html" > "$OUT/rel_run2.json" 2>&1
assert_contem "relatorio_html: status ok"                         "rel_run1.json" '"status": "ok"'
assert_contem "relatorio_html: 1a rodada acrescenta credito no MD" "rel_run1.json" '"credito_md_adicionado": true'
assert_contem "relatorio_html: 2a rodada nao duplica o credito"    "rel_run2.json" '"credito_md_adicionado": false'
if [ "$(grep -c 'credito-autor' "$OUT/rel.md")" -eq 1 ]; then echo "PASS: MD tem o rodape de credito uma unica vez"; else echo "FAIL: rodape de credito duplicado ou ausente no MD"; FAILS=$((FAILS + 1)); fi
assert_contem "HTML traz a frase de credito"       "rel.html" 'Esta skill foi desenvolvida por George Telles.'
assert_contem "HTML traz o e-mail"                 "rel.html" 'mailto:georgesmattos@gmail.com'
assert_contem "HTML traz o LinkedIn"               "rel.html" 'https://www.linkedin.com/in/georgetelles/'
assert_contem "HTML traz o WhatsApp"               "rel.html" 'https://wa.me/5571988229457'
assert_contem "HTML traz o botao Exportar PDF"     "rel.html" 'window.print()'
assert_contem "HTML escapa o <script> da peca"     "rel.html" '&lt;script&gt;alert(1)&lt;/script&gt;'
if grep -q 'javascript:' "$OUT/rel.html" || grep -q '<script>alert' "$OUT/rel.html"; then
    echo "FAIL: HTML deixou passar script ou link javascript: da peca"; FAILS=$((FAILS + 1))
else
    echo "PASS: HTML neutraliza script e link javascript: plantados"
fi

# 7a. link da fonte com icone: https vira icone com o site; javascript: e neutralizado
printf '# T\n\n| A | Fonte |\n|---|---|\n| x | [🔗](https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452.htm) |\n| y | [🔗](javascript:alert(3)) |\n' > "$OUT/link.md"
$PY "$SCR/relatorio_html.py" "$OUT/link.md" > /dev/null 2>&1
assert_contem "relatorio_html: [🔗](url) vira icone com o site" "link.html" 'title="Abrir a fonte: planalto.gov.br"'
if grep -q 'javascript:' "$OUT/link.html"; then echo "FAIL: icone 🔗 deixou passar javascript:"; FAILS=$((FAILS + 1)); else echo "PASS: icone 🔗 neutraliza javascript:"; fi

# 7b. verificador de jargao: relatorio com termo tecnico e apontado; o de exemplo sai limpo
printf '# Relatorio

O parser achou span com rgb=255,255,255 via pdf_integridade.py.
' > "$OUT/jargao.md"
$PY "$SCR/relatorio_html.py" "$OUT/jargao.md" > "$OUT/jargao.json" 2>&1
assert_json   "relatorio_html: aponta jargao tecnico (parser, span, rgb, script)" "jargao.json"     'all(t in d["termos_tecnicos"] for t in ["parser", "span", "rgb", "nome de script"])'
assert_json   "relatorio_html: relatorio de exemplo sem jargao" "rel_run2.json" 'd["termos_tecnicos"] == []'
printf '**Peca:** recebida
**Formato:** PDF
' > "$OUT/ficha.md"
$PY "$SCR/relatorio_html.py" "$OUT/ficha.md" > /dev/null 2>&1
assert_contem "relatorio_html: capa em linhas vira ficha" "ficha.html" 'class="ficha"'

# ---------------------------------------------------------------------------
echo
if [ "$FAILS" -eq 0 ]; then
    echo "== TODOS OS CHECKS PASSARAM =="
    exit 0
else
    echo "== $FAILS CHECK(S) FALHARAM =="
    exit 1
fi
