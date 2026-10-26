# -*- coding: utf-8 -*-
"""La página de una estrategia (la ficha y la pestaña «Cómo decide») en un Chromium de verdad (el kit del
núcleo, ``testing.mobile``) sobre el catálogo de verdad (``real_app``), y su título, que pone el servidor.

- La temporalidad que hay que poner en TradingView va con el nombre de su menú (1D, 1h), como en el tutorial.
- La explicación del indicador sólo está en inglés (``catalogue/indicators.csv``): lo dice su ``lang``, en la
  ficha y en la fila desplegada de la Tabla de Pro.
- En una gratis, la vista previa y los formatos no hablan de comprar: te llega por correo.
- Una estrategia que la cuenta ya tiene dice «Ya es tuya»: su .pine, o Mis estrategias si su enlace ya no vale
  o hay una versión nueva.
- El título de la pestaña dice qué estrategia es, y «Cómo decide» en su pestaña: el servidor y la página.
- El árbol sabe si la estrategia está en el carrito (``inCart``), también después de quitarla con la cabecera.
- Si el código del árbol no llega, se pide otra vez (a otra dirección) al pulsar «Cómo decide» o al volver a
  su pestaña, nunca solo.
"""
import json
import re

from zlecitool_core.testing import mobile

from edgefolio.settings import ROOT
from edgefolio.shop import of
from tests.conftest import ROWS, strategy_id
from tests.test_mine import buy

UI = json.loads((ROOT / "i18n" / "ui.json").read_text(encoding="utf-8"))
TOUR_SEEN = "try { localStorage.setItem('edgefolio-tour-v1', '1'); } catch (e) {}"
SHOP_TITLE = "Edgefolio · " + UI["toolName"]["es"]
# los dos textos con candado de la vista previa (el resto del script y la nota de los formatos)
LOCKS = "() => [...document.querySelectorAll('#app i.fa-lock')].map(i => i.parentElement.textContent.trim())"
PINE_DESC = """() => { const n = [...document.querySelectorAll('#app strong')].find(x => x.textContent === 'Pine Script');
  return n.closest('div').nextElementSibling.textContent; }"""
HEAD_BUTTONS = "() => [...document.querySelectorAll('#app section section :is(button, a)')].map(b => b.textContent.trim())"
# un árbol de mentira: enseña lo que le dice la página del carrito y compra como el de verdad (onBuy)
STUB_TREE = """import { html } from '/static/js/lib/html.js';
export function StrategyTree(p) {
  return html`<div data-stub-tree data-in-cart=${String(p.inCart)}><button type="button"
    onClick=${() => p.onBuy({ stopPropagation() {}, preventDefault() {} })}>stub</button></div>`;
}
"""


def title_of(html: str) -> str:
    return re.search(r"<title>(.*?)</title>", html, re.S).group(1).strip()


def tab_title(row: dict, *more) -> str:
    return " · ".join([row["name"], row["ticker"], row["key"], row["interval"], *more, "Edgefolio"])


def rows(app, query: str) -> list:
    return app.test_client().get("/api/strategies?" + query).json["rows"]


def pick(app):
    """Una gratis y dos de pago (de 1Day y de 1Hour), de las que vende el catálogo."""
    free = next(r for r in rows(app, "tab=free&size=24") if r["interval"] == "1Day")
    paid = rows(app, "paid=1&size=48")
    return free, next(r for r in paid if r["interval"] == "1Day"), next(r for r in paid if r["interval"] == "1Hour")


# ── sin navegador ──────────────────────────────────────────────────────────────


def test_the_tab_title_says_which_strategy_from_the_server(client):
    """B30: la pestaña de una estrategia (también una vista previa del enlace, og:title, y antes de la página)
    dice cuál es: un ticker tiene hasta 17. Sin estrategia, el de la tienda."""
    sid, apple = strategy_id(ROWS[0]), "Apple · AAPL · 1ADX · 1Day"
    page = client.get(f"/s/{sid}").get_data(as_text=True)
    assert title_of(page) == f"{apple} · Edgefolio"
    assert f'<meta property="og:title" content="{apple} · Edgefolio">' in page
    assert title_of(client.get(f"/s/{sid}/tree").get_data(as_text=True)) == f"{apple} · Cómo decide · Edgefolio"
    assert title_of(client.get(f"/s/{sid}/tree?lang=en").get_data(as_text=True)) == f"{apple} · How it decides · Edgefolio"
    assert title_of(client.get("/?lang=es").get_data(as_text=True)) == SHOP_TITLE


# ── en un navegador ────────────────────────────────────────────────────────────


