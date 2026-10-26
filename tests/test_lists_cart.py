# -*- coding: utf-8 -*-
"""Las listas, el carrito y el recorrido de la tienda, en un Chromium de verdad (el kit del núcleo,
``testing.mobile``) sobre el catálogo de verdad (``real_app``), y lo que se comprueba sin navegador.

Lite: «Packs» y «Arma tu pack» esperan a los lotes (sin ellos, la tarjeta del pack salía con «Ahorra un 0 %»
y «5 por 0 €»); «≈» no se queda solo al final de una línea; el chip de la moneda sólo cambia algo si el
idioma tiene otra moneda con su cambio; un buscador no manda más de lo que acepta el servidor; la pestaña
marcada vuelve a pedir su lista después de un fallo; Intro aplica el código; en árabe, «US$» va entero y el
chip del descuento no se da la vuelta. Pro: el recorrido no lleva una cifra vieja, «1 seleccionado» y «1
estrategia mostrada» van en singular, su buscador tampoco pasa de 100, Intro aplica el código de su franja
y la fila desplegada de la Tabla se queda en la parte visible. Al llegar: sin diccionario sale el aviso del
servidor, una favorita que ya no está en el catálogo se va sin error al entrar, y la página de gracias sólo
vacía el carrito con el cobro que paga, y sin enlaces no enseña el tutorial de una estrategia que no tiene."""
import csv
import json
import re

from zlecitool_core.testing import mobile

from edgefolio.settings import ROOT

UI = json.loads((ROOT / "i18n" / "ui.json").read_text(encoding="utf-8"))
JS = ROOT / "static" / "js"
SHOWING = "() => (document.querySelector('#app').innerText.match(/Mostrando \\d+ de \\d+/) || [''])[0]"
CHIP = "[data-ef-bar=end] button[title]:not(.sf-hover0)"     # el de la moneda: los otros dos son del diseño
TOUR_SEEN = "try { localStorage.setItem('edgefolio-tour-v1', '1'); } catch (e) {}"


def text(page, selector="#app"):
    return page.locator(selector).inner_text()


# ── sin navegador ──────────────────────────────────────────────────────────────


def test_the_tour_shows_tickers_the_catalogue_sells():
    """B14: los seis logos del primer paso del recorrido son de tickers del catálogo publicado, con su icono
    grande (el que da su fila, ``path_ico_big``); el diseño traía Apple y Ethereum, que el de 2026-10 no vende."""
    code = (JS / "lib" / "vals_pages.js").read_text(encoding="utf-8")
    tickers = re.findall(r"'([^']+)'", re.search(r"tourIcons:\s*\[([^\]]*)\]", code).group(1))
    with open(ROOT / "catalogue" / "catalogue.csv", newline="", encoding="utf-8") as f:
        big = {row["path_ico_big"] for row in csv.DictReader(f, delimiter="\t")}
    assert len(tickers) == 6
    for ticker in tickers:
        icon = f"assets/icons/{ticker}_big.svg"
        assert icon in big, f"{ticker}: el catálogo no lo vende"
        assert (ROOT / "static" / icon).is_file(), icon


def test_the_search_boxes_send_what_the_server_takes(client):
    """B16: el servidor acepta 100 caracteres en q; la página corta cada consulta ahí (``Q_MAX``) y sus tres
    buscadores no dejan escribir más (``maxlength``)."""
    assert client.get("/api/strategies?q=" + "x" * 100).status_code == 200
    assert client.get("/api/strategies?q=" + "x" * 101).status_code == 400
    filters = (JS / "lib" / "filters.js").read_text(encoding="utf-8")
    assert re.search(r"export const Q_MAX = 100;", filters) and "s.q.trim().slice(0, Q_MAX)" in filters   # la de Pro
    app = (JS / "app.js").read_text(encoding="utf-8")
    assert "s.q.trim().slice(0, Q_MAX)" in app and "s.packQ.trim().slice(0, Q_MAX)" in app
    views = JS / "views"
    for name, hook in (("lite.js", 'data-search="lite"'), ("pro.js", 'data-search="pro"'),
                       ("dialogs.js", "onInput=${v.onPackQ}")):
        inputs = [i for i in re.findall(r"<input [^>]*>", (views / name).read_text(encoding="utf-8")) if hook in i]
        assert len(inputs) == 1 and 'maxlength="100"' in inputs[0], (name, inputs)


