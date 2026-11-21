"""Configuração do app, 100% por variáveis de ambiente (nada de segredo no código)."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "").strip() or default)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    secret_key: str
    admin_password: str
    admin_password_hash: str
    spreadsheet_id: str
    drive_folder_id: str
    google_client_id: str
    google_client_secret: str
    google_refresh_token: str
    google_service_account_json: str
    cache_ttl: int          # segundos que o servidor guarda o conteúdo lido do Sheets
    public_cache: int       # segundos de cache na CDN do Vercel para a página pública
    timezone: str
    max_upload_bytes: int
    on_vercel: bool
    debug: bool

    @property
    def google_configured(self) -> bool:
        oauth = all([self.google_client_id, self.google_client_secret, self.google_refresh_token])
        return bool(oauth or self.google_service_account_json)

    @property
    def sheets_configured(self) -> bool:
        return bool(self.spreadsheet_id and self.google_configured)

    @property
    def drive_configured(self) -> bool:
        return bool(self.drive_folder_id and self.google_configured)

    @property
    def admin_configured(self) -> bool:
        return bool(self.admin_password or self.admin_password_hash)


def load_dotenv(path: str | None = None) -> None:
    """Lê `.env` (uso local). Não sobrescreve variáveis já definidas; ignora no Vercel."""
    if os.environ.get("VERCEL"):
        return
    path = path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        os.environ.setdefault(key.strip(), val)


def load_settings() -> Settings:
    load_dotenv()
    env = os.environ.get
    on_vercel = bool(env("VERCEL"))
    debug = env("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    secret = (env("SECRET_KEY") or "").strip()
    if not secret and not on_vercel:
        secret = "dev-only-secret-change-me"  # somente desenvolvimento local
    return Settings(
        secret_key=secret,
        admin_password=(env("ADMIN_PASSWORD") or "").strip(),
        admin_password_hash=(env("ADMIN_PASSWORD_HASH") or "").strip(),
        spreadsheet_id=(env("SPREADSHEET_ID") or "").strip(),
        drive_folder_id=(env("DRIVE_FOLDER_ID") or "").strip(),
        google_client_id=(env("GOOGLE_CLIENT_ID") or "").strip(),
        google_client_secret=(env("GOOGLE_CLIENT_SECRET") or "").strip(),
        google_refresh_token=(env("GOOGLE_REFRESH_TOKEN") or "").strip(),
        google_service_account_json=(env("GOOGLE_SERVICE_ACCOUNT_JSON") or "").strip(),
        cache_ttl=_int("CACHE_TTL", 30),
        public_cache=_int("PUBLIC_CACHE_SECONDS", 60),
        timezone=(env("TIMEZONE") or "America/Sao_Paulo").strip(),
        max_upload_bytes=_int("MAX_UPLOAD_BYTES", 4_000_000),  # Vercel limita o corpo a ~4,5 MB
        on_vercel=on_vercel,
        debug=debug,
    )
