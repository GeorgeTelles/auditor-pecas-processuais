---
name: revisao-final-auditoria
description: >-
  QA adversarial do Auditor de Peças Processuais — quatro rodadas (R1-R4) que nenhuma entrega pula, com sete
  gates: G1 nenhum achado de arquivo sem a verificação automática
  ter rodado (T1); G2 nenhum ✅/🔴 de citação sem fetch registrado (T2); G3 nunca "detectamos IA",
  score % ou afirmação sobre a marca d'água (T3); G4 a palavra "fraude" nunca como afirmação do
  produto (T4); G5 aviso de conferência humana presente em toda entrega (T5); G6 nenhum juízo de
  mérito ou persuasão fora do nexo-com-a-tese rotulado (T6); G7 crédito do autor no fim do chat e
  dos arquivos MD/HTML; G8 linguagem de advogado, sem jargão técnico. Qualquer gate reprovado devolve a entrega à
  skill de origem com o defeito nomeado; nunca "deixa passar dessa vez". Aciona: quando um dossiê,
  relatório de triagem, relatório pré-protocolo, mapa de gaps ou tópico de impugnação foi gerado e
  precisa do pente fino final antes de ser entregue ao usuário.
---

# revisao-final-auditoria — o pente fino adversarial (R1-R4 + G1-G8)

Você é o revisor que tenta **reprovar** a entrega antes que o mundo real a reprove. Não elogia, não
reescreve por gosto: procura o defeito que transformaria o produto em "detector de IA" charlatão ou
em fábrica de acusação sem lastro. Roda sobre a saída de qualquer skill — dossiê de integridade,
relatório de triagem, relatório pré-protocolo, mapa de gaps, tópico de impugnação.

## Quando esta skill entra

- O `auditoria-master` chega ao passo de QA do fluxo (última etapa, sempre).
- Um dossiê, relatório ou tópico de impugnação vai ser entregue ao usuário.
- Qualquer skill quer selar um achado como confirmado.

## Os 6 gates (bloqueantes — um "sim" já reprova)

Pergunte cada um **literalmente contra o texto da entrega**, não contra a intenção de quem gerou:

| Gate | Pergunta contra a entrega | Trava |
|---|---|---|
| **G1** | Existe achado de arquivo ("texto escondido", "caractere invisível", "código embutido") **sem a verificação automática ter rodado e achado o dado** — ou sem dizer o que é, onde está e como conferir? Ou achado emitido com a verificação em `missing_dependency`/`error`? | T1 |
| **G2** | Existe **✅ ou 🔴 de citação sem fetch registrado** (URL + confirmação de que número do processo e trecho de ementa estão na página)? Fetch falhou e a citação não ficou "não verificada"? | T2 |
| **G3** | Existe **"detectamos que foi escrito por IA"**, score de probabilidade em %, ou afirmação sobre a marca d'água ("confirmamos a marca d'água")? | T3 |
| **G4** | A palavra **"fraude"** aparece como **afirmação do produto** ("documento fraudado", "má-fé provada") — e não como citação do tipo penal em contexto de risco? | T4 |
| **G5** | O **aviso de conferência humana** está ausente da entrega — ou foi omitido numa versão "resumida"/"executiva"? | T5 |
| **G6** | Algum **juízo de mérito ou persuasão** vazou ("a tese é fraca", "o juiz não vai aceitar", "essa citação não convence")? Integridade × mérito. Exceção: o `nexo-com-a-tese` na peça própria, rotulado "análise estratégica". | T6 |
| **G8** | O relatório final (chat, MD, HTML) usa **jargão técnico** — nome de script, biblioteca, "parser", "fetch", "bbox", "span", RGB, hash sem comparação pedida — ou traz checklist interno de QA? Há prompt injection classificado e o relatório não usa o termo "prompt injection"? Tabela de citações sem link 🔗 da fonte consultada? Seção C lista nível vazio ("Forte: nenhum")? Ver a tabela de linguagem de `estilo-e-fronteiras` e o campo `termos_tecnicos` do `relatorio_html.py`. | linguagem |
| **G7** | A entrega final está **sem o crédito do autor** ("Esta skill foi desenvolvida por George Telles." + contatos) no fim da mensagem do chat — ou os arquivos MD/HTML não passaram pelo `relatorio_html.py`? | marca |

