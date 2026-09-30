#!/usr/bin/env python3
"""hash_check.py — Hash de integridade de anexos (auditor-pecas-processuais).

Calcula sha256 (e md5 opcional) de um ou mais arquivos. Com `--declarado <hash>`,
compara o hash calculado de UM arquivo com o hash informado e reporta divergencia.

TRAVA T4 (inviolavel): divergencia de hash e um ALERTA, NUNCA um veredito de fraude.
Fraude e conclusao juridica/pericial — nao tecnica. Este parser so responde
"o conteudo binario e identico ao hash declarado? sim / nao". A leitura do que
isso significa e do advogado.

CONTRATO / USO:
    python3 scripts/hash_check.py <arquivo> [<arquivo2> ...] [--declarado <hash>] [--md5] [--json]

PROIBICOES: sem rede; nunca modifica o arquivo; nunca conclui fraude.
"""

from __future__ import annotations

import hashlib
import sys
from typing import Any

import _contrato as C

PARSER = "hash_check"
_BUF = 1024 * 1024  # 1 MiB por leitura


def _hashes(path: str, com_md5: bool) -> dict[str, str]:
    h256 = hashlib.sha256()
    hmd5 = hashlib.md5() if com_md5 else None
    with open(path, "rb") as fh:
        while True:
            bloco = fh.read(_BUF)
            if not bloco:
                break
            h256.update(bloco)
            if hmd5 is not None:
                hmd5.update(bloco)
    saida = {"sha256": h256.hexdigest()}
    if hmd5 is not None:
        saida["md5"] = hmd5.hexdigest()
    return saida


def _parse_argv(argv: list[str]) -> tuple[list[str], str | None, bool]:
    """Separa arquivos, --declarado <hash> e --md5."""
    arquivos: list[str] = []
    declarado: str | None = None
    com_md5 = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--declarado" and i + 1 < len(argv):
            declarado = argv[i + 1].strip().lower()
            i += 2
            continue
        if a == "--md5":
            com_md5 = True
            i += 1
            continue
        if a == "--json" or a.startswith("--"):
            i += 1
            continue
        arquivos.append(a)
        i += 1
    return arquivos, declarado, com_md5


def analisar(arquivos: list[str], declarado: str | None, com_md5: bool) -> dict[str, Any]:
    achados: list[dict[str, Any]] = []
    extra: dict[str, Any] = {}
    hasheados = 0  # quantos arquivos produziram hash com sucesso

    for path in arquivos:
        msg = C.checar_arquivo(PARSER, path)
        if msg:
            achados.append(C.achado("erro_arquivo", "media", msg, path))
            continue
        try:
            hs = _hashes(path, com_md5)
        except OSError as exc:
            achados.append(C.achado("erro_arquivo", "media", f"Falha ao ler: {exc}", path))
            continue

        hasheados += 1

        ev = "sha256=" + hs["sha256"] + (("  md5=" + hs["md5"]) if "md5" in hs else "")
        achados.append(C.achado("hash", "baixa", ev, path))

        # comparacao contra hash declarado (so faz sentido com 1 arquivo alvo)
        if declarado is not None and len(arquivos) == 1:
            divergente = hs["sha256"].lower() != declarado
            extra["hash_declarado"] = declarado
            extra["divergente"] = divergente
            if divergente:
                achados.append(C.achado(
                    "hash_divergente", "alta",
                    f"sha256 calculado ({hs['sha256']}) difere do declarado ({declarado}) "
                    "— ALERTA de integridade, nao veredito de fraude (trava T4)",
                    path,
                ))
            else:
                achados.append(C.achado(
                    "hash_conferido", "baixa",
                    f"sha256 calculado confere com o declarado ({declarado})",
                    path,
                ))

    arquivo_repr = arquivos[0] if len(arquivos) == 1 else f"{len(arquivos)} arquivos"
    # nenhum arquivo pode ser lido -> status error (declara o problema)
    status = C.STATUS_OK if hasheados else C.STATUS_ERRO
    return C.envelope(PARSER, arquivo_repr, status, "hashlib", achados, extra=extra or None)


def _main(argv: list[str]) -> int:
    arquivos, declarado, com_md5 = _parse_argv(argv)
    if not arquivos:
        C.emitir(C.erro(
            PARSER, "",
            "USO: python3 hash_check.py <arquivo> [<arquivo2> ...] [--declarado <hash>] [--md5] [--json]",
        ))
        return 0

    try:
        env = analisar(arquivos, declarado, com_md5)
    except Exception as exc:
        C.emitir(C.erro(PARSER, arquivos[0], f"Falha inesperada no hash: {exc}"))
        return 0

    return C.emitir(env)


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