# ── Lite ───────────────────────────────────────────────────────────────────────

# lo que pide la lista de Lite: el q de la última petición (B16)
WATCH_Q = """(() => { const fetch0 = window.fetch; window.fetch = (url, ...rest) => {
  const m = String(url).match(/\\/api\\/strategies\\?tab=[^&]*&q=([^&]*)/); if (m) window.__q = decodeURIComponent(m[1]);
  return fetch0(url, ...rest); }; })()"""
# un texto que llega a un buscador sin teclearlo (maxlength no lo corta): [selector, texto]
SET_VALUE = """([sel, text]) => { const i = document.querySelector(sel);
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(i, text);
  i.dispatchEvent(new Event('input', { bubbles: true })); }"""


def test_lite_waits_for_its_data_and_keeps_its_cart_readable(real_app):
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(TOUR_SEEN)
            page.add_init_script(WATCH_Q)
            held = []
            page.route("**/api/bundles", lambda route: held.append(route))
            tab.goto("/")
            page.wait_for_function(SHOWING)
            # B7: sin los lotes (API #4), ni «Packs» ni la tarjeta del pack con sus cifras de relleno
            assert held and UI["packTitle"]["es"] not in text(page) and "Ahorra un 0" not in text(page)
            held[0].continue_()
            page.get_by_text(UI["packTitle"]["es"], exact=True).wait_for()
            # B18: «≈» y el precio, con un espacio que no parte la línea
            hint = page.locator("#app span", has_text="Elige 5 más").inner_text()
            assert re.search("≈\u00a0\\d", hint), repr(hint)

            # B2: en español el chip cambia de EUR a USD y vuelve
            chip = page.locator(CHIP)
            assert (chip.inner_text(), chip.get_attribute("aria-disabled")) == ("EUR", "false")
            chip.click()
            page.wait_for_function("s => document.querySelector(s).textContent.trim() === 'USD'", arg=CHIP)
            chip.click()
            page.wait_for_function("s => document.querySelector(s).textContent.trim() === 'EUR'", arg=CHIP)

            # B16: el buscador no deja pasar de 100, y lo que llega de otra manera se corta igual: sin un 400
            search = page.locator("input[data-search=lite]")
            search.fill("x" * 130)
            assert len(search.input_value()) == 100
            page.wait_for_function("() => (window.__q || '').length === 100")
            page.evaluate(SET_VALUE, ["input[data-search=lite]", "y" * 150])
            page.wait_for_function("() => window.__q === 'y'.repeat(100)")
            search.fill("")
            page.wait_for_function("() => window.__q === '' && /Mostrando 24 de/.test(document.querySelector('#app').innerText)")
            assert page.locator("[role=alert]").count() == 0

            # B17: la lista de una pestaña falla; la pestaña marcada la vuelve a pedir
            failed = []

            def first_fails(route):
                if failed:
                    route.continue_()
                else:
                    failed.append(route.request.url)
                    route.fulfill(status=500, content_type="application/json", body='{"error": "errLater"}')

            page.route(re.compile(r".*/api/strategies\?tab=crypto&.*"), first_fails)
            crypto = page.locator("[role=tablist] [role=tab]").nth(3)
            before = page.evaluate(SHOWING)
            crypto.click()
            page.wait_for_selector("[role=alert]")
            assert crypto.get_attribute("aria-selected") == "true" and page.evaluate(SHOWING) == before
            page.locator("[role=alert] button").click()
            with page.expect_response(re.compile(r".*/api/strategies\?tab=crypto&.*")) as again:
                crypto.click()
            assert again.value.status == 200
            total = again.value.json()["total"]
            page.wait_for_function("t => document.querySelector('#app').innerText.includes(t)",
                                   arg=f"Mostrando {min(24, total)} de {total}")

            # B24: Intro en la casilla del código lo aplica (el servidor lo comprueba: aquí no hay códigos)
            buy = page.locator("#app button", has_text=re.compile(r"^\s*Comprar\s*$"))
            buy.first.click()
            page.get_by_text(UI["haveCode"]["es"], exact=True).click()
            code = page.get_by_placeholder(UI["codePh"]["es"])
            code.fill("demo20")
            with page.expect_request(lambda r: r.url.endswith("/api/quote") and "demo20" in (r.post_data or "")):
                code.press("Enter")
            page.get_by_text(UI["codeBad"]["es"], exact=True).wait_for()

            # B2: en inglés no hay otra moneda: USD, sin elección, y el clic no la cambia para el árabe
            page.evaluate("() => zt.setLanguage('en')")
            page.wait_for_function("s => document.querySelector(s).textContent.trim() === 'USD'", arg=CHIP)
            assert chip.get_attribute("aria-disabled") == "true"
            chip.click(force=True)
            buy = page.locator("#app button", has_text=re.compile(r"^\s*Buy\s*$"))
            for _ in range(2):           # tres en el carrito: más de 160 US$, el escalón del 15 %
                buy.first.click()
                page.wait_for_timeout(150)
            page.evaluate("() => zt.setLanguage('ar')")
            page.wait_for_function("s => document.querySelector(s).textContent.trim() === 'SAR'", arg=CHIP)

            # C6: en árabe, «US$» entero (una marca de izquierda a derecha detrás) y el chip «−15%» aislado
            spans = "() => [...document.querySelectorAll('[data-sf-cart] span')].map(s => s.textContent)"
            page.wait_for_function(spans + ".some(t => t.includes('PayPal') && t.includes('US$'))")
            note = [t for t in page.evaluate(spans) if "PayPal" in t and "US$" in t][-1]
            assert "US$\u200e" in note, repr(note)
            chip_off = next(t for t in page.evaluate(spans) if "\u2212" in t and "%" in t)
            assert chip_off.startswith("\u2066\u2212") and chip_off.endswith("\u2069"), repr(chip_off)
            # (la página pide el catálogo en su idioma, ?ind_lang=: la explicación de cada indicador va en él)
            assert tab.problems() == ["500 GET /api/strategies?tab=crypto&q=&size=24&page=1&ind_lang=es"], tab.problems()
        finally:
            tab.close()


