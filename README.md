# Auditor de Peças Processuais — Marketplace

**Auditoria de integridade de peça processual com IA**: audite a petição recebida da parte
contrária e a sua antes do protocolo.

## O que o plugin faz

1. **Texto oculto e prompt injection**: fonte branca, corpo mínimo e comando escondido dirigido a
   sistema de IA (parsing local determinístico; caso real já sancionado na Justiça do Trabalho). A
   varredura léxica também lê o texto **visível** ("IA, ignore…", "não impugne os documentos"). O
   rodapé PJe/ICP-Brasil é reconhecido e rebaixado, nunca suprimido.
2. **Unicode invisível e homóglifos**: caracteres invisíveis e trocas de alfabeto que enganam
   filtros.
3. **Jurisprudência inventada**: cada citação conferida com fetch real na fonte oficial, na peça
   adversária e na sua (padrão de sanção já consolidado nos tribunais: multas de 1% a 10% do valor
   da causa).
4. **Dispositivo de lei inexistente ou deturpado**: artigo conferido contra a fonte oficial.
5. **Metadados e anexos**: autor real ≠ assinante, revisões esquecidas, hash divergente.
6. **Gaps da tese e nexo das suas citações**: o que a peça adversária deixou de enfrentar e, na sua
   peça, se cada julgado sustenta a sua tese (análise estratégica, rotulada como tal).

**Honestidade técnica por design:** o produto sinaliza com evidência e **não** é "detector de IA"
(não existe detector confiável, e isso está escrito no manual). O parser determinístico decide o
fato; o advogado conclui o direito.

## Instalação (Claude Cowork / Claude Code)

1. Abra **Settings → Plugins**.
2. Na aba **Pessoal**, clique em **"+"** (Uploads locais / Adicionar marketplace).
3. Envie o zip do plugin ou cole a URL deste repositório.
4. Instale o plugin `auditor-pecas-processuais` e abra uma nova conversa.

## Uso

- `/auditar-peca`: auditoria completa da peça recebida
- `/revisar-antes-de-protocolar`: auditoria da sua peça antes do protocolo
- `/conferir-citacoes`: só a camada de citações
- `/relatorio-auditoria`: relatório final consolidado

---

© 2026 George Telles - AG TECH. A conferência humana final é sempre do advogado responsável.
