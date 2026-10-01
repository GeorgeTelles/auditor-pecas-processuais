---
name: conferencia-de-citacoes
description: >
  CONFERÊNCIA-DE-CITAÇÕES — Extrai TODAS as citações de jurisprudência da
  peça em análise — a da parte contrária ou a sua, antes do protocolo — (súmula,
  tema, acórdão, REsp/RE/AgInt) e valida uma
  a uma com o motor anti-alucinação: quando a peça não declara URL (a
  maioria), busca a fonte oficial via WebSearch antes de validar; a validação
  é sempre WebFetch real com 3 evidências (número do processo na página,
  trecho citado presente, metadados batem). Status ✅ VALIDADA · ⚠️ PARCIAL ·
  🔴 NÃO ENCONTRADA · ⬜ NÃO VERIFICADA. Nunca emite ✅ sem fetch
  bem-sucedido; fetch que falhou vira "não verificada", nunca 🔴 por palpite.
  Na peça recebida, cada 🔴 vira candidato a munição de impugnação (padrão
  consolidado de sanção — casos-âncora); na própria, é citação a corrigir.
  Aciona: jurisprudência para conferir, suspeita de citação inventada,
  "valida as citações da contestação", "confere as minhas citações", "esse
  acórdão existe?", roteamento do auditoria-master ou do pre-protocolo.
---

# CONFERÊNCIA-DE-CITAÇÕES — Validação da jurisprudência citada

## 1. O que esta skill faz

Roda o mesmo rigor nas duas peças: na **recebida** (defesa) e na **sua**, antes do protocolo
(prevenção, acionada pelo `auditoria-pre-protocolo`). Cada súmula, tema, acórdão ou recurso citado
é extraído, localizado na fonte oficial e conferido por fetch real. Na peça própria, a voz muda:
🔴 é "citação a corrigir ou retirar", ⬜ é pendência — nada disso libera o protocolo. Citação inventada é padrão
consolidado de sanção em 4+ tribunais (TST 1% · TJ/PR 2% · TJSC · TSE R$ 2 mil + série de
condenações — ver `context/casos-ancora-sancoes.md`): um 🔴 confirmado aqui não é curiosidade,
é munição de impugnação.

**Fronteira (T6):** esta skill afere se a citação **existe e é fiel** — nunca se ela convence,
nunca como o juiz decidirá. Integridade, não mérito.

## 2. FASE 1 — EXTRAÇÃO (exaustiva, sem filtro de "obviamente real")

Varra a peça inteira e liste **TODAS** as citações de jurisprudência, uma linha por citação:

| # | Tipo | Tribunal | Número | Relator | Data | Órgão julgador | Trecho citado na peça | URL declarada | Localização na peça |
|---|---|---|---|---|---|---|---|---|---|

- **Tipo:** súmula, súmula vinculante, tema repetitivo/repercussão geral, acórdão, REsp, RE,
  AgInt, AgRg, EDcl, HC, MS, IRDR etc.
- **Nenhuma citação é pulada por "parecer famosa"** — súmula conhecida também entra: a
  deturpação de teor de julgado real é achado tão grave quanto a invenção.
- Campos que a peça não informa ficam vazios na tabela (nunca completados por memória).
- **URL declarada** é rara em peça — a coluna existe para o caso minoritário; a ausência de
  link **não** dispensa a validação, dispara a FASE 2.

## 3. FASE 2 — BUSCA DA FONTE (buscar → validar)

Para cada citação **sem URL declarada**, localize a fonte oficial antes de validar:

1. **WebSearch** priorizando fontes oficiais: `site:stj.jus.br`, `site:stf.jus.br`,
   `site:tst.jus.br`, portal do tribunal citado (endereços conferidos em
   `context/portais-oficiais-jurisprudencia.md`); agregadores (JusBrasil/Escavador) só como
   pista secundária, sempre marcados `AGREGADOR — conferir no tribunal`.
2. Monte queries com número do processo, e variantes com tribunal + relator + tema.
3. **Documente cada query tentada** — essa lista é requisito para poder emitir 🔴 na FASE 3.
4. Localizou URL candidata → segue para a validação. Não localizou em nenhuma query → registre
   as queries e siga para a FASE 3 com esse dossiê de busca.

## 4. FASE 3 — VALIDAÇÃO (WebFetch real, sem exceção)

Para CADA citação, com a URL (declarada ou localizada):

**Passo 1 — WebFetch real.** Capture HTTP status, conteúdo e redirecionamentos.

**Passo 2 — 3 evidências na página:**

