# -*- coding: utf-8 -*-
"""Los enlaces nunca con la cabecera Host, la bandera Secure de la cookie de quien compra, ningún mapa de la
API, correos estrictos, límites por IP en lo que manda correos y la forma de los rechazos."""
from decimal import Decimal

import pytest

from edgefolio.settings import Settings
from edgefolio.shop import FREE_LIMIT, PROOF_LIMIT
from edgefolio.web import RateLimit
from tests.conftest import outbox, proof_token, signed, visitor
from tests.test_free import FREE_ID, claim, free_file  # noqa: F401 (free_file es un fixture)



def from_evil(app, client, path, json):
    """Un POST como el de ``client`` (su sesión y su token), pero llegado con otro Host. Con un cliente sin
    tarro de cookies: el de pruebas sólo manda las suyas al host que las puso."""
    bare = app.test_client(use_cookies=False)
    cookie = client.get_cookie("zlecitool_session")
    headers = {"Host": "evil.example", "X-CSRFToken": client.environ_base["HTTP_X_CSRFTOKEN"],
               "Cookie": f"zlecitool_session={cookie.value}"}
    return bare.post(path, json=json, headers=headers)


def test_public_url_is_required_with_real_paypal(tmp_path):
    assert Settings.from_env(tmp_path, {}).paypal_mode == "fake", "en local (PayPal de prueba) no hace falta"
    live = {"PAYPAL_MODE": "live", "PAYPAL_CLIENT_ID": "id", "PAYPAL_CLIENT_SECRET": "secret"}
    with pytest.raises(ValueError, match="ZLECITOOL_PUBLIC_URL"):
        Settings.from_env(tmp_path, live)
    assert Settings.from_env(tmp_path, live, public_url="https://shop.example").paypal_mode == "live"
    with pytest.raises(ValueError, match="PAYPAL_CLIENT_ID"):
        Settings.from_env(tmp_path, {"PAYPAL_MODE": "sandbox"}, public_url="https://shop.example")
    with pytest.raises(ValueError, match="PAYPAL_MODE"):
        Settings.from_env(tmp_path, {"PAYPAL_MODE": "maybe"})


def test_the_private_folders_are_in_the_data_dir(tmp_path):
    s = Settings.from_env(tmp_path / "data" / "edgefolio", {})
    assert s.strategies_dir == tmp_path / "data" / "edgefolio" / "strategies"
    assert s.thumbs_dir == tmp_path / "data" / "edgefolio" / "thumbs" and s.fx_today.parent == s.thumbs_dir.parent
    assert Settings.from_env(tmp_path, {"STRATEGIES_DIR": "/srv/scripts"}).strategies_dir.as_posix() == "/srv/scripts"


def test_links_never_come_from_the_host_header(app, client, ids, paypal, free_file, monkeypatch):  # noqa: F811
    sent = []
    create = paypal.create_order
    paypal.create_order = lambda *a, **kw: sent.append(kw) or create(*a, **kw)
    monkeypatch.setenv("ZLECITOOL_PUBLIC_URL", "https://shop.example")
    ana = signed(app, "ana@example.com")
    assert from_evil(app, ana, "/api/mine/proofs", {"email": "ana@example.com"}).status_code == 200
    assert from_evil(app, client, "/api/free", {"id": FREE_ID, "email": "bo@example.com", "news": True}).status_code == 200
    order = from_evil(app, client, "/api/orders", {"items": [ids[0]]}).json
    bodies = [m["body"] for m in outbox()]
    links = [w for b in bodies for w in b.split() if w.startswith("http")]
    links += [order["approve_url"], sent[0]["return_url"], sent[0]["cancel_url"]]
    # confirmar el correo; .pine, .zip, Mis estrategias, novedades y su baja (2026-11-15); los de PayPal
    assert len(links) == 1 + 5 + 3, links
    assert all(u.startswith("https://shop.example/") for u in links), links
    assert "evil.example" not in "".join(bodies)


def test_without_a_public_url_nothing_goes_out_in_production(app, client, ids, free_file, monkeypatch):  # noqa: F811
    """En producción (cookies sólo por https) y sin ZLECITOOL_PUBLIC_URL, un enlace se haría con la cabecera
    Host: no se manda nada, no se apunta nada y PayPal no recibe un pedido. En local (por http) sí, con el
    host de la petición, como hace el núcleo."""
    monkeypatch.delenv("ZLECITOOL_INSECURE_COOKIES")
    r = from_evil(app, client, "/api/free", {"id": FREE_ID, "email": "bo@example.com"})
    assert r.status_code == 503 and r.json == {"error": "errLater"}
    assert from_evil(app, client, "/api/orders", {"items": [ids[0]]}).status_code == 503
    assert outbox() == []
    monkeypatch.setenv("ZLECITOOL_INSECURE_COOKIES", "1")
    assert from_evil(app, client, "/api/free", {"id": FREE_ID, "email": "bo@example.com"}).status_code == 200
    assert "http://evil.example/api/download/" in outbox("bo@example.com")[-1]["body"]
    assert claim(client, "bo@example.com").status_code == 200, "la que no salió no contó para el límite"


