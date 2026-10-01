#!/usr/bin/env python3
"""_contrato.py — Envelope JSON compartilhado dos parsers de integridade do auditor-pecas-processuais.

Todos os parsers (`pdf_integridade`, `unicode_scan`, `lexico_scan`, `metadados`, `hash_check`) emitem
o MESMO envelope JSON no stdout, para que a skill consiga consumir qualquer um deles do
mesmo jeito via subprocess. Este modulo centraliza a montagem desse envelope.

Contrato unico de CLI:
    python3 scripts/<parser>.py <arquivo> [--json]  ->  JSON no stdout

Formato do envelope:
    {
      "parser": "<nome>",
      "versao": "1.1.0",
      "arquivo": "<path>",
      "status": "ok" | "missing_dependency" | "error" | "formato_nao_suportado",
      "motor_usado": "<lib ou 'raw'>",
      "achados": [{"tipo": ..., "gravidade": "alta|media|baixa",
                   "evidencia": ..., "localizacao": ...}, ...],
      "resumo": {"total_achados": <int>},
      "dependency_hint": "<pip install ... quando status=missing_dependency>"
    }

Regra de exit code (todos os parsers): sai SEMPRE com 0 quando o JSON foi emitido —
o campo `status` e quem comunica o problema (dependencia ausente, erro, formato). Um
parser so sai != 0 se nao conseguir sequer emitir o JSON.

PROIBICOES (valem para todos os parsers):
- Nenhuma chamada de rede.
- Nunca modificar o arquivo de entrada.
- Nunca inventar achado: um achado so existe se o motor retornou o dado bruto.
- Onde a varredura NAO pode rodar (lib ausente, formato nao suportado), o envelope
  DECLARA isso no `status` — nunca finge ter varrido.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

VERSAO = "1.1.0"

# status possiveis (o `status` do envelope so pode ser um destes)
STATUS_OK = "ok"
STATUS_DEP = "missing_dependency"
STATUS_ERRO = "error"
STATUS_FORMATO = "formato_nao_suportado"

# gravidades possiveis (o `gravidade` de cada achado so pode ser uma destas)
GRAVIDADES = ("alta", "media", "baixa")


def achado(
    tipo: str, gravidade: str, evidencia: str, localizacao: str = "", **extra: Any
) -> dict[str, Any]:
    """Monta um achado individual. `gravidade` DEVE estar em GRAVIDADES.

    `extra` (opcional) acrescenta campos de evidencia bruta ao achado — ex.: `texto`,
    `zona`, `whitelist`. Nunca sobrescreve os quatro campos canonicos.
    """
    if gravidade not in GRAVIDADES:
        gravidade = "baixa"
    a: dict[str, Any] = {
        "tipo": tipo,
        "gravidade": gravidade,
        "evidencia": evidencia,
        "localizacao": localizacao,
    }
    for k, v in extra.items():
        if k not in a:
            a[k] = v
    return a


def envelope(
    parser: str,
    arquivo: str,
    status: str,
    motor_usado: str,
    achados: list[dict[str, Any]] | None = None,
    dependency_hint: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Monta o envelope completo. `resumo.total_achados` e calculado, nunca informado."""
    achados = achados or []
    env: dict[str, Any] = {
        "parser": parser,
        "versao": VERSAO,
        "arquivo": arquivo,
        "status": status,
        "motor_usado": motor_usado,
        "achados": achados,
        "resumo": {"total_achados": len(achados)},
        "dependency_hint": dependency_hint,
    }
    if extra:
        # nunca sobrescreve campos canonicos do envelope
        for k, v in extra.items():
            if k not in env:
                env[k] = v
    return env


def emitir(env: dict[str, Any]) -> int:
    """Imprime o envelope como JSON no stdout. Retorna 0 (JSON foi emitido)."""
    try:  # console Windows (cp1252) quebraria em texto extraido com caracteres fora do latin-1
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass
    print(json.dumps(env, ensure_ascii=False, indent=2))
    return 0


def erro(parser: str, arquivo: str, mensagem: str, motor_usado: str = "n/a") -> dict[str, Any]:
    """Envelope de erro limpo — mensagem legivel, nunca traceback cru."""
    return envelope(parser, arquivo, STATUS_ERRO, motor_usado, [], extra={"erro": mensagem})


def checar_arquivo(parser: str, arquivo: str) -> str | None:
    """Valida existencia/tipo do caminho.

    Retorna uma mensagem de erro (str) se o caminho for invalido, ou None se OK.
    O chamador emite o envelope de erro e sai com 0.
    """
    if not os.path.exists(arquivo):
        return f"Arquivo nao encontrado: {arquivo}"
    if os.path.isdir(arquivo):
        return f"O caminho e um diretorio, nao um arquivo: {arquivo}"
    return None


def separar_argv(argv: list[str]) -> tuple[list[str], set[str]]:
    """Separa argumentos posicionais de flags (`--json`, `--md5`, etc.).

    `--json` e aceito e ignorado: o JSON e o formato de saida padrao sempre.
    Flags que consomem valor (ex.: `--declarado <hash>`) sao tratadas pelo
    proprio parser antes de chamar isto — aqui e um separador simples.
    """
    posicionais: list[str] = []
    flags: set[str] = set()
    for a in argv:
        if a.startswith("--"):
            flags.add(a)
        else:
            posicionais.append(a)
    return posicionais, flags
