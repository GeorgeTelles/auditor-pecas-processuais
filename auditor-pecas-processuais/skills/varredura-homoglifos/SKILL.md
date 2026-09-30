---
name: varredura-homoglifos
description: >
  VARREDURA-HOMOGLIFOS — Camada 1 do motor de integridade estrutural. Usa o
  parser local unicode_scan.py (.txt/.md/.docx) com foco nos achados de
  homóglifo e mistura de scripts: caracteres de alfabetos diferentes visualmente
  idênticos (ex.: "а" cirílico no lugar do "a" latino), que fazem uma palavra
  parecer igual na tela mas virar outra string para a máquina — escapando de
  busca por palavra-chave e de conferência automática de citações. Vetor
  tecnicamente maduro em segurança da informação, sem caso brasileiro
  documentado em peça processual: proteção preventiva, apresentada como tal.
  Sinaliza — nunca conclui fraude. Aciona: "homóglifo", "homoglifos", "caractere
  cirílico", "mistura de alfabetos", "letra trocada invisível", "varredura de
  homóglifos".
---

# VARREDURA-HOMOGLIFOS — a letra que parece igual mas é outra

## 1. Escopo

Detecta, por varredura determinística, **homóglifos**: caracteres de alfabetos
diferentes que são visualmente idênticos ou quase idênticos —

| Parece | É | Codepoint |
|---|---|---|
| a | а (cirílico) | U+0430 |
| e | е (cirílico) | U+0435 |
| o | о (cirílico) | U+043E |
| c | с (cirílico) | U+0441 |
| p | р (cirílico) | U+0440 |

Uma palavra com um único caractere trocado **parece idêntica na tela, mas é
outra string para a máquina**. Efeito prático numa peça processual:

1. **Escapa de filtro e busca por palavra-chave** — Ctrl+F, sistema do
   tribunal e ferramenta de revisão da parte não encontram o termo ("réu" com
   "е" cirílico não bate com "réu" digitado no teclado).
2. **Quebra conferência automática** de citações, números de processo e nomes —
   a comparação textual falha silenciosamente.
3. **Pode mascarar termo sensível** para passar por triagem automatizada.

**Quem decide é o parser** (`scripts/unicode_scan.py`) — nunca a impressão de
leitura do LLM.

## 2. Honestidade obrigatória — o estágio real deste vetor

O ataque por homóglifo é **tecnicamente maduro em segurança da informação**
(ataques homográficos em domínios e phishing são documentados há anos), mas
**não há caso brasileiro documentado de homóglifo em peça processual** até esta
versão. A apresentação correta é: **"proteção contra a próxima geração do
ataque"** — nunca "isso já aconteceu no seu tribunal". Vender a verdade é parte
do produto: o vetor anterior (fonte branca) também não tinha precedente — até
ter (TRT-8, `context/casos-ancora-sancoes.md` §1).

## 3. Input

| Campo | Obrigatório | Observação |
|---|---|---|
| `arquivo` | sim | `.txt`, `.md` ou `.docx` |
| Peça em PDF | — | Salvar o texto extraído em `.txt` e rodar sobre ele — o parser varre texto |

## 4. Processamento

### Passo 1 — Executar o parser (do root do plugin)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/unicode_scan.py" <arquivo>
```

É a **mesma execução** da `varredura-unicode-invisivel` — se as duas skills
rodarem na mesma triagem, o parser roda uma vez e cada skill consome a sua
família de achados. Retorno em JSON: `parser`, `versao`, `arquivo`, `status`,
`motor_usado`, `achados[]` (`tipo`, `gravidade`, `evidencia`, `localizacao`),
`resumo.total_achados`, `dependency_hint`.

### Passo 2 — Tratar o status (regra T1, sem exceção)

| `status` | Conduta |
|---|---|
| `ok` | Prosseguir para o Passo 3 |
| `missing_dependency` | DECLARAR: "varredura estrutural não executada" + exibir o `dependency_hint`. NUNCA improvisar o achado "no olho" |
| `error` | Reportar o erro literal do parser |
| `formato_nao_suportado` | Informar os formatos aceitos (`.txt`/`.md`/`.docx`) |

Motores possíveis deste parser: `stdlib` (sempre disponível) e
`stdlib+confusable_homoglyphs` (lib opcional) — não há modo degradado.

### Passo 3 — Focar os achados de homóglifo/mistura de scripts

Desta execução interessam os achados de caractere confusável e de palavra com
mistura de scripts (latino + cirílico/grego/outro). Tags, zero-width e bidi
pertencem à skill irmã `varredura-unicode-invisivel` — apontar, sem duplicar.

### Passo 4 — Evidência + leitura

Para CADA achado, anexar: caractere, codepoint, script de origem, **palavra
afetada** e contexto (`localizacao`). Leitura em duas hipóteses, sem escolher
veredito: (a) colagem de fonte digital que já continha o caractere; (b)
ofuscação deliberada para escapar de busca/conferência. Se a palavra afetada
estiver dentro de **citação de jurisprudência ou dispositivo de lei**, avisar
que a conferência automática daquela citação fica comprometida e rotear a
verificação para `conferencia-de-citacoes` / `conferencia-de-dispositivos`.

## 5. Output

```markdown
## 🔍 Varredura de homóglifos — {{arquivo}}

**Parser:** unicode_scan.py v{{versao}} · **Status:** {{status}}
**Achados (homóglifo/mistura de scripts):** {{n}}

| # | Palavra afetada | Caractere | Codepoint | Script | Contexto |
|---|---|---|---|---|---|
| 1 | "execução" | е | U+0435 | cirílico | pág./trecho |

### Leitura

- O termo acima NÃO é encontrável por busca padrão (Ctrl+F/sistema) — teste
  prático que o advogado pode reproduzir na hora.
- Hipóteses de origem: colagem de fonte digital × ofuscação deliberada — a
  conclusão é do advogado.

➡️ Todo achado segue para o `dossie-de-integridade`.

> ⚠️ Conferência humana final é do advogado. Esta varredura sinaliza; não conclui.
```

Sem achados: reportar "0 achados de homóglifo". Lembrar que este é o vetor SEM
precedente brasileiro documentado — ausência é o esperado hoje; a varredura
existe para o dia em que deixar de ser.

## 6. O que esta skill nunca faz

1. Nunca declara homóglifo sem o parser ter retornado caractere + codepoint + palavra afetada (T1).
2. Nunca conclui ofuscação deliberada — apresenta as duas hipóteses e entrega a conclusão ao advogado (T4).
3. Nunca apresenta o vetor como "já documentado em tribunal brasileiro" — a honestidade do §2 é parte da skill.

## 7. Travas desta skill

| Trava | Aplicação aqui |
|---|---|
| **T1** | Achado só existe com o parser rodado + caractere/codepoint/palavra anexados; `missing_dependency` → "varredura estrutural não executada" + `dependency_hint` |
| **T4** | Homóglifo achado = alerta técnico com duas hipóteses de origem; a conclusão (inclusive sobre má-fé) é jurídica, do advogado |
| **T5** | ⚠️ Conferência humana final é do advogado — todo relatório sai com este aviso |

## 8. Integração

- **Upstream:** `auditoria-master` · `auditoria-pre-protocolo`
- **Downstream:** `conferencia-de-citacoes` / `conferencia-de-dispositivos` (quando o homóglifo cai em citação ou dispositivo) · **`dossie-de-integridade` — todo achado termina lá**
- **Irmã:** `varredura-unicode-invisivel` (mesma execução do parser, foco em invisíveis)
