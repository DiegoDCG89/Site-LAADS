"""Armazenamento do conteúdo.

`SheetsStore`  -> Google Sheets via API REST (produção).
`MemoryStore`  -> mesmo contrato, em memória/arquivo JSON (desenvolvimento local e testes).

Contrato (os dois implementam):
    fetch(tabs)                      -> {aba: [linhas] | None}   (None = aba não existe)
    append(tab, row, headers)        -> id
    update(tab, row_id, values)      -> bool
    delete(tab, row_id)              -> bool
    set_order(tab, ids)              -> None   (grava 1..N na coluna `ordem`)
    fill_missing_ids(tab)            -> int    (dá id a linhas digitadas direto na planilha)
    config_set(items, descriptions)  -> None
    ensure_tabs(specs, seed)         -> relatório
    info()                           -> dict   (teste de conexão)

Toda escrita usa valueInputOption=RAW: o que o visitante digita NUNCA é interpretado como
fórmula pelo Google Sheets (evita injeção de fórmulas como =IMPORTXML(...)).
"""
from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from typing import Any
from urllib.parse import quote

from .google import GoogleClient, GoogleError
from .schema import CONFIG_HEADERS, CONFIG_TAB

log = logging.getLogger(__name__)

SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets"
CELL_LIMIT = 4000  # a API aceita 50.000, mas textos longos aqui indicam abuso


class StoreError(Exception):
    """Erro de armazenamento com mensagem pronta para mostrar no painel."""


def new_id() -> str:
    return uuid.uuid4().hex[:10]


def q(tab: str) -> str:
    """Nome de aba entre aspas simples, como exige a notação A1."""
    return "'" + tab.replace("'", "''") + "'"


def col_letter(n: int) -> str:
    """1 -> A, 27 -> AA."""
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def norm_header(cells: list[Any]) -> list[str]:
    return [str(c).strip().lower() for c in cells]


def clean(value: Any) -> str:
    return str(value if value is not None else "")[:CELL_LIMIT]


def parse_tab(values: list[list[Any]]) -> list[dict[str, str]]:
    """Matriz da planilha -> lista de dicts (usa a 1ª linha como cabeçalho)."""
    if not values:
        return []
    header = norm_header(values[0])
    rows: list[dict[str, str]] = []
    for i, raw in enumerate(values[1:], start=2):
        if not any(str(c).strip() for c in raw):
            continue  # ignora linhas totalmente vazias
        row = {h: (str(raw[j]) if j < len(raw) else "") for j, h in enumerate(header) if h}
        row["_row"] = str(i)
        rows.append(row)
    return rows


# --------------------------------------------------------------------------- #
# Google Sheets
# --------------------------------------------------------------------------- #