# ── Pro ────────────────────────────────────────────────────────────────────────

PRO_TABLE = """(() => { localStorage.setItem('tuisku-sf-mode', 'pro'); localStorage.setItem('tuisku-sf-pview5', 'table'); })()"""
# los tres trozos de la fila desplegada y la caja que se desliza, en px de la ventana
OPEN_ROW = """() => { const td = document.querySelector("td[colspan='12']"), box = td.closest('table').parentElement;
  const r = box.getBoundingClientRect();
  return { box: [r.left, r.right], parts: [...td.firstElementChild.children].map(k => { const b = k.getBoundingClientRect();
    return [Math.round(b.left), Math.round(b.right), Math.round(b.top)]; }) }; }"""


def test_pro_tour_texts_and_the_open_table_row(real_app):
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(PRO_TABLE)
            tab.goto("/")                    # la primera vez, en Pro: el recorrido con el texto de Pro
            page.wait_for_selector("[role=dialog]")
            # B1, B13: sin «2.834» (el catálogo de 2024) y con los 16 filtros de más que tiene el panel
            assert page.locator("[role=dialog] p").first.inner_text() == UI["tour1Pro"]["es"]
            assert "16 más" in UI["tour1Pro"]["es"] and not re.search(r"\d\.\d{3}", UI["tour1Pro"]["es"])
            page.keyboard.press("Escape")

            # B21: un desplegable con una sola opción dice «1 seleccionado» (en el catálogo de 2026-10, la fecha
            # de publicación: las 94 salieron el mismo día); con una estrategia, «estrategia mostrada»
            api = real_app.test_client()
            dates = len(api.get("/api/strategies?facets=1&size=1").json["options"]["rel"])
            release = page.locator("aside button[aria-expanded]").filter(has_text="Fecha de publicación").inner_text()
            assert re.search(rf"\b{dates} seleccionado{'' if dates == 1 else 's'}\b", release), release
            one = next(o["v"] for o in api.get("/api/strategies?facets=1&size=1").json["options"]["sym"]
                       if api.get("/api/strategies?q=" + o["v"]).json["total"] == 1)
            page.wait_for_selector("tbody tr")
            page.locator("input[data-search=pro]").fill(one)
            page.wait_for_function("() => document.querySelectorAll('tbody tr').length === 1")
            head = page.locator("aside > div").first
            page.wait_for_function("e => /^1\\n/.test(e.innerText)", arg=head.element_handle())
            assert head.inner_text().split("\n")[:2] == ["1", "estrategia mostrada"]
            page.locator("input[data-search=pro]").fill("")
            page.wait_for_function("() => document.querySelectorAll('tbody tr').length > 1")
            assert head.inner_text().split("\n")[1] == "estrategias mostradas"

            # B16: la consulta de Pro también se corta en 100 (lo que llega sin teclear): sin un 400
            with page.expect_response(lambda r: "/api/strategies?" in r.url and "q=" + "y" * 100 in r.url) as cut:
                page.evaluate(SET_VALUE, ["input[data-search=pro]", "y" * 150])
            assert cut.value.status == 200 and "y" * 101 not in cut.value.url, cut.value.url
            page.locator("input[data-search=pro]").fill("")
            page.wait_for_function("() => document.querySelectorAll('tbody tr').length > 1")

            # B24: en la franja de Pro, Intro en la casilla del código también lo aplica
            page.locator("tbody button[title='%s']" % UI["addToCart"]["es"]).first.click()
            code = page.get_by_placeholder(UI["codePh"]["es"])
            code.fill("demo20")
            with page.expect_request(lambda r: r.url.endswith("/api/quote") and "demo20" in (r.post_data or "")):
                code.press("Enter")
            page.get_by_text(UI["codeBad"]["es"], exact=True).wait_for()

            # B22: la fila desplegada (los dos gráficos y la explicación) cabe en la caja, y se queda al deslizarla
            page.locator("tbody tr").first.locator("td").nth(4).click()
            page.wait_for_selector("td[colspan='12']")
            seen = page.evaluate(OPEN_ROW)
            left, right = seen["box"]
            assert len(seen["parts"]) == 3 and len({top for _, _, top in seen["parts"]}) == 1, seen
            assert all(left <= a and b <= right + 0.5 for a, b, _ in seen["parts"]), seen
            page.evaluate("() => { document.querySelector(\"td[colspan='12']\").closest('table').parentElement.scrollLeft = 400; }")
            page.wait_for_function("() => document.querySelector(\"td[colspan='12']\").closest('table').parentElement.scrollLeft > 0")
            assert page.evaluate(OPEN_ROW)["parts"] == seen["parts"], "la fila se iba con la tabla"
            # en el móvil, en una columna
            page.set_viewport_size({"width": 390, "height": 844})
            page.wait_for_function("() => { const p = [...document.querySelector(\"td[colspan='12']\").firstElementChild.children]"
                                   ".map(k => k.getBoundingClientRect().left); return new Set(p.map(Math.round)).size === 1; }")
            phone = page.evaluate(OPEN_ROW)
            assert all(phone["box"][0] <= a and b <= phone["box"][1] + 0.5 for a, b, _ in phone["parts"]), phone
            assert tab.problems() == []
        finally:
            tab.close()


