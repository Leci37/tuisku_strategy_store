# -*- coding: utf-8 -*-
"""La barra de abajo de la tienda en un móvil (la del diseño, static/js/views/phonebar.js), en un Chromium de
verdad con el kit del núcleo (``testing.mobile``, 0.28): lleva ``data-zt-bottom``, y la carcasa mide lo que
tapa (``--zt-bottom-h``) y deja ese sitio debajo del pie; antes eran 64 px escritos en edgefolio.css. En un
ordenador no hay barra, ni sitio. Sobre el catálogo de verdad (``real_app``): sus miniaturas existen, y la
pestaña no apunta ningún error (un 404, la consola, la CSP). Y con un diálogo abierto, un aviso nunca lo tapa."""
import json
import re

from zlecitool_core.testing import mobile

from edgefolio.settings import ROOT

UI = json.loads((ROOT / "i18n" / "ui.json").read_text(encoding="utf-8"))
BAR = "nav[data-zt-bottom]"
# Lo que mide la pestaña: lo que tapa la barra (de su borde de arriba al de abajo de la ventana), lo que
# dice la carcasa que tapa, el sitio que deja la página y dónde acaban el pie y la barra.
MEASURE = """() => {
  const bar = document.querySelector('nav[data-zt-bottom]');
  const footer = document.querySelector('footer.app-footer');
  return {
    covers: bar ? Math.ceil(window.innerHeight - bar.getBoundingClientRect().top) : 0,
    room: getComputedStyle(document.documentElement).getPropertyValue('--zt-bottom-h').trim(),
    padding: getComputedStyle(document.body).paddingBottom,
    barTop: bar ? bar.getBoundingClientRect().top : null,
    footerBottom: footer.getBoundingClientRect().bottom,
  };
}"""
MEASURED = "() => getComputedStyle(document.documentElement).getPropertyValue('--zt-bottom-h').trim() !== '0px'"
LISTED = "() => document.querySelectorAll('#app img').length > 0"


def test_on_a_phone_the_page_leaves_the_room_the_bottom_bar_covers(real_app):
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "phone")
        try:
            mobile.sign_in(tab)              # con el aviso de cookies contestado: no deja su propio sitio
            tab.goto("/")
            tab.page.wait_for_selector(BAR)
            tab.page.wait_for_function(MEASURED)
            tab.page.wait_for_function(LISTED)
            seen = tab.page.evaluate(MEASURE)
            assert seen["covers"] >= 44 and seen["room"] == f"{seen['covers']}px", seen
            assert seen["padding"] == seen["room"], "la página deja abajo lo que tapa la barra"
            tab.page.evaluate("() => window.scrollTo(0, document.documentElement.scrollHeight)")
            tab.page.wait_for_function("() => window.innerHeight + window.scrollY >= "
                                       "document.documentElement.scrollHeight - 1")
            end = tab.page.evaluate(MEASURE)
            assert end["footerBottom"] <= end["barTop"] + 0.5, f"el final del pie queda bajo la barra: {end}"
            assert tab.problems() == []
        finally:
            tab.close()


def test_on_a_laptop_there_is_no_bar_and_no_room(real_app):
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        try:
            mobile.sign_in(tab)
            tab.goto("/")
            tab.page.wait_for_function(LISTED)
            seen = tab.page.evaluate(MEASURE)
            assert tab.page.locator(BAR).count() == 0
            assert (seen["room"], seen["padding"]) == ("0px", "0px"), seen
            assert tab.problems() == []
        finally:
            tab.close()


# El aviso y el diálogo abierto, en px de la ventana: si se cruzan, si en medio del botón ``name`` del diálogo
# está el botón (y no el aviso encima) y lo que el velo deja arriba, además de sus 16 px, menos lo que mide el
# aviso (8: el aviso medido, no un alto supuesto).
APART = """name => { const d = document.querySelector('[role=dialog]'), t = document.querySelector('[data-ef-toast]');
  const b = [...d.querySelectorAll('button')].find(x => x.textContent.trim() === name), r = b.getBoundingClientRect();
  const at = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2), D = d.getBoundingClientRect(),
    T = t.getBoundingClientRect();
  return { apart: T.bottom <= D.top || D.bottom <= T.top, onTop: !!at && b.contains(at), toastTop: Math.round(T.top),
    room: Math.round(parseFloat(getComputedStyle(d.parentElement).paddingTop) - 16 - T.height) }; }"""
ABOVE_CART = """() => document.querySelector('[data-ef-toast]').getBoundingClientRect().bottom <=
  document.querySelector('[data-sf-cart]').getBoundingClientRect().top"""


def test_on_a_phone_a_toast_never_covers_an_open_dialog(real_app):
    """C13: con un diálogo abierto, su velo tapa el carrito flotante y la barra: el aviso va arriba y el diálogo le
    deja su sitio. Antes, en Lite con algo en el carrito, el aviso de un enlace gastado (encima del carrito
    flotante) tapaba «Enviarme el enlace» de la gratis; y el selector del pack (90vh) no deja sitio ni arriba ni
    abajo. Al cerrarse, el aviso vuelve encima del carrito."""
    paid = real_app.test_client().get("/api/strategies?paid=1&size=1").json["rows"][0]["id"]
    cart = json.dumps({"cart": [paid], "bundles": [], "packIds": [], "code": "", "applied": ""})
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "phone")
        page = tab.page
        try:
            mobile.sign_in(tab)
            page.add_init_script("try { localStorage.setItem('edgefolio-tour-v1', '1'); "
                                 "localStorage.setItem('edgefolio-cart-v1', %s); } catch (e) {}" % json.dumps(cart))
            tab.goto("/?link=errDownloadLimit")       # el enlace de un correo viejo, ya sin descargas
            page.wait_for_selector("[role=alert][data-ef-toast]")
            page.wait_for_function(LISTED)
            page.wait_for_function(ABOVE_CART)
            for opener, name in ((page.locator("#app button", has_text=re.compile(r"^\s*Descargar\s*$")).first, UI["sendLink"]["es"]),
                                 (page.locator("#app button", has_text=re.compile(r"^\+$")).first, UI["done"]["es"])):
                opener.click()
                page.wait_for_selector("[role=dialog]")
                page.wait_for_function(f"n => ({APART})(n).apart", arg=name)
                seen = page.evaluate(APART, name)
                assert seen == {"apart": True, "onTop": True, "toastTop": 16, "room": 8}, (name, seen)
                page.keyboard.press("Escape")
                page.wait_for_selector("[role=dialog]", state="detached")
                page.wait_for_function(ABOVE_CART)
            assert tab.problems() == []
        finally:
            tab.close()
