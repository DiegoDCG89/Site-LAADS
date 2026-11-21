import io
import re

import pytest

from laads import create_app
from laads.config import Settings
from laads.google import GoogleClient
from laads.media import DriveMedia, LocalMedia
from laads.setup import initialize
from laads.store import MemoryStore, SheetsStore
from tests.fakes import FakeGoogle

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
FOLDER = "F" * 28


def settings(**kw):
    base = dict(secret_key="test-secret", admin_password="senha123", admin_password_hash="", spreadsheet_id="",
                drive_folder_id="", google_client_id="", google_client_secret="", google_refresh_token="",
                google_service_account_json="", cache_ttl=0, public_cache=60, timezone="America/Sao_Paulo",
                max_upload_bytes=200_000, on_vercel=False, debug=False)
    base.update(kw)
    return Settings(**base)


def make_app(kind="memory", **kw):
    if kind == "memory":
        store, media = MemoryStore(), LocalMedia()
        initialize(store)
        return create_app(settings(**kw), store=store, media=media)
    fake = FakeGoogle(FOLDER)
    client = GoogleClient(fake)
    store = SheetsStore(client, "SID")
    media = DriveMedia(client, FOLDER)
    app = create_app(settings(spreadsheet_id="SID", drive_folder_id=FOLDER, **kw), store=store, media=media)
    app.fake = fake
    return app


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    from laads import security
    security._hits.clear()


@pytest.fixture(params=["memory", "sheets"])
def app(request):
    a = make_app(request.param)
    if request.param == "sheets":
        initialize(a.extensions["laads"].store)
    return a


def login(client):
    html = client.get("/admin/login").get_data(as_text=True)
    token = re.search(r'name="_csrf" value="([^"]+)"', html).group(1)
    r = client.post("/admin/login", data={"password": "senha123", "_csrf": token})
    assert r.status_code == 302
    return csrf(client)  # o login rotaciona o token CSRF


def csrf(client):
    html = client.get("/admin/").get_data(as_text=True)
    return re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)


# --------------------------------------------------------------------------- site público

def test_public_defaults_without_sheet():
    store = MemoryStore()  # sem abas -> conteúdo padrão
    app = create_app(settings(), store=store, media=LocalMedia())
    html = app.test_client().get("/").get_data(as_text=True)
    for text in ("CONSTRUA", "React do zero ao deploy", "Missão", "contato@laads.edu.br", "Front-end"):
        assert text in html


def test_public_reads_sheet_and_hides_inactive_and_sections(app):
    svc = app.extensions["laads"]
    ev = svc.store.fetch(["eventos"])["eventos"]
    svc.store.update("eventos", ev[0]["id"], {"ativo": "NÃO"})
    svc.store.config_set({"hero_line1": "NOVO TÍTULO", "sec_parcerias": "NÃO"})
    html = app.test_client().get("/").get_data(as_text=True)
    assert "NOVO TÍTULO" in html
    assert "React do zero ao deploy" not in html
    assert 'id="parcerias"' not in html
    assert 'href="#parcerias"' not in html
    assert "Carreira em tecnologia" in html


def test_escaping_and_unsafe_urls(app):
    svc = app.extensions["laads"]
    svc.store.config_set({"hero_text": "<script>alert(1)</script>", "hero_cta1_link": "javascript:alert(1)"})
    ev = svc.store.fetch(["eventos"])["eventos"][0]
    svc.store.update("eventos", ev["id"], {"link": "javascript:alert(2)"})
    html = app.test_client().get("/").get_data(as_text=True)
    assert "<script>alert(1)" not in html
    assert "&lt;script&gt;" in html
    assert "javascript:" not in html


def test_security_headers_and_cache(app):
    r = app.test_client().get("/")
    assert "s-maxage=60" in r.headers["Cache-Control"]
    assert "script-src 'self'" in r.headers["Content-Security-Policy"]
    assert r.headers["X-Frame-Options"] == "DENY"


def test_robots_and_404(app):
    c = app.test_client()
    assert "Disallow: /admin" in c.get("/robots.txt").get_data(as_text=True)
    assert c.get("/nao-existe").status_code == 404


# --------------------------------------------------------------------------- formulários

FORM = {"nome": "Ana Souza", "periodo": "3", "telefone": "(11) 91234-5678", "email": "ana@exemplo.com",
        "squad": "Back-end", "mensagem": "Oi!"}


def test_inscricao_ok_and_saved(app):
    c = app.test_client()
    r = c.post("/api/inscricao", data=FORM, headers={"X-Requested-With": "fetch"})
    assert r.get_json()["ok"] is True
    rows = app.extensions["laads"].store.fetch(["inscricoes"])["inscricoes"]
    assert len(rows) == 1 and rows[0]["nome"] == "Ana Souza" and rows[0]["status"] == "novo"


