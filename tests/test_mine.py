# -*- coding: utf-8 -*-
"""Mis estrategias: lo que tiene una cuenta, sus enlaces, renovar y las versiones nuevas (gratis mientras la estrategia
no ha caducado), el script del propietario, las favoritas; y el zip de un pedido entero."""
import csv
import io
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor

from edgefolio import downloads
from edgefolio.shop import install
from tests.conftest import prove, signed
from tests.test_formats import ONE_TREE
from tests.test_free import FREE_ID, claim, free_file  # noqa: F401 (free_file es un fixture)

AAPL, MSFT = "AAPL_1Day_1ADX_aaaa1111", "MSFT_1Hour_2BB0_bbbb2222"


def buy(client, items):
    order = client.post("/api/orders", json={"items": items})
    assert order.status_code == 200, order.get_data(as_text=True)
    r = client.post(f"/api/orders/{order.json['id']}/capture")
    assert r.status_code == 200, r.get_data(as_text=True)
    return r.json


def my(client):
    r = client.get("/api/mine")
    assert r.status_code == 200, r.get_data(as_text=True)
    return r.json


def test_everything_needs_a_session(client):
    """Un script sin sesión recibe el 401 del núcleo; un navegador, la página de entrar."""
    for method, path, kw in (("get", "/api/mine", {}), ("post", "/api/mine/renew", {"json": {"id": AAPL}}),
                             ("get", f"/api/mine/{AAPL}/script", {}), ("put", f"/api/favourites/{AAPL}", {"json": {}}),
                             ("delete", f"/api/favourites/{AAPL}", {}), ("post", "/api/mine/proofs", {"json": {}})):
        r = getattr(client, method)(path, headers={"Sec-Fetch-Dest": "empty"}, **kw)
        assert r.status_code == 401 and r.json == {"error": "errLoginRequired"}, path
    page = client.get("/mine")
    assert page.status_code == 302 and page.headers["location"] == "/login?next=/mine"


def test_a_purchase_made_signed_in(app):
    ana = signed(app, "ana@example.com")
    receipt = buy(ana, [AAPL])
    body = my(ana)
    assert body["email"] == "ana@example.com" and body["favourites"] == []
    [item] = body["items"]
    assert item["id"] == AAPL and item["kind"] == "paid" and item["order"] == receipt["order_id"]
    assert item["valid"] and item["days_left"] == 7 and item["version"] == 1 and item["update"] is None
    assert item["url"] == receipt["downloads"][0]["url"] and item["zip"] == item["url"] + "?format=zip"
    assert item["row"]["id"] == AAPL and item["row"]["name"] == "Apple"
    assert len(item["date"]) == 10 and item["expires"].endswith("+00:00")
    assert ana.get(item["url"]).status_code == 200


def test_a_purchase_made_signed_out_is_found_once_the_paypal_email_is_proven(app, client):
    buy(client, [AAPL, MSFT])          # quien pagó en FakePayPal es buyer@example.com
    someone = signed(app, "someone@example.com")
    assert my(someone)["items"] == [], "nadie más lo ve"
    buyer = signed(app, "buyer@example.com")
    body = my(buyer)
    assert body["items"] == [] and body["proof_needed"] is True, "el mismo correo, sin demostrar: nada"
    prove(buyer)
    body = my(buyer)
    assert sorted(i["id"] for i in body["items"]) == [AAPL, MSFT]
    assert body["emails"] == ["buyer@example.com"] and body["proof_needed"] is False


def test_free_claims_are_listed(app, client, free_file):  # noqa: F811
    claim(client, "ana@example.com")
    ana = signed(app, "ana@example.com")
    assert my(ana)["items"] == []
    prove(ana)
    [item] = my(ana)["items"]
    assert item["id"] == FREE_ID and item["kind"] == "free" and item["order"] is None and item["valid"]


def test_an_expired_link_is_renewed_once(app, settings):
    ana = signed(app, "ana@example.com")
    settings.download_days = -1
    old = buy(ana, [AAPL])["downloads"][0]["url"]
    [item] = my(ana)["items"]
    assert not item["valid"] and item["url"] is None and item["days_left"] == 0
    settings.download_days = 7
    renewed = ana.post("/api/mine/renew", json={"id": AAPL}).json
    assert renewed["valid"] and renewed["url"] != old and ana.get(renewed["url"]).status_code == 200
    assert ana.get(old).status_code == 410
    again = ana.post("/api/mine/renew", json={"id": AAPL}).json
    assert again["url"] == renewed["url"], "un enlace que funciona no se cambia (su límite sigue)"


