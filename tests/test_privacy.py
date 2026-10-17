# -*- coding: utf-8 -*-
"""Tus datos (núcleo 0.30): lo que la tienda guarda de una cuenta sale en «Descargar mis datos» y se va con
«Borrar mi cuenta»; los pedidos, que pide la ley fiscal, se quedan, sin quién los hizo.

Lo hacen ``export`` y ``erase`` (edgefolio/your_data.py), registradas en app.py con ``privacy.add_privacy``;
el núcleo las corre en el reloj de la tienda (``zt_privacy``), sin la petición de nadie. En las pruebas no
hay reloj: ``testing.export_account`` pide los datos, sirve la parte de la tienda y da el zip;
``testing.close_account`` borra la cuenta como «Borrar mi cuenta», sirve su parte en el acto y da lo que
queda (falso si no queda nada). ``check_tool(app, privacy_sample=sample)`` recorre el borrado entero, con sus
dos confirmaciones (tests/test_smoke.py); aquí, lo de la tienda: lo hecho sin cuenta es de una cuenta sólo
con el correo demostrado (con su prueba, o por el núcleo), y nunca lo de otra.
"""
import json
import secrets
from datetime import timedelta
from decimal import Decimal

from zlecitool_core import testing
from zlecitool_core.db import db, utcnow

from edgefolio.models import Download, EmailProof, Favourite, FreeClaim, Mailbox, Order, Subscriber
from edgefolio.paypal import Capture
from edgefolio.web import digest
from tests.conftest import BUNDLES, ROWS, prove, signed, visitor
from tests.test_alerts import account, follow, republish, run
from tests.test_free import claim, confirm_link, free_file  # noqa: F401 (free_file es un fixture)
from tests.test_mine import AAPL, MSFT, buy

BUYER = "edgefolio_buyer"
TSLA = "TSLA_1Day_1C00_dddd4444"
# Las claves que guardan los pedidos, los enlaces y las favoritas (Strategy.key).
KEYS = {AAPL: "AAPL - 1Day - 1ADX - aaaa1111", MSFT: "MSFT - 1Hour - 2BB0 - bbbb2222",
        TSLA: "TSLA - 1Day - 1C00 - dddd4444", "NVDA": "NVDA - 1Day - 1ULT - cccc3333"}
TABLES = ("orders", "downloads", "free_downloads", "favourites", "email_proofs", "news", "mailboxes")


def sample(subject):
    """Lo que guarda la tienda de una cuenta, como lo de verdad (núcleo 0.30): ``check_tool(app,
    privacy_sample=sample)`` lo exporta, borra la cuenta y comprueba que no queda nada fuera de ``keep``.
    Corre como ``erase``, sin la petición de nadie: las filas, como las escriben las rutas. Cada vez, con
    sus claves y sus correos (check_tool puede correr varias veces sobre la misma base de datos)."""
    now, uid, tag = utcnow(), subject.user_id, secrets.token_hex(4)
    account_email = subject.email or f"cuenta-{uid}-{tag}@example.com"
    paypal = f"compras-{uid}-{tag}@example.com"      # con el que pagó sin cuenta, y lo demostró aquí

    def order(user_id, email, item):
        paypal_id = "FAKE-" + secrets.token_hex(6).upper()
        db.session.add(Order(paypal_id=paypal_id, user_id=user_id, items=[KEYS[item]], code="", total="79.00",
                             currency="USD", status="PAID", payer=paypal, email=email,
                             lines={"items": [{"id": item, "price": "79.00"}], "bundles": [], "pack": None},
                             buyer_hash=digest(secrets.token_urlsafe(32)), created_at=now))
        db.session.flush()
        db.session.add(Download(token=secrets.token_urlsafe(24), paypal_id=paypal_id, item_key=KEYS[item],
                                expires_at=now + timedelta(days=7), count=1, version=1, created_at=now))

    def free(user_id, email, news):
        db.session.add(FreeClaim(token=secrets.token_urlsafe(24), user_id=user_id, email=email, item_key=KEYS["NVDA"],
                                 news=news, consent_at=now, expires_at=now + timedelta(days=7), count=1, version=1,
                                 lang="es"))
        db.session.add(Mailbox(email=email, first_seen_at=now, last_seen_at=now))

    order(uid, account_email, AAPL)                  # con la sesión abierta (pagó con su correo de PayPal)
    order(None, paypal, MSFT)                        # sin cuenta, con el correo que demostró aquí
    free(uid, account_email, False)                  # una gratis, con la sesión abierta
    free(None, paypal, True)                         # y otra sin cuenta, con las novedades confirmadas
    db.session.add(Subscriber(email=paypal, news=True, consent_at=now, source="free", lang="es", token_hash="",
                              confirmed_at=now))
    if subject.email:                                # lo que hizo sin cuenta con el suyo, que demostró el núcleo
        order(None, subject.email, TSLA)
    db.session.add(Favourite(user_id=uid, item_key=KEYS[TSLA], alerts={"nv": True, "pd": True, "bd": False},
                             email=account_email, lang="es", created_at=now))
    db.session.add(EmailProof(user_id=uid, email=paypal, token_hash="", requested_at=now,
                              expires_at=now + timedelta(hours=24), verified_at=now))
    db.session.add(EmailProof(user_id=uid, email=f"pendiente-{uid}-{tag}@example.com", token_hash=digest(tag),
                              requested_at=now, expires_at=now + timedelta(hours=24)))