def test_inscricao_validation(app):
    c = app.test_client()
    bad = {**FORM, "email": "x", "telefone": "12", "squad": "Inexistente", "nome": ""}
    r = c.post("/api/inscricao", data=bad, headers={"X-Requested-With": "fetch"})
    assert r.status_code == 400
    assert set(r.get_json()["errors"]) == {"nome", "telefone", "email", "squad"}
    assert app.extensions["laads"].store.fetch(["inscricoes"])["inscricoes"] == []


def test_honeypot_and_rate_limit(app):
    c = app.test_client()
    r = c.post("/api/contato", data={"website": "spam", "nome": "x"}, headers={"X-Requested-With": "fetch"})
    assert r.get_json()["ok"] is True  # finge sucesso
    assert app.extensions["laads"].store.fetch(["mensagens"])["mensagens"] == []
    payload = {"nome": "Beto", "email": "b@b.com", "mensagem": "Olá, tudo bem?"}
    codes = [c.post("/api/contato", data=payload, headers={"X-Requested-With": "fetch", "X-Real-IP": "9.9.9.9"}).status_code
             for _ in range(8)]
    assert codes[:6] == [200] * 6 and codes[6] == 429


def test_formula_injection_is_stored_as_text():
    app = make_app("sheets")
    initialize(app.extensions["laads"].store)
    c = app.test_client()
    c.post("/api/contato", data={"nome": "=HYPERLINK(1)", "email": "a@b.com", "mensagem": "=1+1 mensagem"},
           headers={"X-Requested-With": "fetch", "X-Real-IP": "7.7.7.7"})
    grid = app.fake.sheets["mensagens"]["grid"]
    assert grid[-1][2] == "=HYPERLINK(1)"  # gravado literal (RAW), não executado
    assert all("USER_ENTERED" not in str(call) for call in app.fake.calls)


# --------------------------------------------------------------------------- painel

def test_admin_requires_login_and_csrf(app):
    c = app.test_client()
    assert c.get("/admin/").status_code == 302
    assert c.get("/admin/api/midia").status_code == 401
    assert c.post("/admin/login", data={"password": "senha123"}).status_code == 403  # sem CSRF
    token = login(c)
    assert c.post("/admin/sistema/cache", data={}).status_code == 403
    assert c.post("/admin/sistema/cache", data={"_csrf": token}).status_code == 302


def test_wrong_password(app):
    c = app.test_client()
    html = c.get("/admin/login").get_data(as_text=True)
    token = re.search(r'name="_csrf" value="([^"]+)"', html).group(1)
    r = c.post("/admin/login", data={"password": "errada", "_csrf": token})
    assert r.status_code == 200 and "Senha incorreta" in r.get_data(as_text=True)


def test_admin_disabled_without_password():
    app = make_app("memory", admin_password="")
    r = app.test_client().get("/admin/login")
    assert r.status_code == 503 and "ADMIN_PASSWORD" in r.get_data(as_text=True)


def test_all_admin_pages_render(app):
    c = app.test_client()
    login(c)
    urls = ["/admin/", "/admin/midia", "/admin/caixa/inscricoes", "/admin/caixa/mensagens"]
    from laads.schema import COLLECTIONS, GROUPS
    urls += [f"/admin/c/{g.id}" for g in GROUPS] + [f"/admin/l/{col.id}" for col in COLLECTIONS]
    urls += [f"/admin/l/{col.id}/novo" for col in COLLECTIONS]
    for u in urls:
        r = c.get(u)
        assert r.status_code == 200, u


def test_group_save_updates_site_and_validates(app):
    c = app.test_client()
    token = login(c)
    bad = c.post("/admin/c/hero", data={"_csrf": token, "hero_line1": "", "hero_cta1_link": "javascript:x"})
    assert b"Campo obrigat" in bad.data and b"Link inv" in bad.data
    form = {"_csrf": token, "hero_line1": "OLÁ MUNDO", "hero_line2": "", "hero_line3": "", "hero_chip": "x",
            "hero_typing": "", "hero_text": "Texto novo", "hero_cta1_label": "Ir", "hero_cta1_link": "#contato",
            "hero_cta2_label": "", "hero_cta2_link": "", "hud_title": "core", "hero_image": ""}
    assert c.post("/admin/c/hero", data=form).status_code == 302
    html = c.get("/").get_data(as_text=True)
    assert "OLÁ MUNDO" in html and "Texto novo" in html and 'href="#contato" class="btn-neon"' in html


