"""Painel de controle (/admin)."""
from __future__ import annotations

import csv
import io
import logging
import time
from typing import Any

from flask import (Blueprint, Response, abort, current_app, flash, jsonify, redirect, render_template,
                   request, url_for)

from .content import default_config
from .google import GoogleError, auth_mode
from .media import MediaError, sniff_mime
from .schema import (ADMIN_MENU, ALL_TABS, COLLECTION_BY_ID, CONFIG_TAB, GROUP_BY_ID, INBOX_BY_ID, F,
                     to_bool)
from .security import (admin_required, check_password, client_ip, login_user, rate_limited, verify_csrf)
from .setup import config_descriptions, initialize
from .store import StoreError, new_id
from .utils import icons, media_ref, safe_url

log = logging.getLogger(__name__)
bp = Blueprint("admin", __name__)

PAGE_SIZE = 30


def svc():
    return current_app.extensions["laads"]


# --------------------------------------------------------------------------- #
# Infra: proteção, erros amigáveis
# --------------------------------------------------------------------------- #

@bp.before_request
def guard():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        verify_csrf()


@bp.after_request
def no_cache(resp):
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    return resp


def friendly(exc: Exception) -> str:
    if isinstance(exc, GoogleError):
        msg = exc.message
        if "invalid_grant" in msg or exc.status == 401:
            return ("O Google recusou as credenciais (refresh token expirado ou revogado). Se o app OAuth está em "
                    "modo “Teste”, o token expira em 7 dias: publique o app e gere um novo GOOGLE_REFRESH_TOKEN.")
        if exc.status == 403:
            return f"Sem permissão no Google. Confira se as APIs Sheets e Drive estão ativadas e se a conta é dona do arquivo. ({msg})"
        if exc.status == 404:
            return "Planilha ou pasta não encontrada. Confira SPREADSHEET_ID e DRIVE_FOLDER_ID."
        if exc.status == 429:
            return "Limite de uso do Google atingido. Aguarde um minuto e tente de novo."
        return msg
    return str(exc)


@bp.errorhandler(StoreError)
@bp.errorhandler(GoogleError)
@bp.errorhandler(MediaError)
def store_failed(exc):
    log.warning("Erro de armazenamento: %s", exc)
    if request.path.startswith("/admin/api/"):
        return jsonify(error=friendly(exc)), 502
    flash(friendly(exc), "error")
    return redirect(request.referrer or url_for("admin.dashboard"))


def invalidate() -> None:
    svc().content.invalidate()


def render(template: str, **ctx: Any):
    ctx.setdefault("menu", ADMIN_MENU)
    ctx.setdefault("collections", {**COLLECTION_BY_ID, **INBOX_BY_ID})
    ctx.setdefault("groups", GROUP_BY_ID)
    ctx.setdefault("store_kind", svc().store.kind)
    ctx.setdefault("media_kind", svc().media.kind)
    return render_template(template, **ctx)


# --------------------------------------------------------------------------- #
# Login
# --------------------------------------------------------------------------- #

def _safe_next(value: str | None) -> str:
    if value and value.startswith("/admin") and not value.startswith("//"):
        return value
    return url_for("admin.dashboard")


@bp.route("/login", methods=["GET", "POST"])
def login():
    s = svc().settings
    blocked = ""
    if not s.admin_configured:
        blocked = "Defina a variável ADMIN_PASSWORD (ou ADMIN_PASSWORD_HASH) para habilitar o painel."
    elif not s.secret_key:
        blocked = "Defina a variável SECRET_KEY (texto longo e aleatório) para habilitar o painel."
    if request.method == "POST" and not blocked:
        if rate_limited(f"login:{client_ip()}", limit=8, window=900):
            flash("Muitas tentativas. Aguarde 15 minutos.", "error")
        elif check_password(request.form.get("password", "")):
            login_user()
            return redirect(_safe_next(request.args.get("next")))
        else:
            time.sleep(0.8)  # freia tentativas em série
            flash("Senha incorreta.", "error")
    return render_template("admin/login.html", blocked=blocked), (200 if not blocked else 503)


@bp.post("/logout")
def logout():
    from flask import session

    session.clear()
    return redirect(url_for("admin.login"))


# --------------------------------------------------------------------------- #
# Painel inicial
# --------------------------------------------------------------------------- #

