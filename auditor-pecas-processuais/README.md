# Auditor de Peças Processuais

**Auditoria de integridade da peça processual: o que está escondido, inventado ou fora de contexto,
antes de você responder ou protocolar.**

Chegou uma petição inicial, contestação ou recurso da parte contrária? Antes de gastar horas
respondendo, rode `/auditar-peca`:

1. **Texto oculto e prompt injection**: fonte branca, corpo mínimo e comando dirigido à IA do
   tribunal ou à sua (caso real: multa de ~R$ 84 mil no TRT-8). Pega também o comando escrito em
   fonte normal (varredura léxica). O rodapé PJe/ICP-Brasil sai como `baixa`, sem alarme.
2. **Os 5 tipos de ataque, em PDF e em Word**: desvio de função da IA, supressão de informação, indução de viés, padrões técnicos (comando em Base64 ou hexadecimal, tags de prompt) e falsa autoridade. No Word, lê corpo, cabeçalho, rodapé, notas, comentários, caixas de texto e propriedades, e acha letra branca mesmo quando ela vem do estilo do documento.
2. **Unicode invisível e homóglifos**: caracteres que o olho não vê e o filtro não pega.
3. **Jurisprudência inventada**: cada citação conferida com fetch real na fonte (padrão consolidado
   de sanção em TST, TJ/PR, TJSC e TSE; multas observadas nos casos-âncora de 1% a 10% do valor da
   causa, o intervalo do CPC art. 81).
4. **Dispositivo de lei inexistente ou deturpado**: artigo conferido contra a fonte oficial.
5. **Metadados e anexos**: autor real ≠ assinante, revisões esquecidas, hash divergente.
6. **Gaps da tese**: o que a peça deixou de enfrentar, mapeado para a sua resposta (análise
   estratégica, rotulada como tal; não fundamenta pedido de multa).

Antes de protocolar a **sua** peça, rode `/revisar-antes-de-protocolar`. Ele faz as mesmas
varreduras, a higiene de metadados e a conferência das suas citações e dispositivos. Se você quiser,
também confere o nexo de cada julgado com a sua tese.

**Honestidade técnica por design:** o produto **sinaliza com evidência** e nunca vende "detector de
IA" (não existe detector confiável, e a marca d'água da Anthropic não tem API pública). O parser
determinístico decide o fato; você conclui o direito.

## Instalação

Settings → Plugins → Pessoal → "+" → envie o zip do plugin ou cole a URL do repositório do
marketplace.

## Saída

O relatório final sai em **dois arquivos**, lado a lado:

- `relatorio-auditoria-<peça>-<data>.md`: o dossiê em markdown;
- `relatorio-auditoria-<peça>-<data>.html`: a mesma análise em página formatada, que abre offline,
  com o botão **Exportar PDF** (A4, texto selecionável, links clicáveis).

## Uso

- `/auditar-peca`: auditoria completa da peça recebida
- `/revisar-antes-de-protocolar`: auditoria da sua peça antes do protocolo
- `/conferir-citacoes`: só a camada de citações
- `/relatorio-auditoria`: consolida os achados no relatório final

## Licença

Uso **gratuito, pessoal e profissional próprio**, inclusive nos casos dos seus clientes. Os
relatórios gerados são seus. É **vedado** copiar, reproduzir, redistribuir, vender, modificar ou
criar versão derivada do plugin sem autorização por escrito. Texto completo em [`LICENSE`](LICENSE).

---

*Esta skill foi desenvolvida por George Telles.*
[E-mail](mailto:georgesmattos@gmail.com) · [LinkedIn](https://www.linkedin.com/in/georgetelles/) · [WhatsApp (71) 98822-9457](https://wa.me/5571988229457)