def test_crud_reorder_toggle(app):
    c = app.test_client()
    token = login(c)
    new = {"_csrf": token, "data": "01 FEV", "tipo": "Meetup", "titulo": "Evento Novo", "local": "Sala 1",
           "vagas": "10", "link": "", "imagem": ""}
    assert c.post("/admin/l/eventos/novo", data=new).status_code == 302
    rows = app.extensions["laads"].store.fetch(["eventos"])["eventos"]
    assert [r["titulo"] for r in rows][-1] == "Evento Novo" and rows[-1]["ordem"] == "4"
    ids = [r["id"] for r in rows]
    # reordenar: último vira primeiro
    r = c.post("/admin/api/eventos/ordem", json={"ids": [ids[-1]] + ids[:-1]}, headers={"X-CSRF-Token": token})
    assert r.status_code == 200
    html = c.get("/").get_data(as_text=True)
    assert html.index("Evento Novo") < html.index("React do zero")
    # desativar
    r = c.post(f"/admin/api/eventos/{ids[-1]}/toggle", json={"ativo": False}, headers={"X-CSRF-Token": token})
    assert r.get_json()["ativo"] is False
    assert "Evento Novo" not in c.get("/").get_data(as_text=True)
    # editar
    edit = {**new, "titulo": "Editado", "_csrf": token}
    assert c.post(f"/admin/l/eventos/{ids[-1]}/editar", data=edit).status_code == 302
    assert "Editado" in c.get("/admin/l/eventos").get_data(as_text=True)
    # excluir
    assert c.post(f"/admin/l/eventos/{ids[-1]}/excluir", data={"_csrf": token}).status_code == 302
    rows = app.extensions["laads"].store.fetch(["eventos"])["eventos"]
    assert len(rows) == 3 and all(r["titulo"] != "Editado" for r in rows)
    # ordem inválida
    assert c.post("/admin/api/eventos/ordem", json={"ids": "x"}, headers={"X-CSRF-Token": token}).status_code == 400


def test_rows_typed_directly_in_sheet_get_ids():
    app = make_app("sheets")
    store = app.extensions["laads"].store
    initialize(store)
    grid = app.fake.sheets["squads"]["grid"]
    grid.append(["", "9", "SIM", "Mobile"])  # linha digitada à mão, sem id
    c = app.test_client()
    login(c)
    assert "Mobile" in c.get("/admin/l/squads").get_data(as_text=True)
    assert app.fake.sheets["squads"]["grid"][-1][0] != ""


def test_upload_serve_and_delete(app):
    c = app.test_client()
    token = login(c)
    h = {"X-CSRF-Token": token}
    r = c.post("/admin/api/upload", data={"file": (io.BytesIO(PNG), "logo.png")}, headers=h)
    assert r.status_code == 200, r.data
    fid = r.get_json()["id"]
    img = c.get(f"/media/{fid}")
    assert img.status_code == 200 and img.mimetype == "image/png" and img.data == PNG
    assert "immutable" in img.headers["Cache-Control"] and "sandbox" in img.headers["Content-Security-Policy"]
    # usar como logo de parceiro aparece no site
    p = {"_csrf": token, "nome": "ACME", "logo": fid, "link": "acme.com"}
    assert c.post("/admin/l/parceiros/novo", data=p).status_code == 302
    html = c.get("/").get_data(as_text=True)
    assert f"/media/{fid}" in html and 'href="https://acme.com"' in html
    assert [f["id"] for f in c.get("/admin/api/midia", headers=h).get_json()["files"]] == [fid]
    assert c.post(f"/admin/api/midia/{fid}/excluir", headers=h).status_code == 200
    assert c.get(f"/media/{fid}").status_code == 404


def test_upload_rejects_bad_files(app):
    c = app.test_client()
    h = {"X-CSRF-Token": login(c)}
    svg = b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>"
    assert c.post("/admin/api/upload", data={"file": (io.BytesIO(svg), "x.png")}, headers=h).status_code == 400
    assert c.post("/admin/api/upload", data={"file": (io.BytesIO(JPG + b"0" * 300_000), "big.jpg")}, headers=h).status_code in (413,)
    assert c.post("/admin/api/upload", data={}, headers=h).status_code == 400


def test_media_proxy_blocks_files_outside_folder():
    app = make_app("sheets")
    fake = app.fake
    fake.files["O" * 28] = {"id": "O" * 28, "name": "segredo.png", "mimeType": "image/png", "parents": ["OUTRA"],
                            "trashed": False, "size": "10", "createdTime": "", "blob": PNG}
    assert app.test_client().get("/media/" + "O" * 28).status_code == 404
    assert app.test_client().get("/media/../../etc/passwd").status_code == 404
    assert app.test_client().get("/media/curto").status_code == 404


