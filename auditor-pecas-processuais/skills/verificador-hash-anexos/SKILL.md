---
name: verificador-hash-anexos
description: >
  VERIFICADOR-HASH-ANEXOS — Camada 1 do motor de integridade estrutural. Executa
  o parser local hash_check.py para conferir a integridade bit a bit de um
  documento ou anexo por SHA-256. Com hash declarado (recibo de protocolo, ata
  notarial, laudo, e-mail) ou arquivo de referência, compara e — se divergente —
  emite alerta com as duas hashes lado a lado, as hipóteses legítimas
  (republicação, re-OCR, carimbo) e a frase obrigatória: divergência sinalizada —
  fraude é conclusão jurídica/pericial, não técnica. Sem hash declarado, gera o
  SHA-256 do arquivo recebido para registro e cadeia de custódia informal.
  Aciona: "hash do anexo", "conferir hash", "sha256", "o arquivo foi alterado",
  "integridade do documento", "verificador de hash", "cadeia de custódia".
---

# VERIFICADOR-HASH-ANEXOS — o mesmo arquivo, bit a bit

## 1. Escopo

SHA-256 é a impressão digital de um arquivo: **um único byte alterado muda a
hash inteira**. Esta skill roda o parser determinístico para responder duas
perguntas de rotina do contencioso:

1. **"Este arquivo é o mesmo que foi declarado?"** — comparar a hash real com a
   hash declarada em recibo de protocolo eletrônico, ata notarial, laudo,
   acordo ou e-mail em que alguém afirmou "este arquivo tem a hash X".
2. **"Como eu provo amanhã que o arquivo de hoje não mudou?"** — sem hash
   declarada, gerar e registrar a hash do arquivo recebido: **cadeia de
   custódia informal**, datada, no dossiê.

**Quem calcula é o parser** (`scripts/hash_check.py`) — nunca comparação "de
olho" de nomes, tamanhos ou aparência do documento.

## 2. O limite desta skill — leia antes de usar o resultado

Hash divergente prova exatamente UMA coisa: **os dois arquivos não são
idênticos bit a bit**. Não prova adulteração, não prova má-fé, não prova
fraude. Existem hipóteses legítimas e frequentes para divergência:

| Hipótese legítima | Por que muda a hash |
|---|---|
| Republicação pelo sistema do tribunal | O sistema regrava/reprocessa o PDF |
| Re-OCR | Nova camada de texto reconhecido sobre a mesma imagem |
| Carimbo, tarja ou assinatura digital aplicada depois | Conteúdo novo somado ao arquivo |
| Conversão/reimpressão para PDF | Outro gerador, outros bytes — mesmo teor visual |

A frase que fecha todo alerta é obrigatória: **"divergência sinalizada — fraude
é conclusão jurídica/pericial, não técnica"** (T4). Se a divergência importar
juridicamente, o caminho é perícia — não o veredito desta skill.

## 3. Input

| Campo | Obrigatório | Observação |
|---|---|---|
| `arquivo` | sim | Caminho local do arquivo recebido |
| `hash_declarado` | opcional | A hash SHA-256 declarada (recibo, ata, e-mail) |
| `arquivo_referencia` | opcional | Alternativa ao hash: o outro exemplar do arquivo, para comparar os dois |

## 4. Processamento

### Fluxo A — com hash declarado

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/hash_check.py" <arquivo> --declarado <hash>
```

Retorno em JSON no stdout: `parser`, `versao`, `arquivo`, `status`,
`motor_usado`, `achados[]` (`tipo`, `gravidade`, `evidencia`, `localizacao`),
`resumo.total_achados`, `dependency_hint`.

- Hashes iguais → registrar a confirmação (arquivo + hash + data) no dossiê.
- **Divergente (`divergente: true` no retorno)** → ALERTA do §5, com as duas
  hashes lado a lado + a tabela de hipóteses legítimas + a frase obrigatória.

### Fluxo A2 — com arquivo de referência (sem hash em texto)

Rodar o parser primeiro **no arquivo de referência** (sem `--declarado`) para
obter a SHA-256 dele; depois rodar no arquivo recebido passando essa hash como
`--declarado`. Registrar no dossiê qual exemplar serviu de referência.

### Fluxo B — sem hash declarado (registro)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/hash_check.py" <arquivo>
```

Gerar a SHA-256 do recebido e registrar **hash + data da geração + origem do
arquivo** no dossiê — é a cadeia de custódia informal: permite provar depois
que o exemplar não mudou desde o registro.

### Tratamento de status (regra T1, sem exceção)

| `status` | Conduta |
|---|---|
| `ok` | Prosseguir |
| `missing_dependency` | DECLARAR: "verificação de hash não executada" + exibir o `dependency_hint`. NUNCA declarar arquivos iguais/diferentes sem o cálculo |
| `error` | Reportar o erro literal do parser |
| `formato_nao_suportado` | Informar a limitação — hash se calcula sobre o arquivo como recebido |

## 5. Output

```markdown
## 🔐 Verificação de hash — {{arquivo}}

**Parser:** hash_check.py v{{versao}} · **Status:** {{status}}

| | SHA-256 |
|---|---|
| **Declarada** | `{{hash_declarada}}` |
| **Calculada** | `{{hash_calculada}}` |

**Resultado:** [✅ idênticas · 🔴 DIVERGENTES]

[se divergente:]
### ⚠️ Alerta de divergência

- Os exemplares NÃO são idênticos bit a bit — evidência acima.
- Hipóteses legítimas a considerar antes de qualquer conclusão: republicação
  pelo sistema do tribunal · re-OCR · carimbo/tarja/assinatura aplicada depois ·
  conversão/reimpressão.
- **Divergência sinalizada — fraude é conclusão jurídica/pericial, não técnica.**
  Se a divergência for juridicamente relevante, o caminho é perícia.

[se sem hash declarada:]
### 📌 Registro para cadeia de custódia informal

- SHA-256 do arquivo recebido: `{{hash}}` · gerada em {{data}} · origem: {{origem}}

➡️ Resultado registrado no `dossie-de-integridade`.

> ⚠️ Conferência humana final é do advogado. Esta verificação sinaliza; não conclui.
```

## 6. O que esta skill nunca faz

1. Nunca declara arquivos iguais ou divergentes sem o parser ter calculado (T1).
2. Nunca conclui "o documento foi adulterado" — divergência é dado técnico com hipóteses múltiplas; fraude é conclusão jurídica/pericial (T4).
3. Nunca omite a tabela de hipóteses legítimas de um alerta de divergência.
4. Nunca apresenta o registro informal como perícia ou como cadeia de custódia formal — é registro datado, útil, com esse nome.
5. Nunca modifica o arquivo original.

## 7. Travas desta skill

| Trava | Aplicação aqui |
|---|---|
| **T1** | Resultado só existe com o parser rodado + as duas hashes anexadas; `missing_dependency` → "verificação de hash não executada" + `dependency_hint` |
| **T4** | Hash divergente = **alerta com hipóteses legítimas**, fechado pela frase obrigatória "divergência sinalizada — fraude é conclusão jurídica/pericial, não técnica" |
| **T5** | ⚠️ Conferência humana final é do advogado — todo relatório sai com este aviso |

## 8. Integração

- **Upstream:** `auditoria-master` · `auditoria-pre-protocolo`
- **Downstream:** **`dossie-de-integridade` — todo resultado (confirmação, divergência ou registro) termina lá**
- **Cross-link:** se o achado evoluir para incidente processual, a peça é domínio dos plugins de contencioso da família — esta skill entrega a evidência técnica
