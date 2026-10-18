# -*- coding: utf-8 -*-
"""Mis estrategias: lo que tiene una cuenta, sus enlaces, renovar y las versiones nuevas, el script del
propietario, las favoritas; y el zip de un pedido entero."""
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
    """Lo último arriba, también el mismo día; y una estrategia comprada dos veces dice la fecha y el pedido
    de la primera compra, no la fecha de una y el pedido de otra."""
    ana = signed(app, "ana@example.com")
    first = buy(ana, [AAPL])["order_id"]
    time.sleep(1.1)  # los segundos de la hora de cada pedido
    buy(ana, [MSFT])
    assert [x["id"] for x in my(ana)["items"]] == [MSFT, AAPL]
    time.sleep(1.1)
    buy(ana, [AAPL])
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