def test_a_new_link_keeps_the_purchase_and_the_thank_you_page_shows_it(app, settings):
    """«Conseguir un enlace nuevo» no cambia la compra (su fecha y su pedido), y la página de gracias de ese
    pedido, abierta otra vez, da el enlace nuevo, no el que caducó."""
    ana = signed(app, "ana@example.com")
    settings.download_days = -1
    order = ana.post("/api/orders", json={"items": [AAPL]}).json["id"]
    old = ana.post(f"/api/orders/{order}/capture").json["downloads"][0]["url"]
    [before] = my(ana)["items"]
    settings.download_days = 7
    renewed = ana.post("/api/mine/renew", json={"id": AAPL}).json
    assert renewed["valid"] and renewed["url"] != old
    assert (renewed["date"], renewed["order"], renewed["version"]) == (before["date"], before["order"], before["version"])
    again = ana.post(f"/api/orders/{order}/capture").json["downloads"][0]["url"]
    assert again == renewed["url"] and ana.get(again).status_code == 200


def test_a_spent_link_opened_in_the_browser_goes_back_to_the_shop(app, client, settings):
    """Un enlace que ya no vale, abierto en la pestaña (un clic en la página, el enlace del correo), vuelve
    a la tienda con el porqué (a Mis estrategias con la sesión abierta), no a una página con el JSON; un
    script sigue recibiendo el JSON."""
    settings.max_downloads = 1
    url = buy(client, [AAPL])["downloads"][0]["url"]
    assert client.get(url).status_code == 200
    browser = {"Accept": "text/html,application/xhtml+xml,*/*;q=0.8", "Sec-Fetch-Dest": "document"}
    r = client.get(url, headers=browser)
    assert r.status_code == 303 and r.headers["Location"] == "/?link=errDownloadLimit"
    assert client.get(url).status_code == 429 and client.get(url).json == {"error": "errDownloadLimit"}
    ana = signed(app, "ana@example.com")
    r = ana.get("/api/download/nope", headers=browser)
    assert r.status_code == 303 and r.headers["Location"] == "/mine?link=errLinkNotFound"
    r = ana.get("/api/download/all?t=nope", headers={"Accept": "text/html"})
    assert r.status_code == 303 and r.headers["Location"].startswith("/mine?link=")


def test_the_newest_purchase_comes_first_and_a_row_is_its_first_purchase(app):
    """Lo último arriba, también el mismo día; y una estrategia comprada dos veces (suelta y después en un lote: suelta
    no se vende otra vez, E8) dice la fecha y el pedido de la primera compra, no la fecha de una y el pedido de otra."""
    ana = signed(app, "ana@example.com")
    first = buy(ana, [AAPL])["order_id"]
    time.sleep(1.1)  # los segundos de la hora de cada pedido
    buy(ana, [MSFT])
    assert [x["id"] for x in my(ana)["items"]] == [MSFT, AAPL]
    time.sleep(1.1)
    order = ana.post("/api/orders", json={"bundles": ["duo"]})        # AAPL y MSFT otra vez, en el lote
    assert order.status_code == 200 and ana.post(f"/api/orders/{order.json['id']}/capture").status_code == 200
    aapl = next(x for x in my(ana)["items"] if x["id"] == AAPL)
    assert aapl["order"] == first


def test_a_link_that_ran_out_is_renewed(app, settings):
    ana = signed(app, "ana@example.com")
    settings.max_downloads = 1
    url = buy(ana, [AAPL])["downloads"][0]["url"]
    ana.get(url)
    assert my(ana)["items"][0]["valid"] is False
    assert ana.post("/api/mine/renew", json={"id": AAPL}).json["valid"] is True


