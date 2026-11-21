"""Lê a planilha e monta o dicionário `site` que o template index.html consome.

Resiliência (o site nunca fica fora do ar por causa do Google):
- cache em memória por instância (CACHE_TTL segundos) => poucas leituras na cota do Sheets;
- se a leitura falhar, serve a última versão boa (mesmo vencida);
- se nunca leu nada ou a aba não existe, usa o conteúdo padrão (cópia do site original).
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Any

from .defaults import DEFAULT_ROWS
from .schema import (ALL_TABS, COLLECTIONS, CONFIG_TAB, GROUPS, to_bool)
from .utils import media_ref, split_paragraphs

log = logging.getLogger(__name__)

SECTIONS = (  # id da âncora, chave do menu, chave de visibilidade
    ("eventos", "nav_eventos", "sec_eventos"),
    ("faca-parte", "nav_facaparte", "sec_facaparte"),
    ("quem-somos", "nav_quemsomos", "sec_quemsomos"),
    ("parcerias", "nav_parcerias", "sec_parcerias"),
    ("contato", "nav_contato", "sec_contato"),
)


def _order_key(row: dict[str, str]) -> tuple[float, int]:
    try:
        o = float(row.get("ordem", ""))
    except ValueError:
        o = 1e6
    return o, int(row.get("_row", "0") or 0)


def default_config() -> dict[str, str]:
    return {f.key: f.d for g in GROUPS for f in g.fields}


def build_site(raw: dict[str, list[dict[str, str]] | None], source: str = "sheets", error: str = "") -> dict[str, Any]:
    cfg = default_config()
    for row in raw.get(CONFIG_TAB) or []:
        key = (row.get("chave") or "").strip()
        if key in cfg:
            cfg[key] = row.get("valor", "")

    site: dict[str, Any] = {"cfg": cfg}
    for col in COLLECTIONS:
        rows = raw.get(col.id)
        if rows is None:  # aba inexistente -> conteúdo original
            rows = [dict(r, _row=str(i + 2)) for i, r in enumerate(DEFAULT_ROWS.get(col.id, []))]
            for i, r in enumerate(rows):
                r.setdefault("ordem", str(i + 1))
        items = []
        for r in sorted(rows, key=_order_key):
            if not to_bool(r.get("ativo"), True):
                continue
            item = {f.key: (r.get(f.key) or "").strip() for f in col.fields}
            item["id"] = r.get("id", "")
            for f in col.fields:
                if f.type == "image":
                    item[f.key] = media_ref(item[f.key])
                elif f.type == "bool":
                    item[f.key] = to_bool(item[f.key], f.d.upper() == "SIM")
            if any(item[f.key] for f in col.fields if f.required) or not any(f.required for f in col.fields):
                items.append(item)
        site[col.id] = items

    for key in ("hero_image", "og_image"):
        cfg[key] = media_ref(cfg.get(key))
    flags = {k: to_bool(cfg.get(k), True) for _, _, k in SECTIONS}
    flags["fx_boot"] = to_bool(cfg.get("fx_boot"), True)
    site["flags"] = flags
    site["nav"] = [(sid, cfg.get(nav) or sid) for sid, nav, vis in SECTIONS if flags[vis]]
    site["about_paragraphs"] = split_paragraphs(cfg.get("qs_text", ""))
    site["meta"] = {"source": source, "error": error}
    return site


class ContentService:
    def __init__(self, store, ttl: int = 30):
        self.store = store
        self.ttl = ttl
        self._lock = threading.Lock()
        self._site: dict[str, Any] | None = None
        self._at = 0.0

    def invalidate(self) -> None:
        with self._lock:
            self._at = 0.0

    def get(self, fresh: bool = False) -> dict[str, Any]:
        now = time.time()
        with self._lock:
            if not fresh and self._site is not None and now - self._at < self.ttl:
                return self._site
        try:
            raw = self.store.fetch(ALL_TABS)
            source = "sheets" if self.store.kind == "sheets" else "local"
            site = build_site(raw, source=source)
        except Exception as exc:  # noqa: BLE001 - qualquer falha deve cair no fallback
            log.exception("Falha ao ler o conteúdo; usando cache/padrão")
            with self._lock:
                if self._site is not None:
                    stale = dict(self._site)
                    stale["meta"] = {"source": "stale", "error": str(exc)}
                    self._at = now - self.ttl + 10  # tenta de novo em 10 s
                    return stale
            site = build_site({}, source="defaults", error=str(exc))
            with self._lock:
                self._site, self._at = site, now - self.ttl + 10
            return site
        with self._lock:
            self._site, self._at = site, now
        return site
