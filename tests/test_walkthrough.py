# -*- coding: utf-8 -*-
"""El camino de compra de punta a punta, a clics, en un Chromium de verdad (el kit del núcleo,
``testing.mobile``) sobre el catálogo de verdad (``real_app``): lo que tools/screenshots.py recorre fuera de
pytest, aquí en cada vuelta y en la CI.

Sin cuenta: Lite, «Comprar» en una ficha → el buscador → la página de otra estrategia y «Añadir al carrito» →
volver a la tienda y «Pagar» con el PayPal de prueba → Gracias, con las dos. Después, con una cuenta del núcleo:
Mis estrategias, «¿Compraste sin cuenta?» con el correo con el que se pagó → el enlace del correo → «Sí,
<correo> es mío» → Mis estrategias con lo comprado.
"""
import json
import re

from zlecitool_core.testing import mobile

from edgefolio.settings import ROOT
from tests.conftest import proof_token

UI = json.loads((ROOT / "i18n" / "ui.json").read_text(encoding="utf-8"))
TOUR_SEEN = "try { localStorage.setItem('edgefolio-tour-v1', '1'); } catch (e) {}"
CART = "() => { try { return JSON.parse(localStorage.getItem('edgefolio-cart-v1')).cart; } catch (e) { return null; } }"
BUYER = "buyer@example.com"   # el que da el PayPal de prueba (paypal.FakePayPal) al cobrar


def es(key: str) -> str:
    return UI[key]["es"]


def button(page, text: str):
    return page.locator("#app button", has_text=re.compile(r"^\s*" + re.escape(text) + r"\s*$"))


def picks(app):
    """La de la ficha de Lite (la primera de pago de Destacadas) y la del buscador (la primera de pago de otro
    ticker, sola la primera de su búsqueda)."""
    def rows(query):
        return app.test_client().get("/api/strategies?" + query).json
    card = next(r for r in rows("tab=hot&size=24")["rows"] if r["price"] > 0)
    for r in rows("paid=1&sort=hot&size=48")["rows"]:
        found = rows(f"tab=hot&size=24&q={r['ticker']}")
        if r["ticker"] != card["ticker"] and found["rows"][0]["id"] == r["id"]:
            return card, r, found["total"]
    raise AssertionError("ninguna estrategia de pago es la primera de la búsqueda de su ticker")


def test_buy_by_clicking_then_see_it_in_my_strategies(real_app):
    card, searched, found = picks(real_app)
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(TOUR_SEEN)

            # Lite: «Comprar» en la primera ficha de pago
            tab.goto("/?lang=es")
            page.get_by_text(re.compile(r"^Mostrando \d+ de \d+")).wait_for()
            button(page, "Comprar").first.click()
            page.wait_for_function(f"() => JSON.stringify(({CART})()) === JSON.stringify({json.dumps([card['id']])})")

            # el buscador acota la lista; la primera ficha lleva a su página
            page.locator("input[data-search=lite]").fill(searched["ticker"])
            page.get_by_text(re.compile(rf"^Mostrando \d+ de {found}$")).wait_for()
            page.locator(f"#app [title='{es('openPage')}']").first.click()
            page.wait_for_url(f"**/s/{searched['id']}")
            button(page, es("addToCart")).first.click()
            button(page, es("inCartBtn")).first.wait_for()
            assert page.evaluate(CART) == [card["id"], searched["id"]]

            # de vuelta a la tienda, «Pagar» con el PayPal de prueba → Gracias, con las dos
            button(page, es("backShop")).first.click()
            page.wait_for_url(re.compile(r"/(\?.*)?$"))
            button(page, es("checkout")).first.click()
            page.wait_for_url("**/thanks**")
            page.get_by_text(es("thanksTitle")).first.wait_for()
            page.keyboard.press("Escape")                   # el tutorial de instalación se abre solo la primera vez
            for r in (card, searched):
                page.get_by_text(f"{r['name']} · {r['ticker']}").first.wait_for()

            # con una cuenta del núcleo: demostrar el correo con el que se pagó, a clics y con el enlace del correo
            mobile.sign_in(tab)
            tab.goto("/mine")
            page.locator("section input[type=email]").fill(BUYER)
            page.get_by_role("button", name=es("sendLink"), exact=True).click()
            page.get_by_text(es("proofSent")).first.wait_for()
            tab.goto(f"/mine?proof={proof_token(BUYER)}")
            page.get_by_role("button", name=es("proofAs").replace("{e}", BUYER)).click()

            # Mis estrategias, con lo comprado
            for r in (card, searched):
                page.locator(f"#app a[href='/s/{r['id']}']").first.wait_for()
            assert tab.problems() == [], tab.problems()
        finally:
            tab.close()
