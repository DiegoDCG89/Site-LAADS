"""Credenciais Google + cliente HTTP fino (Sheets e Drive usam a mesma sessão).

Dois modos de autenticação, nesta ordem de preferência:

1. OAuth de usuário (GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / GOOGLE_REFRESH_TOKEN)
   -> recomendado: funciona com Gmail comum e permite enviar imagens para o seu Drive.
2. Conta de serviço (GOOGLE_SERVICE_ACCOUNT_JSON)
   -> funciona para o Sheets. No Drive só envia arquivos para *Drives compartilhados*
      (contas de serviço não têm cota de armazenamento no "Meu Drive").
"""
from __future__ import annotations

import base64
import json
import logging
import time
from typing import Any

from .config import Settings

log = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
TOKEN_URI = "https://oauth2.googleapis.com/token"


class GoogleError(Exception):
    """Erro devolvido pela API do Google (ou falha de rede)."""

    def __init__(self, status: int, message: str):
        super().__init__(f"[{status}] {message}")
        self.status = status
        self.message = message


def _load_service_account(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    if not raw.startswith("{"):  # aceita também o JSON em base64
        raw = base64.b64decode(raw).decode("utf-8")
    info = json.loads(raw)
    if "private_key" in info:
        info["private_key"] = info["private_key"].replace("\\n", "\n")
    return info


def build_session(settings: Settings):
    """Cria uma sessão autenticada (google.auth AuthorizedSession)."""
    from google.auth.transport.requests import AuthorizedSession

    if all([settings.google_client_id, settings.google_client_secret, settings.google_refresh_token]):
        from google.oauth2.credentials import Credentials

        creds = Credentials(
            token=None,
            refresh_token=settings.google_refresh_token,
            token_uri=TOKEN_URI,
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=SCOPES,
        )
    elif settings.google_service_account_json:
        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_info(
            _load_service_account(settings.google_service_account_json), scopes=SCOPES
        )
    else:
        raise GoogleError(0, "Credenciais do Google não configuradas.")
    return AuthorizedSession(creds)


def auth_mode(settings: Settings) -> str:
    if all([settings.google_client_id, settings.google_client_secret, settings.google_refresh_token]):
        return "oauth"
    if settings.google_service_account_json:
        return "service_account"
    return "none"


class GoogleClient:
    """Envolve uma sessão `requests` com timeout, retry e erros legíveis."""

    def __init__(self, session, timeout: int = 20):
        self.session = session
        self.timeout = timeout

    def request(self, method: str, url: str, **kwargs):
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                resp = self.session.request(method, url, timeout=self.timeout, **kwargs)
            except Exception as exc:  # rede, DNS, refresh de token...
                last_exc = exc
                log.warning("Falha de rede em %s %s: %s", method, url, exc)
                if attempt < 2:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                raise GoogleError(0, f"Falha de conexão com o Google: {exc}") from exc
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(0.7 * (attempt + 1))
                continue
            if resp.status_code >= 400:
                raise GoogleError(resp.status_code, _error_message(resp))
            return resp
        raise GoogleError(0, f"Falha de conexão com o Google: {last_exc}")


def _error_message(resp) -> str:
    try:
        data = resp.json()
        err = data.get("error", {})
        if isinstance(err, dict):
            return err.get("message") or str(err)
        return data.get("error_description") or str(err)
    except Exception:
        return (resp.text or "")[:300] or f"HTTP {resp.status_code}"
