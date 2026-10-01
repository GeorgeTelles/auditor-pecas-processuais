---
name: auditoria-pre-protocolo
description: >-
  Uso preventivo do Auditor de Peças Processuais — a auditoria de integridade na SUA peça, antes do
  protocolo. O Conselho Federal da OAB recomenda verificar peça produzida com apoio de IA; este
  comando é o instrumento sistemático desse dever: (1) as mesmas varreduras determinísticas da
  peça recebida (texto oculto acidental, unicode de copy-paste, metadados vazando, revisões não
  aceitas — parser real, mesmo contrato JSON); (2) limpeza guiada pela higiene-de-metadados;
  (3) citações e dispositivos PRÓPRIOS conferidos pelo próprio plugin (conferencia-de-citacoes e
  conferencia-de-dispositivos, WebFetch real) e, a pedido, o nexo de cada julgado com a sua tese
  (nexo-com-a-tese, análise estratégica); (4) checklist final pré-protocolo com evidência por item. Aciona: quando o usuário pede /revisar-antes-de-protocolar,
  "auditar a minha peça", "conferir antes de protocolar", "limpar metadados antes de enviar", ou
  pergunta se a peça dele está segura para o protocolo.
---

# auditoria-pre-protocolo — a auditoria na SUA peça, antes do protocolo

Este é o uso preventivo do produto: o mesmo motor que varre a peça recebida da parte contrária,
apontado para a peça que **você** vai protocolar. O objetivo não é desconfiar do seu trabalho — é
impedir que um descuido técnico (um trecho de rascunho em fonte branca, um comentário interno
esquecido, uma revisão não aceita, uma citação que o modelo inventou) chegue ao juiz com o seu
nome embaixo.

## Por que isto é um dever prático, não paranoia

O Conselho Federal da OAB aprovou recomendações para o uso de IA generativa na prática jurídica
(`context/normas-ia-judiciario-oab.md` §2): legislação aplicável, confidencialidade, prática
jurídica ética e comunicação ao cliente sobre o uso de IA. **Verificar a peça produzida com apoio
de IA é dever prático do advogado** — e este comando é o instrumento sistemático dessa
verificação: parser e evidência, em vez de "passar o olho". Os casos-âncora do produto mostram o
custo de não verificar: em todas as sanções, a responsabilidade pelo que a peça afirma foi do
advogado, nunca da ferramenta.

## Quando esta skill entra

- O usuário pede `/revisar-antes-de-protocolar`, "audita a minha peça", "confere antes de protocolar".
- O onboarding registrou uso principal "as próprias peças" e chegou um arquivo.
- O `auditoria-master` identificou na triagem que a peça em análise é a **própria** do usuário.

> **🖱️ Escolha de lista fechada = botões:** pergunte com **AskUserQuestion** qual arquivo será
> auditado — **DOCX de trabalho** × **PDF final** × **os dois**. O ideal é auditar os dois: o DOCX
> carrega revisões e comentários; o PDF é o que o tribunal recebe.

## Etapa 1 — Varreduras determinísticas (as mesmas de C1, mesmo contrato)

Rode os mesmos parsers da peça recebida — `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/<parser>.py"
<arquivo>` → JSON no stdout com
`status: ok | missing_dependency | error | formato_nao_suportado` + `achados[]`. Vale a trava T1 sem exceção: sem lib
instalada, a skill **declara** que a varredura estrutural não rodou e instrui a instalação —
nunca finge ter varrido.

| Varredura | O que ela pega na SUA peça |
|---|---|
| `varredura-comando-lexico` | Comando a IA que a ferramenta do escritório colou no rascunho (ex.: resquício de prompt, "ignore as instruções…") — em fonte normal ou oculto |
| `varredura-texto-oculto` | Trecho de rascunho ou prompt que ficou em fonte branca/corpo mínimo por acidente de edição |
| `varredura-unicode-invisivel` | Caracteres invisíveis que vieram de copy-paste (chat de IA, web, outro PDF) — zero-width, Tags |
| `varredura-homoglifos` | Confusáveis que entraram por colagem e quebram a busca textual do tribunal |
| `varredura-metadados` | Autor real ≠ assinante, revisões não aceitas, comentários internos, propriedades ocultas |
| `varredura-pdf-ativo` | `/OpenAction`, `/JS`, `/Launch` herdados de conversor ou modelo de PDF |

