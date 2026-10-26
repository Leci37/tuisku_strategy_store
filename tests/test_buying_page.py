# -*- coding: utf-8 -*-
"""Comprar lo que ya es de la cuenta, las actualizaciones y tres arreglos pequeños, en un Chromium de verdad (el kit
del núcleo, ``testing.mobile``) sobre el catálogo de verdad (``real_app``). Decisiones del dueño del 2026-10-26.

- E8: con la sesión abierta, una estrategia que ya es de la cuenta dice «Ya es tuya» en las fichas de Lite y en las
  Filas, Fichas y Tabla de Pro, como en su página, y nunca «Comprar»; donde el precio va con el botón, sin él (en la
  Tabla, su columna se queda). Su .pine si el enlace vale, si no Mis estrategias, sin recargar. Un carrito que la
  lleva (el de antes de entrar) la pierde: el servidor la rechaza (409 errAlreadyOwned) y la página la quita y lo
  dice el aviso. Su página dice «Ya es tuya» sin el precio encima.
- Las actualizaciones, gratis mientras la estrategia no ha caducado: después, ni «Obtener la actualización» en Mis
  estrategias ni «Actualización disponible» en su página (con una v2 inventada: hoy todas son v1).
- La gratis, más alta que un móvil tumbado (844×390), se desliza por dentro: «Enviarme el enlace» se alcanza.
- «Hecho» de «¿Compraste sin cuenta?» se anuncia (una región viva, ya en la página antes de pedir el enlace).
- El buscador de Pro, desde la barra de abajo, queda justo debajo de la barra fija del núcleo (``--zt-sticky-top``),
  también en una pantalla baja, donde la barra se suelta y no tapa nada.
"""
import json
import re
from contextlib import contextmanager
from dataclasses import replace
from datetime import date

from zlecitool_core.testing import mobile

from edgefolio.settings import ROOT
from edgefolio.shop import of
from tests.test_mine import buy

UI = json.loads((ROOT / "i18n" / "ui.json").read_text(encoding="utf-8"))
TOUR_SEEN = "try { localStorage.setItem('edgefolio-tour-v1', '1'); } catch (e) {}"
OWNED = "#app [data-ef-owned]"
NOTICE = "[role=status][data-ef-toast]"
CART = "() => { try { return JSON.parse(localStorage.getItem('edgefolio-cart-v1')).cart; } catch (e) { return null; } }"
# lo que se ve de la fila, tarjeta o ficha de lista donde está [data-ef-owned]: su texto, su enlace y si enseña un
# precio (los de la tienda: «… US$», «≈ … €», «Gratis»)
AROUND = """sel => [...document.querySelectorAll(sel)].map(a => { const box = a.closest('.sf-hover2, .sf-hover7, tr')
  || a.parentElement.parentElement; return { text: (a.textContent.trim() || a.getAttribute('aria-label')), href: a.getAttribute('href'),
  price: [...box.querySelectorAll('span, td')].some(x => x.children.length === 0 && /US\\$|€|^Gratis$/.test(x.textContent.trim())) }; })"""


def say(key, lang="es"):
    return UI[key][lang]


def rows(app, query):
    return app.test_client().get("/api/strategies?" + query).json["rows"]


def first_paid_in_both(app, n):
    """``n`` estrategias de pago que salen en la primera página de Lite (Destacadas) y en la de Pro."""
    lite = [r["id"] for r in rows(app, "tab=hot&size=24") if r["price"] > 0]
    pro = {r["id"] for r in rows(app, "sort=np&size=25")}
    both = [i for i in lite if i in pro]
    assert len(both) >= n, both
    return both[:n]


@contextmanager
def published_as(app, sid, **changes):
    """La estrategia ``sid`` como si el catálogo la trajera así (``version``, ``expiry``): la tienda de las pruebas es
    de toda la sesión, así que vuelve a como estaba."""
    cat = of(app).catalogue
    s = cat.resolve(sid)
    row = {**s.row, "version": str(changes.pop("version"))} if "version" in changes else s.row
    cat.items[s.key] = cat.by_id[s.id] = replace(s, row=row, **changes)
    try:
        yield
    finally:
        cat.items[s.key] = cat.by_id[s.id] = s


