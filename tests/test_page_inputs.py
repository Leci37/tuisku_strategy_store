# -*- coding: utf-8 -*-
"""La página aguanta lo que le llega de fuera, en un Chromium de verdad (el kit del núcleo, ``testing.mobile``): un
enlace #s= mal formado y un código de descuento guardado que el servidor no acepta (14-11-2026: la página en blanco y
un carrito atascado en «Pagas 0,00 US$»)."""
import json

from zlecitool_core.testing import mobile

from edgefolio.settings import ROOT

UI = json.loads((ROOT / "i18n" / "ui.json").read_text(encoding="utf-8"))
TOUR_SEEN = "try { localStorage.setItem('edgefolio-tour-v1', '1'); } catch (e) {}"
SAVED = "() => { try { return JSON.parse(localStorage.getItem('edgefolio-cart-v1')); } catch (e) { return null; } }"


def test_a_malformed_strategy_link_says_it_is_not_found(real_app):
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page, errors = tab.page, []
        page.on("pageerror", lambda e: errors.append(str(e)))
        try:
            page.add_init_script(TOUR_SEEN)
            tab.goto("/?lang=es#s=%E0%A4")
            page.get_by_text(UI["errUnknownStrategy"]["es"]).first.wait_for()
            assert errors == []
        finally:
            tab.close()


def test_a_saved_code_the_server_refuses_is_forgotten(real_app):
    paid = next(r for r in real_app.test_client().get("/api/strategies?paid=1&size=1").json["rows"])
    saved = json.dumps({"cart": [paid["id"]], "bundles": [], "packIds": [], "code": "x" * 70, "applied": "x" * 70})
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(TOUR_SEEN)
            page.add_init_script("if (!sessionStorage.getItem('seeded')) { sessionStorage.setItem('seeded', '1'); "
                                 f"localStorage.setItem('edgefolio-cart-v1', {json.dumps(saved)}); }}")
            quotes = []
            page.on("response", lambda r: quotes.append(r.status) if r.url.endswith("/api/quote") else None)
            tab.goto("/?lang=es")
            page.wait_for_function(f"() => ({SAVED})() && ({SAVED})().code === ''")
            page.wait_for_load_state("networkidle")
            assert quotes and set(quotes) == {200}, quotes
            assert page.locator("[data-ef-toast]").count() == 0
            assert page.evaluate(SAVED)["cart"] == [paid["id"]]
            assert all(n == 64 for n in page.locator("input[maxlength='64']").evaluate_all("e => e.map(i => i.maxLength)"))
        finally:
            tab.close()