def test_the_buyer_cookie_is_secure_when_the_shop_is_https(app, client, ids):
    app.config["SESSION_COOKIE_SECURE"] = True   # lo que pone el núcleo sin ZLECITOOL_INSECURE_COOKIES
    order = client.post("/api/orders", json={"items": [ids[0]]})
    assert order.headers["set-cookie"].startswith("edgefolio_buyer=") and "Secure" in order.headers["set-cookie"]


def test_no_map_of_the_api(client):
    for path in ("/api/docs", "/api/openapi.json", "/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code == 404, path


BAD = ("a,b@example.com", "a;b@example.com", "<a@example.com>", "Ana <a@example.com>", "a(b)@example.com",
       '"a"@example.com', "a[b]@example.com", "a:b@example.com", "a b@example.com", "a\tb@example.com",
       "a@b@example.com", "a@example.com\r\nBcc: x@example.com", "a@exam ple.com", "a\x00@example.com",
       "a\\b@example.com", "a@example.com,b@example.com", "x" * 250 + "@example.com", "no-at-sign", "a@b")


def test_addresses_a_mail_program_would_read_differently(app, client, free_file):  # noqa: F811
    ana = signed(app, "ana@example.com")
    for bad in BAD:
        r = ana.post("/api/mine/proofs", json={"email": bad})
        assert r.status_code == 400 and r.json == {"error": "errEmailInvalid", "field": "email"}, repr(bad)
        assert claim(client, bad).status_code == 400, repr(bad)
    assert claim(client, "").json == {"error": "errEmailInvalid", "field": "email"}
    assert outbox() == []
    for good in ("ana.maria+shop@example.co.uk", "  Ana@Example.COM ", "o'neil@example.ie", "josé@example.es"):
        assert ana.post("/api/mine/proofs", json={"email": good}).json == {"sent": True}, good
    assert [m["to"] for m in outbox()] == ["ana.maria+shop@example.co.uk", "ana@example.com", "o'neil@example.ie",
                                           "josé@example.es"]


def test_proof_emails_are_limited_per_ip(app):
    ana = signed(app, "ana@example.com")
    for i in range(PROOF_LIMIT):
        assert ana.post("/api/mine/proofs", json={"email": f"p{i % 4}@example.com"}).status_code == 200
    r = ana.post("/api/mine/proofs", json={"email": "one-more@example.com"})
    assert r.status_code == 429 and r.json == {"error": "errTooMany"} and outbox("one-more@example.com") == []
    ana.environ_base["REMOTE_ADDR"] = "203.0.113.9"
    assert ana.post("/api/mine/proofs", json={"email": "one-more@example.com"}).status_code == 200
    assert proof_token("one-more@example.com")


def test_free_claims_are_limited_per_ip(app, client, free_file):  # noqa: F811
    for i in range(FREE_LIMIT):
        assert claim(client, f"p{i // 5}@example.com").status_code == 200
    r = claim(client, "fresh@example.com")
    assert r.status_code == 429 and r.json == {"error": "errTooMany"}
    assert outbox("fresh@example.com") == []
    other = visitor(app, ip="198.51.100.7")
    assert claim(other, "fresh@example.com").status_code == 200


def test_discount_codes_cannot_be_guessed(app, client, ids):
    # /api/quote decía de cualquier código si valía, sin límite: 300 probados en un segundo (14-11-2026). Una IP que
    # ya probó CODE_LIMIT que no valen no ve ninguno más, tampoco uno que vale; el presupuesto sin código, sí.
    from edgefolio.shop import CODE_LIMIT
    for i in range(CODE_LIMIT):
        r = client.post("/api/quote", json={"items": [ids[0]], "code": f"guess{i}"})
        assert r.status_code == 200 and r.json["code_status"] == "invalid", i
    r = client.post("/api/quote", json={"items": [ids[0]], "code": "spring20"})
    assert r.status_code == 429 and r.json == {"error": "errTooMany"}
    assert client.post("/api/orders", json={"items": [ids[0]], "code": "spring20"}).status_code == 429
    assert client.post("/api/quote", json={"items": [ids[0]]}).status_code == 200
    other = visitor(app, ip="198.51.100.8")
    assert other.post("/api/quote", json={"items": [ids[0]], "code": "spring20"}).json["code_status"] == "applied"
    # un código que vale no gasta: quien lo tiene aplicado presupuesta las veces que quiera
    for _ in range(CODE_LIMIT + 5):
        assert other.post("/api/quote", json={"items": [ids[0]], "code": "spring20"}).status_code == 200


def test_proof_emails_to_one_address_are_limited_per_day(app, monkeypatch):
    # Una cuenta podía pedir «Confirma tu correo» para la misma dirección ajena cada 61 segundos, sin fin; y crear
    # cuentas no cuesta nada (14-11-2026). Ahora, PROOF_TO_LIMIT al día por dirección, de cualquier cuenta.
    from edgefolio import proofs
    from edgefolio.shop import PROOF_TO_LIMIT
    monkeypatch.setattr(proofs, "RESEND_SECONDS", 0)
    for n in range(PROOF_TO_LIMIT + 3):
        who = signed(app, f"acct{n % 2}@example.com")
        who.environ_base["REMOTE_ADDR"] = f"203.0.113.{n + 1}"
        assert who.post("/api/mine/proofs", json={"email": "victim@example.com"}).json == {"sent": True}
    assert len(outbox("victim@example.com")) == PROOF_TO_LIMIT
    assert signed(app, "acct9@example.com").post("/api/mine/proofs", json={"email": "other@example.com"}).json == {"sent": True}
    assert len(outbox("other@example.com")) == 1


@pytest.mark.parametrize("env", [{"DISCOUNT_CODES": "spring20=20"}, {"DISCOUNT_CODES": "up=-0.10"},
                                 {"DISCOUNT_CODES": "all=1"}, {"FLAT_PRICE_CODES": "zero=0"},
                                 {"MAX_DISCOUNT": "1"}, {"MAX_DISCOUNT": "70"},
                                 {"DISCOUNT_CODES": "odd=0.125"}])     # tres decimales: las líneas no suman el total
def test_money_settings_that_make_no_sense_do_not_start(tmp_path, env):
    # «código=porcentaje» invita a escribir spring20=20: arrancaba y ese código daba el tope del 70 % (14-11-2026)
    with pytest.raises(ValueError):
        Settings.from_env(tmp_path, env)
    assert Settings.from_env(tmp_path, {"DISCOUNT_CODES": "spring20=0.20", "FLAT_PRICE_CODES": "launch=0.99",
                                        "MAX_DISCOUNT": "0.70"}).discount_codes == {"spring20": Decimal("0.20")}


def test_an_ipv6_network_shares_one_limit(app, client, free_file):  # noqa: F811
    # Un /64 es una casa o un servidor, que cambia de dirección dentro de él cuando quiere: hasta el 14-11-2026, cada
    # IPv6 tenía su límite, y bastaba con cambiar los últimos números.
    for i in range(FREE_LIMIT):
        assert claim(visitor(app, ip=f"2001:db8:1:2::{i + 1:x}"), f"p{i // 5}@example.com").status_code == 200
    assert claim(visitor(app, ip="2001:db8:1:2:ffff::9"), "fresh@example.com").status_code == 429
    assert claim(visitor(app, ip="2001:db8:1:3::1"), "fresh@example.com").status_code == 200


def test_the_limit_is_a_sliding_window():
    now = [0.0]
    limit = RateLimit(3, 60, clock=lambda: now[0])
    assert [limit.hit("ip") for _ in range(4)] == [True, True, True, False]
    assert limit.full("ip") and not limit.full("other") and not limit.full("never")
    assert limit.hit("other")
    now[0] = 30
    assert not limit.hit("ip"), "lo rechazado no cuenta, pero la ventana aún no ha pasado de los primeros"
    now[0] = 60.5
    assert [limit.hit("ip") for _ in range(4)] == [True, True, True, False]
    quiet = RateLimit(1, 10, clock=lambda: now[0])
    quiet.SWEEP_EVERY = 4
    for key in "abc":
        quiet.hit(key)
    now[0] = 100
    quiet.hit("d")
    assert set(quiet.hits) == {"d"}, "las direcciones que se callan se olvidan"


def test_invalid_requests_answer_like_the_rest_of_the_api(app, client, ids):
    ana = signed(app, "ana@example.com")
    cases = ((client, "post", "/api/free", {"json": {}}, "id"),
             (client, "post", "/api/free", {"json": {"id": FREE_ID, "email": "a@example.com", "news": "maybe"}}, "news"),
             (client, "post", "/api/quote", {"json": {"items": "not a list"}}, "items"),
             (client, "post", "/api/quote", {"json": {"items": [ids[0], 7]}}, "items"),
             (client, "post", "/api/quote", {"data": "{broken", "headers": {"Content-Type": "application/json"}}, "body"),
             (client, "post", "/api/quote", {"json": ["a list"]}, "body"),
             (client, "get", "/api/strategies?page=0", {}, "page"),
             (ana, "put", "/api/favourites/X", {"json": {"alerts": {"nv": "loud"}}}, "alerts.nv"),
             (ana, "post", "/api/mine/proofs/peek", {"json": {"token": "x" * 201}}, "token"))
    for who, method, path, kw, field in cases:
        r = getattr(who, method)(path, **kw)
        assert r.status_code == 400 and r.json == {"error": "errRequest", "field": field}, (path, r.get_data(as_text=True))
        assert r.headers["x-content-type-options"] == "nosniff", "las cabeceras de seguridad también"


def test_a_post_without_the_csrf_token_is_refused(app, ids):
    bare = app.test_client()
    r = bare.post("/api/quote", json={"items": [ids[0]]}, headers={"Sec-Fetch-Dest": "empty"})
    assert r.status_code == 400 and r.json == {"error": "errStaleForm"}
    assert bare.get("/api/strategies?size=1").status_code == 200, "lo que sólo lee, sin token"
