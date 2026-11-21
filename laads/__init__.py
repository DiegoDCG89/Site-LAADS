"""LaADS: site Flask com painel de controle, Google Sheets (banco) e Google Drive (imagens)."""
from __future__ import annotations

import logging
import os
from types import SimpleNamespace

from flask import Flask, jsonify, render_template, request, url_for

from .config import Settings, load_settings
from .content import ContentService
from .google import GoogleClient, build_session
from .media import ID_RE, DriveMedia, LocalMedia
from .security import csrf_token, is_admin
from .setup import initialize
from .store import MemoryStore, SheetsStore
from .utils import icon, icons, media_ref, safe_url

log = logging.getLogger(__name__)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_services(settings: Settings, store=None, media=None) -> SimpleNamespace:
    init_error = ""
    client = None
    if (store is None and settings.sheets_configured) or (media is None and settings.drive_configured):
        try:
            client = GoogleClient(build_session(settings))
        except Exception as exc:  # noqa: BLE001 - credencial inválida não pode derrubar o site
            init_error = f"Credenciais do Google inválidas: {exc}"
            log.error(init_error)

    if store is None:
        if client and settings.sheets_configured:
            store = SheetsStore(client, settings.spreadsheet_id)
        else:
            path = None if settings.on_vercel else os.path.join(ROOT, ".localdata", "db.json")
            store = MemoryStore(path)
            initialize(store)  # em modo local já nasce com o conteúdo original
    if media is None:
        if client and settings.drive_configured:
            media = DriveMedia(client, settings.drive_folder_id)
        else:
            media = LocalMedia(None if settings.on_vercel else os.path.join(ROOT, ".localdata", "media"))

    return SimpleNamespace(
        settings=settings, store=store, media=media,
        content=ContentService(store, settings.cache_ttl), init_error=init_error,
    )


def create_app(settings: Settings | None = None, store=None, media=None) -> Flask:
    settings = settings or load_settings()
    app = Flask(
        __name__,
        static_folder=os.path.join(ROOT, "public", "static"),  # só vale no dev; no Vercel a CDN serve public/
        static_url_path="/static",
        template_folder=os.path.join(ROOT, "templates"),
    )
    app.config.update(
        SECRET_KEY=settings.secret_key or os.urandom(32),
        MAX_CONTENT_LENGTH=settings.max_upload_bytes + 400_000,  # sobra para o multipart
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=settings.on_vercel,  # cookie só em HTTPS (Vercel); dev local usa http
        PERMANENT_SESSION_LIFETIME=60 * 60 * 12,
        JSON_AS_ASCII=False,
        TEMPLATES_AUTO_RELOAD=settings.debug,
    )
    app.extensions["laads"] = build_services(settings, store, media)

    asset_version = (os.environ.get("VERCEL_GIT_COMMIT_SHA") or "")[:8] or _css_mtime()

    def img_url(value: str | None) -> str:
        ref = media_ref(value)
        if ID_RE.match(ref):
            return url_for("public.media", file_id=ref)
        return ref

    # Globals (e não context_processor) para que também funcionem dentro de macros importados.
    app.jinja_env.globals.update(
        icon=icon, icon_names=sorted(icons()), safe_url=safe_url, img_url=img_url,
        csrf_token=csrf_token, is_admin=is_admin, asset_v=asset_version,
    )

    from .admin import bp as admin_bp
    from .public import bp as public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if resp.mimetype == "text/html":
            resp.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src https://fonts.gstatic.com; img-src 'self' data: blob:; connect-src 'self'; "
                "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
            )
        return resp

    @app.errorhandler(404)
    def not_found(_e):
        if request.path.startswith(("/admin/api/", "/api/")):
            return jsonify(error="Não encontrado."), 404
        return render_template("error.html", code=404, title="Página não encontrada",
                               text="O endereço não existe ou foi movido."), 404

    @app.errorhandler(413)
    def too_large(_e):
        return jsonify(error="Arquivo grande demais. O limite é de 4 MB."), 413

    @app.errorhandler(500)
    def server_error(_e):
        if request.path.startswith(("/admin/api/", "/api/")):
            return jsonify(error="Erro interno. Tente novamente."), 500
        return render_template("error.html", code=500, title="Algo deu errado",
                               text="Não foi possível carregar a página agora. Tente de novo em instantes."), 500

    return app


def _css_mtime() -> str:
    try:
        return str(int(os.path.getmtime(os.path.join(ROOT, "public", "static", "css", "site.css"))))
    except OSError:
        return "0"