def test_what_the_account_has_is_already_yours_everywhere_and_leaves_the_cart(real_app):
    owned, gone = first_paid_in_both(real_app, 2)
    other = next(r["id"] for r in rows(real_app, "paid=1&size=48") if r["id"] not in (owned, gone))
    days = of(real_app).settings.download_days
    cart = json.dumps({"cart": [owned, other], "bundles": [], "packIds": [], "code": "", "applied": ""})
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            # el carrito de antes de entrar, una vez (no en cada página)
            page.add_init_script(TOUR_SEEN + "try { if (!sessionStorage.getItem('set')) { sessionStorage.setItem('set', '1');"
                                 " localStorage.setItem('edgefolio-cart-v1', %s); } } catch (e) {}" % json.dumps(cart))
            client = mobile.sign_in(tab)
            buy(client, [owned])
            of(real_app).settings.download_days = -1             # nacido caducado: «Ya es tuya» lleva a Mis estrategias
            try:
                buy(client, [gone])
            finally:
                of(real_app).settings.download_days = days
            link = next(i["url"] for i in client.get("/api/mine").json["items"] if i["id"] == owned)

            # el presupuesto la rechaza; la página la quita del carrito y lo dice
            tab.goto("/")
            page.locator(NOTICE).wait_for()
            assert page.locator(NOTICE).inner_text().split("\n")[:2] == [say("cartUpdatedTitle"), say("errAlreadyOwned")]
            page.wait_for_function(f"o => JSON.stringify(({CART})()) === JSON.stringify(o)", arg=[other])
            # y lo que queda se presupuesta otra vez: «Pagas 73,00 US$ con PayPal»
            pays = "Pagas " + client.post("/api/quote", json={"items": [other]}).json["total"].replace(".", ",")
            page.wait_for_function("t => document.querySelector('[data-sf-cart]').innerText.includes(t)", arg=pays)
            # Lite: «Ya es tuya», su .pine o Mis estrategias, sin precio ni «Comprar»
            page.wait_for_function(f"() => document.querySelectorAll('{OWNED}').length === 2")
            ours = {x["href"]: x for x in page.evaluate(AROUND, OWNED)}
            assert ours == {link: {"text": say("ownedYours") + " · " + say("download"), "href": link, "price": False},
                            "/mine": {"text": say("ownedYours") + " · " + say("myStrategies"), "href": "/mine", "price": False}}
            assert mobile.contrast_problems(tab, OWNED) == []
            page.evaluate("() => zt.setLanguage('ar')")
            page.wait_for_function("t => [...document.querySelectorAll('#app [data-ef-owned]')].some(a => a.textContent.trim() === t)",
                                   arg=say("ownedYours", "ar") + " · " + UI["download"]["ar"])
            page.evaluate("() => zt.setLanguage('es')")

            # Pro: Filas y Fichas, sin precio; la Tabla conserva su columna y el icono lo dice (su nombre)
            for view, price in (("rows", False), ("cards", False), ("table", True)):
                page.evaluate("v => { localStorage.setItem('tuisku-sf-mode', 'pro'); localStorage.setItem('tuisku-sf-pview5', v); }", view)
                tab.goto("/")
                page.wait_for_function(f"() => document.querySelectorAll('{OWNED}').length === 2")
                seen = {x["href"]: (x["text"], x["price"]) for x in page.evaluate(AROUND, OWNED)}
                assert seen == {link: (say("ownedYours") + " · " + say("download"), price),
                                "/mine": (say("ownedYours") + " · " + say("myStrategies"), price)}, view
            # en la Tabla, el clic no abre la fila: a Mis estrategias sin recargar, y al volver, la fila sigue cerrada
            page.evaluate("() => { window.__same = true; }")
            page.locator("#app tbody [data-ef-owned][href='/mine']").click()
            page.get_by_role("heading", name=say("myStrategies")).wait_for()
            assert page.evaluate("() => location.pathname === '/mine' && window.__same === true")
            page.go_back()
            page.wait_for_selector("#app tbody [data-ef-owned]")
            assert page.locator("td[colspan='12']").count() == 0, "el clic abría también la fila"

            # su página: «Ya es tuya», sin el precio encima (decisión del dueño)
            page.evaluate("() => { localStorage.setItem('tuisku-sf-mode', 'lite'); }")
            tab.goto(f"/s/{owned}")
            page.locator(OWNED).wait_for()
            head = page.locator(OWNED).locator("xpath=..").inner_text()
            assert head.startswith(say("ownedYours")) and "US$" not in head and "€" not in head, head
            assert tab.problems() == ["409 POST /api/quote"], tab.problems()
        finally:
            tab.close()


