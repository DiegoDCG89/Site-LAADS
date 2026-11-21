"""Funções auxiliares usadas nos templates e nas rotas."""
from __future__ import annotations

import html as _html
import json
import os
import re
from urllib.parse import urlparse

from markupsafe import Markup, escape

from .media import ID_RE

_ICONS: dict[str, str] | None = None
_DOMAIN_RE = re.compile(r"^[a-z0-9][a-z0-9-]*(\.[a-z0-9-]+)+(/.*)?$", re.I)


def icons() -> dict[str, str]:
    global _ICONS
    if _ICONS is None:
        path = os.path.join(os.path.dirname(__file__), "icons.json")
        with open(path, encoding="utf-8") as fh:
            _ICONS = json.load(fh)
    return _ICONS


def icon(name: str, cls: str = "h-5 w-5") -> Markup:
    """SVG inline (Lucide). Nome desconhecido cai no ícone 'zap' em vez de quebrar a página."""
    body = icons().get(name) or icons()["zap"]
    return Markup(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{escape(cls)}" '
        f'aria-hidden="true">{body}</svg>'
    )


def safe_url(value: str | None, default: str = "") -> str:
    """Só deixa passar #âncora, /caminho, http(s), mailto e tel. Bloqueia javascript:, data: etc."""
    v = (value or "").strip()
    if not v:
        return default
    if (v.startswith("#") or v.startswith("/")) and not v.startswith("//"):
        return v
    parsed = urlparse(v)
    if parsed.scheme in ("http", "https", "mailto", "tel") and (parsed.netloc or parsed.scheme in ("mailto", "tel")):
        return v
    if not parsed.scheme and _DOMAIN_RE.match(v):  # "instagram.com/la.ads" -> https://...
        return "https://" + v
    return default


def media_ref(value: str | None) -> str:
    """Normaliza o valor de um campo de imagem: id do Drive, URL http(s) ou caminho local."""
    v = (value or "").strip()
    if ID_RE.match(v):
        return v
    if v.startswith("/") and not v.startswith("//"):
        return v
    if v.startswith(("http://", "https://")):
        return v
    return ""


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]


# --------------------------------------------------------------------------- #
# Texto formatado simples (páginas legais). Tudo é escapado ANTES de aplicar a formatação.
# --------------------------------------------------------------------------- #

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def _inline(raw: str) -> str:
    out = str(escape(raw))

    def link(m: re.Match) -> str:
        url = safe_url(_html.unescape(m.group(2)))
        if not url:
            return m.group(1)
        ext = ' target="_blank" rel="noopener noreferrer"' if url.startswith("http") else ""
        return (f'<a href="{escape(url)}"{ext} class="text-electric underline-offset-4 hover:underline">'
                f"{m.group(1)}</a>")

    out = _LINK.sub(link, out)
    return _BOLD.sub(r'<strong class="font-semibold text-foreground">\1</strong>', out)


def render_rich(text: str, tokens: dict[str, str] | None = None) -> Markup:
    """`## Título`, `- lista`, **negrito**, [link](url), parágrafos por linha em branco."""
    text = (text or "").replace("\r\n", "\n")
    for key, val in (tokens or {}).items():
        text = text.replace("{" + key + "}", val)
    html_out: list[str] = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [ln.rstrip() for ln in block.split("\n") if ln.strip()]
        if lines and lines[0].startswith("## "):
            html_out.append(f'<h2 class="mt-12 font-display text-xl font-bold tracking-tight text-foreground">'
                            f"{_inline(lines[0][3:])}</h2>")
            lines = lines[1:]
        if not lines:
            continue
        if all(ln.startswith("- ") for ln in lines):
            items = "".join(f'<li class="pl-1">{_inline(ln[2:])}</li>' for ln in lines)
            html_out.append(f'<ul class="mt-4 list-disc space-y-2 pl-6 marker:text-primary">{items}</ul>')
        else:
            html_out.append(f'<p class="mt-4">{"<br>".join(_inline(ln) for ln in lines)}</p>')
    return Markup("\n".join(html_out))