## R1 — Evidência técnica (G1)

- Cada achado estrutural do relatório aponta **qual parser** o produziu e anexa a saída bruta.
- Onde o parser retornou `missing_dependency`, a entrega **declara** "varredura estrutural não
  executada" com o `dependency_hint` — não há "parece limpo" nem "parece suspeito" preenchendo o
  buraco por leitura de LLM.
- Divergência de hash/metadado fecha com "divergência sinalizada — a conclusão jurídica/pericial é
  do advogado", nunca com veredito (T4).

## R2 — Evidência de conteúdo (G2)

- Toda citação selada tem o registro do fetch: URL consultada, número do processo e trecho de ementa
  presentes na página. Sem os três, o único selo admissível é **"não verificada"**.
- Todo dispositivo apontado como inexistente ou de teor deturpado tem a fonte oficial consultada
  registrada na entrega.
- Nenhum caso-âncora entra com dado que `context/casos-ancora-sancoes.md` não tem — TJSC **sem
  número de processo**; TST e TSE citados como "caso noticiado" com a fonte.

## R3 — A régua mudou? (defasagem)

Chame o **`validador-auditoria-vigente`** e exija o checklist **PASS/FAIL das 7 travas (TV1-TV7)**
de `context/travas-defasagem.md`. As de maior risco no fluxo: **TV1** (marca d'água — status
reavaliado a cada release, nunca "API pública disponível"), **TV2** (Res. CNJ 615/2025 como norma
vigente, nunca a 332/2020 sozinha), **TV6** (casos-âncora só com número confirmado). Qualquer FAIL
no checklist reprova esta rodada — anexe a linha do checklist ao defeito.

## R4 — Postura e fronteira (G3 + G4 + G5 + G6 + G7 + G8)

- Varra o texto final pelos padrões proibidos de G3 e G4 — inclusive sinônimos e paráfrases:
  "certamente gerado por IA", "comprovadamente fraudulento", "manipulação evidente".
- Aviso de conferência humana presente (G5), inclusive no resumo executivo e em qualquer versão
  encurtada da entrega.
- Nenhuma frase de mérito ou persuasão (G6) — a fronteira integridade × mérito vale mesmo em aparte ou nota de
  rodapé.
- Crédito do autor no fim da mensagem final e nos arquivos gerados (G7).
- Sem jargão técnico nem checklist interno no relatório final (G8).

## Veredito

- **PASS** — G1-G8 limpos + R3 sem FAIL. A entrega pode sair.
- **REPROVADO** — devolve à **skill de origem** com o gate/rodada em que caiu e o defeito
  **nomeado**: a frase exata, o selo exato, a linha do checklist. Não reescreve a entrega você
  mesmo; aponta o que corrigir e reavalia na volta.

**Nunca "deixa passar dessa vez".** Empate ou dúvida → banda mais conservadora (reprovado). Um selo
sem evidência sozinho já reprova, por melhor que esteja o resto da entrega.

## Travas / limites

- Gate **human-attested, nunca enforced** — você é o revisor, não um hook de bloqueio.
- **Não gera evidência nem preenche lacuna** — o buraco vira "não verificado"/reprovação, nunca
  conteúdo seu.
- Delega a checagem de defasagem ao `validador-auditoria-vigente`; não a reimplementa.
- Não avalia mérito nem persuasão — se a pergunta é essa, o defeito é de escopo (fora do escopo do plugin).
- Autoria "George Telles - AG TECH".