def test_paying_does_not_refuse_what_was_just_bought(real_app):
    """De vuelta de PayPal, el carrito espera al cobro: antes se presupuestaba enseguida lo que se acababa de pagar,
    el servidor lo rechazaba (ya es de la cuenta) y la página de gracias salía con «Carrito actualizado»."""
    [sid] = first_paid_in_both(real_app, 1)
    cart = json.dumps({"cart": [sid], "bundles": [], "packIds": [], "code": "", "applied": ""})
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(TOUR_SEEN + "try { localStorage.setItem('edgefolio-install-v1', '1');"
                                 " if (!sessionStorage.getItem('set')) { sessionStorage.setItem('set', '1');"
                                 " localStorage.setItem('edgefolio-cart-v1', %s); } } catch (e) {}" % json.dumps(cart))
            mobile.sign_in(tab)
            tab.goto("/")
            pay = page.locator("[data-sf-cart] button", has=page.locator("i.fa-paypal"))
            pay.wait_for()
            with page.expect_navigation(url=lambda u: "/thanks" in u):
                pay.click()
            page.wait_for_selector("#app a[href*='/api/download/']")
            page.wait_for_function(f"() => ({CART})().length === 0")
            page.wait_for_timeout(400)
            assert page.locator(NOTICE).count() == 0 and tab.problems() == [], tab.problems()
        finally:
            tab.close()


def test_an_update_is_offered_only_until_the_strategy_expires(real_app):
    [sid] = first_paid_in_both(real_app, 1)
    get_update = say("getUpdate") + " · v2"
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(TOUR_SEEN)
            client = mobile.sign_in(tab)
            buy(client, [sid])
            for expiry, offered in ((date(2099, 1, 1), True), (date(2020, 1, 1), False)):
                with published_as(real_app, sid, version=2, expiry=expiry):
                    tab.goto("/mine")
                    page.get_by_text(say("favEmpty")).wait_for()          # API #15 ya está
                    assert (page.get_by_role("button", name=get_update).count() == 1) is offered, expiry
                    tab.goto(f"/s/{sid}")
                    page.locator(OWNED).wait_for()
                    page.locator("#app strong", has_text=re.compile(r"^v2 · ")).wait_for()     # la v2 en «Versiones»
                    assert (page.get_by_text(say("updateAvail"), exact=True).count() == 1) is offered, expiry
            assert tab.problems() == []
        finally:
            tab.close()


