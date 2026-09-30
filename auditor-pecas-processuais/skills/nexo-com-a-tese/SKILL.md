---
name: nexo-com-a-tese
description: >
  NEXO-COM-A-TESE — Etapa OPCIONAL da revisão da SUA peça antes do protocolo: para cada julgado
  que você cita (já conferido pela conferencia-de-citacoes), verifica em três camadas se ele
  realmente sustenta a sua tese — (1) o inteiro teor foi lido, não só a ementa; (2) o link foi
  confirmado por WebFetch real; (3) o nexo com a tese, estruturado: A FAVOR · CONTRA · NEUTRO ·
  DEPENDE, com a distinção relevante e o risco se citado. Veredito por citação: ✅ APROVADA · 📝
  REVISAR · 🚫 BLOQUEADA. Jurisprudência verdadeira que decide CONTRA a sua tese é tão perigosa
  quanto inventada. É ANÁLISE ESTRATÉGICA, rotulada assim — a única exceção à trava integridade ×
  mérito, e só existe na peça própria, a pedido do advogado. Nunca roda na peça recebida. Aciona:
  o auditoria-pre-protocolo oferece e o advogado aceita; "minhas citações sustentam a tese?",
  "confere o nexo dos julgados que eu cito", "esse acórdão ajuda ou atrapalha meu pedido?".
---

# NEXO-COM-A-TESE — a sua citação sustenta o que você pede?

## 1. Por que existe

A `conferencia-de-citacoes` prova que o julgado **existe e foi citado com fidelidade**. Isso não
basta antes de protocolar: um julgado real que decide **contra** a sua tese, ou que trata de fato
diferente, é tão perigoso quanto um julgado inventado. Esta skill é a última linha antes do
protocolo para as **suas** citações.

**Rótulo obrigatório no topo de toda saída:** *"Análise estratégica — não é achado de
integridade."* É a única análise de mérito do plugin (exceção à trava T6) e vale **só para a peça
própria**. Pedido de nexo sobre a peça da parte contrária → recuse e explique que está fora do
escopo (integridade × mérito).

## 2. Entrada necessária

1. **A tese ou o pedido do advogado**, em 1-2 frases, nas palavras dele.
2. **As citações** que ele pretende usar, com o status da `conferencia-de-citacoes`
   (✅/⚠️/🔴/⬜) e a URL.
3. (Opcional) O trecho da peça onde cada citação entra.

Faltou (1) ou (2) → pergunte **uma vez**. Não prossiga sem os dois. Citação 🔴 ou ⬜ não entra:
já está bloqueada pela conferência.

## 3. As três camadas (uma citação por vez)

### Camada 1 — O inteiro teor foi lido?

Faça um **WebFetch fresco** na URL. Leia o voto/acórdão (15-30 parágrafos centrais, se a página
trouxer) e registre:

- **Fato base** do caso julgado (1 frase);
- **Fundamento legal central** (lei, artigo, súmula);
- **Razão de decidir** (1-2 frases);
- **Distinções ou exceções** que o tribunal apontou.

Só ementa disponível → marque `📄 INTEIRO TEOR NÃO DISPONÍVEL — análise restrita à ementa` e
siga, com essa ressalva no veredito.

### Camada 2 — O link está confirmado?

Use o status da `conferencia-de-citacoes`. Sem registro prévio → rode a conferência antes
(WebFetch real, 3 evidências — trava T2).

| Status | Tratamento aqui |
|---|---|
| ✅ | Segue para a Camada 3 |
| ⚠️ | Segue, com ressalva no veredito |
| 🔴 / ⬜ | **BLOQUEADA** na hora. Não segue para a Camada 3 |

### Camada 3 — Nexo com a tese (estruturado, nunca "no feeling")

```markdown
**Sua tese (transcrição):** > [a tese nas palavras do advogado]
**Tese do julgado (síntese):** > [o que o tribunal decidiu, em 1 frase]

**Alinhamento:** A FAVOR | CONTRA | NEUTRO | DEPENDE
- A FAVOR — sustenta diretamente a sua tese
- CONTRA — decide em sentido oposto
- NEUTRO — tema parecido, mas não decide a questão em jogo
- DEPENDE — só sustenta se o fato X estiver presente no seu caso

**Distinção relevante:** [fato do caso julgado que diverge do seu e pode afastar a aplicação]
**Risco se citado:** baixo | médio (pode sofrer distinguishing) | alto (contrário, ou superado por
entendimento posterior)
```

## 4. Veredito por citação

| Veredito | Quando |
|---|---|
| ✅ **APROVADA** | Inteiro teor lido + link ✅ + A FAVOR com risco baixo |
| 📝 **REVISAR** | 1 ou 2 ressalvas: só ementa · link ⚠️ · DEPENDE · risco médio |
| 🚫 **BLOQUEADA** | Link 🔴/⬜ **ou** CONTRA **ou** risco alto |

## 5. Saída

```markdown
## Nexo com a tese — [N] citações
> Análise estratégica — não é achado de integridade.

**Sua tese:** [transcrição] · **Data:** [DD/MM/AAAA]

### Citação 1 — [Tribunal · número · relator]
- 🔍 Camada 1: [inteiro teor lido | só ementa] — fato base · fundamento · razão de decidir
- 🔗 Camada 2: ✅ | ⚠️ (fonte: <URL>)
- ⚖️ Camada 3: sua tese × tese do julgado · alinhamento · distinção · risco
- **Veredito:** ✅ APROVADA | 📝 REVISAR | 🚫 BLOQUEADA — [como usar, ou por que não usar]

## Resumo
| # | Tribunal | Veredito | Ação |
|---|---|---|---|
**Aprovadas:** N · **Revisar:** N · **Bloqueadas:** N
```

O resultado volta ao checklist do `auditoria-pre-protocolo` ("nenhuma citação 🚫 BLOQUEADA").

Toda saída fecha com: **"Análise assistida por IA. A conferência do inteiro teor e da pertinência
ao caso concreto é responsabilidade exclusiva do advogado antes de protocolar."** (T5)

## 6. Proibições

1. Nunca ✅ APROVADA sem WebFetch fresco na URL.
2. Nunca avaliar o nexo "no olho": transcreva a sua tese e sintetize a do julgado, lado a lado.
3. Uma citação por vez; nunca misture citações num veredito único.
4. Nunca esconda 🚫 BLOQUEADA — ela aparece destacada no resumo.
5. Nunca rode na peça recebida, nem para prognosticar como o juiz vai decidir o caso.
6. Nunca omita o rótulo "análise estratégica" nem o aviso final.

## Travas

- **T2:** sem WebFetch real, não há selo; 🔴/⬜ bloqueia.
- **T6:** exceção única e delimitada — só na peça própria, a pedido, rotulada estratégica.
- **T5:** aviso de conferência humana em toda saída.

**Cross-links:** upstream `auditoria-pre-protocolo` (oferece a etapa) e `conferencia-de-citacoes`
(status de cada citação) · rotulagem das 4 naturezas: `estilo-e-fronteiras` · QA:
`revisao-final-auditoria`.
