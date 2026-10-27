# -*- coding: utf-8 -*-
"""Los lotes y «Crea tu pack»: con precio del servidor, y una estrategia nunca se cobra dos veces."""
import json
from decimal import Decimal

from edgefolio import orders
from edgefolio.catalogue import Catalogue
from edgefolio.models import Order
from edgefolio.settings import ROOT
from edgefolio.shop import install
from tests.conftest import BUNDLES, ROWS, strategy_id

AAPL, MSFT, NVDA, TSLA = (strategy_id(r) for r in ROWS)


def quote(client, **cart):
    return client.post("/api/quote", json=cart)


def test_bundles_and_pack_are_listed(client):
    body = client.get("/api/bundles").json
    assert body == {"bundles": [{"key": "duo", "name_key": "bundleTop", "ids": [AAPL, MSFT], "price": 150,
                                 "was": 172}], "pack": {"size": 5, "price": 249, "was": 395}}  # 5 x median $79


def test_shipped_bundles_come_from_the_real_catalogue(real_client):
    """catalogue/bundles.json, by its rules: top5 = each ticker's best paid strategy by npp, the first five (the
    'hot' order of /api/strategies); crypto = the 2 best paid crypto by npp; amzn = the 2 best paid AMZN daily ones
    by npp that are not in top5. No two of them share a strategy (a cart with both would be refused). Rebuilt when
    the 49 hourly stock strategies left the catalogue (E2: two of top5 and one of amzn were hourly stocks), at the
    same prices: the same saving as before, 32 % on top5 and 14 % on amzn."""
    cat = Catalogue(ROOT / "catalogue" / "catalogue.csv")
    paid = sorted((s for s in cat if s.price > 0), key=lambda s: -s.numbers["npp"])
    best = {}
    for s in paid:
        best.setdefault(s.ticker, s)
    top5 = [s.id for s in sorted(best.values(), key=lambda s: -s.numbers["npp"])[:5]]
    hot = real_client.get("/api/strategies?paid=1&sort=hot&size=5").json["rows"]
    assert [r["id"] for r in hot] == top5, "the same five as the shop's own 'hot' order"
    bundles = {b["key"]: b for b in real_client.get("/api/bundles").json["bundles"]}
    assert list(bundles) == ["top5", "crypto", "amzn"]
    assert bundles["top5"]["ids"] == top5 and bundles["top5"]["price"] == 249
    assert len({cat.resolve(i).ticker for i in top5}) == 5, "five different tickers"
    assert bundles["crypto"]["ids"] == [s.id for s in paid if s.market == "crypto"][:2]
    assert bundles["amzn"]["ids"] == [s.id for s in paid if s.ticker == "AMZN" and s.interval == "1Day"
                                      and s.id not in top5][:2]
    every = [i for b in bundles.values() for i in b["ids"]]
    assert len(every) == len(set(every)) == 9, "no two shipped bundles share a strategy"
    for b in bundles.values():
        assert b["price"] < b["was"] == sum(float(cat.resolve(i).price) for i in b["ids"])
    saving = {k: round(1 - b["price"] / b["was"], 2) for k, b in bundles.items()}
    assert saving == {"top5": 0.32, "crypto": 0.16, "amzn": 0.14}, saving


def test_a_bundle_that_lost_a_strategy_or_its_saving_is_left_out(app, client, settings, paypal, caplog):
    # (a bundle with an unknown id used to be sold with what was left of it, at its old price)
    settings.bundles.write_text(json.dumps([{"key": "duo", "ids": [AAPL, "GONE_1Day_X_0"], "price": 70},
                                            {"key": "ghost", "ids": ["GONE_1Day_X_0"], "price": 9},
                                            {"key": "empty", "ids": [], "price": 9},
                                            {"key": "dear", "ids": [AAPL, TSLA], "price": 129},   # was 129
                                            {"key": "fair", "ids": [AAPL, TSLA], "price": 128.99}]))
    with caplog.at_level("ERROR"):
        install(app, settings, paypal)   # la tienda, arrancada otra vez con el bundles.json nuevo
    body = client.get("/api/bundles").json
    assert [(b["key"], b["ids"], b["price"], b["was"]) for b in body["bundles"]] == [
        ("fair", [AAPL, TSLA], 128.99, 129)]
    errors = [r.getMessage() for r in caplog.records if r.levelname == "ERROR"]
    assert any("duo" in e and "GONE_1Day_X_0" in e for e in errors) and any("ghost" in e for e in errors)
    assert any("dear" in e and "129" in e for e in errors) and any("empty" in e for e in errors)
    assert client.post("/api/quote", json={"bundles": ["duo"]}).status_code == 400


