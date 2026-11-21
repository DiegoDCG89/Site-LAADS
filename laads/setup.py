"""Cria/repara as abas da planilha e grava o conteúdo inicial (cópia do site original)."""
from __future__ import annotations

from .defaults import DEFAULT_ROWS
from .schema import COLLECTIONS, CONFIG_HEADERS, CONFIG_TAB, GROUPS, INBOXES
from .store import new_id


def tab_specs() -> dict[str, list[str]]:
    specs = {CONFIG_TAB: list(CONFIG_HEADERS)}
    for col in (*COLLECTIONS, *INBOXES):
        specs[col.id] = col.headers
    return specs


def seed_rows() -> dict[str, list[dict[str, str]]]:
    seed: dict[str, list[dict[str, str]]] = {
        CONFIG_TAB: [{"chave": f.key, "valor": f.d, "descricao": f.label} for g in GROUPS for f in g.fields]
    }
    for col in COLLECTIONS:
        rows = []
        for i, row in enumerate(DEFAULT_ROWS.get(col.id, []), start=1):
            rows.append({"id": new_id(), "ordem": str(i), "ativo": "SIM", **row})
        seed[col.id] = rows
    return seed


def initialize(store) -> dict[str, list[str]]:
    """Idempotente: só cria o que falta e só preenche abas novas/vazias. Nunca apaga dados."""
    return store.ensure_tabs(tab_specs(), seed_rows())


def config_descriptions() -> dict[str, str]:
    return {f.key: f.label for g in GROUPS for f in g.fields}