| Evidência | Verificação |
|---|---|
| (a) Número do processo | Aparece literal no texto retornado? |
| (b) Trecho citado | O trecho que a peça transcreve aparece literal ou com diferenças mínimas (acentos/quebras)? |
| (c) Metadados | Órgão julgador, relator e data batem com o que a peça afirma? |

**Passo 3 — status:**

| Status | Quando emitir |
|---|---|
| ✅ **VALIDADA** | Fetch 200 + (a) + (b) + (c) todos presentes |
| ⚠️ **PARCIAL** | Fetch ok mas: trecho parafraseado · metadado diverge em 1 campo · só agregador, sem confirmação no oficial · página exige render JS |
| 🔴 **NÃO ENCONTRADA** | **Busca ativa documentada** (FASE 2) não localizou a citação nas fontes oficiais — as queries tentadas acompanham o achado |
| ⬜ **NÃO VERIFICADA** | Fetch falhou (403/404/timeout/anti-bot) e a busca não pôde ser concluída — falha técnica, não veredito |

**Regra de bloqueio (T2):** nunca ✅ sem fetch bem-sucedido com as 3 evidências. E a distinção
que sustenta o produto: **🔴 é afirmação positiva de ausência** — exige busca ativa que NÃO
encontrou, com as queries documentadas no relatório. Fetch que falhou por razão técnica **nunca**
vira 🔴 por palpite: fica ⬜ com a instrução "validação manual recomendada".

**Agregador com link para o tribunal:** faça o segundo fetch no oficial; confirmou → ✅ com
observação; divergiu → ⚠️ `agregador divergente do oficial`.

## 5. FASE 4 — SAÍDA

```markdown
## Citações da peça [recebida | própria] — [N] extraídas

| # | Citação (Tribunal · número) | Status | Evidência | Fonte | Ação |
|---|---|---|---|---|---|
| 1 | STJ · REsp ... | ✅ | fetch 200, nº + trecho + metadados | [🔗](URL da página aberta) | citação íntegra — mérito é outro exame |
| 2 | TJXX · ... | 🔴 | queries: [lista] — não localizada | — | candidato a munição → gerador-topico-impugnacao |

**Resumo:** ✅ N · ⚠️ N · 🔴 N · ⬜ N
```

Para cada 🔴: anexe as queries tentadas + a nota **"padrão consolidado de sanção — ver
casos-âncora (`context/casos-ancora-sancoes.md`)"** e roteie para o
`gerador-topico-impugnacao` (peça recebida) — ou marque "corrigir ou retirar antes do protocolo"
(peça própria). Cada ⚠️ e ⬜ sai com a recomendação de conferência manual antes de qualquer uso.

**Fonte:** a coluna leva `[🔗](URL)` da página em que a validação foi feita — a mesma do fetch. Sem
página aberta (⬜, 🔴 sem URL), "—". Agregador: `[🔗](URL) agregador`.

**Proibições absolutas:**
1. Nunca "completar" campo da citação (relator, data, órgão) com o que não apareceu na página.
2. Nunca "validada via busca", "via memória do modelo" ou "via Google" — só via WebFetch real.
3. Nunca silenciar 🔴 ou ⬜ — aparecem destacados no resumo, com a ação recomendada.
4. Página que exige JavaScript ou captcha → ⚠️ "validação manual recomendada", nunca ✅ por chute.

## 6. Fallback MCP (opcional, nunca dependência)

Se o usuário tiver **firecrawl** MCP configurado, use como fallback quando o WebFetch nativo
falhar por anti-bot ou página JS-heavy. Sem MCP, o fluxo roda stock com WebSearch + WebFetch —
**nunca** falhe por ausência de MCP.

## Travas desta skill

- **T2:** nenhuma citação recebe ✅/🔴 sem WebFetch real. Fetch falhou = ⬜ não verificada,
  nunca 🔴 por palpite; 🔴 exige busca ativa documentada que não encontrou.
- **T6:** integridade, não mérito — se a citação é real e fiel, esta skill não opina se ela
  convence (integridade × mérito). Nexo com a tese só pelo `nexo-com-a-tese`, na peça própria.
- **T5:** toda entrega fecha com o aviso: *validação assistida por IA — a conferência humana
  final, especialmente do inteiro teor, é responsabilidade exclusiva do advogado.*

**Cross-links:** achados consolidados no `dossie-de-integridade` · 🔴 confirmado →
`gerador-topico-impugnacao` (peça recebida) · na peça própria, o resultado alimenta o checklist do
`auditoria-pre-protocolo` e, a pedido, o `nexo-com-a-tese` · portais de busca:
`context/portais-oficiais-jurisprudencia.md`.
