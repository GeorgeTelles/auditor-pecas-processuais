---
name: varredura-texto-oculto
description: >
  VARREDURA-TEXTO-OCULTO — Camada 1 do motor de integridade estrutural. Executa o
  parser local pdf_integridade.py (PDF) ou docx_integridade.py (Word, em todas as partes:
  corpo, cabeçalho, rodapé, notas, comentários, caixas de texto, propriedades) e reporta
  texto invisível ao leitor humano: fonte branca ou da cor do fundo, corpo menor que 4pt,
  texto marcado como oculto no Word, texto fora da página, opacidade próxima de zero e
  modo de renderização invisível — o vetor do caso TRT-8 (multa
  de 10% do valor da causa). Todo achado anexa a evidência bruta extraída pelo
  parser (RGB, tamanho de fonte, modo de render) e o texto encontrado é roteado ao
  classificador-prompt-injection, que julga a intenção. Sinaliza — nunca conclui
  fraude. Aciona: "texto oculto", "fonte branca", "texto invisível no PDF", "tem
  algo escondido nessa petição", "varredura de texto oculto", "letra branca",
  "prompt escondido no PDF".
---

# VARREDURA-TEXTO-OCULTO — texto invisível ao leitor humano

## 1. Escopo

Detecta, por varredura determinística, texto presente no PDF que o leitor humano
não vê ao abrir o arquivo:

| Classe | Como se esconde |
|---|---|
| Fonte branca/quase-branca | Cor do texto igual (ou quase igual) ao fundo — RGB ~(1,1,1) sobre página branca |
| Corpo mínimo | Tamanho de fonte < 4pt — ilegível a olho nu, legível pela máquina |
| Opacidade ~0 | Texto transparente via canal alfa/estado gráfico |
| Modo de render invisível | Text rendering mode 3 (não preenche nem contorna) — o texto existe no stream, mas não é pintado |

**Em Word (.docx)** o `docx_integridade.py` lê todas as partes do arquivo e resolve a formatação
como o Word (padrão → estilo de parágrafo → estilo de caractere → formatação direta), então pega
também letra branca **herdada de estilo**. Motivos: letra branca ou da mesma cor do fundo (página,
célula, realce), letra < 4pt, texto marcado como oculto no Word, e frase de comando a IA guardada
em comentário, propriedades do arquivo, dados anexos ou texto alternativo de imagem. Em PDF, também
o texto posicionado **fora da área visível** da página. Conferência visual só existe para PDF.

Quem lê a peça no visualizador não vê nada; quem processa o arquivo por máquina
(inclusive uma IA que resuma ou conteste a peça) lê tudo. É exatamente o canal
usado para embutir comandos dirigidos a assistentes de IA.

**Quem decide se há texto oculto é o parser** (`scripts/pdf_integridade.py`),
nunca a leitura da peça "no olho" pelo LLM. Esta skill orquestra o parser,
interpreta o JSON retornado e roteia o julgamento de intenção.

## 2. Por que importa — o precedente

Caso documentado no anexo `context/casos-ancora-sancoes.md` (§1): **TRT-8, ATOrd
nº 0001062-55.2025.5.08.0130** (3ª Vara do Trabalho de Parauapebas, maio/2026) —
texto em fonte branca sobre fundo branco com comando dirigido à IA. Resultado:
**multa solidária de 10% do valor da causa (~R$ 84,2 mil)** + ofício à OAB/PA e à
Corregedoria do TRT-8. Foi detectado por ferramenta interna do Judiciário; o
achado desta varredura é a matéria-prima da mesma constatação — feita pelo
próprio advogado, antes de responder a peça.

## 3. Input

| Campo | Obrigatório | Observação |
|---|---|---|
| `arquivo` | sim | Caminho local do PDF (peça recebida ou a própria) |
| Contexto da peça | desejável | Recebida da parte contrária × própria pré-protocolo — muda o framing do relatório |

## 4. Processamento

