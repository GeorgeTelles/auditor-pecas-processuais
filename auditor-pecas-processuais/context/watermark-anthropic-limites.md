# Marca d'água da Anthropic — o que existe, os limites declarados e a régua da detecção de IA

> Levantamento de 18/08/2026. Este anexo é a base técnica da trava T3 e
> da trava TV1 — a `heuristica-uso-de-ia` e todo material comercial dependem dele. Selo herdado da
> pesquisa: ✅ confirmado em fonte primária/oficial · 🟡 fonte secundária, sem confirmação
> primária.

---

## 1. O anúncio (12/08/2026) e o mecanismo ✅

Em **12/08/2026** a Anthropic anunciou que todo modelo Claude lançado a partir de **02/08/2026**
embute uma marca d'água invisível em todo texto que gera, usando uma variante do **SynthID-Text**
(método publicado pela Google DeepMind na Nature, 2024).

**Mecanismo:** em pontos onde múltiplas palavras serviriam igualmente bem, o modelo usa uma chave
criptográfica derivada das palavras anteriores para decidir — as escolhas continuam parecendo
aleatórias para o leitor, mas são verificáveis por quem tem a chave. A Anthropic afirma que isso
não altera conteúdo, criatividade ou legibilidade do texto, e não usa caracteres ocultos nem
tokens extras.

— Fontes: anthropic.com/news/claude-text-watermark (12/08/2026) · TechCrunch, 15/08/2026 (✅
confirmação secundária de veículo estabelecido).

## 2. A tabela completa das 6 limitações declaradas pela própria Anthropic ✅

Estas limitações têm de virar **disclaimer explícito no produto, não nota de rodapé**:

| # | Limitação declarada pela Anthropic | O que significa para o produto |
|---|---|---|
| 1 | Só detecta texto do **Claude**, não confirma nem nega autoria de outros modelos (ChatGPT, Gemini, Copilot, DeepSeek etc.) | Uma petição gerada por qualquer outro modelo passa **sem sinal nenhum** — o produto não pode dizer "não é IA" |
| 2 | API de detecção de terceiros ainda **não está disponível** — anunciada, sem data, sem preço, sem tier de acesso definido | Não dá para construir uma skill que consulta essa API hoje; é item de roadmap (v0.2 rotulada, condicionada à API), não feature v0.1 |
| 3 | Edição leve provavelmente não remove a marca; **reescrita completa palavra-por-palavra remove** | Um advogado que pede ao Claude um rascunho e reescreve à mão invalida a detecção — o que é o fluxo normal de qualquer peça |
| 4 | Não funciona bem em textos curtos, nem em passagens factuais (nomes próprios, números, citações) — exatamente o que mais aparece em petição | O texto jurídico é rico em nomes de partes, números de processo e citações literais — o pior caso de uso para a marca |
| 5 | Não prova "Claude escreveu isto" vs. "Claude editou pesadamente isto"; não confirma nem nega autoria humana | Não serve como prova jurídica de autoria — nem a Anthropic reivindica isso |
| 6 | Modelos anteriores a 02/08/2026 não têm marca (retrofit "nos próximos meses", sem data) | Qualquer petição escrita com Claude antes de agosto de 2026 é invisível à marca, mesmo que a API existisse hoje |

## 3. Demonstração pública de remoção 🟡

Já existe demonstração pública de **remoção da marca** ("Four Cents" — techtimes.com, 12/08/2026;
🟡 fonte não-primária, WebFetch bloqueado por 403 na pesquisa, conteúdo obtido só via snippet de
busca). Reforça que qualquer coisa construída sobre a marca d'água é uma **corrida armamentista,
não uma garantia**.

## 4. A régua — detectores de "texto de IA" em geral (§1.2 da pesquisa) ✅

A premissa de que **detector de IA confiável pode não existir** está confirmada com evidência
dura:

- A **OpenAI descontinuou o próprio classificador** em 20/07/2023 por baixa acurácia: identificava
  corretamente só **26%** dos textos gerados por IA como "provavelmente IA", e classificava errado
  **9%** dos textos humanos como IA. Sem substituto anunciado até hoje. — Fonte: TechCrunch,
  25/07/2023 (✅).
- Detectores comerciais em 2026 (GPTZero, Originality.ai, Copyleaks, Pangram) reportam números
  **inconsistentes entre si**: um estudo cita GPTZero com 99,3% de acurácia e 0,24% de falso
  positivo; outro cita GPTZero com **11% de falso positivo** em texto humano; Originality.ai
  aparece ora com 100% de acurácia, ora com 4,79% de falso positivo. **A dispersão entre estudos
  é, em si, o achado** — não há consenso técnico sobre confiabilidade. — Fontes: agregadores e
  vendors (🟡, sem auditoria independente terceirizada localizada na pesquisa). **Trava TV5:
  nunca citar acurácia de vendor como fato.**
- Pesquisa acadêmica recente (arXiv 2511.16690, nov/2025) documenta que detectores **classificam
  erroneamente texto humano levemente editado** — confundir "polimento" com "geração" generaliza
  para qualquer segunda língua ou revisão humana de rascunho de IA. 🟡 preprint, não
  peer-reviewed confirmado na pesquisa.

## 5. Fechamento — o que o produto PODE e o que NUNCA pode dizer

**PODE dizer, honestamente:**

> "sinal heurístico probabilístico, nunca prova"

**NUNCA pode dizer:**

- "detectamos que isto foi escrito por IA";
- "score de X% de probabilidade de IA" com precisão implícita;
- "confirmamos a marca d'água da Anthropic" (a API não existe publicamente ainda).

É o mesmo princípio que rege a `conferencia-de-citacoes` deste plugin: **nenhum selo ✅ sem
confirmação por evidência real** — nunca por inferência estatística vendida como certeza.
