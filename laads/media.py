"""Imagens: Google Drive (produção) ou pasta local/memória (desenvolvimento).

As imagens ficam PRIVADAS no Drive. O site as entrega por `/media/<id>`, uma rota do próprio Flask que:
  1. confirma que o arquivo está na pasta configurada (ninguém baixa outros arquivos do seu Drive);
  2. devolve a imagem com cache longo na CDN do Vercel (o id nunca muda de conteúdo).
Assim não dependemos de links públicos do Drive, que o Google limita e às vezes bloqueia em <img>.
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid
from typing import Any

from .google import GoogleClient, GoogleError

DRIVE_API = "https://www.googleapis.com/drive/v3/files"
UPLOAD_API = "https://www.googleapis.com/upload/drive/v3/files"

ALLOWED_MIME = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
ID_RE = re.compile(r"^[A-Za-z0-9_-]{20,80}$")
MAX_DOWNLOAD = 4_400_000  # a resposta de uma função do Vercel também é limitada a ~4,5 MB


class MediaError(Exception):
    pass


def sniff_mime(data: bytes) -> str | None:
    """Identifica o tipo real pelo conteúdo (não confia no nome nem no Content-Type enviado)."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def safe_filename(name: str, mime: str) -> str:
    stem = re.sub(r"\.[A-Za-z0-9]+$", "", name or "imagem")
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", stem).strip("-")[:50] or "imagem"
    return f"{time.strftime('%Y%m%d-%H%M%S')}-{stem}.{ALLOWED_MIME[mime]}"


# --------------------------------------------------------------------------- #

class DriveMedia:
    kind = "drive"

    def __init__(self, client: GoogleClient, folder_id: str):
        if not ID_RE.match(folder_id):
            raise MediaError("DRIVE_FOLDER_ID inválido. Use só o código final do link da pasta.")
        self.c = client
        self.folder = folder_id
        self._verified: dict[str, tuple[str, float]] = {}

    def upload(self, filename: str, data: bytes, mime: str) -> dict[str, Any]:
        name = safe_filename(filename, mime)
        boundary = "laads" + uuid.uuid4().hex
        meta = json.dumps({"name": name, "parents": [self.folder], "mimeType": mime})
        body = (
            f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{meta}\r\n"
            f"--{boundary}\r\nContent-Type: {mime}\r\n\r\n"
        ).encode() + data + f"\r\n--{boundary}--".encode()
        r = self.c.request(
            "POST", UPLOAD_API,
            params={"uploadType": "multipart", "supportsAllDrives": "true",
                    "fields": "id,name,mimeType,size,createdTime"},
            data=body, headers={"Content-Type": f"multipart/related; boundary={boundary}"},
        )
        return _norm(r.json())

    def list(self, limit: int = 100) -> list[dict[str, Any]]:
        r = self.c.request("GET", DRIVE_API, params={
            "q": f"'{self.folder}' in parents and trashed = false and mimeType contains 'image/'",
            "fields": "files(id,name,mimeType,size,createdTime)",
            "orderBy": "createdTime desc", "pageSize": str(min(limit, 200)),
            "supportsAllDrives": "true", "includeItemsFromAllDrives": "true",
        })
        return [_norm(f) for f in r.json().get("files", [])]

    def delete(self, file_id: str) -> None:
        """Move para a lixeira do Drive (dá para restaurar de lá se foi engano)."""
        if self.fetch_meta(file_id) is None:
            raise MediaError("Imagem não encontrada na pasta.")
        self.c.request("PATCH", f"{DRIVE_API}/{file_id}", params={"supportsAllDrives": "true"},
                       json={"trashed": True})
        self._verified.pop(file_id, None)

    def fetch_meta(self, file_id: str) -> str | None:
        """Devolve o mime se o arquivo existe, está na nossa pasta e é imagem; senão None."""
        if not ID_RE.match(file_id):
            return None
        hit = self._verified.get(file_id)
        if hit and hit[1] > time.time():
            return hit[0]
        try:
            r = self.c.request("GET", f"{DRIVE_API}/{file_id}", params={
                "fields": "id,mimeType,parents,trashed,size", "supportsAllDrives": "true"})
        except GoogleError as exc:
            if exc.status in (403, 404):
                return None
            raise
        m = r.json()
        if m.get("trashed") or self.folder not in (m.get("parents") or []) or m.get("mimeType") not in ALLOWED_MIME:
            return None
        if int(m.get("size", 0) or 0) > MAX_DOWNLOAD:
            return None
        self._verified[file_id] = (m["mimeType"], time.time() + 600)
        return m["mimeType"]

    def fetch(self, file_id: str) -> tuple[bytes, str] | None:
        mime = self.fetch_meta(file_id)
        if not mime:
            return None
        r = self.c.request("GET", f"{DRIVE_API}/{file_id}", params={"alt": "media", "supportsAllDrives": "true"})
        return r.content, mime

    def info(self) -> dict[str, Any]:
        r = self.c.request("GET", f"{DRIVE_API}/{self.folder}", params={
            "fields": "id,name,mimeType,capabilities(canAddChildren)", "supportsAllDrives": "true"})
        m = r.json()
        if m.get("mimeType") != "application/vnd.google-apps.folder":
            raise MediaError("DRIVE_FOLDER_ID aponta para um arquivo, não para uma pasta.")
        can_add = m.get("capabilities", {}).get("canAddChildren", True)
        return {"name": m.get("name", ""), "can_write": bool(can_add)}


