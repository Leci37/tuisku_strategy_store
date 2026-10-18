# -*- coding: utf-8 -*-
"""Los precios salen del catálogo y los descuentos se calculan en el servidor: nunca se fían del navegador."""
from decimal import Decimal

from edgefolio.pricing import quote


def test_quote_uses_catalogue_prices_not_the_browsers(client, ids):
    # la página de antes mandaba el importe; un carrito trucado que dice un precio no lo cambia
    r = client.post("/api/quote", json={"items": ids[:2], "code": "", "price": "0.01", "total": "0.01"})
    assert r.status_code == 200
    assert r.json["subtotal"] == "172.00" and r.json["total"] == "146.20"  # 79 + 93, escalón del 15 % sobre 160 $


def test_each_strategy_counts_once(client, ids):
    r = client.post("/api/quote", json={"items": [ids[0]] * 5})
    assert r.json["total"] == "79.00"


def test_code_adds_to_the_tier(client, ids):
    r = client.post("/api/quote", json={"items": ids[:2], "code": " Spring20 "})
    assert r.json["code_status"] == "applied"
    assert Decimal(r.json["discount_rate"]) == Decimal("0.35")  # 15 % del escalón + 20 % del código
    assert (r.json["tier_rate"], r.json["code_rate"]) == ("0.15", "0.20")


def test_stacked_discounts_are_capped(settings):
    # la página de antes sumaba el escalón del 70 % a un código del 60 % y mandaba a PayPal un importe negativo
    from edgefolio.catalogue import Strategy
    big = [Strategy("T", "1Day", f"K{i}", f"id{i}", Decimal("99"), {}) for i in range(30)]  # 2.970 $
    q = quote(big, "big60", settings)
    assert q.discount_rate == settings.max_discount
    assert q.total == Decimal("891.00") and q.total > 0


def test_flat_price_code(client, ids):
    r = client.post("/api/quote", json={"items": ids[:2], "code": "launch"})
    assert r.json["total"] == "1.98" and r.json["code_status"] == "applied"


def test_unknown_code_gives_no_discount(client, ids):
    r = client.post("/api/quote", json={"items": [ids[0]], "code": "free60"})
    assert r.json["code_status"] == "invalid" and r.json["total"] == "79.00"


def test_unknown_item_and_empty_cart(client):
    r = client.post("/api/quote", json={"items": ["bm90LWEtc3RyYXRlZ3k"]})
    assert r.status_code == 400 and r.json == {"error": "errUnknownItems", "items": ["bm90LWEtc3RyYXRlZ3k"]}
    r = client.post("/api/quote", json={"items": []})
    assert r.status_code == 400 and r.json == {"error": "errCartEmpty"}


def test_plain_key_is_accepted_too(client):
    r = client.post("/api/quote", json={"items": ["AAPL - 1Day - 1ADX - aaaa1111"]})
    assert r.json["total"] == "79.00"


def test_new_id_and_old_cart_id_are_the_same_item(client, ids):
    r = client.post("/api/quote", json={"items": ["AAPL_1Day_1ADX_aaaa1111", ids[0]]})
    assert r.json["total"] == "79.00" and r.json["items"] == [{"id": "AAPL_1Day_1ADX_aaaa1111", "price": "79.00"}]


def test_config_exposes_no_codes_or_secrets(client, settings):
    body = client.get("/api/config").get_data(as_text=True)
    for secret in ("spring20", "big60", "launch"):
        assert secret not in body
    assert client.get("/api/config").json["tiers"][0] == {"over": "2500", "rate": "0.70"}
