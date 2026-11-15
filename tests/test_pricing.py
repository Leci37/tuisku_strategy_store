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
    # en el tope, el código no quita nada: la franja de Pro no puede prometer «70 % + 60 % con el código»
    assert q.tier_rate + q.code_rate == q.discount_rate and q.code_rate == 0 and q.code_status == "applied"
    assert q.as_dict()["code_rate"] == "0.00"


def test_the_code_part_is_what_it_takes_off_after_the_cap(settings):
    from edgefolio.catalogue import Strategy
    two = [Strategy("T", "1Day", f"K{i}", f"id{i}", Decimal("600"), {}) for i in range(2)]  # 1.200 $: escalón del 40 %
    q = quote(two, "big60", settings)            # 40 % + 60 %, con el tope del 70 %: el código quita un 30 %
    assert (q.tier_rate, q.code_rate, q.discount_rate) == (Decimal("0.40"), Decimal("0.30"), Decimal("0.70"))
    settings.max_discount = Decimal("0.30")      # un tope por debajo del escalón: el escalón también se corta
    q = quote(two, "", settings)
    assert (q.tier_rate, q.code_rate, q.discount_rate) == (Decimal("0.30"), Decimal("0"), Decimal("0.30"))
    assert q.total == Decimal("840.00")


def test_no_next_tier_is_offered_once_the_cap_is_reached(settings):
    # «Añade X más para llegar al N %» no miraba el tope: con big60 (60 %) y el escalón del 15 %, ya en el 70 %,
    # prometía el del 20 %, que no quita nada más (14-11-2026). Sin código, el siguiente escalón sí se ofrece.
    from edgefolio.catalogue import Strategy
    two = [Strategy("T", "1Day", f"K{i}", f"id{i}", Decimal("90"), {}) for i in range(2)]  # 180 $: escalón del 15 %
    assert quote(two, "", settings).next_tier["rate"] == "0.20"
    capped = quote(two, "big60", settings)
    assert capped.discount_rate == settings.max_discount and capped.next_tier is None
    assert quote(two, "spring20", settings).next_tier["rate"] == "0.20"   # 35 % → 40 %: sí quita más


def test_a_bundle_never_makes_the_cart_dearer(settings):
    # M1: con su precio de oferta, un lote bajaba el carrito de tramo: 15 sueltas de 69 (1.035 $, −40 %) costaban
    # 621,00, y las mismas con 5 en un lote de 229 (919 $, −25 %), 689,25. Cuando la oferta costaría más que sueltas,
    # el tramo cuenta lo que valen sueltas; si no, el precio es el de siempre.
    from types import SimpleNamespace
    from edgefolio.catalogue import Strategy
    fifteen = [Strategy("T", "1Day", f"K{i}", f"id{i}", Decimal("69"), {}) for i in range(15)]
    bundle = SimpleNamespace(key="top5", price=Decimal("229"), items=fifteen[:5])
    loose = quote(fifteen, "", settings)
    packed = quote(fifteen[5:], "", settings, [bundle])
    assert (loose.total, loose.discount_rate) == (Decimal("621.00"), Decimal("0.40"))
    assert packed.discount_rate == Decimal("0.40") and packed.total == Decimal("551.40") and packed.total < loose.total
    own = quote(fifteen[5:], "", settings, pack=fifteen[:5])          # «Arma tu pack», igual
    assert own.discount_rate == Decimal("0.40") and own.total < loose.total
    alone = quote([], "", settings, [bundle])                         # el lote solo, más barato que suelto: igual
    assert (alone.total, alone.discount_rate) == (Decimal("194.65"), Decimal("0.15"))


def test_flat_price_code(client, ids):
    # 0,99 por cada suelta, pero nunca más del tope (MAX_DISCOUNT, 70 %): 79 → 23,70 y 93 → 27,90 (2026-11-15; antes,
    # 1,98 las dos: un 98,8 % menos)
    r = client.post("/api/quote", json={"items": ids[:2], "code": "launch"})
    assert r.json["total"] == "51.60" and r.json["code_status"] == "applied"


def test_a_flat_price_code_never_raises_the_total(settings):
    # M8: con un código de precio fijo, los lotes pierden su escalón: una suelta y un lote grande costaban más con el
    # código que sin él. Si sin él cuesta menos, se cobra como sin él.
    from types import SimpleNamespace
    from edgefolio.catalogue import Strategy
    one = Strategy("T", "1Day", "K0", "id0", Decimal("69"), {})
    many = [Strategy("T", "1Day", f"B{i}", f"b{i}", Decimal("99"), {}) for i in range(30)]
    big = SimpleNamespace(key="big", price=Decimal("2600"), items=many)
    plain = quote([one], "", settings, [big])
    coded = quote([one], "launch", settings, [big])
    assert plain.discount_rate == Decimal("0.70") and coded.total == plain.total and coded.code_status == "applied"


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
