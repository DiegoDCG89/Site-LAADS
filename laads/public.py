"""Rotas públicas: página inicial, formulários, proxy de imagens, robots."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

from flask import (Blueprint, Response, abort, current_app, jsonify, make_response, redirect,
                   render_template, request, url_for)

from .security import client_ip, is_admin, rate_limited

log = logging.getLogger(__name__)
bp = Blueprint("public", __name__)

EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s.]{2,}$")


def svc():
    return current_app.extensions["laads"]


def now_str() -> str:
    tz_name = svc().settings.timezone
    try:
        from zoneinfo import ZoneInfo

        now = datetime.now(ZoneInfo(tz_name))
    except Exception:  # noqa: BLE001 - sem tzdata no servidor
        now = datetime.now(timezone(timedelta(hours=-3)))
    return now.strftime("%Y-%m-%d %H:%M:%S")


# --------------------------------------------------------------------------- #

@bp.get("/")
def index():
    preview = bool(request.args.get("preview")) and is_admin()
    site = svc().content.get(fresh=preview)
    resp = make_response(render_template("index.html", site=site, sent=request.args.get("enviado", "")))
    if preview or request.args.get("enviado"):
        resp.headers["Cache-Control"] = "no-store"
    else:
        ttl = svc().settings.public_cache
        resp.headers["Cache-Control"] = f"public, max-age=0, s-maxage={ttl}, stale-while-revalidate=300"
    return resp


@bp.get("/robots.txt")
def robots():
    body = ("User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /api/\n"
            f"\nSitemap: {request.url_root}sitemap.xml\n")
    return Response(body, mimetype="text/plain")


@bp.get("/sitemap.xml")
def sitemap():
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           f"<url><loc>{request.url_root}</loc></url></urlset>")
    return Response(xml, mimetype="application/xml")


@bp.get("/favicon.ico")
def favicon():
    return redirect(url_for("static", filename="favicon.svg"), code=301)


@bp.get("/healthz")
def healthz():
    s = svc()
    return jsonify(ok=True, store=s.store.kind, media=s.media.kind)


# --------------------------------------------------------------------------- #
# Imagens (proxy do Drive)
# --------------------------------------------------------------------------- #

@bp.get("/media/<file_id>")
def media(file_id: str):
    try:
        hit = svc().media.fetch(file_id)
    except Exception:  # noqa: BLE001
        log.exception("Falha ao buscar imagem %s", file_id)
        abort(502)
    if not hit:
        abort(404)
    data, mime = hit
    resp = Response(data, mimetype=mime)
    # O conteúdo de um id nunca muda: a CDN do Vercel pode guardar por um ano.
    resp.headers["Cache-Control"] = "public, max-age=86400, s-maxage=31536000, immutable"
    resp.headers["Content-Security-Policy"] = "default-src 'none'; sandbox"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


# --------------------------------------------------------------------------- #
# Formulários
# --------------------------------------------------------------------------- #

def _field(name: str, maxlen: int, multiline: bool = False) -> str:
    raw = request.form.get(name) or ""
    if multiline:
        return raw.replace("\r\n", "\n").strip()[:maxlen]
    return " ".join(raw.split())[:maxlen]


def _respond(ok: bool, anchor: str, kind: str, errors: dict | None = None, status: int = 200):
    wants_json = request.headers.get("X-Requested-With") == "fetch"
    if wants_json:
        return jsonify(ok=ok, errors=errors or {}), (200 if ok else status)
    if ok:
        return redirect(f"{url_for('public.index', enviado=kind)}#{anchor}", code=303)
    return render_template("error.html", code=status, title="Confira os dados",
                           text=" ".join((errors or {}).values()) or "Não foi possível enviar."), status


def _gate(kind: str):
    """Anti-spam: campo isca + limite por IP. Devolve resposta se deve bloquear, senão None."""
    if request.form.get("website"):  # robôs preenchem o campo escondido: finge sucesso e descarta
        return "bot"
    if rate_limited(f"form:{kind}:{client_ip()}", limit=6, window=600):
        return "limit"
    return None


@bp.post("/api/inscricao")
def inscricao():
    gate = _gate("inscricao")
    if gate == "bot":
        return _respond(True, "faca-parte", "inscricao")
    if gate == "limit":
        return _respond(False, "faca-parte", "inscricao", {"_": "Muitas tentativas. Aguarde alguns minutos."}, 429)

    nome, periodo = _field("nome", 100), _field("periodo", 20)
    telefone, email = _field("telefone", 30), _field("email", 120).lower()
    squad, mensagem = _field("squad", 60), _field("mensagem", 1000)
    errors: dict[str, str] = {}
    if len(nome) < 2:
        errors["nome"] = "Informe seu nome."
    if not periodo:
        errors["periodo"] = "Informe seu período."
    if not 8 <= len(re.sub(r"\D", "", telefone)) <= 15:
        errors["telefone"] = "Telefone inválido."
    if not EMAIL_RE.match(email):
        errors["email"] = "E-mail inválido."
    squads = [s["nome"] for s in svc().content.get()["squads"]]
    if squads and squad not in squads:
        errors["squad"] = "Escolha um squad da lista."
    if errors:
        return _respond(False, "faca-parte", "inscricao", errors, 400)
    return _save("inscricoes", {
        "data_hora": now_str(), "nome": nome, "periodo": periodo, "telefone": telefone,
        "email": email, "squad": squad, "mensagem": mensagem, "status": "novo",
    }, "faca-parte", "inscricao")


@bp.post("/api/contato")
def contato():
    gate = _gate("contato")
    if gate == "bot":
        return _respond(True, "contato", "contato")
    if gate == "limit":
        return _respond(False, "contato", "contato", {"_": "Muitas tentativas. Aguarde alguns minutos."}, 429)

    nome, email = _field("nome", 100), _field("email", 120).lower()
    mensagem = _field("mensagem", 2000, multiline=True)
    errors: dict[str, str] = {}
    if len(nome) < 2:
        errors["nome"] = "Informe seu nome."
    if not EMAIL_RE.match(email):
        errors["email"] = "E-mail inválido."
    if len(mensagem) < 5:
        errors["mensagem"] = "Escreva uma mensagem."
    if errors:
        return _respond(False, "contato", "contato", errors, 400)
    return _save("mensagens", {
        "data_hora": now_str(), "nome": nome, "email": email, "mensagem": mensagem, "status": "novo",
    }, "contato", "contato")


def _save(tab: str, row: dict, anchor: str, kind: str):
    from .schema import INBOX_BY_ID

    try:
        svc().store.append(tab, row, INBOX_BY_ID[tab].headers)
    except Exception:  # noqa: BLE001 - nunca vaze detalhes internos ao visitante
        log.exception("Falha ao gravar em %s", tab)
        return _respond(False, anchor, kind, {"_": "Não conseguimos registrar agora. Tente novamente em instantes."}, 503)
    return _respond(True, anchor, kind)