def exported(app, user_id) -> dict:
    """Lo de la tienda en el zip de «Descargar mis datos»: {tabla: filas}."""
    archive = testing.export_account(app, user_id)
    return {name: json.loads(archive.read(f"edgefolio/{name}.json")) for name in TABLES}


def paid_by(paypal, payer):
    """PayPal cobra, y quien pagó es ``payer`` (FakePayPal siempre dice buyer@example.com)."""
    def capture(order_id):
        total, currency = paypal.orders[order_id]
        return Capture("COMPLETED", total, currency, payer)
    return capture


def order_row(app, paypal_id) -> dict:
    with app.app_context():
        o = db.session.get(Order, paypal_id)
        return {c.name: getattr(o, c.name) for c in Order.__table__.columns}


def receipt_for(client, order_id) -> dict:
    r = client.post(f"/api/orders/{order_id}/capture")
    assert r.status_code == 200, r.get_data(as_text=True)
    return r.json


def test_my_data_carry_what_is_mine_and_nothing_else(app, client, free_file):  # noqa: F811
    first = buy(client, [AAPL])                      # sin cuenta: pagó buyer@example.com en PayPal
    claim(client, "nadie@example.com")               # sin cuenta, con un correo de otra persona
    ana = signed(app, "ana@example.com")             # el núcleo demostró su correo (signed_in_client)
    mine = buy(ana, [MSFT])                          # con la sesión abierta
    claim(ana, "ana@example.com")
    follow(ana, AAPL, nv=True)
    prove(ana, "buyer@example.com")                  # «¿Compraste sin cuenta?»: el correo de PayPal, suyo
    luis = signed(app, "luis@example.com")
    buy(luis, [AAPL])                                # lo de otra cuenta (también pagado con buyer@…)
    follow(luis, MSFT, pd=True)

    data = exported(app, ana.user_id)

    orders = sorted(data["orders"], key=lambda o: o["paypal_id"] == mine["order_id"])
    assert [(o["paypal_id"], o["user_id"], o["email"], o["status"]) for o in orders] == [
        (first["order_id"], None, "buyer@example.com", "PAID"), (mine["order_id"], ana.user_id, "ana@example.com", "PAID")]
    assert orders[1]["lines"]["items"] == [{"id": MSFT, "price": "93.00"}] and orders[1]["total"] == "93.00"
    assert all("buyer_hash" not in o for o in orders), "de la cookie de quien compra, ni su hash"
    assert sorted(d["item_key"] for d in data["downloads"]) == sorted([KEYS[AAPL], KEYS[MSFT]])
    assert all("token" not in d and d["count"] == 0 for d in data["downloads"]), "los enlaces no salen: son llaves"
    [free] = data["free_downloads"]
    assert (free["user_id"], free["email"], free["news"]) == (ana.user_id, "ana@example.com", False)
    assert "token" not in free
    assert [(f["user_id"], f["item_key"], f["alerts"]) for f in data["favourites"]] == [
        (ana.user_id, KEYS[AAPL], {"nv": True, "pd": False, "bd": False})]
    [proof] = data["email_proofs"]
    assert proof["email"] == "buyer@example.com" and proof["verified_at"].endswith("Z")
    assert "token_hash" not in proof and "id" not in proof
    assert data["news"] == []
    assert [m["email"] for m in data["mailboxes"]] == ["ana@example.com"], "la de nadie@… no es suya"


