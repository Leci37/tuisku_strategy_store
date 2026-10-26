# -*- coding: utf-8 -*-
"""Pagar y descargar: un fichero sólo sale del servidor por un enlace de un pedido pagado, y los enlaces del
recibo sólo van al navegador que hizo el pedido, a la cuenta que lo hizo o a la que demostró su correo. Y lo que la
cuenta ya tiene no se le vende otra vez suelto (E8)."""
import csv
import time
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from edgefolio import downloads, orders
from edgefolio.paypal import Capture
from edgefolio.shop import install
from edgefolio.web import digest
from tests.conftest import prove, signed, visitor
from tests.test_free import FREE_ID, claim, free_file  # noqa: F401 (free_file es un fixture)

BUYER = "edgefolio_buyer"


def buy(client, items, code=""):
    order = client.post("/api/orders", json={"items": items, "code": code})
    assert order.status_code == 200, order.get_data(as_text=True)
    return client.post(f"/api/orders/{order.json['id']}/capture")


def stored(app, paypal_id):
    with app.app_context():
        o = orders.find(paypal_id)
        return {c: getattr(o, c) for c in ("status", "email", "buyer_hash", "user_id", "items", "lines", "payer")}


def test_full_purchase(client, ids):
    r = buy(client, ids[:2])
    assert r.status_code == 200
    body = r.json
    assert body["status"] == "PAID" and body["total"] == "146.20"
    assert {d["ticker"] for d in body["downloads"]} == {"AAPL", "MSFT"}
    f = client.get(body["downloads"][0]["url"])
    assert f.status_code == 200 and f.get_data(as_text=True).startswith("//@version=5")
    # con el nombre del script en TradingView, el del tutorial y el del zip (antes era <id>_TW.pine)
    assert 'filename="Tuisku_AAPL_1Day_1ADX_aaaa1111.pine"' in f.headers["content-disposition"]
    assert f.headers["cache-control"] == "private, no-store"


def test_capture_twice_returns_the_same_links(client, ids):
    order = client.post("/api/orders", json={"items": [ids[0]]}).json["id"]
    first = client.post(f"/api/orders/{order}/capture").json
    again = client.post(f"/api/orders/{order}/capture").json
    assert first["downloads"][0]["url"] == again["downloads"][0]["url"]


def test_only_the_capture_that_pays_says_paid_now(app, client, ids):
    # el navegador que vuelve de PayPal vacía su carrito con paid_now; una página de gracias abierta otra vez
    # (el historial) o en otro navegador, no: antes, cualquiera vaciaba el carrito que hubiera
    order = client.post("/api/orders", json={"items": [ids[0]]}).json["id"]
    assert client.post(f"/api/orders/{order}/capture").json["paid_now"] is True
    assert client.post(f"/api/orders/{order}/capture").json["paid_now"] is False
    other = visitor(app).post(f"/api/orders/{order}/capture").json
    assert other["paid_now"] is False and other["links_hidden"] is True


def test_no_download_without_paying(client, ids):
    # un pedido creado y nunca cobrado no tiene enlaces; adivinar uno no sirve
    client.post("/api/orders", json={"items": [ids[0]]})
    assert client.get("/api/download/guessed-token").json == {"error": "errLinkNotFound"}
    r = client.post("/api/orders/FAKE-NOTREAL/capture")
    assert r.status_code == 404 and r.json == {"error": "errUnknownOrder"}


def test_payment_for_a_different_amount_is_refused(app, client, ids, paypal):
    order = client.post("/api/orders", json={"items": [ids[0]]}).json["id"]
    paypal.capture = lambda _id: Capture("COMPLETED", Decimal("0.01"), "USD", "x@example.com")
    r = client.post(f"/api/orders/{order}/capture")
    assert r.status_code == 402 and r.json == {"error": "errPayment", "paid": "0.01 USD COMPLETED"}
    assert stored(app, order)["status"] == "FAILED"
    assert client.get("/api/download/all?t=x").status_code == 404


def test_only_free_items_cannot_be_ordered(client, ids):
    r = client.post("/api/orders", json={"items": [ids[2]]})
    assert r.status_code == 400 and r.json == {"error": "errNothingToPay"}


def test_expired_link(client, ids, settings):
    settings.download_days = -1
    url = buy(client, [ids[0]]).json["downloads"][0]["url"]
    r = client.get(url)
    assert r.status_code == 410 and r.json == {"error": "errLinkExpired", "vars": {"e": "sales@tuisku.ai"}}


