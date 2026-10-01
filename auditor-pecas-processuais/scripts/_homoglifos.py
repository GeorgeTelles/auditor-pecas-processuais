#!/usr/bin/env python3
"""_homoglifos.py — Tabela de letras de outros alfabetos que imitam letras latinas.

Compartilhada por `unicode_scan.py` (aponta a letra trocada) e `_padroes.py` (dobra a letra para
a latina antes de procurar frases de comando, para "Ignоre" com "о" cirilico nao escapar).
"""

from __future__ import annotations

# (d) tabela minima embutida de confusaveis (cirilico/grego -> latino).
# Chave = codepoint do confusavel; valor = (letra latina imitada, script).
HOMOGLIFOS: dict[int, tuple[str, str]] = {
    # --- cirilico minusculo ---
    0x0430: ("a", "CIRILICO"),  # а
    0x0435: ("e", "CIRILICO"),  # е
    0x043E: ("o", "CIRILICO"),  # о
    0x0440: ("p", "CIRILICO"),  # р
    0x0441: ("c", "CIRILICO"),  # с
    0x0443: ("y", "CIRILICO"),  # у
    0x0445: ("x", "CIRILICO"),  # х
    0x0456: ("i", "CIRILICO"),  # і
    0x0455: ("s", "CIRILICO"),  # ѕ
    0x0458: ("j", "CIRILICO"),  # ј
    0x04BB: ("h", "CIRILICO"),  # һ
    # --- cirilico maiusculo ---
    0x0410: ("A", "CIRILICO"),  # А
    0x0412: ("B", "CIRILICO"),  # В
    0x0415: ("E", "CIRILICO"),  # Е
    0x041A: ("K", "CIRILICO"),  # К
    0x041C: ("M", "CIRILICO"),  # М
    0x041D: ("H", "CIRILICO"),  # Н
    0x041E: ("O", "CIRILICO"),  # О
    0x0420: ("P", "CIRILICO"),  # Р
    0x0421: ("C", "CIRILICO"),  # С
    0x0422: ("T", "CIRILICO"),  # Т
    0x0425: ("X", "CIRILICO"),  # Х
    0x0423: ("Y", "CIRILICO"),  # У
    0x0406: ("I", "CIRILICO"),  # І
    # --- grego ---
    0x03BF: ("o", "GREGO"),  # ο
    0x03BD: ("v", "GREGO"),  # ν
    0x03C1: ("p", "GREGO"),  # ρ
    0x0391: ("A", "GREGO"),  # Α
    0x0392: ("B", "GREGO"),  # Β
    0x0395: ("E", "GREGO"),  # Ε
    0x0396: ("Z", "GREGO"),  # Ζ
    0x0397: ("H", "GREGO"),  # Η
    0x0399: ("I", "GREGO"),  # Ι
    0x039A: ("K", "GREGO"),  # Κ
    0x039C: ("M", "GREGO"),  # Μ
    0x039D: ("N", "GREGO"),  # Ν
    0x039F: ("O", "GREGO"),  # Ο
    0x03A1: ("P", "GREGO"),  # Ρ
    0x03A4: ("T", "GREGO"),  # Τ
    0x03A7: ("X", "GREGO"),  # Χ
    0x03A5: ("Y", "GREGO"),  # Υ
}