def test_items_in_a_bundle_are_not_charged_twice(client):
    r = quote(client, items=[AAPL, TSLA], bundles=["duo"]).json
    assert r["items"] == [{"id": TSLA, "price": "42.50"}] and r["bundles"] == [{"key": "duo", "price": "127.50"}]
    assert r["subtotal"] == "200.00" and r["tier_rate"] == "0.15" and r["total"] == "170.00"  # 150 + 50, 15% tier
    assert r["pack"] is None


def test_code_adds_to_the_tier_with_bundles(client):
    r = quote(client, bundles=["duo", "duo"], code="spring20").json
    assert r["subtotal"] == "150.00" and r["code_rate"] == "0.20" and r["tier_rate"] == "0"
    assert r["total"] == "120.00" and r["code_status"] == "applied"


def test_flat_price_code_is_for_loose_items_only(client):
    r = quote(client, items=[TSLA], bundles=["duo"], code="launch").json
    assert r["items"] == [{"id": TSLA, "price": "0.99"}] and r["bundles"] == [{"key": "duo", "price": "150.00"}]
    assert r["total"] == "150.99" and r["discount_rate"] == "0" and r["subtotal"] == "200.00"


def test_pack(client, settings):
    settings.pack_size, settings.pack_price = 2, Decimal("120")
    r = quote(client, items=[AAPL, MSFT, TSLA], pack=[AAPL, TSLA]).json
    # price is what the cart charges (120 less the 15% tier); save is the pack's own: 1 - 120/129
    assert r["pack"] == {"ids": [AAPL, TSLA], "price": "102.00", "was": "129.00", "save": "0.07"}
    assert [i["id"] for i in r["items"]] == [MSFT]
    assert r["subtotal"] == "213.00" and r["total"] == "181.05"  # 93 + 120, 15% tier


def test_a_pack_needs_exactly_its_size_of_paid_strategies(client, settings):
    settings.pack_size = 2
    for pack in ([AAPL], [AAPL, AAPL], [AAPL, NVDA], [AAPL, MSFT, TSLA]):
        r = quote(client, pack=pack)
        assert r.status_code == 400 and r.json == {"error": "errPackSize", "vars": {"n": 2}}, pack


def test_unknown_bundle_and_empty_cart(client):
    assert quote(client, bundles=["gold"]).json == {"error": "errUnknownBundles", "bundles": ["gold"]}
    assert quote(client, items=[], bundles=[], pack=[]).json == {"error": "errCartEmpty"}


def test_buying_a_bundle_and_a_pack(app, client, settings):
    # (this cart was duo + a pack of TSLA and AAPL: AAPL is in duo, so that cart is now refused, see below)
    settings.pack_size, settings.pack_price = 1, Decimal("40")
    order = client.post("/api/orders", json={"bundles": ["duo"], "pack": [TSLA]})
    assert order.status_code == 200, order.text
    o = order.json
    assert o["total"] == "161.50"  # 150 + 40 = 190, 15% tier
    with app.app_context():
        stored = orders.find(o["id"])
        assert sorted(stored.items) == sorted(" - ".join(r[k] for k in ("ticker", "interval", "key_techs", "id_model"))
                                              for r in (ROWS[0], ROWS[1], ROWS[3]))
        assert stored.lines["bundles"] == [{"key": "duo", "price": "127.50"}]
    receipt = client.post(f"/api/orders/{o['id']}/capture").json
    assert {d["id"] for d in receipt["downloads"]} == {AAPL, MSFT, TSLA}


TWICE = {"error": "errBundleOverlap", "items": [AAPL]}


def test_a_bundle_and_a_pack_never_charge_a_strategy_twice(app, client, settings):
    settings.pack_size, settings.pack_price = 2, Decimal("80")
    for path in ("/api/quote", "/api/orders"):
        r = client.post(path, json={"bundles": ["duo"], "pack": [TSLA, AAPL]})
        assert r.status_code == 400 and r.json == TWICE, path
    with app.app_context():
        assert Order.query.count() == 0
    assert quote(client, items=[AAPL], pack=[TSLA, AAPL]).status_code == 200, "a loose item is just dropped"


def test_two_bundles_never_charge_a_strategy_twice(app, client, settings, paypal):
    settings.bundles.write_text(json.dumps(BUNDLES + [{"key": "apple", "ids": [AAPL, TSLA], "price": 110}]))
    install(app, settings, paypal)
    for path in ("/api/quote", "/api/orders"):
        r = client.post(path, json={"bundles": ["duo", "apple"]})
        assert r.status_code == 400 and r.json == TWICE, path
    assert quote(client, bundles=["duo", "duo"]).status_code == 200, "the same bundle twice counts once"
    assert quote(client, bundles=["apple"], items=[AAPL, MSFT]).json["total"] == "172.55"  # 110 + 93, 15%