def test_inbox_actions_and_csv(app):
    c = app.test_client()
    token = login(c)
    c.post("/api/contato", data={"nome": "=cmd|x", "email": "a@b.com", "mensagem": "Mensagem de teste"},
           headers={"X-Requested-With": "fetch", "X-Real-IP": "5.5.5.5"})
    page = c.get("/admin/caixa/mensagens").get_data(as_text=True)
    assert "Mensagem de teste" in page and "1 nova" in page
    csv_text = c.get("/admin/caixa/mensagens.csv").get_data(as_text=True)
    assert "'=cmd|x" in csv_text and csv_text.startswith("\ufeff")
    rid = app.extensions["laads"].store.fetch(["mensagens"])["mensagens"][0]["id"]
    c.post(f"/admin/caixa/mensagens/{rid}/status", data={"_csrf": token, "status": "lido"})
    assert "0 novas" in c.get("/admin/caixa/mensagens").get_data(as_text=True)
    c.post(f"/admin/caixa/mensagens/{rid}/excluir", data={"_csrf": token})
    assert app.extensions["laads"].store.fetch(["mensagens"])["mensagens"] == []


# --------------------------------------------------------------------------- Sheets específico

def test_initialize_is_idempotent_and_non_destructive():
    app = make_app("sheets")
    store = app.extensions["laads"].store
    r1 = initialize(store)
    assert "eventos" in r1["created"] and "eventos" in r1["seeded"]
    store.update("eventos", store.fetch(["eventos"])["eventos"][0]["id"], {"titulo": "Meu título"})
    r2 = initialize(store)
    assert r2 == {"created": [], "seeded": [], "repaired": []}
    assert store.fetch(["eventos"])["eventos"][0]["titulo"] == "Meu título"


def test_missing_tabs_fall_back_to_defaults_in_sheets():
    app = make_app("sheets")  # planilha vazia, nenhuma aba
    html = app.test_client().get("/").get_data(as_text=True)
    assert "React do zero ao deploy" in html
    c = app.test_client()
    login(c)
    assert b"Inicializar planilha" in c.get("/admin/l/eventos").data


def test_site_survives_google_outage():
    app = make_app("sheets")
    store = app.extensions["laads"].store
    initialize(store)
    c = app.test_client()
    assert "CONSTRUA" in c.get("/").get_data(as_text=True)

    def boom(*a, **k):
        raise RuntimeError("Google fora do ar")

    store.fetch = boom
    r = c.get("/")
    assert r.status_code == 200 and "CONSTRUA" in r.get_data(as_text=True)  # última versão boa


def test_new_column_is_added_when_missing():
    app = make_app("sheets")
    store = app.extensions["laads"].store
    initialize(store)
    app.fake.sheets["squads"]["grid"][0] = ["id", "ordem", "ativo"]  # usuário apagou a coluna "nome"
    store.append("squads", {"nome": "Mobile", "ordem": "9", "ativo": "SIM"}, ["id", "ordem", "ativo", "nome"])
    assert app.fake.sheets["squads"]["grid"][0][-1] == "nome"
    assert store.fetch(["squads"])["squads"][-1]["nome"] == "Mobile"


# --------------------------------------------------------------------------- páginas legais

def test_legal_pages_render_with_tokens(app):
    c = app.test_client()
    priv = c.get("/privacidade").get_data(as_text=True)
    terms = c.get("/termos").get_data(as_text=True)
    assert "Política de Privacidade" in priv and "LGPD" in priv and "{entidade}" not in priv and "{email}" not in priv
    assert 'href="mailto:contato@laads.edu.br"' in priv
    assert 'href="/privacidade"' in terms and "Termos de Uso" in terms
    home = c.get("/").get_data(as_text=True)
    assert 'href="/privacidade"' in home and 'href="/termos"' in home


def test_legal_text_is_editable_and_safe(app):
    svc = app.extensions["laads"]
    svc.store.config_set({"privacy_text": "## Meu título\n\n- <b>item</b>\n\n[x](javascript:alert(1)) e **forte**",
                          "legal_email": "dpo@liga.org"})
    html = app.test_client().get("/privacidade").get_data(as_text=True)
    assert "Meu título" in html and "<b>item</b>" not in html and "&lt;b&gt;item" in html
    assert "javascript:" not in html and "<strong" in html
    assert "privacidade" in app.test_client().get("/sitemap.xml").get_data(as_text=True)


def test_long_legal_text_survives_sheets_roundtrip():
    app = make_app("sheets")
    initialize(app.extensions["laads"].store)
    long_text = "## Seção\n\n" + ("Parágrafo de teste com acentuação. " * 400)  # ~14 mil caracteres
    c = app.test_client()
    token = login(c)
    from laads.schema import GROUP_BY_ID
    form = {f.key: f.d for f in GROUP_BY_ID["legal"].fields}
    form.update({"_csrf": token, "privacy_text": long_text})
    assert c.post("/admin/c/legal", data=form).status_code == 302
    assert "Parágrafo de teste" in c.get("/privacidade").get_data(as_text=True)
    stored = app.fake.sheets["config"]["grid"]
    assert any(len(row) > 1 and len(row[1]) > 10000 for row in stored)