@bp.get("/")
@admin_required
def dashboard():
    s = svc()
    info: dict[str, Any] = {"sheets": None, "sheets_error": "", "drive": None, "drive_error": "",
                            "missing": [], "counts": {}}
    try:
        info["sheets"] = s.store.info()
        raw = s.store.fetch(ALL_TABS)
        info["missing"] = [t for t, rows in raw.items() if rows is None]
        info["counts"] = {
            "eventos": sum(1 for r in raw.get("eventos") or [] if to_bool(r.get("ativo"), True)),
            "inscricoes_novas": sum(1 for r in raw.get("inscricoes") or [] if (r.get("status") or "novo") == "novo"),
            "inscricoes": len(raw.get("inscricoes") or []),
            "mensagens_novas": sum(1 for r in raw.get("mensagens") or [] if (r.get("status") or "novo") == "novo"),
            "mensagens": len(raw.get("mensagens") or []),
        }
    except Exception as exc:  # noqa: BLE001
        info["sheets_error"] = friendly(exc)
    try:
        info["drive"] = s.media.info()
    except Exception as exc:  # noqa: BLE001
        info["drive_error"] = friendly(exc)
    return render("admin/dashboard.html", info=info, init_error=s.init_error,
                  auth_mode=auth_mode(s.settings), settings=s.settings, tabs=ALL_TABS)


@bp.post("/sistema/iniciar")
@admin_required
def system_init():
    report = initialize(svc().store)
    invalidate()
    parts = []
    if report["created"]:
        parts.append("abas criadas: " + ", ".join(report["created"]))
    if report["repaired"]:
        parts.append("colunas adicionadas em: " + ", ".join(report["repaired"]))
    flash("Planilha pronta. " + ("; ".join(parts) if parts else "Nada a fazer: já estava completa."), "ok")
    return redirect(url_for("admin.dashboard"))


@bp.post("/sistema/cache")
@admin_required
def system_cache():
    invalidate()
    flash("Cache do servidor limpo. A CDN pode levar até 1 minuto para atualizar.", "ok")
    return redirect(request.referrer or url_for("admin.dashboard"))


# --------------------------------------------------------------------------- #
# Validação de campos (compartilhada por grupos e listas)
# --------------------------------------------------------------------------- #

def parse_value(f: F, form) -> tuple[str, str | None]:
    if f.type == "bool":
        vals = form.getlist(f.key)
        return ("SIM" if vals and vals[-1] == "SIM" else "NÃO"), None
    raw = form.get(f.key, "")
    v = raw.replace("\r\n", "\n").strip() if f.type == "textarea" else " ".join(raw.split())
    if len(v) > f.maxlength:
        return v, f"Máximo de {f.maxlength} caracteres (tem {len(v)})."
    if not v:
        return "", ("Campo obrigatório." if f.required else None)
    if f.type == "url":
        u = safe_url(v)
        return (u, None) if u else (v, "Link inválido. Use https://…, mailto:…, #secao ou um caminho começando com /.")
    if f.type == "image":
        r = media_ref(v)
        return (r, None) if r else (v, "Imagem inválida.")
    if f.type == "icon":
        return (v, None) if v in icons() else (v, "Ícone desconhecido.")
    if f.type == "number":
        try:
            float(v.replace(",", "."))
        except ValueError:
            return v, "Digite um número."
    if f.type == "select" and v not in f.options:
        return v, "Opção inválida."
    return v, None


def parse_form(fields) -> tuple[dict[str, str], dict[str, str]]:
    values: dict[str, str] = {}
    errors: dict[str, str] = {}
    for f in fields:
        v, err = parse_value(f, request.form)
        values[f.key] = v
        if err:
            errors[f.key] = err
    return values, errors


# --------------------------------------------------------------------------- #
# Textos (aba config)
# --------------------------------------------------------------------------- #

@bp.route("/c/<gid>", methods=["GET", "POST"])
@admin_required
def group(gid: str):
    g = GROUP_BY_ID.get(gid) or abort(404)
    rows = svc().store.fetch([CONFIG_TAB])[CONFIG_TAB]
    values = default_config()
    for r in rows or []:
        if r.get("chave") in values:
            values[r["chave"]] = r.get("valor", "")
    errors: dict[str, str] = {}
    if request.method == "POST":
        new_values, errors = parse_form(g.fields)
        values.update(new_values)
        if not errors:
            svc().store.config_set(new_values, config_descriptions())
            invalidate()
            flash("Alterações salvas. O site já usa o novo conteúdo (a CDN pode levar até 1 minuto).", "ok")
            return redirect(url_for("admin.group", gid=gid))
        flash("Corrija os campos destacados.", "error")
    return render("admin/group.html", g=g, values=values, errors=errors, needs_init=rows is None)