class SheetsStore:
    kind = "sheets"

    def __init__(self, client: GoogleClient, spreadsheet_id: str):
        self.c = client
        self.sid = spreadsheet_id
        self.base = f"{SHEETS_API}/{spreadsheet_id}"

    # -- leitura ----------------------------------------------------------- #

    def _get_values(self, tab: str) -> list[list[Any]]:
        r = self.c.request(
            "GET", f"{self.base}/values/{quote(q(tab), safe='')}",
            params={"valueRenderOption": "FORMATTED_VALUE", "majorDimension": "ROWS"},
        )
        return r.json().get("values", [])

    def _batch_get(self, tabs: list[str]) -> dict[str, list[list[Any]]]:
        params = [("ranges", q(t)) for t in tabs]
        params += [("valueRenderOption", "FORMATTED_VALUE"), ("majorDimension", "ROWS")]
        r = self.c.request("GET", f"{self.base}/values:batchGet", params=params)
        ranges = r.json().get("valueRanges", [])
        return {tab: (ranges[i].get("values", []) if i < len(ranges) else []) for i, tab in enumerate(tabs)}

    def tab_titles(self) -> dict[str, int]:
        r = self.c.request("GET", self.base, params={"fields": "sheets.properties(sheetId,title)"})
        return {s["properties"]["title"]: s["properties"]["sheetId"] for s in r.json().get("sheets", [])}

    def fetch(self, tabs: list[str]) -> dict[str, list[dict[str, str]] | None]:
        try:
            raw: dict[str, list[list[Any]] | None] = dict(self._batch_get(tabs))
        except GoogleError as exc:
            if exc.status != 400:  # 400 = alguma aba da lista não existe
                raise
            existing = self.tab_titles()
            present = [t for t in tabs if t in existing]
            raw = {t: None for t in tabs}
            if present:
                raw.update(self._batch_get(present))
        return {t: (None if v is None else parse_tab(v)) for t, v in raw.items()}

    # -- escrita ----------------------------------------------------------- #

    def _write_cells(self, tab: str, cells: list[tuple[int, int, str]]) -> None:
        if not cells:
            return
        data = [
            {"range": f"{q(tab)}!{col_letter(c)}{r}", "values": [[clean(v)]]}
            for r, c, v in cells
        ]
        self.c.request("POST", f"{self.base}/values:batchUpdate",
                       json={"valueInputOption": "RAW", "data": data})

    def _require_tab(self, tab: str) -> list[list[Any]]:
        try:
            return self._get_values(tab)
        except GoogleError as exc:
            if exc.status == 400:
                raise StoreError(
                    f"A aba “{tab}” não existe na planilha. Use “Inicializar planilha” no painel."
                ) from exc
            raise

    @staticmethod
    def _find_row(values: list[list[Any]], header: list[str], row_id: str) -> int | None:
        if "id" not in header:
            return None
        idc = header.index("id")
        for i, raw in enumerate(values[1:], start=2):
            if idc < len(raw) and str(raw[idc]).strip() == row_id:
                return i
        return None

    def append(self, tab: str, row: dict[str, Any], headers: list[str]) -> str:
        values = self._require_tab(tab)
        header = norm_header(values[0]) if values else []
        cells: list[tuple[int, int, str]] = []
        for h in headers:  # garante que todas as colunas do schema existam
            if h not in header:
                header.append(h)
                cells.append((1, len(header), h))
        self._write_cells(tab, cells)
        row = dict(row)
        row.setdefault("id", new_id())
        line = [clean(row.get(h, "")) for h in header]
        self.c.request(
            "POST", f"{self.base}/values/{quote(q(tab) + '!A1', safe='')}:append",
            params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
            json={"values": [line]},
        )
        return row["id"]

    def update(self, tab: str, row_id: str, values_in: dict[str, Any]) -> bool:
        values = self._require_tab(tab)
        header = norm_header(values[0]) if values else []
        r = self._find_row(values, header, row_id)
        if r is None:
            return False
        cells: list[tuple[int, int, str]] = []
        for k in values_in:
            if k not in header:
                header.append(k)
                cells.append((1, len(header), k))
        for k, v in values_in.items():
            cells.append((r, header.index(k) + 1, clean(v)))
        self._write_cells(tab, cells)
        return True

    def delete(self, tab: str, row_id: str) -> bool:
        values = self._require_tab(tab)
        header = norm_header(values[0]) if values else []
        r = self._find_row(values, header, row_id)
        if r is None:
            return False
        sheet_id = self.tab_titles()[tab]
        self.c.request("POST", f"{self.base}:batchUpdate", json={"requests": [{
            "deleteDimension": {"range": {
                "sheetId": sheet_id, "dimension": "ROWS", "startIndex": r - 1, "endIndex": r}}
        }]})
        return True

    def set_order(self, tab: str, ids: list[str]) -> None:
        values = self._require_tab(tab)
        header = norm_header(values[0]) if values else []
        cells: list[tuple[int, int, str]] = []
        if "ordem" not in header:
            header.append("ordem")
            cells.append((1, len(header), "ordem"))
        col = header.index("ordem") + 1
        pos = {rid: i + 1 for i, rid in enumerate(ids)}
        idc = header.index("id") if "id" in header else -1
        extra = len(ids)
        for i, raw in enumerate(values[1:], start=2):
            rid = str(raw[idc]).strip() if 0 <= idc < len(raw) else ""
            if rid in pos:
                cells.append((i, col, str(pos[rid])))
            elif any(str(c).strip() for c in raw):
                extra += 1
                cells.append((i, col, str(extra)))
        self._write_cells(tab, cells)

    def fill_missing_ids(self, tab: str) -> int:
        values = self._require_tab(tab)
        if not values:
            return 0
        header = norm_header(values[0])
        cells: list[tuple[int, int, str]] = []
        if "id" not in header:
            header.append("id")
            cells.append((1, len(header), "id"))
        col = header.index("id") + 1
        n = 0
        for i, raw in enumerate(values[1:], start=2):
            has_content = any(str(c).strip() for c in raw)
            current = str(raw[col - 1]).strip() if col - 1 < len(raw) else ""
            if has_content and not current:
                cells.append((i, col, new_id()))
                n += 1
        self._write_cells(tab, cells)
        return n

    def config_set(self, items: dict[str, str], descriptions: dict[str, str] | None = None) -> None:
        descriptions = descriptions or {}
        values = self._require_tab(CONFIG_TAB)
        header = norm_header(values[0]) if values else []
        if "chave" not in header or "valor" not in header:
            raise StoreError("A aba “config” precisa das colunas chave e valor. Use “Inicializar planilha”.")
        kc, vc = header.index("chave"), header.index("valor") + 1
        dc = header.index("descricao") + 1 if "descricao" in header else None
        existing = {
            str(raw[kc]).strip(): i
            for i, raw in enumerate(values[1:], start=2) if kc < len(raw) and str(raw[kc]).strip()
        }
        cells: list[tuple[int, int, str]] = []
        new_lines: list[list[str]] = []
        for key, val in items.items():
            if key in existing:
                cells.append((existing[key], vc, val))
            else:
                line = [""] * len(header)
                line[kc] = key
                line[vc - 1] = clean(val)
                if dc:
                    line[dc - 1] = descriptions.get(key, "")
                new_lines.append(line)
        self._write_cells(CONFIG_TAB, cells)
        if new_lines:
            self.c.request(
                "POST", f"{self.base}/values/{quote(q(CONFIG_TAB) + '!A1', safe='')}:append",
                params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
                json={"values": new_lines},
            )

    # -- manutenção -------------------------------------------------------- #

    def ensure_tabs(self, specs: dict[str, list[str]], seed: dict[str, list[dict[str, str]]]) -> dict[str, list[str]]:
        report: dict[str, list[str]] = {"created": [], "seeded": [], "repaired": []}
        existing = self.tab_titles()
        missing = [t for t in specs if t not in existing]
        if missing:
            self.c.request("POST", f"{self.base}:batchUpdate", json={"requests": [
                {"addSheet": {"properties": {"title": t, "gridProperties": {"frozenRowCount": 1}}}}
                for t in missing
            ]})
            report["created"] = missing
        for tab, headers in specs.items():
            values = [] if tab in missing else self._get_values(tab)
            header = norm_header(values[0]) if values else []
            if not any(header):
                rows = [headers] + [[clean(r.get(h, "")) for h in headers] for r in seed.get(tab, [])]
                self.c.request(
                    "PUT", f"{self.base}/values/{quote(q(tab) + '!A1', safe='')}",
                    params={"valueInputOption": "RAW"}, json={"values": rows},
                )
                if seed.get(tab):
                    report["seeded"].append(tab)
            else:
                cells = []
                for h in headers:
                    if h not in header:
                        header.append(h)
                        cells.append((1, len(header), h))
                if cells:
                    self._write_cells(tab, cells)
                    report["repaired"].append(tab)
        return report

    def info(self) -> dict[str, Any]:
        r = self.c.request("GET", self.base, params={"fields": "properties.title,spreadsheetUrl,sheets.properties.title"})
        data = r.json()
        return {
            "title": data.get("properties", {}).get("title", ""),
            "url": data.get("spreadsheetUrl", ""),
            "tabs": [s["properties"]["title"] for s in data.get("sheets", [])],
        }


