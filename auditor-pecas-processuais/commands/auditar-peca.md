---
description: Triagem completa de integridade da peça recebida — o que está escondido, inventado ou fora de contexto, antes de você responder.
---

# /auditar-peca

Chegou peça da parte contrária (inicial, contestação, recurso)? Antes de responder, rode a triagem
de integridade nos **5 pontos**: uso de IA (sinal heurístico, a pedido) · jurisprudência inventada ·
prompt injection (texto oculto/unicode/homóglifos/comando léxico) · dispositivo de lei inexistente ou deturpado ·
gaps da tese (análise estratégica, a pedido).

**Skill a acionar:** `auditoria-master`

O master identifica **qual peça** (recebida × a própria) e **qual formato** (PDF / DOCX / texto
colado), roda o motor determinístico (C1 — parsers de `scripts/`, nunca "parece suspeito" por
leitura), passa o conteúdo pela camada de citações e dispositivos (C2 — WebFetch real, sem exceção)
e entrega pelo `dossie-de-integridade`, com opção de `gerador-topico-impugnacao` quando houver
achado confirmado.

Regra da casa: **sinal ≠ veredito**. Parser acha o fato; a conclusão jurídica (fraude, má-fé) é sua.
Nunca emitimos "foi escrito por IA" — sinal heurístico é rotulado como tal (trava T3).

Feche sempre por `validador-auditoria-vigente` e `revisao-final-auditoria`.