def test_the_free_dialog_scrolls_inside_on_a_phone_lying_down(real_app):
    """En alemán (o en francés) y con un aviso arriba, la gratis mide más que lo que le deja un móvil tumbado: antes
    se salía por abajo, y «Enviarme el enlace» con ella; ahora cabe y se desliza por dentro."""
    send_de, download_de = UI["sendLink"]["de"], UI["download"]["de"]
    reachable = """t => { const b = [...document.querySelectorAll('[role=dialog] button')].find(x => x.textContent.trim() === t);
      const r = b.getBoundingClientRect(), at = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
      return !!at && b.contains(at); }"""
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "phone_landscape")
        page = tab.page
        try:
            page.add_init_script(TOUR_SEEN)
            tab.goto("/?link=errDownloadLimit")                 # un aviso arriba: el velo le deja su sitio
            page.locator("[role=alert][data-ef-toast]").wait_for()
            page.evaluate("() => zt.setLanguage('de')")
            page.locator("#app button", has_text=download_de).first.tap()
            dialog = page.locator("[role=dialog]")
            dialog.wait_for()
            box = page.evaluate("""() => { const d = document.querySelector('[role=dialog]'), r = d.getBoundingClientRect();
              return { top: r.top, bottom: r.bottom, natural: d.scrollHeight, shown: d.clientHeight, height: innerHeight,
                room: innerHeight - parseFloat(getComputedStyle(d.parentElement).paddingTop) - 16 }; }""")
            assert box["natural"] > box["room"], f"cabía entera: la prueba no prueba nada {box}"
            assert box["top"] >= 0 and box["bottom"] <= box["height"] and box["shown"] < box["natural"], box
            send = dialog.get_by_role("button", name=send_de)
            send.scroll_into_view_if_needed()
            assert page.evaluate(reachable, send_de), "«Enviarme el enlace» se queda fuera de la pantalla"
            send.tap()
            dialog.locator("[role=alert]").wait_for()           # sin correo: lo dice bajo el campo
            send.scroll_into_view_if_needed()
            assert page.evaluate(reachable, send_de)
            assert tab.problems() == []
        finally:
            tab.close()


def test_done_is_announced(real_app):
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(TOUR_SEEN)
            mobile.sign_in(tab)
            tab.goto("/mine")
            live_region = page.locator("section [aria-live=polite]")
            live_region.wait_for()
            # la región ya está antes de pedir el enlace (lo que se añade a una que ya estaba es lo que se anuncia)
            page.evaluate("() => { window.__live = document.querySelector('section [aria-live=polite]'); }")
            assert live_region.locator("h2").inner_text() == say("proofTitle")
            page.get_by_role("button", name=say("sendLink"), exact=True).click()
            page.get_by_text(say("proofSent")).wait_for()
            assert page.evaluate("t => window.__live.isConnected && window.__live.innerText.includes(t)", say("proofSent"))
            assert tab.problems() == []
        finally:
            tab.close()


# dónde queda el buscador de Pro, lo que mide lo fijo de arriba y el alto de la barra (fija o no)
WHERE = """() => { const css = getComputedStyle(document.documentElement);
  return { top: document.querySelector('input[data-search=pro]').getBoundingClientRect().top,
    sticky: parseFloat(css.getPropertyValue('--zt-sticky-top')) || 0, bar: document.querySelector('header').offsetHeight,
    focused: document.activeElement === document.querySelector('input[data-search=pro]') }; }"""


def test_the_phone_bar_search_lands_just_under_the_fixed_bar(real_app):
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        for screen in ("phone", (600, 480, True, 2)):
            tab = mobile.open_page(chromium, live, screen)
            page = tab.page
            try:
                page.add_init_script(TOUR_SEEN + "try { localStorage.setItem('tuisku-sf-mode', 'pro'); } catch (e) {}")
                tab.goto("/")
                page.wait_for_selector("#app [data-search=pro]")
                page.wait_for_function("() => document.querySelectorAll('#app img').length > 4")
                page.locator("nav[data-zt-bottom] button").nth(1).tap()          # Buscar
                page.wait_for_function("() => document.activeElement === document.querySelector('input[data-search=pro]')")
                page.wait_for_timeout(300)
                seen = page.evaluate(WHERE)
                assert abs(seen["top"] - (seen["sticky"] + 12)) <= 2, (screen, seen)
                if screen != "phone":
                    # una pantalla baja: la barra se suelta (0px) y no tapa nada; antes se restaba su alto igual
                    assert seen["sticky"] == 0 and seen["bar"] > 40, seen
                else:
                    assert seen["sticky"] > 40, seen
                assert tab.problems() == []
            finally:
                tab.close()
