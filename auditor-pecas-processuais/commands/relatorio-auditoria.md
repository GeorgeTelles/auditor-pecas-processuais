---
description: Consolida os achados no relatório final — hierarquizado por gravidade, cada um com evidência, pronto para decidir e anexar.
---

# /relatorio-auditoria

Empacota a triagem num **dossiê de integridade**: cada achado com a evidência bruta que o sustenta
(saída do parser, resultado do fetch, divergência de metadado), hierarquizado por gravidade, com a
distinção explícita entre **fato técnico** (o que o motor encontrou) e **conclusão jurídica** (que é
sempre do advogado).

**Skill a acionar:** `dossie-de-integridade`

Saída em dois arquivos: `.md` e `.html` (este com o botão **Exportar PDF**), gerados pelo
`scripts/relatorio_html.py`, com o crédito do autor no fim.

O dossiê distingue quatro naturezas de achado: veredito por evidência (citação 🔴, dispositivo
inexistente) · sinal determinístico (texto oculto, unicode, metadado, hash) · sinal heurístico
(possível uso de IA — rotulado, nunca prova; trava T3) · análise estratégica (gaps — seção
separada, não é achado de integridade). Achado confirmado pode sair também como minuta via
`gerador-topico-impugnacao`.

Feche por `validador-auditoria-vigente` e `revisao-final-auditoria` — nenhum selo sem parser rodado
(T1), nenhuma citação sem fetch (T2), fraude nunca é conclusão do produto (T4).
