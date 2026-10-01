---
name: conferencia-de-dispositivos
description: >
  CONFERÊNCIA-DE-DISPOSITIVOS — Extrai TODOS os dispositivos legais citados
  na peça em análise — a da parte contrária ou a sua, antes do protocolo — (lei
  nº + artigo + inciso/parágrafo + o teor que a peça atribui) e confere cada um
  em duas vias: local, contra os anexos verbatim do plugin (CPC 77/79-81 e CP 299/347) com comparação de espaço
  normalizado; remota, via WebFetch no Planalto para os demais diplomas.
  Classifica: ✅ existe e o teor bate · ⚠️ existe mas o teor citado está
  deturpado/parcial (lado a lado) · 🔴 inexistente (só após fetch da fonte) ·
  ⚠️ revogado/alterado (com a redação vigente). Sem fetch bem-sucedido o
  dispositivo fica "não verificado", nunca "inexistente" por palpite.
  Na peça recebida, 🔴/deturpado confirmado vira munição de impugnação; na
  própria, é dispositivo a corrigir antes do protocolo. Aciona: "esse artigo
  existe?", "confere a base legal da contestação", suspeita de lei inventada
  ou teor deturpado, roteamento do auditoria-master.
---

# CONFERÊNCIA-DE-DISPOSITIVOS — Conferência da base legal citada

## 1. O que esta skill faz

O par da `conferencia-de-citacoes`, apontado para a **lei**: pega a "base de lei criada" —
artigo que não existe no diploma, inciso inventado, parágrafo atribuído ao artigo errado — e o
caso mais sutil e mais frequente: o dispositivo **existe, mas o teor que a peça lhe atribui está
deturpado** (paráfrase que muda o sentido, recorte que omite a ressalva, redação revogada citada
como vigente). O dever de expor os fatos **conforme a verdade** (CPC art. 77, I — verbatim em
`context/cpc-litigancia-ma-fe.md`) alcança a transcrição fiel da norma.

**Regra de ouro (espelho da T2):** nenhum dispositivo é declarado 🔴 inexistente sem que a
fonte oficial tenha sido efetivamente aberta e varrida. Fetch que falhou = **não verificado**,
nunca "inexistente" por palpite.

## 2. FASE 1 — EXTRAÇÃO (exaustiva)

Varra a peça inteira e liste **TODOS** os dispositivos citados:

| # | Diploma (lei nº/sigla) | Artigo | Inciso/§ | Teor que a peça atribui (citação direta ou paráfrase) | Localização na peça |
|---|---|---|---|---|---|

- Inclui Constituição, códigos, leis, LCs, decretos, súmulas administrativas de órgão etc.
- **Registre o teor exatamente como a peça o apresenta** — entre aspas quando ela transcreve;
  marcado como "paráfrase" quando ela resume. É contra esse teor que a conferência roda.
- Dispositivo citado só por número, sem teor atribuído, também entra (a conferência vira só
  existência + vigência).

## 3. FASE 2 — CONFERÊNCIA EM DUAS VIAS

### Via local — diplomas anexados na família

| Diploma citado | Anexo local (fonte verbatim do Planalto) |
|---|---|
| CPC arts. 77, 79-81 e 96 | `context/cpc-litigancia-ma-fe.md` |
| CP arts. 299 e 347 | `context/cp-falsidade-fraude.md` |

Confira o teor atribuído contra o anexo com **comparação de espaço normalizado** (colapse
espaços múltiplos e quebras de linha antes de comparar — o Planalto quebra linha no meio da
frase; um grep ingênuo dá falso "não achei"). Ancore no **caput** do artigo, não na última
ocorrência do número.

### Via remota — todos os demais diplomas

1. Monte a URL do diploma no **Planalto** (`planalto.gov.br`) — para diplomas de numeração
   conhecida, a página consolidada; caso contrário, WebSearch `site:planalto.gov.br` primeiro.