### Passo 1 — Executar o parser (do root do plugin)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pdf_integridade.py" <arquivo.pdf>
```

Retorno em JSON no stdout: `parser`, `versao`, `arquivo`, `status`,
`motor_usado`, `achados[]` (cada um com `tipo`, `gravidade`, `evidencia`,
`localizacao`), `resumo.total_achados`, `dependency_hint`.

### Passo 2 — Tratar o status (regra T1, sem exceção)

| `status` | Conduta |
|---|---|
| `ok` | Prosseguir para o Passo 3 |
| `missing_dependency` | DECLARAR: "varredura estrutural não executada" + exibir o `dependency_hint` (instrução de instalação). NUNCA improvisar o achado lendo o texto da peça "no olho" |
| `error` | Reportar o erro literal do parser; não substituir por impressão de leitura |
| `formato_nao_suportado` | Informar que esta varredura cobre PDF; DOCX/texto seguem para as varreduras de unicode e de metadados |

Se `motor_usado: "raw"`, declarar a limitação junto ao resultado: **"cobertura
limitada a streams não comprimidos"** — ausência de achado nesse modo NÃO
equivale a peça limpa.

### Passo 3 — Focar os achados de texto oculto

Desta execução interessam os achados cujo `tipo` indique texto oculto (fonte
branca/quase-branca, corpo < 4pt, opacidade ~0, modo de render invisível). Se o
parser também retornar achados de conteúdo ativo (`/OpenAction`, `/JS` etc.),
apontar a skill irmã `varredura-pdf-ativo` — sem duplicar a análise aqui.

### Passo 3b — Zona, texto e whitelist

Com motor `PyMuPDF` ou `pdfplumber`, cada achado traz `texto` (trecho literal, **é o que vai ao
classificador**), `zona` (`rodape` · `cabecalho` · `corpo`) e `whitelist`. Fonte < 4pt em
rodapé/cabeçalho com marcador forte de documento oficial (PJe, ICP-Brasil, OAB, "documento
assinado eletronicamente") e **sem** padrão léxico de comando sai `baixa` + `whitelist: true`:
relate como "rodapé oficial reconhecido", **mantido na lista com o texto** — nunca suprimido. Fonte
**branca** nunca é rebaixada. Com `pikepdf`/`raw` não há zona nem whitelist (o envelope avisa em
`aviso`): declare que achados de fonte pequena não foram triados por zona. Fonte pequena cujo
trecho também casa comando a IA sobe para `alta`.

### Passo 4 — Evidência bruta + roteamento do julgamento

Para CADA achado:

1. **Anexar a evidência bruta do parser** — os valores extraídos (RGB da fonte,
   tamanho em pt, modo de render, página/posição em `localizacao`). Sem a
   evidência bruta, o achado não entra no relatório.
2. **Rotear o texto encontrado ao `classificador-prompt-injection`** — quem
   julga se o trecho é comando dirigido a IA, resíduo de formatação inofensivo
   (marca d'água de editor, texto de template) ou outra coisa é aquela skill.
   Esta varredura reporta O QUE está oculto e ONDE; não conclui POR QUÊ.

## 5. Output

```markdown
## 🔍 Varredura de texto oculto — {{arquivo}}

**Parser:** pdf_integridade.py v{{versao}} · **Motor:** {{motor_usado}}
**Status:** {{status}} · **Achados de texto oculto:** {{n}}

| # | Tipo | Evidência bruta | Localização |
|---|---|---|---|
| 1 | fonte quase-branca | RGB (0.99, 0.99, 0.99), corpo 9pt | pág. 4 |

### Texto extraído (encaminhado ao classificador de intenção)

> [trecho literal extraído — julgamento de intenção: `classificador-prompt-injection`]

### Leitura

- Achado estrutural CONFIRMADO pelo parser (dado bruto acima).
- A INTENÇÃO do texto (comando a IA × resíduo inofensivo) é julgada pelo
  `classificador-prompt-injection`.
- Precedente de referência: TRT-8, ATOrd 0001062-55.2025.5.08.0130 — multa de
  10% do valor da causa (~R$ 84,2 mil) por fonte branca com comando dirigido a IA.

➡️ Este achado segue para o `dossie-de-integridade`.

> ⚠️ Conferência humana final é do advogado. Esta varredura sinaliza; não conclui.
```

Sem achados: reportar "0 achados de texto oculto" + motor usado + a ressalva do
modo `raw` quando aplicável. Silêncio do parser com motor completo é bom sinal;
nunca prometer "peça garantidamente limpa".

## 6. O que esta skill nunca faz

1. Nunca emite selo de texto oculto sem o parser ter rodado e retornado o dado bruto (T1).
2. Nunca conclui "fraude", "má-fé" ou "manipulação dolosa" — sinaliza o dado técnico; a conclusão jurídica é do advogado (T4).
3. Nunca julga a intenção do texto achado — isso é do `classificador-prompt-injection`.
4. Nunca modifica o PDF original.
5. Nunca nomeia os profissionais sancionados nos casos-âncora.

## 7. Travas desta skill

| Trava | Aplicação aqui |
|---|---|
| **T1** | Achado só existe com o parser rodado + dado bruto anexado; `missing_dependency` → "varredura estrutural não executada" + `dependency_hint` |
| **T4** | Texto oculto achado = alerta técnico com evidência; fraude é conclusão jurídica/pericial do advogado, nunca desta skill |
| **T5** | ⚠️ Conferência humana final é do advogado — todo relatório sai com este aviso |

## 8. Integração

- **Upstream:** `auditoria-master` (triagem) · `auditoria-pre-protocolo` (uso preventivo na própria peça)
- **Downstream:** `classificador-prompt-injection` (julga a intenção do texto achado) · **`dossie-de-integridade` — todo achado termina lá**
- **Irmã:** `varredura-pdf-ativo` (mesmo parser, foco em conteúdo ativo)
