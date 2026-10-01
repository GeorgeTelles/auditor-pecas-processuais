#!/usr/bin/env python3
"""_marca.py — Credito do autor e contatos, em um lugar so.

Usado por `relatorio_html.py` para o rodape do MD, do HTML e do PDF. As skills repetem a
mesma frase no texto do chat (ver `estilo-e-fronteiras`).
"""

from __future__ import annotations

PRODUTO = "Auditor de Peças Processuais"
AUTOR = "George Telles"
CREDITO = "Esta skill foi desenvolvida por George Telles."

EMAIL = "georgesmattos@gmail.com"
LINKEDIN = "https://www.linkedin.com/in/georgetelles/"
WHATSAPP_URL = "https://wa.me/5571988229457"
WHATSAPP_EXIBIDO = "(71) 98822-9457"

# (rotulo, texto exibido, url, id do icone)
CONTATOS = [
    ("E-mail", EMAIL, "mailto:" + EMAIL, "email"),
    ("LinkedIn", "linkedin.com/in/georgetelles", LINKEDIN, "linkedin"),
    ("WhatsApp", WHATSAPP_EXIBIDO, WHATSAPP_URL, "whatsapp"),
]

MARCADOR_RODAPE = "<!-- credito-autor -->"


def rodape_md() -> str:
    """Bloco markdown do credito, com os tres contatos como link."""
    links = " · ".join(f"[{rotulo}: {texto}]({url})" for rotulo, texto, url, _ in CONTATOS)
    return f"\n\n{MARCADOR_RODAPE}\n---\n\n*{CREDITO}*\n\n{links}\n"