def _norm(f: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f.get("id", ""), "name": f.get("name", ""), "mime": f.get("mimeType", ""),
        "size": int(f.get("size", 0) or 0), "created": f.get("createdTime", ""),
    }


# --------------------------------------------------------------------------- #

class LocalMedia:
    """Mesmo contrato do DriveMedia, guardando em disco (ou só em memória se o disco for somente leitura)."""

    kind = "local"

    def __init__(self, directory: str | None = None):
        self.dir = directory
        self._mem: dict[str, tuple[bytes, dict[str, Any]]] = {}
        if directory:
            try:
                os.makedirs(directory, exist_ok=True)
            except OSError:
                self.dir = None

    def _meta_path(self, fid: str) -> str:
        return os.path.join(self.dir or "", fid + ".json")

    def upload(self, filename: str, data: bytes, mime: str) -> dict[str, Any]:
        fid = uuid.uuid4().hex
        meta = {"id": fid, "name": safe_filename(filename, mime), "mime": mime, "size": len(data),
                "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        self._mem[fid] = (data, meta)
        if self.dir:
            try:
                with open(os.path.join(self.dir, fid + ".bin"), "wb") as fh:
                    fh.write(data)
                with open(self._meta_path(fid), "w", encoding="utf-8") as fh:
                    json.dump(meta, fh)
            except OSError:
                pass
        return meta

    def _load(self, fid: str) -> tuple[bytes, dict[str, Any]] | None:
        if not ID_RE.match(fid):
            return None
        if fid in self._mem:
            return self._mem[fid]
        if self.dir:
            try:
                with open(os.path.join(self.dir, fid + ".bin"), "rb") as fh:
                    data = fh.read()
                with open(self._meta_path(fid), encoding="utf-8") as fh:
                    return data, json.load(fh)
            except (OSError, ValueError):
                return None
        return None

    def list(self, limit: int = 100) -> list[dict[str, Any]]:
        metas = {fid: m for fid, (_, m) in self._mem.items()}
        if self.dir:
            try:
                for name in os.listdir(self.dir):
                    if name.endswith(".json"):
                        with open(os.path.join(self.dir, name), encoding="utf-8") as fh:
                            m = json.load(fh)
                            metas.setdefault(m["id"], m)
            except (OSError, ValueError, KeyError):
                pass
        return sorted(metas.values(), key=lambda m: m["created"], reverse=True)[:limit]

    def delete(self, file_id: str) -> None:
        if not self._load(file_id):
            raise MediaError("Imagem não encontrada.")
        self._mem.pop(file_id, None)
        if self.dir:
            for ext in (".bin", ".json"):
                try:
                    os.remove(os.path.join(self.dir, file_id + ext))
                except OSError:
                    pass

    def fetch(self, file_id: str) -> tuple[bytes, str] | None:
        hit = self._load(file_id)
        return (hit[0], hit[1]["mime"]) if hit else None

    def info(self) -> dict[str, Any]:
        return {"name": self.dir or "memória", "can_write": True}
