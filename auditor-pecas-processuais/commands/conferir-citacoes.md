---
description: Só a camada de citações — cada súmula, tema e acórdão da peça (adversária ou sua) conferido com fetch real na fonte.
---

# /conferir-citacoes

Extrai **todas** as citações de jurisprudência da peça (a recebida ou a sua) e confere cada uma contra a
fonte oficial, com o motor anti-alucinação do plugin: WebFetch real na URL, número do processo na
página, trecho de ementa presente. Status ✅ VALIDADA · ⚠️ PARCIAL · 🔴 NÃO ENCONTRADA · ⬜ NÃO
VERIFICADA (falha técnica de fetch — nunca vira 🔴 por palpite) — **nunca ✅ sem fetch
bem-sucedido** (trava T2).

**Skill a acionar:** `conferencia-de-citacoes`

Complementos no mesmo passo: `conferencia-de-dispositivos` (artigos/leis citados conferidos contra
fonte oficial — pega "base de lei criada" e teor deturpado).

Na peça recebida, um 🔴 confirmado é munição (na sua, é citação a corrigir antes do protocolo): o padrão de sanção já está consolidado (TST 1% · TJ/PR 2% · TJSC ·
TSE — multa + ofício à OAB/MPF por padrão, CPC arts. 79-81; ver `context/casos-ancora-sancoes.md`). Para transformar em
tópico de peça: `gerador-topico-impugnacao`.
