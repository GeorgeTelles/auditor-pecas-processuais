#!/usr/bin/env python3
"""avaliar_corpus.py — Mede a deteccao do plugin contra um corpus de prompt injection.

Roda as tres verificacoes automaticas (texto escondido, frases de comando a IA e caracteres
invisiveis/letras de outro alfabeto) em cada arquivo da pasta e compara com `gabarito.json`:

    - arquivo de ataque: cada achado esperado (tipo, grupo, zona, visivel, gravidade minima) tem
      de aparecer;
    - controle limpo: nenhum achado de gravidade media ou alta, nenhum caractere suspeito.

Imprime a tabela por arquivo, a taxa de deteccao por grupo de ataque e os alarmes falsos.
Sai com codigo 1 se faltar deteccao ou houver alarme falso.

Sem `gabarito.json` na pasta (ex.: arquivos de treinamento de terceiros), so lista o que foi
achado em cada arquivo, por grupo e local, para conferencia manual.

USO:
    python3 scripts/avaliar_corpus.py [pasta]      (padrao: scripts/fixtures/corpus)
"""

from __future__ import annotations

import io
import json
import os
import sys
import unicodedata
from contextlib import redirect_stderr
from typing import Any

import lexico_scan
import pdf_integridade
import unicode_scan
import _padroes as P

ORDEM = {"baixa": 0, "media": 1, "alta": 2}
PASTA_PADRAO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "corpus")


def _sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", (t or "").lower()) if unicodedata.category(c) != "Mn")


def rodar(path: str) -> dict[str, list[dict[str, Any]]]:
    with redirect_stderr(io.StringIO()):
        return {
            "integridade": pdf_integridade.analisar(path).get("achados", []),
            "lexico_scan": lexico_scan.analisar(path).get("achados", []),
            "unicode_scan": unicode_scan.analisar(path).get("achados", []),
        }


def _casa(a: dict[str, Any], e: dict[str, Any]) -> bool:
    if a.get("tipo") != e.get("tipo"):
        return False
    if "grupo" in e and a.get("grupo") != e["grupo"] and e["grupo"] not in (a.get("grupos") or []):
        return False
    if "tag" in e and a.get("tag") != e["tag"]:
        return False
    if "zona" in e:
        local = _sem_acento(f"{a.get('zona', '')} {a.get('localizacao', '')}")
        if _sem_acento(e["zona"]) not in local:
            return False
    if "visivel" in e and a.get("visivel") is not e["visivel"]:
        return False
    if "gravidade_min" in e and ORDEM.get(a.get("gravidade", ""), -1) < ORDEM[e["gravidade_min"]]:
        return False
    return True


def avaliar(pasta: str) -> int:
    gab_path = os.path.join(pasta, "gabarito.json")
    if not os.path.exists(gab_path):
        return listar(pasta)
    gab = json.load(open(gab_path, encoding="utf-8"))
    falhas = 0
    por_grupo: dict[str, list[bool]] = {}
    alarmes: list[str] = []
    print(f"{'arquivo':44} {'resultado':10} detalhe")
    print("-" * 100)
    for item in gab:
        path = os.path.join(pasta, item["arquivo"])
        if not os.path.exists(path):
            print(f"{item['arquivo']:44} {'AUSENTE':10}")
            falhas += 1
            continue
        res = rodar(path)
        if item.get("controle"):
            ruins = [f"{p}:{a.get('tipo')}({a.get('gravidade')}) {a.get('tag', '')} {a.get('localizacao', '')}"
                     for p, lista in res.items() for a in lista
                     if p == "unicode_scan" or ORDEM.get(a.get("gravidade", ""), 0) >= 1]
            ok = not ruins
            alarmes += [f"{item['arquivo']}: {r}" for r in ruins]
            print(f"{item['arquivo']:44} {'LIMPO' if ok else 'ALARME':10} {'' if ok else '; '.join(ruins)[:200]}")
            falhas += 0 if ok else 1
            continue
        faltas = []
        for e in item["esperado"]:
            if not any(_casa(a, e) for a in res.get(e["parser"], [])):
                faltas.append(e)
        grupos = {e.get("grupo") for e in item["esperado"] if e.get("grupo")}
        for gr in grupos:
            por_grupo.setdefault(gr, []).append(not faltas)
        achou = sorted({f"{a.get('grupo') or ''}{'/' if a.get('grupo') else ''}{a.get('tipo')}@{a.get('zona') or a.get('localizacao', '')}"
                        for lista in res.values() for a in lista})
        print(f"{item['arquivo']:44} {'OK' if not faltas else 'FALHOU':10} "
              f"{'achou: ' + ', '.join(achou)[:150] if not faltas else 'faltou: ' + json.dumps(faltas, ensure_ascii=False)[:200]}")
        falhas += 1 if faltas else 0
    print("-" * 100)
    for gr in sorted(por_grupo):
        oks = por_grupo[gr]
        print(f"Grupo {gr} ({P.GRUPOS[gr]}): {sum(oks)}/{len(oks)} detectados")
    print(f"Alarmes falsos nos controles: {len(alarmes)}")
    for a in alarmes:
        print("   ", a)
    print("RESULTADO:", "100% detectado, 0 alarme falso" if falhas == 0 else f"{falhas} arquivo(s) com problema")
    return 1 if falhas else 0


def listar(pasta: str) -> int:
    for nome in sorted(os.listdir(pasta)):
        if not nome.lower().endswith((".pdf", ".docx", ".txt", ".md")):
            continue
        res = rodar(os.path.join(pasta, nome))
        print(f"\n== {nome}")
        total = 0
        for p, lista in res.items():
            for a in lista:
                total += 1
                print(f"   [{a.get('gravidade')}] {p}: {a.get('tipo')} {('grupo ' + a['grupo']) if a.get('grupo') else ''} "
                      f"em {a.get('zona') or a.get('localizacao')}: {(a.get('trecho') or a.get('texto') or a.get('evidencia', ''))[:110]}")
        if not total:
            print("   nada encontrado")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass
    sys.exit(avaliar(sys.argv[1] if len(sys.argv) > 1 else PASTA_PADRAO))
