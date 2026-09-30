---
name: dossie-de-integridade
description: >
  O entregável-síntese da triagem: consolida tudo num dossiê que nunca mistura naturezas —
  seção A vereditos por evidência (citação 🔴 com queries documentadas, dispositivo
  inexistente/deturpado com o lado a lado), seção B sinais determinísticos (texto oculto com
  RGB/tamanho, unicode com codepoints, metadados, hash — cada um com a evidência bruta do
  parser anexada), seção C sinais heurísticos (possível uso de IA — rotulado, sem número, com
  disclaimer), seção D análise estratégica (gaps — separada, rotulada como não-integridade).
  Capa declara o que rodou e o que NÃO rodou (parser sem dependência = dito com todas as
  letras); hierarquia de gravidade por seção; fecho com próximos passos (tópico de impugnação,
  perícia formal ou "nenhum achado") e aviso de conferência humana. Voz ajustável: advogado
  autônomo × departamento jurídico. Aciona: "/relatorio-auditoria", "consolida a análise",
  "relatório final da peça", "dossiê da triagem", "junta tudo o que foi encontrado".
---

# Dossiê de integridade

## Quando esta skill entra

No fim da triagem — depois que as varreduras estruturais (C1), as verificações de conteúdo (C2)
e, opcionalmente, o mapa de gaps (C3) rodaram — para consolidar tudo num único entregável: o
relatório que o advogado leva para a decisão (impugnar? periciar? arquivar?) e que o
departamento jurídico circula internamente. Também via comando `/relatorio-auditoria`.

## Capa — honestidade de escopo antes de qualquer achado

A capa declara, antes de qualquer resultado:

- **Peça analisada**: arquivo (nome, formato, páginas) ou texto colado; data da análise.
- **O que RODOU**: cada varredura executada com status `ok` do parser; cada verificação de
  citação/dispositivo com fetch realizado.
- **O que NÃO rodou — e por quê**: parser com `missing_dependency` → o dossiê DIZ ("varredura
  estrutural não executada — instale a dependência indicada e rode novamente"); texto colado
  sem arquivo → varreduras estruturais de PDF/DOCX não se aplicam (declarado); fetch
  indisponível → citações ficam "não verificadas". Silêncio sobre o que não rodou é proibido —
  ausência de varredura nunca vira "nada encontrado" (T1).

## As 4 seções — naturezas que NUNCA se misturam

| Seção | Natureza | O que entra | Linguagem |
|---|---|---|---|
| **A — VEREDITOS POR EVIDÊNCIA** | Fato verificado contra fonte | Citação 🔴 com as queries documentadas (base consultada, termo, resultado); dispositivo inexistente/deturpado com o lado a lado (o que a peça diz × o que a fonte oficial diz) | "Reprovada na verificação" + evidência |
| **B — SINAIS DETERMINÍSTICOS** | Dado bruto do parser | Texto oculto (RGB/tamanho/opacidade, com zona e whitelist de rodapé PJe), padrão léxico de comando a IA (regra, trecho, visível × oculto), unicode invisível (codepoints), metadados (autor ≠ assinante, revisões, comentários), divergência de hash — cada um com a saída bruta do parser anexada (T1) | Alerta técnico, nunca conclusão (T4) |
| **C — SINAIS HEURÍSTICOS** | Julgamento de plausibilidade | Possível uso de IA: sinais listados, rótulo "heurístico — nunca prova", SEM número/score, com o disclaimer íntegro (T3) | "Sinal, não prova" |
| **D — ANÁLISE ESTRATÉGICA** | Leitura de consistência interna | Gaps do `mapa-de-gaps-da-tese` (peça recebida) ou vereditos do `nexo-com-a-tese` (peça própria), com o rótulo "análise estratégica — não é achado de integridade" | Sugestão de enfrentamento |

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

O sumário da capa conta os itens por seção e gravidade — nunca um "score" único (um número
agregado esconderia a diferença de natureza entre as seções).

## Fecho — próximos passos + T5

O dossiê termina roteando, conforme o que existe:

- Achado confirmado em A, ou em B com intenção classificada → oferecer o
  `gerador-topico-impugnacao` (a munição).
- Alerta de hash/metadado relevante → considerar **perícia formal** (o dossiê não conclui).
- Nada relevante → o dossiê diz com todas as letras: "nenhum achado nas varreduras
  executadas" — resultado honesto também é entregável (e a capa lembra o que não rodou).

E, sem exceção nem versão resumida que o omita (T5):

> ⚠️ **Conferência humana obrigatória.** Este dossiê sinaliza; quem conclui é o advogado.
> Verifique cada evidência anexada antes de qualquer uso processual.

## Voz ajustável (do onboarding)

- **Advogado autônomo / escritório**: endereçado a quem atua no processo — direto, próximos
  passos processuais em primeiro plano.
- **Departamento jurídico PJ**: relatório de circulação interna — sumário executivo no topo
  (contagem por seção + recomendação), linguagem para o gestor que não milita no processo,
  seções técnicas na sequência.

A estrutura A–D e as travas são idênticas nas duas vozes — muda o empacotamento, nunca o rigor.

## Travas / limites

- **Separação de naturezas é inegociável**: veredito ≠ sinal ≠ heurística ≠ estratégia.
- **T1**: nada em B sem a saída bruta do parser; o que não rodou é declarado na capa.
- **T2**: nenhum 🔴 sem fetch real; falha de fetch = "não verificada".
- **T3**: seção C sem score, com disclaimer; **T4**: "fraude" nunca como afirmação.
- **T5**: aviso de conferência humana no fecho, sempre.
- Cálculo do valor da multa (percentual sobre o valor da causa) e juízo de persuasão/julgador (T6)
  estão fora do escopo: o dossiê entrega a base legal e as evidências, e diz isso.