def test_a_renewed_free_link_does_not_count_against_the_daily_limit(app, client, settings, free_file):  # noqa: F811
    settings.download_days = -1
    claim(client, "ana@example.com")
    with app.app_context():                    # la pidió anteayer
        from datetime import timedelta
        from zlecitool_core.db import db
        from edgefolio.models import FreeClaim
        FreeClaim.query.one().consent_at -= timedelta(days=2)
        db.session.commit()
    ana = signed(app, "ana@example.com")
    prove(ana)
    settings.download_days = 7
    renewed = ana.post("/api/mine/renew", json={"id": FREE_ID}).json
    assert renewed["valid"] and renewed["kind"] == "free" and ana.get(renewed["url"]).status_code == 200
    assert renewed["date"] == my(ana)["items"][0]["date"], "la fecha es la de la primera vez"
    assert [claim(client, "ana@example.com").status_code for _ in range(11)] == [200] * 10 + [429]


def test_a_new_version_is_offered_and_delivered(app, settings, paypal):
    ana = signed(app, "ana@example.com")
    buy(ana, [AAPL])
    with open(settings.catalogue, newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    for r in rows:
        r["version"] = "2" if r["ticker"] == "AAPL" else "1"
    with open(settings.catalogue, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    install(app, settings, paypal)   # la tienda, arrancada otra vez con el catálogo nuevo
    [item] = my(ana)["items"]
    assert item["valid"] and item["version"] == 1 and item["update"] == 2
    got = ana.post("/api/mine/renew", json={"id": AAPL}).json
    assert got["version"] == 2 and got["update"] is None and got["url"] != item["url"]


def test_a_bought_strategy_that_left_the_catalogue(app, settings, paypal):
    """Las 49 horarias de acciones salieron del catálogo (E2, 2026-10-26), y alguien pudo comprar una antes. La regla
    de la tienda no cambia: lo que ya no está en el catálogo no se enseña ni se entrega. Mis estrategias sigue con lo
    demás, sin romperse; el enlace de la que salió dice errStrategyGone (abierto en el navegador, vuelve a Mis
    estrategias con el aviso); el zip y la página de gracias del pedido dan lo que queda; renovarla, 404."""
    ana = signed(app, "ana@example.com")
    receipt = buy(ana, [AAPL, MSFT])
    links = {d["id"]: d["url"] for d in receipt["downloads"]}
    assert ana.put(f"/api/favourites/{MSFT}", json={}).status_code == 200
    with open(settings.catalogue, newline="") as f:
        rows = [r for r in csv.DictReader(f, delimiter="\t") if r["ticker"] != "MSFT"]
    with open(settings.catalogue, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    install(app, settings, paypal)   # la tienda, arrancada otra vez sin MSFT
    body = my(ana)
    assert [i["id"] for i in body["items"]] == [AAPL] and body["favourites"] == []
    gone = ana.get(links[MSFT])
    assert gone.status_code == 404 and gone.json == {"error": "errStrategyGone"}
    opened = ana.get(links[MSFT], headers={"Sec-Fetch-Dest": "document"})
    assert opened.status_code == 303 and opened.headers["location"] == "/mine?link=errStrategyGone"
    assert zipfile.ZipFile(io.BytesIO(ana.get(receipt["download_all"]).data)).namelist() == [f"Tuisku_{AAPL}.pine"]
    again = ana.post(f"/api/orders/{receipt['order_id']}/capture")
    assert again.status_code == 200 and [d["id"] for d in again.json["downloads"]] == [AAPL]
    renewed = ana.post("/api/mine/renew", json={"id": MSFT})
    assert renewed.status_code == 404 and renewed.json == {"error": "errUnknownStrategy"}
    assert ana.get(links[AAPL]).status_code == 200


def test_the_owner_reads_the_full_script(app, client, free_file):  # noqa: F811
    claim(client, "ana@example.com")
    ana = signed(app, "ana@example.com")
    assert ana.get(f"/api/mine/{FREE_ID}/script").json == {"error": "errNotOwned"}, "sin demostrar el correo"
    prove(ana)
    r = ana.get(f"/api/mine/{FREE_ID}/script")
    assert r.status_code == 200 and r.get_data(as_text=True) == ONE_TREE
    assert r.headers["cache-control"] == "private, no-store"
    assert ana.get(f"/api/mine/{AAPL}/script").status_code == 404, "no comprada"
    assert ana.post("/api/mine/renew", json={"id": AAPL}).json == {"error": "errNotOwned"}
    assert ana.get("/api/mine/NOPE/script").json == {"error": "errUnknownStrategy"}


def test_favourites_with_alerts(app):
    ana = signed(app, "ana@example.com")
    r = ana.put(f"/api/favourites/{AAPL}", json={"alerts": {"nv": True, "pd": True}})
    assert r.status_code == 200 and r.json["alerts"] == {"nv": True, "pd": True, "bd": False}
    ana.put(f"/api/favourites/{MSFT}", json={})
    ana.put(f"/api/favourites/{AAPL}", json={"alerts": {"bd": True}})
    favs = my(ana)["favourites"]
    assert [(f["id"], f["alerts"]) for f in favs] == [(AAPL, {"nv": False, "pd": False, "bd": True}),
                                                       (MSFT, {"nv": False, "pd": False, "bd": False})]
    assert favs[0]["row"]["ticker"] == "AAPL"
    assert ana.delete(f"/api/favourites/{AAPL}").json == {"id": AAPL, "deleted": True}
    assert [f["id"] for f in my(ana)["favourites"]] == [MSFT]
    assert ana.put("/api/favourites/NOPE", json={}).status_code == 404
    assert my(signed(app, "other@example.com"))["favourites"] == []


def test_download_all_in_one_zip(client, settings):
    receipt = buy(client, [AAPL, MSFT])
    url = receipt["download_all"]
    assert url.startswith("/api/download/all?t=")
    r = client.get(url + "&t=made-up")
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
    z = zipfile.ZipFile(io.BytesIO(r.data))
    assert sorted(z.namelist()) == ["Tuisku_AAPL_1Day_1ADX_aaaa1111.pine", "Tuisku_MSFT_1Hour_2BB0_bbbb2222.pine"]
    assert client.get("/api/download/all?t=made-up").status_code == 404
    assert client.get("/api/download/all").status_code == 404
    settings.max_downloads = 2
    client.get(url)
    assert client.get(url).status_code == 429, "cada fichero cuenta una descarga"


def test_parallel_download_all_never_passes_the_limit(app, client, settings, monkeypatch):
    settings.max_downloads = 2
    receipt = buy(client, [AAPL, MSFT])
    read = downloads.find_link

    def slow(token):  # cada petición lee las cuentas antes de que ninguna las sume
        row = read(token)
        time.sleep(0.1)
        return row
    monkeypatch.setattr(downloads, "find_link", slow)
    with ThreadPoolExecutor(8) as pool:
        answers = list(pool.map(lambda _: client.get(receipt["download_all"]), range(8)))
    sent = [n for r in answers if r.status_code == 200 for n in zipfile.ZipFile(io.BytesIO(r.data)).namelist()]
    assert sorted(sent) == sorted([f"Tuisku_{AAPL}.pine", f"Tuisku_{MSFT}.pine"] * 2), "cada fichero, dos veces como mucho"
    assert {r.status_code for r in answers} <= {200, 429}
    with app.app_context():
        assert [read(d["url"].rsplit("/", 1)[1]).count for d in receipt["downloads"]] == [2, 2]


def test_one_script_through_two_links_is_sent_and_counted_once(app, settings):
    ana = signed(app, "ana@example.com")
    settings.download_days = -1
    old = buy(ana, [AAPL])["downloads"][0]["url"].rsplit("/", 1)[1]
    settings.download_days = 7
    new = ana.post("/api/mine/renew", json={"id": AAPL}).json["url"].rsplit("/", 1)[1]
    with app.app_context():                              # un tercer enlace del mismo pedido
        link = downloads.find_link(new)
        from edgefolio.models import Download
        from zlecitool_core.db import db
        db.session.add(Download(token="third-link-token", paypal_id=link.paypal_id, item_key=link.item_key,
                                expires_at=link.expires_at, count=0, version=1))
        db.session.commit()
    r = ana.get(f"/api/download/all?t={old}&t={new}&t=third-link-token")
    assert zipfile.ZipFile(io.BytesIO(r.data)).namelist() == [f"Tuisku_{AAPL}.pine"]
    with app.app_context():
        assert (downloads.find_link(new).count, downloads.find_link("third-link-token").count) == (1, 0)


def published_again(app, settings, paypal, versions: dict, expiries: dict):
    """El catálogo publicado otra vez: ``versions`` (ticker → versión) y la «Expiry date» de la cabecera de la vista
    previa de cada una (``expiries``, ticker → 'AAAA/MM/DD'), en una carpeta static de la prueba. Y la tienda,
    arrancada otra vez con él."""
    with open(settings.catalogue, newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    settings.static = settings.catalogue.parent.parent / "static"
    previews = settings.static / "assets" / "previews"
    previews.mkdir(parents=True, exist_ok=True)
    for r in rows:
        r["version"] = str(versions.get(r["ticker"], 1))
        r["pine_path_shadow"] = f"assets/previews/{r['ticker']}.pine"
        if r["ticker"] in expiries:
            sid = f"{r['ticker']}_{r['interval']}_{r['key_techs']}_{r['id_model']}"
            (previews / f"{r['ticker']}.pine").write_text(
                f"//Welcome to © Tuisku Trading Strategy\n\n// ID_model: {sid} Date Creation: 2026/10/13 Expiry date: "
                f"{expiries[r['ticker']]} (no new trades after it; download the updated version)\n//@version=5\n")
    with open(settings.catalogue, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    install(app, settings, paypal)


def test_an_update_is_free_until_the_strategy_expires(app, client, settings, paypal, free_file):  # noqa: F811
    """Decisión del dueño (2026-10-26): «Obtener la actualización» es gratis mientras la estrategia no ha caducado,
    según la «Expiry date» de la cabecera de su script (la línea de su vista previa pública). Después, Mis estrategias
    no la ofrece (``update`` es null) y #16 no da la versión nueva (403 errUpdateExpired), tampoco con el enlace de la
    de antes caducado: la tienda guarda sólo el script de hoy, y el enlace nuevo lo daría. Renovar el enlace de la
    versión comprada, cuando es la de hoy, sigue valiendo aunque haya caducado. Una gratis se actualiza siempre: se
    pide otra vez sin pagar. Hoy ninguna pasa de la v1: con una v2 inventada."""
    TSLA, NVDA = "TSLA_1Day_1C00_dddd4444", FREE_ID
    ana = signed(app, "ana@example.com")
    buy(ana, [AAPL, MSFT])
    settings.download_days = -1                       # nacido caducado: el de TSLA se renueva
    buy(ana, [TSLA])
    assert claim(ana, "ana@example.com").json == {"sent": True}
    settings.download_days = 7
    published_again(app, settings, paypal, {"AAPL": 2, "MSFT": 2, "NVDA": 2},
                    {"AAPL": "2099/01/01", "MSFT": "2020/01/01", "TSLA": "2020/01/01", "NVDA": "2020/01/01"})
    with app.app_context():
        from edgefolio.shop import of
        cat = of(app).catalogue
        assert [cat.resolve(i).expired for i in (AAPL, MSFT, TSLA)] == [False, True, True]
        assert cat.resolve(AAPL).expiry.isoformat() == "2099-01-01"
    items = {i["id"]: i for i in my(ana)["items"]}
    assert (items[AAPL]["update"], items[MSFT]["update"], items[TSLA]["update"], items[NVDA]["update"]) == (2, None, None, 2)
    got = ana.post("/api/mine/renew", json={"id": AAPL}).json
    assert got["version"] == 2 and got["update"] is None, "sin caducar: la versión nueva, gratis"
    refused = ana.post("/api/mine/renew", json={"id": MSFT})
    assert refused.status_code == 403 and refused.json == {"error": "errUpdateExpired"}
    assert next(i for i in my(ana)["items"] if i["id"] == MSFT)["version"] == 1, "la de antes, como estaba"
    renewed = ana.post("/api/mine/renew", json={"id": TSLA}).json
    assert renewed["valid"] and renewed["version"] == 1, "el enlace de la versión comprada, aunque haya caducado"
    free = ana.post("/api/mine/renew", json={"id": NVDA}).json
    assert free["version"] == 2 and free["kind"] == "free", "una gratis, siempre"


def test_an_old_link_does_not_give_the_new_version_once_the_strategy_has_expired(app, settings, paypal):
    """La tienda guarda un script por estrategia, el de hoy: un enlace aún válido de la versión de antes da la nueva.
    Sin caducar, vale (la actualización es gratis); caducada, ni Mis estrategias lo da por válido (sin .pine: «Ya es
    tuya» lleva a Mis estrategias) ni descarga nada (API #10: 403 errUpdateExpired; abierto en el navegador, a Mis
    estrategias con el aviso), como al renovarlo, ni la vista de propietario del árbol lo enseña entero (API #17). El de
    la versión comprada, cuando es la de hoy, sí, aunque caducara."""
    ana = signed(app, "ana@example.com")
    links = {d["id"]: d["url"] for d in buy(ana, [AAPL, MSFT])["downloads"]}
    published_again(app, settings, paypal, {"AAPL": 2, "MSFT": 2}, {"AAPL": "2099/01/01", "MSFT": "2020/01/01"})
    items = {i["id"]: i for i in my(ana)["items"]}
    assert (items[AAPL]["valid"], items[AAPL]["url"], items[AAPL]["update"]) == (True, links[AAPL], 2)
    assert (items[MSFT]["valid"], items[MSFT]["url"], items[MSFT]["update"]) == (False, None, None)
    assert ana.get(links[AAPL]).status_code == 200, "sin caducar: la versión nueva, gratis"
    refused = ana.get(links[MSFT])
    assert refused.status_code == 403 and refused.json == {"error": "errUpdateExpired"}
    opened = ana.get(links[MSFT], headers={"Sec-Fetch-Dest": "document"})
    assert opened.status_code == 303 and opened.headers["location"] == "/mine?link=errUpdateExpired"
    assert ana.post("/api/mine/renew", json={"id": MSFT}).json == {"error": "errUpdateExpired"}
    # el script entero de la vista de propietario del árbol (API #17) es también el de hoy
    assert ana.get(f"/api/mine/{AAPL}/script").status_code == 200
    whole = ana.get(f"/api/mine/{MSFT}/script")
    assert whole.status_code == 403 and whole.json == {"error": "errUpdateExpired"}
    published_again(app, settings, paypal, {"AAPL": 2}, {"AAPL": "2099/01/01", "MSFT": "2020/01/01"})
    assert ana.get(links[MSFT]).status_code == 200, "la versión que compró, aunque haya caducado"
    assert next(i for i in my(ana)["items"] if i["id"] == MSFT)["valid"]
    assert ana.get(f"/api/mine/{MSFT}/script").status_code == 200


def test_a_strategy_expires_at_midnight_utc_as_its_script(monkeypatch):
    """Como el script (``isExpired = time >= expiryTime``, ``expiryTime`` a las 00:00 UTC de su «Expiry date»): el día
    de antes a las 23:59:59 UTC aún no ha caducado; a las 00:00 UTC del día, sí. En UTC y no en la hora de la máquina:
    con un reloj de UTC+14, el mediodía UTC del día de antes ya sería el día de la caducidad."""
    from datetime import date, datetime, timedelta, timezone
    from decimal import Decimal

    from edgefolio import catalogue
    from edgefolio.catalogue import Strategy

    class At(datetime):
        moment = None

        @classmethod
        def now(cls, tz=None):
            return cls.moment.astimezone(tz) if tz else (cls.moment + timedelta(hours=14)).replace(tzinfo=None)

    monkeypatch.setattr(catalogue, "datetime", At)
    s = Strategy("AAPL", "1Day", "1ADX", "aaaa1111", Decimal("79"), {"version": "2"}, expiry=date(2027, 6, 13))
    for moment, expired in (((2027, 6, 12, 12, 0, 0), False), ((2027, 6, 12, 23, 59, 59), False),
                            ((2027, 6, 13, 0, 0, 0), True)):
        At.moment = datetime(*moment, tzinfo=timezone.utc)
        assert (s.expired, s.serves(1), s.serves(2), s.serves(1, paid=False)) == (expired, not expired, True, True), moment


def test_every_published_strategy_says_when_it_expires(real_app):
    """La caducidad de cada estrategia del catálogo publicado sale de la cabecera de su vista previa (el generador la
    escribe en cada script): todas la dicen, y es después de su publicación."""
    from edgefolio.shop import of
    catalogue = of(real_app).catalogue
    assert len(catalogue) > 0
    for s in catalogue:
        assert s.expiry and s.release_date and s.expiry > s.release_date, s.id