# --------------------------------------------------------------------------- #
# Listas
# --------------------------------------------------------------------------- #

def _load_rows(col) -> list[dict[str, str]] | None:
    rows = svc().store.fetch([col.id])[col.id]
    if rows is None:
        return None
    if any(not r.get("id") for r in rows):  # linhas digitadas direto na planilha ganham id
        svc().store.fill_missing_ids(col.id)
        rows = svc().store.fetch([col.id])[col.id] or []
    return rows


def _order_key(r: dict[str, str]):
    try:
        o = float(r.get("ordem", ""))
    except ValueError:
        o = 1e6
    return o, int(r.get("_row", "0") or 0)


def _list_item(col, r: dict[str, str]) -> dict[str, Any]:
    meta = [r.get(k, "") for k in col.meta_keys if r.get(k, "")]
    return {
        "id": r["id"], "label": (r.get(col.label_key) or "(sem título)")[:110],
        "meta": " · ".join(meta)[:120], "image": r.get(col.image_key, "") if col.image_key else "",
        "ativo": to_bool(r.get("ativo"), True), "icon": r.get("icone", ""),
    }


@bp.get("/l/<cid>")
@admin_required
def list_view(cid: str):
    col = COLLECTION_BY_ID.get(cid) or abort(404)
    rows = _load_rows(col)
    items = [_list_item(col, r) for r in sorted(rows or [], key=_order_key)]
    return render("admin/list.html", col=col, items=items, needs_init=rows is None)


@bp.route("/l/<cid>/novo", methods=["GET", "POST"])
@admin_required
def item_new(cid: str):
    col = COLLECTION_BY_ID.get(cid) or abort(404)
    values = {f.key: f.d for f in col.fields}
    errors: dict[str, str] = {}
    if request.method == "POST":
        values, errors = parse_form(col.fields)
        if not errors:
            rows = _load_rows(col)
            if rows is None:
                raise StoreError("Planilha não inicializada. Use “Inicializar planilha” no painel inicial.")
            nxt = max([int(float(r.get("ordem") or 0)) for r in rows if _is_num(r.get("ordem"))] + [0]) + 1
            svc().store.append(col.id, {"id": new_id(), "ordem": str(nxt), "ativo": "SIM", **values}, col.headers)
            invalidate()
            flash("Item criado.", "ok")
            return redirect(url_for("admin.list_view", cid=cid))
        flash("Corrija os campos destacados.", "error")
    return render("admin/item.html", col=col, values=values, errors=errors, item_id=None)


def _is_num(v: Any) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


@bp.route("/l/<cid>/<rid>/editar", methods=["GET", "POST"])
@admin_required
def item_edit(cid: str, rid: str):
    col = COLLECTION_BY_ID.get(cid) or abort(404)
    rows = _load_rows(col)
    row = next((r for r in rows or [] if r.get("id") == rid), None) or abort(404)
    values = {f.key: row.get(f.key, "") for f in col.fields}
    errors: dict[str, str] = {}
    if request.method == "POST":
        values, errors = parse_form(col.fields)
        if not errors:
            if not svc().store.update(col.id, rid, values):
                abort(404)
            invalidate()
            flash("Alterações salvas.", "ok")
            return redirect(url_for("admin.list_view", cid=cid))
        flash("Corrija os campos destacados.", "error")
    return render("admin/item.html", col=col, values=values, errors=errors, item_id=rid)


@bp.post("/l/<cid>/<rid>/excluir")
@admin_required
def item_delete(cid: str, rid: str):
    col = COLLECTION_BY_ID.get(cid) or abort(404)
    if svc().store.delete(col.id, rid):
        invalidate()
        flash("Item excluído.", "ok")
    else:
        flash("Item não encontrado (talvez já tenha sido excluído).", "error")
    return redirect(url_for("admin.list_view", cid=cid))


@bp.post("/api/<cid>/<rid>/toggle")
@admin_required
def api_toggle(cid: str, rid: str):
    col = COLLECTION_BY_ID.get(cid) or abort(404)
    active = bool((request.get_json(silent=True) or {}).get("ativo"))
    if not svc().store.update(col.id, rid, {"ativo": "SIM" if active else "NÃO"}):
        return jsonify(error="Item não encontrado."), 404
    invalidate()
    return jsonify(ok=True, ativo=active)


