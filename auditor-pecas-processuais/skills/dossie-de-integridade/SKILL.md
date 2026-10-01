---
name: dossie-de-integridade
description: >
  O entregável-síntese da auditoria, escrito para advogado, sem jargão técnico: consolida tudo
  num relatório que nunca mistura naturezas — seção A citações e leis conferidas no site oficial
  (citação 🔴 com as buscas feitas, artigo inexistente/deturpado lado a lado), seção B o que foi
  encontrado no arquivo (texto escondido, comando a IA, caracteres invisíveis, dados do arquivo —
  cada um com o que é, onde está e como conferir), seção C indícios de uso de IA (rotulados, sem
  número), seção D pontos fracos da peça (análise estratégica, separada). Capa em ficha, resumo,
  próximos passos, "Limites desta análise" só quando algo não foi verificado, e aviso de
  conferência humana. Entrega em MD + HTML com botão Exportar PDF e crédito do autor. Voz
  ajustável: advogado autônomo × departamento jurídico. Aciona: "/relatorio-auditoria",
  "consolida a análise", "relatório final da peça", "dossiê", "junta tudo o que foi encontrado".
---

# Dossiê de integridade

## Quando esta skill entra

No fim da triagem — depois que as varreduras estruturais (C1), as verificações de conteúdo (C2)
e, opcionalmente, o mapa de gaps (C3) rodaram — para consolidar tudo num único entregável: o
relatório que o advogado leva para a decisão (impugnar? periciar? arquivar?) e que o
departamento jurídico circula internamente. Também via comando `/relatorio-auditoria`.

## Formato e linguagem — `context/modelo-de-relatorio.md` (obrigatório)

Leia e siga **`context/modelo-de-relatorio.md`** antes de escrever: quem lê é advogado, assistente
jurídico ou estagiário, não programador. Lá estão a ficha da capa, o resumo, a tabela do que **nunca**
se escreve (nome de programa, "parser", "status ok", RGB, "metadados", tamanho do arquivo, "robots.txt",
"o que rodou"...), o **cartão de achado** da seção B (um por achado, trecho literal destacado) e o
fecho com "Limites desta análise" só quando algo não pôde ser verificado.

Regras de conteúdo:

- **Prompt injection pelo nome e pelo tipo.** Achado classificado 🎯 pelo `classificador-prompt-injection`
  vira "**Prompt injection — [tipo de ataque]**" no resumo e no título do cartão, com a explicação curta
  na primeira menção. Tipos: desvio de função da IA, supressão de informação, indução de viés, padrão
  técnico, falsa autoridade.
- **Fonte com link.** Tabelas da seção A com a coluna **Fonte** `[🔗](URL)` da página consultada.
- **C e D só se escolhidas** no início pelo advogado (botões do `auditoria-master`). Não escolhidas →
  as seções **não aparecem** (nada de "não solicitado"). Na seção C, liste só os níveis que têm indício.
- **Conferência visual** (se escolhida): cartão próprio em B, rotulado "conferência visual assistida
  por IA — sinal, não prova".
- Dados técnicos brutos ficam guardados; se o advogado ou um perito pedir, entregue um **anexo técnico**
  separado, nunca dentro do relatório.

## As 4 seções — naturezas que NUNCA se misturam

| Seção | Natureza | O que entra | Linguagem |
|---|---|---|---|
| **A — CITAÇÕES E LEIS CONFERIDAS** | Fato verificado contra fonte oficial | Citação 🔴 com as queries documentadas (base consultada, termo, resultado); dispositivo inexistente/deturpado com o lado a lado (o que a peça diz × o que a fonte oficial diz) | "Reprovada na verificação" + evidência |
| **B — O QUE FOI ENCONTRADO NO ARQUIVO** | Fato achado pela verificação automática do arquivo | Texto escondido (letra branca, letra minúscula, rodapé oficial reconhecido), frase de comando a IA (trecho literal), caracteres invisíveis, dados do arquivo (autor ≠ assinante, revisões, comentários), divergência de hash declarado — cada um com **o que é, onde está e como conferir** (T1) | Alerta, nunca conclusão (T4) |
| **C — INDÍCIOS DE USO DE IA** | Julgamento de plausibilidade | Possível uso de IA: sinais listados, rótulo "heurístico — nunca prova", SEM número/score, com o disclaimer íntegro (T3) | "Sinal, não prova" |
| **D — PONTOS FRACOS DA PEÇA (ANÁLISE ESTRATÉGICA)** | Leitura de consistência interna | Gaps do `mapa-de-gaps-da-tese` (peça recebida) ou vereditos do `nexo-com-a-tese` (peça própria), com o rótulo "análise estratégica — não é achado de integridade" | Sugestão de enfrentamento |