def test_download_limit(client, ids, settings):
    settings.max_downloads = 2
    url = buy(client, [ids[0]]).json["downloads"][0]["url"]
    assert [client.get(url).status_code for _ in range(3)] == [200, 200, 429]
    assert client.get(url).json == {"error": "errDownloadLimit"}


def test_missing_private_file(client, ids, settings):
    url = buy(client, [ids[1]]).json["downloads"][0]["url"]
    for f in settings.strategies_dir.iterdir():
        f.unlink()
    r = client.get(url)
    assert r.status_code == 404 and r.json["error"] == "errFileMissing"


def test_order_sends_the_buyer_to_paypal_and_back(client, ids, monkeypatch):
    o = client.post("/api/orders", json={"items": [ids[0]]}).json
    assert o["approve_url"] == f"http://localhost/thanks?token={o['id']}&PayerID=FAKE"
    assert o["total"] == "79.00" and o["items"] == [{"id": "AAPL_1Day_1ADX_aaaa1111", "price": "79.00"}]
    monkeypatch.setenv("ZLECITOOL_PUBLIC_URL", "https://shop.example")
    assert client.post("/api/orders", json={"items": [ids[0]]}).json["approve_url"].startswith(
        "https://shop.example/thanks?token=")


def test_receipt(app, client, ids, settings):
    body = buy(client, ids[:2]).json
    assert body["valid_days"] == settings.download_days and body["max_downloads"] == settings.max_downloads
    d = body["downloads"][0]
    assert d["id"] == "AAPL_1Day_1ADX_aaaa1111" and d["file"] == "Tuisku_AAPL_1Day_1ADX_aaaa1111"
    assert d["zip"] == d["url"] + "?format=zip" and d["price"] == 79 and d["name"] == "Apple"
    tokens = [x["url"].rsplit("/", 1)[1] for x in body["downloads"]]
    assert body["download_all"] == "/api/download/all?" + "&".join(f"t={t}" for t in tokens)
    order = stored(app, body["order_id"])
    assert order["email"] == "buyer@example.com" and order["user_id"] is None, "sin cuenta: el correo de PayPal"


def test_paypal_rest_order(monkeypatch):
    from edgefolio import paypal as pp
    sent = []

    class Answer:
        def __init__(self, body, status=201):
            self.status_code, self.body, self.text = status, body, ""

        def json(self):
            return self.body

    def post(url, **kw):
        sent.append((url, kw.get("json")))
        if url.endswith("/oauth2/token"):
            return Answer({"access_token": "T"}, 200)
        return Answer({"id": "5O190127", "links": [{"rel": "self", "href": "https://x/self"},
                                                   {"rel": "payer-action", "href": "https://paypal/checkoutnow"}]})

    monkeypatch.setattr(pp.httpx, "post", post)
    created = pp.PayPalREST("sandbox", "id", "secret").create_order(Decimal("12.50"), "USD", "edgefolio-1",
                                                                    "https://s/thanks", "https://s/?checkout=cancel")
    assert (created.id, created.approve_url) == ("5O190127", "https://paypal/checkoutnow")
    ctx = sent[-1][1]["payment_source"]["paypal"]["experience_context"]
    assert ctx == {"brand_name": "Edgefolio", "user_action": "PAY_NOW", "shipping_preference": "NO_SHIPPING",
                   "return_url": "https://s/thanks", "cancel_url": "https://s/?checkout=cancel"}
    assert sent[-1][1]["purchase_units"][0]["amount"] == {"currency_code": "USD", "value": "12.50"}


def test_parallel_downloads_never_pass_the_limit(app, client, ids, settings, monkeypatch):
    settings.max_downloads = 3
    url = buy(client, [ids[0]]).json["downloads"][0]["url"]
    read = downloads.find_link

    def slow(token):  # cada petición lee la cuenta antes de que ninguna la sume
        row = read(token)
        time.sleep(0.2)
        return row
    monkeypatch.setattr(downloads, "find_link", slow)
    with ThreadPoolExecutor(12) as pool:
        codes = sorted(pool.map(lambda _: client.get(url).status_code, range(12)))
    assert codes == [200] * 3 + [429] * 9
    with app.app_context():
        assert read(url.rsplit("/", 1)[1]).count == 3
    with ThreadPoolExecutor(4) as pool:
        assert set(pool.map(lambda _: client.get(url + "?format=zip").status_code, range(4))) == {429}