# ── al llegar ──────────────────────────────────────────────────────────────────

DEAD = "AAPL_1Day_1S00_deadbeef"         # una favorita guardada con el catálogo de 2024


def test_on_arrival_dictionary_favourites_and_thanks(real_app):
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        # B6: sin diccionario, el aviso que escribió el servidor (antes, la página se quedaba en blanco)
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.route("**/zt/i18n.json", lambda route: route.fulfill(status=500, body="no"))
            tab.goto("/")
            page.wait_for_selector("[data-ef-nodict]:not([hidden])")
            assert text(page, "[data-ef-nodict]") == UI["errShopNetwork"]["es"] and text(page) == ""
        finally:
            tab.close()

        # B4: al entrar, una favorita que ya no está en el catálogo (aunque su ficha llegue antes que su
        # subida) se va sin error; la otra pasa a la cuenta
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            client = mobile.sign_in(tab)
            alive = client.get("/api/strategies?paid=1&size=1").json["rows"][0]["id"]
            page.add_init_script(TOUR_SEEN + "localStorage.setItem('edgefolio-favs-v1', %s);"
                                 % json.dumps(json.dumps({"favs": [DEAD, alive], "alerts": {}})))
            stub = {"id": DEAD, "ticker": "AAPL", "name": "Apple", "price": 79, "interval": "1Day", "key": "1S00"}
            page.route(re.compile(".*/api/strategies/" + re.escape(DEAD) + r"(\?.*)?$"),
                       lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(stub)))
            with page.expect_response("**/api/mine") as mine:
                tab.goto("/")
            assert [x["id"] for x in mine.value.json()["favourites"]] == [alive]
            page.wait_for_function(SHOWING)
            assert page.locator("[role=alert]").count() == 0, text(page, "[role=alert]")
            assert page.evaluate("() => localStorage.getItem('edgefolio-favs-v1')") is None
            assert tab.problems() == [f"404 PUT /api/favourites/{DEAD}"], tab.problems()
        finally:
            tab.close()

        # C3, C4: la página de gracias en otro navegador (sin enlaces): el carrito de este se queda y no hay
        # tutorial de una estrategia que no tiene; la del cobro que paga vacía el carrito y lo enseña
        row = real_app.test_client().get("/api/strategies?paid=1&size=2").json["rows"]
        base = {"order_id": "FAKE-K3", "status": "PAID", "total": "146.00", "currency": "USD", "payer": "b•••@example.com",
                "valid_days": 7, "max_downloads": 10}
        hidden = {**base, "download_all": None, "downloads": [], "links_hidden": True, "paid_now": False}
        shown = {**base, "download_all": "/api/download/all?t=x", "links_hidden": False, "paid_now": True,
                 "downloads": [{**r, "url": "/api/download/x", "zip": "/api/download/x?format=zip"} for r in row]}
        cart = json.dumps({"cart": [r["id"] for r in row], "bundles": [], "packIds": [], "code": "", "applied": ""})
        for receipt in (hidden, shown):
            tab = mobile.open_page(chromium, live, "laptop")
            page = tab.page
            try:
                page.add_init_script("try { localStorage.setItem('edgefolio-cart-v1', %s); "
                                     "localStorage.setItem('edgefolio-install-v1', '1'); } catch (e) {}" % json.dumps(cart))
                body = json.dumps(receipt)    # fuera de la lambda: con un segundo argumento, Playwright le da la petición
                page.route("**/api/orders/*/capture",
                           lambda route: route.fulfill(status=200, content_type="application/json", body=body))
                tab.goto("/thanks?token=FAKE-K3")
                page.get_by_text("Pedido FAKE-K3").wait_for()
                page.wait_for_timeout(300)
                kept = json.loads(page.evaluate("() => localStorage.getItem('edgefolio-cart-v1')"))
                install = UI["installTitle"]["es"] in text(page) and UI["instWatch"]["es"] in text(page)
                if receipt is hidden:
                    assert kept["cart"] == [r["id"] for r in row], "otro navegador vaciaba este carrito"
                    assert not install, "el tutorial de una estrategia que no hay"
                else:
                    assert kept["cart"] == [] and install
                assert tab.problems() == []
            finally:
                tab.close()
