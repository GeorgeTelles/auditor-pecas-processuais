# Portais oficiais de jurisprudência — onde a `conferencia-de-citacoes` busca a fonte

> Usado na FASE 2 (busca da fonte) da `conferencia-de-citacoes`. Endereço de portal é ponto de
> partida para localizar o julgado, **nunca** prova de validação: o selo continua exigindo WebFetch
> real na página do julgado, com as 3 evidências (trava T2).
>
> **Conferência dos endereços: 30/09/2026**, por requisição HTTP a partir da máquina de build. Um
> portal que não respondeu **não está necessariamente fora do ar**: pode bloquear robô, exigir
> JavaScript ou recusar conexão de fora do país. Reconfira a cada release.

## Tribunais superiores

| Tribunal | Portal de busca | Conferência 30/09/2026 | Busca por WebSearch |
|---|---|---|---|
| STF | `https://jurisprudencia.stf.jus.br/pages/search` | ✅ respondeu (HTTP 202) | `site:stf.jus.br` |
| STJ | `https://scon.stj.jus.br/SCON/` | ⚠️ HTTP 403 (bloqueia robô) — use WebSearch + fetch na página do acórdão | `site:stj.jus.br` · `site:scon.stj.jus.br` |
| TST | `https://jurisprudencia.tst.jus.br/` | ✅ respondeu (HTTP 200) | `site:tst.jus.br` |
| TST — súmulas | `https://www.tst.jus.br/sumulas` (redireciona para a busca de súmulas do portal acima) | ✅ respondeu (HTTP 200) | `site:tst.jus.br súmula` |

## Tribunais Regionais Federais

| Tribunal | Portal de busca | Conferência 30/09/2026 | Busca por WebSearch |
|---|---|---|---|
| TRF1 | `https://jurisprudencia.trf1.jus.br/` | ⬜ sem resposta (conexão recusada/tempo esgotado) | `site:trf1.jus.br` |
| TRF2 | `https://www.trf2.jus.br/` | ✅ respondeu (HTTP 200; o endereço antigo de consulta redireciona para a home) | `site:trf2.jus.br` |
| TRF3 | `https://web.trf3.jus.br/base-textual` | ⬜ sem resposta | `site:trf3.jus.br` |
| TRF4 | `https://jurisprudencia.trf4.jus.br/` (redireciona para a pesquisa do eproc) | ✅ respondeu (HTTP 200) | `site:trf4.jus.br` |
| TRF5 | `https://julia-pesquisa.trf5.jus.br/julia-pesquisa/` | ⬜ sem resposta | `site:trf5.jus.br` |
| TRF6 | `https://jurisprudencia.trf6.jus.br/` | ⬜ sem resposta | `site:trf6.jus.br` |

## Tribunais de Justiça (os de maior volume)

| Tribunal | Portal de busca | Conferência 30/09/2026 | Busca por WebSearch |
|---|---|---|---|
| TJSP | `https://esaj.tjsp.jus.br/cjsg/consultaCompleta.do` | ✅ respondeu (HTTP 200) | `site:tjsp.jus.br` |
| TJRJ | `https://www3.tjrj.jus.br/ejuris/ConsultarJurisprudencia.aspx` | ✅ respondeu (HTTP 200) | `site:tjrj.jus.br` |
| TJMG | `https://www5.tjmg.jus.br/jurisprudencia/` | ✅ respondeu (HTTP 200) | `site:tjmg.jus.br` |
| TJRS | `https://www.tjrs.jus.br/buscas/jurisprudencia/` | ✅ respondeu (HTTP 200) | `site:tjrs.jus.br` |

Outros TJs, TRTs e TREs: WebSearch com `site:tjXX.jus.br`, `site:trtNN.jus.br` ou `site:treXX.jus.br`
(padrão `jus.br` do tribunal citado). Não invente endereço de portal: se não localizar, registre a
query e siga a regra da FASE 3.

## Como usar

1. **Ordem de busca:** portal/`site:` do tribunal citado → tribunal superior correspondente →
   agregador (JusBrasil, Escavador) só como pista, marcado `AGREGADOR — conferir no tribunal`.
2. Portal ⚠️/⬜ na tabela: não conclua nada pela falha dele. Tente WebSearch `site:` e o fetch na
   página do julgado; se tudo falhar, a citação fica ⬜ **não verificada** — nunca 🔴.
3. **Súmula e tese vinculante** (repetitivo, repercussão geral, IAC, IRDR): confira na página oficial
   do enunciado ou do tema, não em reprodução de terceiros.
4. Número de processo no padrão CNJ (`NNNNNNN-DD.AAAA.J.TR.OOOO`) quando a peça trouxer; senão, o
   formato histórico do tribunal (REsp 1.234.567/SP, RE 123.456 etc.).