def receipt_for(client, order_id):
    r = client.post(f"/api/orders/{order_id}/capture")
    assert r.status_code == 200, r.get_data(as_text=True)
    return r.json


def test_the_receipt_links_go_only_to_the_buyers_browser(app, client, ids):
    order = client.post("/api/orders", json={"items": ids[:2]})
    cookie = order.headers["set-cookie"]
    assert cookie.startswith(f"{BUYER}=") and "HttpOnly" in cookie and "samesite=lax" in cookie.lower()
    assert "Max-Age=2592000" in cookie and "Secure" not in cookie, "30 días; por http (en local) no se guardaría"
    order_id, buyer = order.json["id"], client.get_cookie(BUYER).value
    stranger = visitor(app)  # alguien que sólo tiene el id del pedido (va en la dirección de vuelta de PayPal)
    hidden = receipt_for(stranger, order_id)
    assert hidden == {"order_id": order_id, "status": "PAID", "total": "146.20", "currency": "USD",
                      "payer": "b•••@example.com", "valid_days": 7, "max_downloads": 10, "download_all": None,
                      "downloads": [], "links_hidden": True, "paid_now": True}
    assert stored(app, order_id)["status"] == "PAID", "cobrar lo puede pedir cualquiera"
    mine = receipt_for(client, order_id)
    assert mine["links_hidden"] is False and len(mine["downloads"]) == 2 and mine["download_all"]
    assert mine["paid_now"] is False, "ya estaba pagado"
    assert mine["payer"] == "b•••@example.com", "nunca el correo entero de quien pagó"
    assert client.get(mine["downloads"][0]["url"]).status_code == 200
    assert stored(app, order_id)["buyer_hash"] == digest(buyer)
    from zlecitool_core.db import db
    with app.app_context():
        dump = "\n".join(str(row) for row in db.session.execute(db.text("SELECT * FROM edgefolio_order")))
    assert buyer not in dump, "de la cookie, sólo su hash"


def test_a_browser_keeps_its_buyer_cookie(app, client, ids):
    first = client.post("/api/orders", json={"items": [ids[0]]}).json["id"]
    buyer = client.get_cookie(BUYER).value
    second = client.post("/api/orders", json={"items": [ids[1]]})
    assert second.headers["set-cookie"].startswith(f"{BUYER}={buyer};"), "la misma, 30 días más"
    assert stored(app, first)["buyer_hash"] == stored(app, second.json["id"])["buyer_hash"] == digest(buyer)
    forged = visitor(app)
    forged.set_cookie(BUYER, "x")
    given = forged.post("/api/orders", json={"items": [ids[0]]}).headers["set-cookie"].split(";")[0]
    assert given.startswith(f"{BUYER}=") and len(given) > 40 and given != f"{BUYER}={buyer}", "mal hecha: otra"


def test_an_account_sees_the_links_of_an_order_made_without_one_only_once_it_proves_the_email(app, client, ids):
    order_id = client.post("/api/orders", json={"items": [ids[0]]}).json["id"]
    receipt_for(client, order_id)                       # lo pagó buyer@example.com (FakePayPal), sin cuenta
    someone = signed(app, "someone@example.com")
    assert receipt_for(someone, order_id)["links_hidden"] is True
    # El núcleo no comprueba el correo al darse de alta: registrarse con el de quien pagó no basta.
    impostor = signed(app, "buyer@example.com")
    assert receipt_for(impostor, order_id)["links_hidden"] is True
    prove(impostor)                                     # quien abre el buzón de buyer@example.com
    r = receipt_for(impostor, order_id)
    assert r["links_hidden"] is False and [d["id"] for d in r["downloads"]] == ["AAPL_1Day_1ADX_aaaa1111"]


def test_an_order_made_signed_in_belongs_to_that_account(app, ids):
    ana = signed(app, "ana@example.com")
    order_id = ana.post("/api/orders", json={"items": [ids[0]]}).json["id"]
    assert stored(app, order_id)["user_id"] == ana.user_id and stored(app, order_id)["email"] == "ana@example.com"
    phone = visitor(app)                                # otro navegador, sin la cookie de quien compra
    assert receipt_for(phone, order_id)["links_hidden"] is True
    ana_phone = signed(app, "ana@example.com")          # la misma cuenta, en el móvil
    assert receipt_for(ana_phone, order_id)["links_hidden"] is False
    other = signed(app, "other@example.com")
    prove(other, "buyer@example.com")                   # el correo de PayPal no hace suyo un pedido con cuenta
    assert receipt_for(other, order_id)["links_hidden"] is True