def test_the_sheet_of_a_free_and_a_paid_strategy_and_its_title(real_app):
    free, _, hourly = pick(real_app)
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(TOUR_SEEN + "try { localStorage.setItem('tuisku-sf-pview5', 'table'); } catch (e) {}")
            tab.goto(f"/s/{free['id']}")
            page.wait_for_function("() => document.querySelectorAll('#app i.fa-lock').length === 2")
            assert page.title() == tab_title(free)
            # B25: lo que dice el menú de TradingView, no «1Day»
            note = page.locator("#app i.fa-clock + span").inner_text()
            assert note == UI["tfNote"]["es"].replace("{tf}", "1D"), note
            # B27: la explicación del indicador, en inglés y dicho
            about = page.locator("#app p[lang=en]")
            assert about.inner_text() == free["ind_text"] and about.get_attribute("dir") == "auto"
            # B28: en una gratis, nada de «compras»: te llega por correo
            assert page.evaluate(LOCKS) == [UI["scriptRestFree"]["es"], UI["formatsNoteFree"]["es"]]
            assert page.get_by_text(UI["buyScriptTitleFree"]["es"], exact=True).count() == 1
            assert page.evaluate(PINE_DESC) == UI["fmtPineDescFree"]["es"]

            # B30: la pestaña sigue a la página (sin recargar) y al idioma
            page.get_by_role("tab", name=UI["howItDecides"]["es"]).click()
            page.wait_for_function("t => document.title === t", arg=tab_title(free, UI["howItDecides"]["es"]))
            page.evaluate("() => zt.setLanguage('en')")
            page.wait_for_function("t => document.title === t", arg=tab_title(free, UI["howItDecides"]["en"]))
            page.evaluate("() => zt.setLanguage('es')")
            page.wait_for_function("t => document.title === t", arg=tab_title(free, UI["howItDecides"]["es"]))
            page.get_by_role("button", name=UI["toSheet"]["es"]).click()
            page.wait_for_function("t => document.title === t", arg=tab_title(free))
            page.get_by_role("button", name=UI["backShop"]["es"]).click()
            page.wait_for_function("t => document.title === t", arg=SHOP_TITLE)
            page.go_back()
            page.wait_for_function("t => document.title === t", arg=tab_title(free))

            # una de pago (y de 1Hour): «1h», y sus textos de compra
            tab.goto(f"/s/{hourly['id']}")
            page.wait_for_function("() => document.querySelectorAll('#app i.fa-lock').length === 2")
            assert page.title() == tab_title(hourly)
            assert page.locator("#app i.fa-clock + span").inner_text() == UI["tfNote"]["es"].replace("{tf}", "1h")
            assert page.evaluate(LOCKS) == [UI["scriptRest"]["es"], UI["formatsNote"]["es"]]
            assert page.evaluate(PINE_DESC) == UI["fmtPineDesc"]["es"]
            assert UI["addToCart"]["es"] in page.evaluate(HEAD_BUTTONS)

            # B27: también en la fila desplegada de la Tabla de Pro (la misma explicación que su celda)
            page.get_by_role("radio", name="Pro").click()
            page.wait_for_selector("tbody tr")
            page.locator("tbody tr").first.locator("td").nth(4).click()
            ex = page.locator("td[colspan='12'] span[lang=en]")
            ex.wait_for()
            cell = page.locator("tbody tr").first.locator("div[title]").first.get_attribute("title")
            assert ex.inner_text() == cell and cell and ex.get_attribute("dir") == "auto"
            assert tab.problems() == []
        finally:
            tab.close()


def test_the_tree_tab_tries_again_and_follows_the_cart(real_app):
    _, paid, _ = pick(real_app)
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(TOUR_SEEN)
            asked = []

            def tree_js(route):            # dos fallos, y después un árbol de mentira
                asked.append(route.request.url[len(live.origin):])
                if len(asked) <= 2:
                    route.fulfill(status=500, content_type="text/plain", body="no")
                else:
                    route.fulfill(status=200, content_type="text/javascript", body=STUB_TREE)

            page.route(re.compile(r".*/static/js/tree\.js(\?.*)?$"), tree_js)
            how = page.get_by_role("tab", name=UI["howItDecides"]["es"])
            alert = page.locator("[role=alert]")
            tab.goto(f"/s/{paid['id']}/tree")
            alert.wait_for()
            assert page.title() == tab_title(paid, UI["howItDecides"]["es"])
            page.wait_for_timeout(600)
            assert asked == ["/static/js/tree.js"], "sin red se pedía sin parar (o nada)"
            # B35: pulsar «Cómo decide» otra vez, ya puesta, lo pide de nuevo, a otra dirección
            alert.locator("button").click()
            how.click()
            alert.wait_for()
            page.wait_for_timeout(300)
            assert asked == ["/static/js/tree.js", "/static/js/tree.js?retry=1"]
            # y volver a su pestaña sin pulsarla: a la ficha, y Atrás del navegador
            alert.locator("button").click()
            page.get_by_role("tab", name=UI["overviewTab"]["es"]).click()
            page.wait_for_function("() => location.pathname.endsWith('/tree') === false")
            page.go_back()
            stub = page.locator("[data-stub-tree]")
            stub.wait_for()
            assert asked[2:] == ["/static/js/tree.js?retry=2"] and alert.count() == 0

            # B31: el árbol sabe del carrito: «Comprar para desbloquear» la añade; quitada con la cabecera, ya no está
            assert stub.get_attribute("data-in-cart") == "false"
            stub.locator("button").click()
            page.wait_for_function("() => document.querySelector('[data-stub-tree]').dataset.inCart === 'true'")
            head = page.locator("#app section section button", has_text=UI["inCartBtn"]["es"])
            head.click()
            page.wait_for_function("() => document.querySelector('[data-stub-tree]').dataset.inCart === 'false'")
            assert UI["addToCart"]["es"] in page.evaluate(HEAD_BUTTONS)
            assert json.loads(page.evaluate("() => localStorage.getItem('edgefolio-cart-v1')"))["cart"] == []
            assert tab.problems() == ["500 GET /static/js/tree.js", "500 GET /static/js/tree.js?retry=1"], tab.problems()
        finally:
            tab.close()