@bp.post("/api/<cid>/ordem")
@admin_required
def api_reorder(cid: str):
    col = COLLECTION_BY_ID.get(cid) or abort(404)
    ids = (request.get_json(silent=True) or {}).get("ids")
    if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids) or len(ids) > 500:
        return jsonify(error="Pedido inválido."), 400
    svc().store.set_order(col.id, ids)
    invalidate()
    return jsonify(ok=True)


# --------------------------------------------------------------------------- #
# Caixas de entrada
# --------------------------------------------------------------------------- #

def _inbox_rows(col) -> list[dict[str, str]]:
    rows = _load_rows(col)
    if rows is None:
        raise StoreError("Planilha não inicializada. Use “Inicializar planilha” no painel inicial.")
    return sorted(rows, key=lambda r: (r.get("data_hora", ""), int(r.get("_row", "0") or 0)), reverse=True)


@bp.get("/caixa/<iid>")
@admin_required
def inbox(iid: str):
    col = INBOX_BY_ID.get(iid) or abort(404)
    rows = _inbox_rows(col)
    page = max(1, request.args.get("p", 1, type=int))
    total = len(rows)
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(page, pages)
    chunk = rows[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]
    new_count = sum(1 for r in rows if (r.get("status") or "novo") == "novo")
    return render("admin/inbox.html", col=col, rows=chunk, total=total, page=page, pages=pages, new_count=new_count)


@bp.post("/caixa/<iid>/<rid>/status")
@admin_required
def inbox_status(iid: str, rid: str):
    col = INBOX_BY_ID.get(iid) or abort(404)
    status = "lido" if request.form.get("status") == "lido" else "novo"
    svc().store.update(col.id, rid, {"status": status})
    return redirect(request.referrer or url_for("admin.inbox", iid=iid))


@bp.post("/caixa/<iid>/<rid>/excluir")
@admin_required
def inbox_delete(iid: str, rid: str):
    col = INBOX_BY_ID.get(iid) or abort(404)
    svc().store.delete(col.id, rid)
    flash("Registro excluído.", "ok")
    return redirect(request.referrer or url_for("admin.inbox", iid=iid))


@bp.get("/caixa/<iid>.csv")
@admin_required
def inbox_csv(iid: str):
    col = INBOX_BY_ID.get(iid) or abort(404)
    rows = _inbox_rows(col)

    def safe(cell: str) -> str:  # neutraliza fórmulas ao abrir no Excel/Sheets
        return "'" + cell if cell[:1] in ("=", "+", "-", "@", "\t", "\r") else cell

    out = io.StringIO()
    w = csv.writer(out)
    w.writerow([f.label for f in col.fields])
    for r in rows:
        w.writerow([safe(r.get(f.key, "")) for f in col.fields])
    data = "\ufeff" + out.getvalue()  # BOM: o Excel abre acentos corretamente
    return Response(data, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{col.id}.csv"'})


# --------------------------------------------------------------------------- #
# Imagens
# --------------------------------------------------------------------------- #

@bp.get("/midia")
@admin_required
def media_page():
    files = svc().media.list()
    return render("admin/media.html", files=files)


@bp.get("/api/midia")
@admin_required
def api_media_list():
    files = svc().media.list()
    return jsonify(files=[{**f, "url": url_for("public.media", file_id=f["id"])} for f in files])


@bp.post("/api/upload")
@admin_required
def api_upload():
    s = svc()
    f = request.files.get("file")
    if not f:
        return jsonify(error="Nenhum arquivo enviado."), 400
    data = f.read(s.settings.max_upload_bytes + 1)
    if not data:
        return jsonify(error="Arquivo vazio."), 400
    if len(data) > s.settings.max_upload_bytes:
        return jsonify(error=f"Imagem maior que {s.settings.max_upload_bytes // 1_000_000} MB. Reduza e tente de novo."), 413
    mime = sniff_mime(data)
    if not mime:
        return jsonify(error="Formato não aceito. Envie JPG, PNG, WebP ou GIF."), 400
    meta = s.media.upload(f.filename or "imagem", data, mime)
    return jsonify(ok=True, id=meta["id"], name=meta["name"], url=url_for("public.media", file_id=meta["id"]))


@bp.post("/api/midia/<file_id>/excluir")
@admin_required
def api_media_delete(file_id: str):
    svc().media.delete(file_id)
    return jsonify(ok=True)
