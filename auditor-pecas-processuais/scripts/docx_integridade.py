#!/usr/bin/env python3
"""docx_integridade.py — Texto escondido em arquivo Word (.docx) (auditor-pecas-processuais).

Le TODAS as partes do DOCX (corpo, cabecalho, rodape, notas, comentarios, caixas de texto,
texto alternativo de imagem, propriedades e dados anexos) e aponta texto que o leitor nao ve:

    - letra branca sobre fundo branco, ou da mesma cor do fundo (pagina, celula, realce);
    - letra menor que 4 pontos;
    - texto marcado como oculto no Word;
    - frase de comando a IA guardada em parte que nao sai no texto impresso
      (comentario, propriedades do arquivo, dados anexos, texto alternativo de imagem).

A formatacao e resolvida como o Word resolve: padrao do documento -> estilo de paragrafo ->
estilo de caractere -> formatacao direta (texto branco herdado de estilo e pego).

GRAVIDADE: escondido + frase de comando a IA -> alta; escondido sem comando -> media;
rodape/cabecalho oficial reconhecido (PJe, ICP-Brasil...) sem comando -> baixa (rebaixado,
nunca suprimido).

CONTRATO / USO:
    python3 scripts/docx_integridade.py <arquivo.docx> [--json]

PROIBICOES: sem rede; nunca modifica o arquivo; nunca inventa achado.
"""

from __future__ import annotations

import sys
import zipfile
from typing import Any

import _contrato as C
import _docx as D
import _padroes as P

PARSER = "docx_integridade"
_MAX = 240


def _grupos(texto: str) -> list[str]:
    return sorted({P.grupo_de(t) for t, *_ in P.achados_lexicos(texto)})


def analisar(path: str) -> dict[str, Any]:
    if not D.eh_docx(path):
        return C.envelope(PARSER, path, C.STATUS_FORMATO, "stdlib", [],
                          extra={"erro": "Arquivo nao e um .docx valido (falta word/document.xml)."})
    achados: list[dict[str, Any]] = []
    for z in D.ler(path):
        for _ini, _fim, motivos, texto in D.blocos_ocultos(z):
            comando = P.tem_padrao_lexico(texto)
            if comando:
                grav, wl = "alta", False
            elif z.nome in ("cabeçalho", "rodapé") and P.eh_marcador_legitimo(texto):
                grav, wl = "baixa", True
            else:
                grav, wl = "media", False
            ev = "; ".join(motivos)
            if comando:
                ev += " — o trecho tambem traz frase de comando a IA"
            if wl:
                ev += " — rodape/cabecalho oficial reconhecido (PJe/ICP/OAB): rebaixado, mantido com evidencia"
            achados.append(C.achado("texto_oculto", grav, ev, z.nome, texto=texto[:_MAX], zona=z.nome,
                                    whitelist=wl, motivos=motivos, grupos=_grupos(texto) if comando else []))
        if z.nao_exibida and P.tem_padrao_lexico(z.texto):
            achados.append(C.achado(
                "texto_oculto", "alta",
                f"frase de comando a IA guardada em {z.nome}, que nao sai no texto impresso da peca",
                z.nome, texto=z.texto.strip()[:_MAX], zona=z.nome, whitelist=False,
                motivos=[f"guardado em {z.nome}"], grupos=_grupos(z.texto),
            ))
    return C.envelope(PARSER, path, C.STATUS_OK, "stdlib", achados)


def _main(argv: list[str]) -> int:
    posicionais, _flags = C.separar_argv(argv)
    if not posicionais:
        C.emitir(C.erro(PARSER, "", "USO: python3 docx_integridade.py <arquivo.docx> [--json]"))
        return 0
    path = posicionais[0]
    msg = C.checar_arquivo(PARSER, path)
    if msg:
        C.emitir(C.erro(PARSER, path, msg))
        return 0
    try:
        env = analisar(path)
    except (zipfile.BadZipFile, Exception) as exc:  # noqa: BLE001 — erro limpo, nunca traceback
        C.emitir(C.erro(PARSER, path, f"Falha ao analisar o DOCX: {exc}"))
        return 0
    return C.emitir(env)


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
