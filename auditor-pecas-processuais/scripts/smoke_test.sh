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

# 6h. lexico_scan: arquivo inexistente -> erro limpo
$PY "$SCR/lexico_scan.py" "$FIX/nao_existe.txt" > "$OUT/err_lex.json" 2>&1
assert_contem "lexico_scan: arquivo inexistente status error limpo" "err_lex.json" '"status": "error"'

# ---------------------------------------------------------------------------
echo
if [ "$FAILS" -eq 0 ]; then
    echo "== TODOS OS CHECKS PASSARAM =="
    exit 0
else
    echo "== $FAILS CHECK(S) FALHARAM =="
    exit 1
fi