def test_the_shipped_bundles_can_all_be_bought_together(real_client):
    # (top5 and amzn used to share AMZN_1Day_1T00_912096cc, and such a cart is refused)
    r = real_client.post("/api/quote", json={"bundles": ["top5", "crypto", "amzn"]})
    assert r.status_code == 200 and r.json["subtotal"] == "487.00"  # 249 + 119 + 119
    top5 = real_client.get("/api/bundles").json["bundles"][0]["ids"]
    others = [r["id"] for r in real_client.get("/api/strategies?paid=1&sort=npp&size=40").json["rows"]
              if r["id"] not in top5][:4]
    r = real_client.post("/api/quote", json={"bundles": ["top5"], "pack": [top5[0], *others]})
    assert r.status_code == 400 and r.json == {"error": "errBundleOverlap", "items": [top5[0]]}


def test_a_pack_never_costs_more_than_its_strategies(app, client, settings):
    settings.pack_size, settings.pack_price = 2, Decimal("249")
    r = quote(client, pack=[AAPL, TSLA]).json  # $79 + $50 = $129 < $249
    assert r["pack"] == {"ids": [AAPL, TSLA], "price": "129.00", "was": "129.00", "save": "0"}
    assert r["subtotal"] == "129.00" and r["total"] == "129.00"
    settings.pack_price = Decimal("120")
    r = quote(client, pack=[AAPL, TSLA]).json
    assert r["pack"] == {"ids": [AAPL, TSLA], "price": "120.00", "was": "129.00", "save": "0.07"}
    order = client.post("/api/orders", json={"pack": [AAPL, TSLA]}).json
    with app.app_context():
        assert order["total"] == "120.00" and orders.find(order["id"]).lines["pack"]["was"] == "129.00"


def test_a_pack_of_the_cheapest_real_strategies(real_client):
    cat = Catalogue(ROOT / "catalogue" / "catalogue.csv")
    cheap = sorted((s for s in cat if s.price > 0), key=lambda s: s.price)[:5]
    was = sum(s.price for s in cheap)
    r = real_client.post("/api/quote", json={"pack": [s.id for s in cheap]}).json
    assert r["pack"]["was"] == str(was)
    assert r["subtotal"] == f"{min(was, Decimal(249)):.2f}", "a pack never costs more than its strategies"
    if was < 249:  # the pack itself saves nothing on them; price is what the cart charges, after its tier
        assert r["pack"]["save"] == "0" and r["pack"]["price"] == r["total"]
    pack = real_client.get("/api/bundles").json["pack"]
    assert pack["was"] == 5 * float(cat.median_paid_price) and pack["was"] > pack["price"]


def test_the_ladder_comes_from_the_server(client, settings):
    settings.pack_size, settings.pack_price = 2, Decimal("160")
    r = quote(client, pack=[AAPL, MSFT]).json            # subtotal exactly $160: not above it
    assert (r["subtotal"], r["tier_rate"], r["tier_index"]) == ("160.00", "0", 0)
    assert r["next_tier"] == {"over": "160", "rate": "0.15", "missing": "0.01"}
    r = quote(client, items=[TSLA]).json                  # $50
    assert r["tier_index"] == 0 and r["next_tier"] == {"over": "160", "rate": "0.15", "missing": "110.01"}
    r = quote(client, items=[AAPL, MSFT]).json            # $172: the 15% tier, the 20% one next
    assert (r["tier_rate"], r["tier_index"]) == ("0.15", 1)
    assert r["next_tier"] == {"over": "290", "rate": "0.20", "missing": "118.01"}
    r = quote(client, items=[AAPL, MSFT], code="launch").json
    assert (r["tier_index"], r["next_tier"]) == (0, None), "a flat-price code: no tier applies at all"


def test_past_the_last_tier(settings):
    from edgefolio.catalogue import Strategy
    from edgefolio.pricing import quote as price
    big = [Strategy("T", "1Day", f"K{i}", f"id{i}", Decimal("99"), {}) for i in range(30)]  # $2,970
    q = price(big, "", settings).as_dict()
    assert (q["tier_rate"], q["tier_index"], q["next_tier"]) == ("0.70", 5, None)
    assert price(big[:5], "", settings).as_dict()["next_tier"] == {"over": "500", "rate": "0.25", "missing": "5.01"}