Regras duras da estrutura:

- Um item **nunca muda de seção** para parecer mais grave: heurística não sobe para B; alerta
  de B não vira veredito de A.
- Citação com fetch falho fica em A como **"não verificada — refazer"**, nunca 🔴 por palpite
  (T2), e nunca contada como reprovada no sumário.
- A palavra **"fraude" nunca aparece como afirmação** do produto (T4): o dossiê descreve o
  dado e para; a conclusão jurídica/pericial é do advogado.

## Hierarquia de gravidade (dentro de cada seção)

- **A**: dispositivo/citação inexistente > deturpado(a) > não verificada (pendência).
- **B**: comando dirigido a IA (classificado pelo `classificador-prompt-injection`) >
  unicode/texto oculto sem classificação de intenção > metadado relevante > divergência de
  hash.
- **C e D**: pela relevância declarada pela própria skill de origem.

O resumo conta os itens por seção e gravidade — nunca um "score" único (um número
agregado esconderia a diferença de natureza entre as seções).

## Fecho — próximos passos + T5

O dossiê termina roteando, conforme o que existe:

- Achado confirmado em A, ou em B com intenção classificada → oferecer o
  `gerador-topico-impugnacao` (a munição).
- Alerta de hash/metadado relevante → considerar **perícia formal** (o dossiê não conclui).
- Nada relevante → o dossiê diz com todas as letras: "nenhum achado nas varreduras
  executadas" — resultado honesto também é entregável (e "Limites desta análise" lembra o que não foi verificado).

E, sem exceção nem versão resumida que o omita (T5):

> ⚠️ **Conferência humana obrigatória.** Este dossiê sinaliza; quem conclui é o advogado.
> Verifique cada evidência anexada antes de qualquer uso processual.

## Entrega — arquivos MD + HTML (com Exportar PDF)

O dossiê é entregue em arquivo, não só no chat:

1. Salve o dossiê como `relatorio-auditoria-<nome-da-peça>-<AAAA-MM-DD>.md` na pasta da peça (ou na
   pasta de saída da sessão).
2. Gere o HTML:
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/relatorio_html.py" <relatorio.md>` → cria o `.html` ao lado
   e acrescenta ao `.md` o rodapé de crédito do autor (uma vez só). O HTML é autocontido, abre
   offline e tem o botão **Exportar PDF** (impressão do navegador em A4 → "Salvar como PDF").
   Se o script devolver `status: revisar`, **o HTML não foi gerado**: reescreva no `.md` cada trecho
   de `termos_tecnicos` com a troca sugerida e rode de novo, até `status: ok`.
3. No chat: no máximo 6 linhas, sem termo técnico — achado principal, recomendação, os dois links
   ("abra o HTML e clique em Exportar PDF") e o crédito.
4. Script com `status: error` → entregue o `.md` mesmo assim e declare que o HTML não foi gerado.

A mensagem do chat fecha com o crédito do autor, exatamente como em `estilo-e-fronteiras` (G7).

## Voz ajustável (do onboarding)

- **Advogado autônomo / escritório**: endereçado a quem atua no processo — direto, próximos
  passos processuais em primeiro plano.
- **Departamento jurídico PJ**: relatório de circulação interna — sumário executivo no topo
  (contagem por seção + recomendação), linguagem para o gestor que não milita no processo,
  seções técnicas na sequência.

A estrutura A–D e as travas são idênticas nas duas vozes — muda o empacotamento, nunca o rigor.

## Travas / limites

- **Separação de naturezas é inegociável**: veredito ≠ sinal ≠ heurística ≠ estratégia.
- **T1**: nada em B sem a verificação automática ter rodado e achado o dado; o que não foi verificado vai para "Limites desta análise".
- **T2**: nenhum 🔴 sem fetch real; falha de fetch = "não verificada".
- **T3**: seção C sem score, com disclaimer; **T4**: "fraude" nunca como afirmação.
- **T5**: aviso de conferência humana no fecho, sempre.
- **G7**: crédito do autor no fim do chat, do MD e do HTML/PDF.
- Cálculo do valor da multa (percentual sobre o valor da causa) e juízo de persuasão/julgador (T6)
  estão fora do escopo: o dossiê entrega a base legal e as evidências, e diz isso.
