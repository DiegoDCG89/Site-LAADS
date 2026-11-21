"""Funções auxiliares usadas nos templates e nas rotas."""
from __future__ import annotations

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