# ── lo que la cuenta ya tiene (E8, decisión del dueño del 2026-10-26) ─────────

AAPL_ID = "AAPL_1Day_1ADX_aaaa1111"


def test_a_single_strategy_the_account_has_is_not_sold_again(app, ids, settings, paypal):
    """Con la sesión abierta, el presupuesto y el pedido no venden otra vez, suelta, una estrategia que la cuenta ya
    tiene (lo de Mis estrategias): 409 errAlreadyOwned con sus ids, como los mandó el navegador (aquí, el alias del
    carrito de antes y el id), que las quita del carrito. Ningún pedido de PayPal. Lo demás del carrito se vende; un
    lote o el pack que la llevan, también (son otra oferta), y una suelta que va además en el lote no se cobra suelta.
    Sin sesión no se sabe de quién es: se presupuesta."""
    ana = signed(app, "ana@example.com")
    assert buy(ana, [ids[0]]).status_code == 200                       # AAPL
    made = len(paypal.orders)
    for path in ("/api/quote", "/api/orders"):
        r = ana.post(path, json={"items": [ids[0], ids[1], AAPL_ID]})
        assert r.status_code == 409 and r.json == {"error": "errAlreadyOwned", "items": [ids[0], AAPL_ID]}, path
    assert len(paypal.orders) == made, "ningún pedido en PayPal"
    assert ana.post("/api/quote", json={"items": [ids[1]]}).json["total"] == "93.00"
    assert ana.post("/api/quote", json={"bundles": ["duo"]}).json["total"] == "150.00"
    both = ana.post("/api/quote", json={"items": [ids[0]], "bundles": ["duo"]})
    assert both.status_code == 200 and both.json["items"] == [] and both.json["total"] == "150.00"
    settings.pack_size = 2
    assert ana.post("/api/quote", json={"pack": [AAPL_ID, "TSLA_1Day_1C00_dddd4444"]}).json["total"] == "129.00"
    assert visitor(app).post("/api/quote", json={"items": [ids[0]]}).status_code == 200, "sin sesión, de nadie"


def test_what_the_account_has_includes_its_proven_emails_and_free_downloads(app, client, ids, settings, paypal,
                                                                           free_file):  # noqa: F811
    """Lo que tiene la cuenta es lo de Mis estrategias: también lo comprado sin cuenta con un correo que la cuenta
    demostró (no con el mismo correo sin demostrar) y sus descargas gratis (una gratis que pasa a ser de pago). Nunca
    lo que otra cuenta compró con la sesión abierta, aunque se pagara con el correo demostrado."""
    assert buy(client, [ids[3]]).status_code == 200                    # TSLA, sin cuenta: lo pagó buyer@example.com
    ana = signed(app, "ana@example.com")
    assert buy(ana, [ids[1]]).status_code == 200                       # MSFT, otra cuenta (PayPal: buyer@example.com)
    bo = signed(app, "buyer@example.com")
    assert bo.post("/api/quote", json={"items": [ids[3]]}).status_code == 200, "sin demostrar el correo, no es suya"
    prove(bo)
    r = bo.post("/api/quote", json={"items": [ids[3], ids[1]]})
    assert r.status_code == 409 and r.json["items"] == [ids[3]], "la de otra cuenta no es suya"
    assert bo.post("/api/quote", json={"items": [ids[1]]}).json["total"] == "93.00"
    assert claim(bo, "buyer@example.com").json == {"sent": True}      # la gratis, con la sesión abierta
    with open(settings.catalogue, newline="") as f:
        rows = [dict(r, Price="30" if r["ticker"] == "NVDA" else r["Price"]) for r in csv.DictReader(f, delimiter="\t")]
    with open(settings.catalogue, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    install(app, settings, paypal)                                     # NVDA, ahora de pago
    r = bo.post("/api/orders", json={"items": [FREE_ID]})
    assert r.status_code == 409 and r.json == {"error": "errAlreadyOwned", "items": [FREE_ID]}