def test_a_strategy_the_account_has_says_so(real_app):
    """B29: con la sesión abierta, la ficha de una estrategia que ya es de la cuenta dice «Ya es tuya» en vez
    de «Añadir al carrito» (o «Descargar», en una gratis): su .pine si su enlace vale y es de la versión de
    hoy; si no, Mis estrategias (que da otro, o la actualización), sin recargar la página. El servidor la
    sigue presupuestando (decisión del dueño)."""
    shop = of(real_app)
    free, paid, hourly = pick(real_app)
    other = next(r for r in rows(real_app, "paid=1&size=48")[::-1] if r["id"] not in (paid["id"], hourly["id"]))
    script = shop.settings.strategies_dir / shop.catalogue.resolve(free["id"]).private_file
    made = not script.exists()          # la tienda de las pruebas es de toda la sesión: sólo se quita lo puesto
    if made:
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("//@version=5\nstrategy(\"free\")\n", encoding="utf-8")
    days = shop.settings.download_days
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(TOUR_SEEN)
            client = mobile.sign_in(tab)
            buy(client, [paid["id"]])
            shop.settings.download_days = -1          # nacido caducado: Mis estrategias da otro
            try:
                buy(client, [hourly["id"]])
            finally:
                shop.settings.download_days = days
            assert client.post("/api/free", json={"id": free["id"], "email": client.email}).json == {"sent": True}
            items = {x["id"]: x for x in client.get("/api/mine").json["items"]}
            assert items[paid["id"]]["url"] and items[free["id"]]["url"] and items[hourly["id"]]["url"] is None

            owned = page.locator("[data-ef-owned]")
            for row, href, word in ((paid, items[paid["id"]]["url"], "download"), (free, items[free["id"]]["url"], "download"),
                                    (hourly, "/mine", "myStrategies")):
                tab.goto(f"/s/{row['id']}")
                owned.wait_for()
                assert owned.inner_text().strip() == UI["ownedYours"]["es"] + " · " + UI[word]["es"]
                assert owned.get_attribute("href") == href
                buttons = page.evaluate(HEAD_BUTTONS)
                assert UI["addToCart"]["es"] not in buttons and UI["download"]["es"] not in buttons, buttons
            assert mobile.contrast_problems(tab, "[data-ef-owned]") == []
            # sin su enlace, a Mis estrategias en la misma página
            page.evaluate("() => { window.__same = true; }")
            owned.click()
            page.get_by_role("heading", name=UI["myStrategies"]["es"]).wait_for()
            assert page.evaluate("() => location.pathname === '/mine' && window.__same === true")
            # con una versión nueva, también a Mis estrategias, que ofrece la actualización (la fila que enseña
            # la tienda, ya leída, se queda en la suya)
            strategy = shop.catalogue.resolve(paid["id"])
            assert strategy.summary["version"] == strategy.version
            before = strategy.row.get("version")
            strategy.row["version"] = str(strategy.version + 1)
            try:
                tab.goto(f"/s/{paid['id']}")
                owned.wait_for()
                assert owned.inner_text().strip() == UI["ownedYours"]["es"] + " · " + UI["myStrategies"]["es"]
                assert owned.get_attribute("href") == "/mine"
            finally:
                if before is None:
                    del strategy.row["version"]
                else:
                    strategy.row["version"] = before
            # una que no tiene, como siempre
            tab.goto(f"/s/{other['id']}")
            page.wait_for_function("t => document.title === t", arg=tab_title(other))
            page.wait_for_timeout(300)
            assert owned.count() == 0 and UI["addToCart"]["es"] in page.evaluate(HEAD_BUTTONS)
            assert tab.problems() == []
        finally:
            tab.close()
            if made:
                script.unlink()