def test_an_email_that_is_not_proven_finds_nothing(app, client, paypal, free_file):  # noqa: F811
    """Darse de alta no demuestra el correo: quien se registra con el de otra persona no se lleva en sus datos,
    ni se borra al irse, lo que esa persona hizo sin cuenta."""
    paypal.capture = paid_by(paypal, "eva@example.com")
    bought = buy(client, [AAPL])                     # sin cuenta, pagado por eva@example.com
    claim(client, "eva@example.com", news=True)
    impostor = testing.signed_in_client(app, email="eva@example.com", proven=False)

    assert all(rows == [] for rows in exported(app, impostor.user_id).values())
    assert not testing.close_account(app, impostor.user_id)

    left = order_row(app, bought["order_id"])
    assert (left["email"], left["payer"]) == ("eva@example.com", "eva@example.com"), "de eva, intacto"
    with app.app_context():
        assert [c.email for c in FreeClaim.query.all()] == ["eva@example.com"]
        assert db.session.get(Subscriber, "eva@example.com") is not None
        assert db.session.get(Mailbox, "eva@example.com") is not None


def test_the_email_proven_by_the_core_finds_what_was_done_without_an_account(app, client, paypal, free_file):  # noqa: F811
    """El correo de la cuenta demostrado en el núcleo (entró con un enlace, núcleo 0.26: ``subject.email``)
    también es suyo para «Tus datos», sin la prueba de la tienda: lo hecho sin cuenta con él sale en el zip y
    se va con la cuenta."""
    paypal.capture = paid_by(paypal, "Ana@Example.com")
    bought = buy(client, [AAPL])                     # sin cuenta, antes de darse de alta
    claim(client, "ana@example.com", news=True)
    client.get(confirm_link("ana@example.com"))      # y confirmó las novedades desde el correo
    ana = signed(app, "ana@example.com")

    data = exported(app, ana.user_id)
    assert [(o["paypal_id"], o["user_id"]) for o in data["orders"]] == [(bought["order_id"], None)]
    assert [(c["user_id"], c["email"], c["news"]) for c in data["free_downloads"]] == [(None, "ana@example.com", True)]
    assert [(n["email"], n["source"]) for n in data["news"]] == [("ana@example.com", "free")]
    assert data["news"][0]["confirmed_at"] and "token_hash" not in data["news"][0]
    assert [m["email"] for m in data["mailboxes"]] == ["ana@example.com"]

    assert not testing.close_account(app, ana.user_id)
    left = order_row(app, bought["order_id"])
    assert (left["user_id"], left["email"], left["payer"], left["buyer_hash"]) == (None, "", "", "")
    assert (left["status"], left["total"], left["items"]) == ("PAID", "79.00", [KEYS[AAPL]]), "la venta se queda"
    with app.app_context():
        assert FreeClaim.query.count() == 0 and Subscriber.query.count() == 0 and Mailbox.query.count() == 0


def test_deleting_my_account_keeps_my_orders_without_who_made_them(app, client, free_file):  # noqa: F811
    """Los pedidos son el registro de una venta: se quedan, con lo vendido, el importe y la fecha, y sin
    quién los hizo (ni su correo, ni el de PayPal, ni la cookie del navegador que compró). Los de la cuenta
    siguen apuntando a la cuenta borrada. Lo demás de la cuenta se va; lo de las demás, en su sitio."""
    anonymous = buy(client, [AAPL])                  # sin cuenta, con buyer@example.com…
    ana = signed(app, "ana@example.com")
    mine = buy(ana, [MSFT])
    claim(ana, "ana@example.com")
    follow(ana, AAPL, nv=True)
    prove(ana, "buyer@example.com")                  # …que ana demostró: es suyo
    luis = signed(app, "luis@example.com")
    his = buy(luis, [AAPL])
    follow(luis, MSFT, pd=True)
    before = {oid: order_row(app, oid) for oid in (anonymous["order_id"], mine["order_id"], his["order_id"])}

    assert not testing.close_account(app, ana.user_id), "no queda nada suyo"

    for oid, owner in ((mine["order_id"], ana.user_id), (anonymous["order_id"], None)):
        now = order_row(app, oid)
        assert (now["user_id"], now["email"], now["payer"], now["buyer_hash"]) == (owner, "", "", ""), oid
        kept = ("status", "total", "currency", "items", "lines", "code", "created_at")
        assert {c: now[c] for c in kept} == {c: before[oid][c] for c in kept}, "la venta, tal cual"
    assert order_row(app, his["order_id"]) == before[his["order_id"]], "el de luis, intacto"
    with app.app_context():
        assert Download.query.count() == 3, "los enlaces de los pedidos se quedan con ellos (caducan solos)"
        assert FreeClaim.query.filter_by(user_id=ana.user_id).count() == 0
        assert EmailProof.query.filter_by(user_id=ana.user_id).count() == 0
        assert [(f.user_id, f.item_key) for f in Favourite.query.all()] == [(luis.user_id, KEYS[MSFT])]
    # Nadie ve ya sus enlaces: ni el navegador que compró sin cuenta, ni el que compró con ella.
    assert receipt_for(client, anonymous["order_id"])["links_hidden"] is True
    browser = visitor(app)
    browser.set_cookie(BUYER, ana.get_cookie(BUYER).value)
    assert receipt_for(browser, mine["order_id"])["links_hidden"] is True
    assert receipt_for(luis, his["order_id"])["links_hidden"] is False


