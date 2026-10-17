# -*- coding: utf-8 -*-
"""La barra de abajo de la tienda en un móvil (la del diseño, static/js/views/phonebar.js), en un Chromium de
verdad con el kit del núcleo (``testing.mobile``, 0.28): lleva ``data-zt-bottom``, y la carcasa mide lo que
tapa (``--zt-bottom-h``) y deja ese sitio debajo del pie; antes eran 64 px escritos en edgefolio.css. En un
ordenador no hay barra, ni sitio. Sobre el catálogo de verdad (``real_app``): sus miniaturas existen, y la
pestaña no apunta ningún error (un 404, la consola, la CSP)."""
from zlecitool_core.testing import mobile

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