# --------------------------------------------------------------------------- #
# Memória / arquivo local (desenvolvimento e testes)
# --------------------------------------------------------------------------- #

class MemoryStore:
    kind = "local"

    def __init__(self, path: str | None = None):
        self.path = path
        self._lock = threading.RLock()
        self.tabs: dict[str, dict[str, Any]] = {}
        if path and os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as fh:
                    self.tabs = json.load(fh)
            except (OSError, ValueError):
                log.warning("Não foi possível ler %s; começando vazio.", path)

    def _save(self) -> None:
        if not self.path:
            return
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump(self.tabs, fh, ensure_ascii=False, indent=1)
        except OSError:
            pass  # sistema de arquivos somente leitura: segue só em memória

    def _tab(self, tab: str) -> dict[str, Any]:
        if tab not in self.tabs:
            raise StoreError(f"A aba “{tab}” não existe. Use “Inicializar planilha” no painel.")
        return self.tabs[tab]

    def fetch(self, tabs: list[str]) -> dict[str, list[dict[str, str]] | None]:
        with self._lock:
            out: dict[str, list[dict[str, str]] | None] = {}
            for t in tabs:
                if t not in self.tabs:
                    out[t] = None
                    continue
                out[t] = [dict(r, _row=str(i + 2)) for i, r in enumerate(self.tabs[t]["rows"])]
            return out

    def append(self, tab: str, row: dict[str, Any], headers: list[str]) -> str:
        with self._lock:
            t = self._tab(tab)
            row = {k: clean(v) for k, v in row.items()}
            row.setdefault("id", new_id())
            t["rows"].append(row)
            for h in headers:
                if h not in t["header"]:
                    t["header"].append(h)
            self._save()
            return row["id"]

    def update(self, tab: str, row_id: str, values: dict[str, Any]) -> bool:
        with self._lock:
            for r in self._tab(tab)["rows"]:
                if r.get("id") == row_id:
                    r.update({k: clean(v) for k, v in values.items()})
                    self._save()
                    return True
            return False

    def delete(self, tab: str, row_id: str) -> bool:
        with self._lock:
            t = self._tab(tab)
            n = len(t["rows"])
            t["rows"] = [r for r in t["rows"] if r.get("id") != row_id]
            self._save()
            return len(t["rows"]) != n

    def set_order(self, tab: str, ids: list[str]) -> None:
        with self._lock:
            pos = {rid: i + 1 for i, rid in enumerate(ids)}
            extra = len(ids)
            for r in self._tab(tab)["rows"]:
                if r.get("id") in pos:
                    r["ordem"] = str(pos[r["id"]])
                else:
                    extra += 1
                    r["ordem"] = str(extra)
            self._save()

    def fill_missing_ids(self, tab: str) -> int:
        with self._lock:
            n = 0
            for r in self._tab(tab)["rows"]:
                if not r.get("id"):
                    r["id"] = new_id()
                    n += 1
            self._save()
            return n

    def config_set(self, items: dict[str, str], descriptions: dict[str, str] | None = None) -> None:
        with self._lock:
            rows = self._tab(CONFIG_TAB)["rows"]
            by_key = {r.get("chave"): r for r in rows}
            for k, v in items.items():
                if k in by_key:
                    by_key[k]["valor"] = clean(v)
                else:
                    rows.append({"chave": k, "valor": clean(v), "descricao": (descriptions or {}).get(k, "")})
            self._save()

    def ensure_tabs(self, specs: dict[str, list[str]], seed: dict[str, list[dict[str, str]]]) -> dict[str, list[str]]:
        with self._lock:
            report: dict[str, list[str]] = {"created": [], "seeded": [], "repaired": []}
            for tab, headers in specs.items():
                if tab not in self.tabs:
                    self.tabs[tab] = {"header": list(headers), "rows": [dict(r) for r in seed.get(tab, [])]}
                    report["created"].append(tab)
                    if seed.get(tab):
                        report["seeded"].append(tab)
                else:
                    missing = [h for h in headers if h not in self.tabs[tab]["header"]]
                    if missing:
                        self.tabs[tab]["header"] += missing
                        report["repaired"].append(tab)
            self._save()
            return report

    def info(self) -> dict[str, Any]:
        return {"title": "Armazenamento local (sem Google Sheets)", "url": "", "tabs": list(self.tabs)}


__all__ = ["SheetsStore", "MemoryStore", "StoreError", "new_id", "CONFIG_HEADERS"]
