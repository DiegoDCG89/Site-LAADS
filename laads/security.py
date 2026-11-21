"""Login do painel, proteção CSRF e limitação de requisições."""
from __future__ import annotations

import hmac
import secrets
import time
from collections import defaultdict, deque
from functools import wraps

from flask import abort, current_app, jsonify, redirect, request, session, url_for
from werkzeug.security import check_password_hash

# --------------------------------------------------------------------------- #
# Sessão do administrador
# --------------------------------------------------------------------------- #


def is_admin() -> bool:
    return session.get("admin") is True


def check_password(password: str) -> bool:
    s = current_app.extensions["laads"].settings
    if s.admin_password_hash:
        try:
            return check_password_hash(s.admin_password_hash, password)
        except ValueError:
            return False
    if s.admin_password:
        return hmac.compare_digest(password.encode(), s.admin_password.encode())
    return False


def login_user() -> None:
    session.clear()  # troca a sessão inteira (evita fixação de sessão)
    session["admin"] = True
    session["_csrf"] = secrets.token_urlsafe(32)
    session.permanent = True


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not is_admin():
            if request.path.startswith("/admin/api/"):
                return jsonify(error="Sessão expirada. Entre novamente."), 401
            return redirect(url_for("admin.login", next=request.full_path.rstrip("?")))
        return view(*args, **kwargs)

    return wrapper


# --------------------------------------------------------------------------- #
# CSRF
# --------------------------------------------------------------------------- #


def csrf_token() -> str:
    tok = session.get("_csrf")
    if not tok:
        tok = session["_csrf"] = secrets.token_urlsafe(32)
    return tok


def verify_csrf() -> None:
    sent = request.headers.get("X-CSRF-Token") or request.form.get("_csrf") or ""
    expected = session.get("_csrf") or ""
    if not expected or not hmac.compare_digest(sent, expected):
        if request.path.startswith("/admin/api/") or request.is_json:
            abort(jsonify(error="Sessão inválida. Recarregue a página."), 403)
        abort(403)


# --------------------------------------------------------------------------- #
# Limite de requisições (melhor esforço: a memória é por instância serverless)
# --------------------------------------------------------------------------- #

_hits: dict[str, deque] = defaultdict(deque)


def rate_limited(key: str, limit: int, window: int) -> bool:
    now = time.time()
    if len(_hits) > 5000:  # evita crescer sem limite
        for k in [k for k, d in _hits.items() if not d or d[-1] < now - window]:
            _hits.pop(k, None)
    dq = _hits[key]
    while dq and dq[0] < now - window:
        dq.popleft()
    if len(dq) >= limit:
        return True
    dq.append(now)
    return False


def client_ip() -> str:
    fwd = request.headers.get("X-Forwarded-For", "")
    return (request.headers.get("X-Real-IP") or fwd.split(",")[0].strip() or request.remote_addr or "?")
