---
name: higiene-de-metadados
description: >-
  Guia de limpeza de metadados da peça antes do protocolo — orienta o advogado passo a passo,
  sem executar nada destrutivo no arquivo dele. Por ferramenta: Word (Inspetor de Documento —
  autor, comentários, revisões não aceitas, propriedades ocultas), LibreOffice (remover
  informações pessoais ao salvar), Google Docs (exportação limpa — sugestão pendente vira track
  change no .docx exportado) e PDF (regenerar via impressão para PDF, que descarta histórico e
  objetos, em vez de "salvar como"). Explica o que cada metadado vaza e o risco concreto: autor
  real diferente do assinante, comentário interno esquecido, campo Company de outro escritório em
  peça terceirizada. Fecha exigindo a prova de limpeza: re-rodar a varredura-metadados no arquivo
  final. Aciona: quando a varredura-metadados ou a auditoria-pre-protocolo encontrou metadado
  comprometedor na peça própria, ou o usuário pergunta como limpar autor, comentários ou revisões
  do Word, LibreOffice, Google Docs ou PDF antes de protocolar.
---

# higiene-de-metadados — o guia de limpeza (orienta, nunca executa)

Esta skill é um **guia**. Ela orienta o advogado a limpar os metadados da própria peça, ferramenta
por ferramenta — mas **nunca executa nada destrutivo no arquivo do usuário**: quem aceita revisão,
apaga comentário e regenera o PDF é o advogado, na ferramenta dele. O papel do auditor é dizer
exatamente onde clicar, explicar o que cada metadado vaza — e depois **provar** a limpeza,
re-rodando a varredura no arquivo final.

## Quando esta skill entra

- A `varredura-metadados` (normalmente via `auditoria-pre-protocolo`) encontrou na peça própria:
  autor estranho, revisões não aceitas, comentários ou propriedades ocultas.
- O usuário pergunta "como limpo os metadados", "como tiro o autor do Word", "como removo os
  comentários antes de protocolar".

## O que cada metadado vaza — e o risco concreto

| Metadado | Onde mora | O que vaza | Risco concreto |
|---|---|---|---|
| Autor / Último salvo por | DOCX `docProps/core.xml` · PDF Info/XMP | Quem realmente redigiu e revisou | **Autor real ≠ assinante** — a parte contrária pergunta quem escreveu a peça |
| Comentários | DOCX `word/comments.xml` | A conversa interna da equipe | O comentário **"não mandar isso pro juiz"** esquecido — lido por quem não devia |
| Revisões não aceitas (track changes) | DOCX (`w:ins`/`w:del`) | O texto apagado — valores, teses e estratégias abandonadas | A versão anterior da estratégia visível a qualquer um que abrir o arquivo |
| Company / Gerente | DOCX `docProps/app.xml` | A organização de origem do modelo usado | **Company de OUTRO escritório** numa peça "própria" — o vazamento clássico da peça terceirizada, crítico para o departamento jurídico que recebe volume de terceirizados |
| Histórico e objetos do PDF | Revisões incrementais, objetos órfãos | Versões anteriores recuperáveis | "Salvar como" preserva camadas; uma perícia adversária recupera o que você achou que apagou |

## Limpeza por ferramenta

Os nomes de menu variam por versão e idioma — descreva sempre o **objetivo** junto com o caminho,
para o usuário achar o equivalente na versão dele.

### Word

1. **Antes de tudo, às claras:** aceite ou rejeite TODAS as revisões (Revisão → Aceitar → Aceitar
   Todas as Alterações) e exclua todos os comentários (Revisão → Excluir → Excluir Todos os
   Comentários do Documento). O Inspetor também remove, mas fazer manualmente evita surpresa.
2. Arquivo → Informações → Verificar Problemas → **Inspecionar Documento**.
3. Marque ao menos: Comentários/Revisões/Versões · **Propriedades do Documento e Informações
   Pessoais** · Dados XML personalizados · Texto oculto.
4. **Remover Tudo** em cada categoria encontrada.
5. Salve como **cópia final** — e é essa cópia que segue o fluxo.

### LibreOffice

1. Editar → Registrar alterações → **Gerenciar** → aceitar todas; apague os comentários.
2. Ferramentas → Opções → LibreOffice → Segurança → Opções de segurança → marque **"Remover
   informações pessoais ao salvar"**.
3. Arquivo → Propriedades → desmarque "Utilizar dados de usuário" e use **Redefinir propriedades**.

### Google Docs

1. **Resolva TODAS as sugestões antes de exportar** — sugestão pendente vira **track change no
   .docx exportado**, com autor e texto rejeitado dentro.
2. Apague ou resolva os comentários.
3. Exportação limpa: Arquivo → Fazer download → **PDF** (não carrega o histórico de versões nem
   comentários resolvidos). Se precisar do `.docx`, inspecione-o no Word depois — o export grava
   autor nas propriedades.
4. O histórico de versões fica **no Doc**, não no arquivo exportado — mas cuidado ao
   **compartilhar o link** do Doc: quem tem acesso de edição vê o histórico inteiro.

### PDF (o passo final, sempre)

1. **Regenere via impressão para PDF** (Ctrl/Cmd+P → "Salvar como PDF" / "Microsoft Print to
   PDF") em vez de "Salvar como": a impressão **achata** o documento — descarta revisões
   incrementais, objetos órfãos, scripts e anexos que o "salvar como" preserva.
2. Custo honesto da regeneração: perdem-se hyperlinks clicáveis, marcações de acessibilidade e
   **qualquer assinatura digital existente**. Por isso a ordem é fixa: **regenerar primeiro,
   assinar depois** — nunca o contrário.
3. Confira o resultado: os campos Info e XMP do PDF final devem sair limpos (a prova é a varredura
   abaixo, não a impressão de que "deve ter limpado").

## A prova de limpeza (obrigatória)

Limpeza sem verificação é fé. Depois de limpar, rode a **`varredura-metadados`** no arquivo
**final** — o que vai ao protocolo:

- `achados[]` vazio, ou só o esperado (autor = assinante, datas coerentes) → **limpeza provada**,
  com o JSON do parser como evidência no checklist do `auditoria-pre-protocolo`.
- Ainda aparece autor estranho, revisão ou comentário → repita a etapa da ferramenta
  correspondente; quase sempre a edição foi salva na cópia errada.

É a mesma régua do produto inteiro (T1): nenhum "está limpo" por impressão — só com o parser
re-rodado no arquivo final.

## Travas / limites

- **Guia, nunca executor:** esta skill não abre, edita nem regrava o arquivo do usuário, e não
  roda script de limpeza destrutivo. Orienta, e depois verifica com o parser.
- **Peça recebida é outro fluxo:** metadado estranho na peça da parte contrária é achado da
  `varredura-metadados` com a trava T4 (alerta, nunca veredito de fraude) — esta skill limpa a
  peça **própria**.
- **Assinatura digital sempre por último**, depois da regeneração do PDF.
- **Nenhum "limpo" sem parser re-rodado** no arquivo final (T1) — a conferência humana final é do
  advogado (T5).
- Autoria "George Telles - AG TECH". PT-BR com acentuação correta.