Na peça própria, a leitura do achado muda de tom: quase tudo aqui é **descuido, não malícia** —
mas o efeito no tribunal é o mesmo. Um comentário "conferir se esse prazo está certo" esquecido no
DOCX é lido pela parte contrária; um bloco de prompt em fonte branca vira o caso TRT-8 com o seu
nome. Anexe a cada achado o dado bruto do parser (cor/tamanho, codepoint, campo de metadado) e a
recomendação de correção.

## Etapa 2 — Limpeza guiada

Apareceu metadado estranho, revisão pendente ou comentário? Roteie para a **`higiene-de-metadados`**
— o guia de limpeza por ferramenta (Word, LibreOffice, Google Docs, PDF). A divisão de trabalho é
fixa: o auditor **orienta** a limpeza e depois **verifica** o resultado; quem executa, no próprio
arquivo, é o advogado. Nada destrutivo roda por aqui.

## Etapa 3 — Citações e dispositivos PRÓPRIOS (motor interno)

O mesmo rigor que o plugin aplica na peça adversária vale para a sua:

1. **`conferencia-de-citacoes`** na sua peça: toda súmula, tema e acórdão extraído e conferido
   com WebFetch real e as 3 evidências. Voz de prevenção: 🔴 aqui não é "munição de impugnação", é
   **citação a corrigir ou retirar antes do protocolo**. Fetch que falhou vira "não verificada",
   nunca ✅ (T2) — e "não verificada" na peça própria é pendência, não liberação.
2. **`conferencia-de-dispositivos`** na sua peça: cada artigo citado conferido contra a fonte
   oficial; teor deturpado aparece lado a lado com a redação vigente para você corrigir.
3. **Nexo com a tese (opcional, a pedido):** pergunte com **AskUserQuestion** se o advogado quer
   rodar o **`nexo-com-a-tese`** — **Sim, conferir o nexo** × **Não, só integridade**. Se sim, peça
   a tese em 1-2 frases e rode a skill sobre as citações ✅/⚠️ da etapa 1. É **análise
   estratégica** (rotulada assim), a única exceção à trava T6, e só existe na peça própria.

Nunca valide citação "por leitura": sem WebFetch real, não há selo (T2).

## Etapa 4 — Checklist final pré-protocolo

Só libere o "pronto para protocolo" com todas as caixas marcadas — e cada caixa com a **evidência**
ao lado, nunca de memória:

- [ ] **Metadados limpos?** — `varredura-metadados` re-rodada no arquivo final; `achados[]` vazio ou só o esperado (autor = assinante, datas coerentes)
- [ ] **Revisões aceitas?** — nenhum track change pendente no DOCX
- [ ] **Comentários removidos?** — zero comentários no arquivo final
- [ ] **Citações validadas?** — cada julgado com selo da `conferencia-de-citacoes`, ou declaradamente "não verificada" (pendência)
- [ ] **Dispositivos conferidos?** — cada artigo com o resultado da `conferencia-de-dispositivos`
- [ ] **Nexo conferido?** (só se rodou) — nenhuma citação 🚫 BLOQUEADA no `nexo-com-a-tese`
- [ ] **PDF final regenerado?** — via impressão para PDF (não "salvar como"), e re-varrido depois

Caixa sem evidência = caixa aberta. O relatório sai na voz do perfil definido no onboarding
(individual: direta e prática; departamento jurídico: formal, com sumário executivo) e fecha
**sempre** com o aviso da trava T5: a conferência final antes do protocolo é do advogado.

**Entrega em arquivo:** salve o relatório como `revisao-pre-protocolo-<nome-da-peça>-<AAAA-MM-DD>.md` e
rode `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/relatorio_html.py" <relatorio.md>` para gerar o HTML com
o botão **Exportar PDF** (mesmo fluxo do `dossie-de-integridade`). No chat, resumo + links dos dois
arquivos, fechando com o crédito do autor (`estilo-e-fronteiras`).

## Travas / limites

- **T1** — nenhum selo estrutural sem o parser ter rodado e retornado o dado bruto; sem lib,
  declara e instrui.
- **T2** — nenhuma citação selada sem verificação real, na peça própria como na recebida.
- **T6** — o `nexo-com-a-tese` é a única análise de mérito, só na peça própria, a pedido e rotulada
  "análise estratégica".
- **T5** — a conferência humana final é do advogado; o checklist organiza, não substitui.
- **Nada destrutivo:** esta skill não edita nem "limpa" o arquivo do usuário — orienta (via
  `higiene-de-metadados`) e verifica o resultado.
- **Sinal ≠ veredito** vale também na peça própria: achado técnico é achado técnico, com evidência.
- Autoria "George Telles - AG TECH". PT-BR com acentuação correta.
