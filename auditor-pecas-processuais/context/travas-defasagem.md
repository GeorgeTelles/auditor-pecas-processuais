# Travas de defasagem — o `validador-auditoria-vigente`

> Distintas das travas invioláveis (`travas-auditoria.md`): estas pegam "o fato mudou e o modelo
> não sabe" — a marca d’água é de 6 dias antes do levantamento, a norma do CNJ foi atualizada, o texto
> de lei tem de bater com a captura. Cada uma tem origem no levantamento de 18/08/2026.

| # | Trava | Origem |
|---|---|---|
| **TV1** | **Marca d'água Anthropic:** existe (12/08/2026), só Claude pós-02/08/2026, edição pesada remove, ruim em texto curto/factual, **API de terceiros NÃO pública** — reavaliar a cada release; qualquer mudança é 🔴 até confirmada em fonte primária | levantamento 18/08/2026 |
| **TV2** | **Res. CNJ 615/2025 atualizou a 332/2020** — citar a 615 como norma vigente de IA no Judiciário, nunca a 332 sozinha | levantamento 18/08/2026 |
| **TV3** | **CPC arts. 77, 79-81 verbatim** contra `context/` no build — conferir por fetch no Planalto, não só por busca | levantamento 18/08/2026 |
| **TV4** | **CP arts. 299 e 347 verbatim** contra `context/` no build (fetch no Planalto) | levantamento 18/08/2026 |
| **TV5** | Números de acurácia de detectores comerciais (GPTZero etc.) são **inconsistentes entre estudos** — nunca citar acurácia de vendor como fato | levantamento 18/08/2026 |
| **TV6** | Casos-âncora só com o que está confirmado: TRT-8 ATOrd 0001062-55.2025.5.08.0130 (10%, ~R$ 84,2 mil) · TJ/PR 0108267-74.2025.8.16.0000 (2%) · TST 6ª Turma (1%) · TSE (R$ 2 mil + 9 condenações). **TJSC sem número de processo coletado → citar sem número ou localizar no build** | levantamento 18/08/2026 |
| **TV7** | Grep de frase literal contra `context/` normaliza espaço (Planalto quebra linha no meio da frase); âncora de caput, não última ocorrência | normalização do Planalto |

**Status de TV3/TV4 neste build (19/08/2026): CUMPRIDAS.** Os anexos `cpc-litigancia-ma-fe.md` e
`cp-falsidade-fraude.md` deste `context/` foram copiados verbatim de capturas verificadas do
Planalto (Lei nº 13.105/2015 e Decreto-Lei nº 2.848/1940), com verificação por grep de trecho literal
contra a fonte + controle negativo.
