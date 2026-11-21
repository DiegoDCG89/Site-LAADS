"""Simula (em memória) os endpoints REST do Google Sheets v4 e Drive v3 usados pelo app."""
from __future__ import annotations

import json
import re
import uuid
from urllib.parse import unquote


class Resp:
    def __init__(self, status=200, body=None, content=b""):
        self.status_code = status
        self._body = body if body is not None else {}
        self.content = content
        self.text = json.dumps(self._body)

    def json(self):
        return self._body


def err(status, msg):
    return Resp(status, {"error": {"code": status, "message": msg}})


def col_index(letters: str) -> int:
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n


class FakeGoogle:
    """Objeto com `.request(...)` no formato da sessão `requests`."""

    def __init__(self, folder="F" * 28):
        self.sheets: dict[str, dict] = {}  # título -> {"id": int, "grid": list[list[str]]}
        self.files: dict[str, dict] = {}
        self.folder = folder
        self.calls: list[tuple[str, str]] = []
        self._next_sheet = 1

    # ---- utilidades de sheet ---------------------------------------------- #
    def add_sheet(self, title):
        self.sheets[title] = {"id": self._next_sheet, "grid": []}
        self._next_sheet += 1

    def _parse_range(self, rng):
        rng = unquote(rng)
        m = re.match(r"^'((?:[^']|'')+)'(?:!(.+))?$", rng)
        title = m.group(1).replace("''", "'")
        return title, m.group(2)

    def _set(self, grid, r, c, v):
        while len(grid) < r:
            grid.append([])
        row = grid[r - 1]
        while len(row) < c:
            row.append("")
        row[c - 1] = v

    def _read(self, title, a1):
        grid = self.sheets[title]["grid"]
        rows = [list(r) for r in grid]
        for r in rows:
            while r and r[-1] == "":
                r.pop()
        while rows and not rows[-1]:
            rows.pop()
        if a1 is None:
            return rows
        m = re.match(r"^(\d+):(\d+)$", a1)
        if m:  # linhas inteiras
            return rows[int(m.group(1)) - 1: int(m.group(2))]
        raise AssertionError(f"range não suportado no fake: {a1}")

    # ---- entrada principal ------------------------------------------------- #
    def request(self, method, url, params=None, json=None, data=None, headers=None, timeout=None, **_):
        self.calls.append((method, url.split("?")[0]))
        if "sheets.googleapis.com" in url:
            return self._sheets(method, url, params, json)
        return self._drive(method, url, params, json, data, headers)

    # ---- Sheets ------------------------------------------------------------ #
    def _sheets(self, method, url, params, body):
        path = url.split("/v4/spreadsheets/", 1)[1]
        sid = path.split("/")[0].split(":")[0]
        tail = path[len(sid):]
        if tail == "" and method == "GET":
            return Resp(200, {"properties": {"title": "Planilha Teste"}, "spreadsheetUrl": "https://x/y",
                              "sheets": [{"properties": {"sheetId": s["id"], "title": t}} for t, s in self.sheets.items()]})
        if tail == ":batchUpdate":
            for req in body["requests"]:
                if "addSheet" in req:
                    title = req["addSheet"]["properties"]["title"]
                    if title in self.sheets:
                        return err(400, "already exists")
                    self.add_sheet(title)
                elif "deleteDimension" in req:
                    rg = req["deleteDimension"]["range"]
                    t = next(t for t, s in self.sheets.items() if s["id"] == rg["sheetId"])
                    del self.sheets[t]["grid"][rg["startIndex"]: rg["endIndex"]]
            return Resp(200, {})
        if tail == "/values:batchGet":
            ranges = [v for k, v in params if k == "ranges"]
            out = []
            for rng in ranges:
                title, a1 = self._parse_range(rng)
                if title not in self.sheets:
                    return err(400, f"Unable to parse range: {rng}")
                out.append({"values": self._read(title, a1)})
            return Resp(200, {"valueRanges": out})
        if tail == "/values:batchUpdate":
            for item in body["data"]:
                title, a1 = self._parse_range(item["range"])
                m = re.match(r"^([A-Z]+)(\d+)$", a1)
                self._set(self.sheets[title]["grid"], int(m.group(2)), col_index(m.group(1)), item["values"][0][0])
            return Resp(200, {})
        if tail.startswith("/values/"):
            rng = tail[len("/values/"):]
            action = None
            if rng.endswith(":append"):
                rng, action = rng[: -len(":append")], "append"
            title, a1 = self._parse_range(rng)
            if title not in self.sheets:
                return err(400, f"Unable to parse range: {rng}")
            grid = self.sheets[title]["grid"]
            if action == "append":
                for row in body["values"]:
                    grid.append(list(row))
                return Resp(200, {})
            if method == "PUT":
                for i, row in enumerate(body["values"]):
                    for j, v in enumerate(row):
                        self._set(grid, i + 1, j + 1, v)
                return Resp(200, {})
            return Resp(200, {"values": self._read(title, a1)})
        raise AssertionError(f"rota Sheets não suportada: {method} {tail}")

    # ---- Drive ------------------------------------------------------------- #
    def _drive(self, method, url, params, body, data, headers):
        if "/upload/drive/v3/files" in url:
            raw = data
            boundary = headers["Content-Type"].split("boundary=")[1].encode()
            parts = raw.split(b"--" + boundary)
            meta = json.loads(parts[1].split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n", 1)[0])
            blob = parts[2].split(b"\r\n\r\n", 1)[1][:-2]
            fid = uuid.uuid4().hex[:28]
            self.files[fid] = {"id": fid, "name": meta["name"], "mimeType": meta["mimeType"], "parents": meta["parents"],
                               "trashed": False, "size": str(len(blob)), "createdTime": "2026-11-19T10:00:00Z", "blob": blob}
            return Resp(200, {k: self.files[fid][k] for k in ("id", "name", "mimeType", "size", "createdTime")})
        fid = url.rstrip("/").split("/drive/v3/files")[1].lstrip("/")
        if not fid:  # listagem
            q = params["q"]
            res = [f for f in self.files.values()
                   if self.folder in f["parents"] and not f["trashed"] and f["mimeType"].startswith("image/")]
            assert f"'{self.folder}' in parents" in q
            return Resp(200, {"files": [{k: f[k] for k in ("id", "name", "mimeType", "size", "createdTime")} for f in res]})
        if fid == self.folder:
            return Resp(200, {"id": fid, "name": "Pasta Imagens", "mimeType": "application/vnd.google-apps.folder",
                              "capabilities": {"canAddChildren": True}})
        f = self.files.get(fid)
        if not f:
            return err(404, "File not found")
        if method == "PATCH":
            f["trashed"] = bool(body.get("trashed"))
            return Resp(200, {})
        if params.get("alt") == "media":
            return Resp(200, content=f["blob"])
        return Resp(200, {k: f[k] for k in ("id", "mimeType", "parents", "trashed", "size")})