def test_what_was_done_without_an_account_goes_with_its_email(app, client):
    """Un correo que demostraron dos cuentas es de quien lo controla: al borrar una, lo hecho sin cuenta con
    él se va (sin correo, la otra ya no lo ve), como pide el núcleo (su correo demostrado no queda en
    ninguna fila de nadie). Lo hecho con la sesión abierta de la otra, no."""
    anonymous = buy(client, [AAPL])                  # buyer@example.com, sin cuenta
    ana, bo = signed(app, "ana@example.com"), signed(app, "bo@example.com")
    prove(ana, "buyer@example.com")
    prove(bo, "buyer@example.com")
    assert receipt_for(bo, anonymous["order_id"])["links_hidden"] is False

    assert not testing.close_account(app, ana.user_id)

    assert order_row(app, anonymous["order_id"])["email"] == ""
    assert receipt_for(bo, anonymous["order_id"])["links_hidden"] is True
    assert bo.get("/api/mine").json["emails"] == ["buyer@example.com"], "su prueba es suya: se queda"


def test_a_closed_account_s_order_is_not_charged(app, paypal):
    """La cuenta se borra mientras paga en PayPal (en otra pestaña, otro dispositivo): al volver, el pedido
    no se cobra (el dinero no se mueve) y no vuelve a tener un correo."""
    ana = signed(app, "ana@example.com")
    order_id = ana.post("/api/orders", json={"items": [AAPL]}).json["id"]
    buyer = ana.get_cookie(BUYER).value
    assert not testing.close_account(app, ana.user_id)

    called = []
    paypal.capture = lambda oid: called.append(oid)
    back = visitor(app)                              # de vuelta de PayPal, sin la sesión de la cuenta borrada
    back.set_cookie(BUYER, buyer)
    r = back.post(f"/api/orders/{order_id}/capture")
    assert r.status_code == 409 and r.json == {"error": "errAccountClosed"} and called == []
    row = order_row(app, order_id)
    assert (row["status"], row["user_id"], row["email"], row["payer"]) == ("CREATED", ana.user_id, "", "")


def test_the_alerts_never_write_to_a_closed_account(app, settings, paypal):
    """Entre «Borrar mi cuenta» y la parte de la tienda pasan minutos (núcleo 0.30): sus favoritas y la
    prueba de su correo siguen ahí, y el trabajo de los avisos no le escribe (``privacy.closed``)."""
    ana = account(app)
    follow(ana, TSLA, pd=True)
    run(app)                                         # la primera vuelta: la foto
    assert not testing.close_account(app, ana.user_id)
    with app.app_context():                          # lo que había antes de que se sirviera su parte
        now = utcnow()
        db.session.add(Favourite(user_id=ana.user_id, item_key=KEYS[TSLA], alerts={"nv": False, "pd": True, "bd": False},
                                 email="ana@example.com", lang="es", created_at=now))
        db.session.add(EmailProof(user_id=ana.user_id, email="ana@example.com", token_hash="", requested_at=now,
                                  expires_at=now + timedelta(hours=24), verified_at=now))
        db.session.commit()
    rows = [dict(r) for r in ROWS]
    rows[3]["Price"] = "40"                          # TSLA, más barata
    republish(app, settings, paypal, rows, BUNDLES)
    assert "1 estrategias cambiaron; 0 correos" in run(app)
    assert [m for m in testing.mail_outbox() if m["X-ZT-Kind"] == "edgefolio-alert"] == []


def test_the_sample_is_what_the_shop_writes(app):
    """``sample`` (la de check_tool) escribe lo que escriben las rutas: sus pedidos los ve Mis estrategias."""
    ana = signed(app, "ana@example.com")
    with app.app_context():
        from zlecitool_core.privacy import Subject
        sample(Subject(user_id=ana.user_id, kind="account", email="ana@example.com", org_id=None, org_ids=(),
                       language="es", requested_at=utcnow(), key="zt-privacy:prueba:edgefolio"))
        db.session.commit()
    items = ana.get("/api/mine").json["items"]
    assert {i["id"] for i in items} >= {AAPL, MSFT, "NVDA_1Day_1ULT_cccc3333"}
    data = exported(app, ana.user_id)
    assert len(data["orders"]) == 3 and len(data["free_downloads"]) == 2 and len(data["email_proofs"]) == 2
    assert Decimal(data["orders"][0]["total"]) == Decimal("79.00")