2. **WebFetch real** na página do diploma. Capture status e conteúdo.
3. Localize o artigo/inciso/parágrafo citado no texto retornado (mesma normalização de espaço).
4. **Rigor T2 espelhado:** sem fetch bem-sucedido (403/timeout/página incompleta), o
   dispositivo fica **⬜ NÃO VERIFICADO** com a instrução de conferência manual — nunca 🔴.
5. Atenção à **vigência**: o Planalto marca "(Revogado)", "(Redação dada pela Lei nº ...)" —
   capture essas anotações, elas decidem a classificação ⚠️ revogado/alterado.

## 4. FASE 3 — CLASSIFICAÇÃO

| Status | Quando emitir |
|---|---|
| ✅ **EXISTE E O TEOR BATE** | Dispositivo localizado na fonte + teor atribuído fiel (literal ou paráfrase que preserva o sentido e as ressalvas) |
| ⚠️ **TEOR DETURPADO/PARCIAL** | Dispositivo existe, mas o teor citado diverge — **mostrar lado a lado** (tabela abaixo) |
| ⚠️ **REVOGADO/ALTERADO** | Dispositivo citado na redação antiga ou revogada — **citar a redação vigente** capturada na fonte |
| 🔴 **INEXISTENTE** | Artigo/inciso/parágrafo **não existe no diploma** — só após fetch bem-sucedido da fonte oficial com varredura do texto |
| ⬜ **NÃO VERIFICADO** | Fetch falhou — falha técnica declarada, nunca convertida em veredito |

Lado a lado obrigatório para todo ⚠️ deturpado:

```markdown
| O que a peça atribui | O que a fonte oficial diz | Divergência |
|---|---|---|
| "..." | "..." (fonte: URL/anexo) | [omite ressalva do § X / troca "poderá" por "deverá" / ...] |
```

## 5. FASE 4 — SAÍDA E ROTEAMENTO

```markdown
## Dispositivos da peça [recebida | própria] — [N] extraídos

| # | Dispositivo | Status | Evidência | Fonte | Ação |
|---|---|---|---|---|---|

**Resumo:** ✅ N · ⚠️ deturpado N · ⚠️ revogado N · 🔴 N · ⬜ N
```

Coluna **Fonte**: `[🔗](URL)` da página oficial aberta (ex.: a lei no Planalto); anexo local →
"anexo do plugin"; sem página aberta → "—".

**🔴 inexistente confirmado e ⚠️ deturpado confirmado → munição:** anexe a evidência (fonte
aberta + lado a lado) e roteie para o `gerador-topico-impugnacao` — o fundamento do tópico é o
mesmo padrão da citação inventada (CPC 77, I + 80 — dever de veracidade; casos-âncora em
`context/casos-ancora-sancoes.md`). ⬜ e ⚠️ revogado saem com recomendação de conferência
manual antes de uso na resposta.

## 6. Fallback MCP (opcional, nunca dependência)

**firecrawl** MCP pode servir de fallback quando o WebFetch falhar no Planalto (anti-bot,
página longa truncada). Sem MCP, o fluxo roda stock — nunca falhe por ausência de MCP.

## Travas desta skill

- **T2 (espelhada para lei):** nenhum dispositivo recebe ✅/🔴 sem a fonte oficial aberta por
  fetch real (ou anexo verbatim local). Fetch falhou = ⬜ não verificado, nunca 🔴.
- **T6:** existência, vigência e fidelidade de teor — nunca se o argumento construído sobre o
  dispositivo convence (integridade × mérito).
- **T5:** toda entrega fecha com o aviso: *conferência assistida por IA — a leitura da fonte
  oficial e a conclusão jurídica final são responsabilidade exclusiva do advogado.*

**Cross-links:** achados consolidados no `dossie-de-integridade` · 🔴/deturpado confirmado →
`gerador-topico-impugnacao` · anexos locais: `context/cpc-litigancia-ma-fe.md` ·
`context/cp-falsidade-fraude.md`.
