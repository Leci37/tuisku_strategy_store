# -*- coding: utf-8 -*-
"""La página de una estrategia (la ficha y la pestaña «Cómo decide») en un Chromium de verdad (el kit del
núcleo, ``testing.mobile``) sobre el catálogo de verdad (``real_app``), y su título, que pone el servidor.

- La temporalidad que hay que poner en TradingView va con el nombre de su menú (1D, 1h), como en el tutorial.
- La explicación del indicador sale en el idioma de la página (``catalogue/indicators.csv``, E12a), en la ficha y en
  la fila desplegada de la Tabla de Pro, y cambia con él sin recargar; sólo una sin traducir sale en inglés, y lo
  dice (``lang="en"``, ``dir="auto"``).
- En una gratis, la vista previa y los formatos no hablan de comprar: te llega por correo.
- Una estrategia que la cuenta ya tiene dice «Ya es tuya»: su .pine, o Mis estrategias si su enlace ya no vale
  o hay una versión nueva.
- El título de la pestaña dice qué estrategia es, y «Cómo decide» en su pestaña: el servidor y la página.
- «Comprar para desbloquear» del árbol sigue al carrito de la página (``inCart``), también después de quitarla con
  la cabecera: con el árbol de verdad, de punta a punta.
- Si el código del árbol no llega, se pide otra vez (a otra dirección) al pulsar «Cómo decide» o al volver a
  su pestaña, nunca solo; cuando llega, su aviso de red se va.
- El árbol y la cabecera dicen lo mismo de una que ya es de la cuenta: su vista de visitante no la vende ni la
  pide otra vez, y su botón lleva a la de propietario (con el foco en ella).
- La «i» de cada valor del árbol y la × de su explicación hablan el idioma de la página («¿Qué es …?», «Cerrar»).
"""
import csv
import json
import re
from pathlib import Path

import zlecitool_core
from zlecitool_core.testing import mobile

from edgefolio.settings import ROOT
from edgefolio.shop import of
from tests.conftest import ROWS, strategy_id
from tests.test_mine import buy
from tests.test_tree import CART, CRAFTED_PREVIEW, OWNED_SCRIPT, es, text_of

UI = json.loads((ROOT / "i18n" / "ui.json").read_text(encoding="utf-8"))
CORE = json.loads((Path(zlecitool_core.__file__).resolve().parent / "i18n" / "common.json").read_text(encoding="utf-8"))
TOUR_SEEN = "try { localStorage.setItem('edgefolio-tour-v1', '1'); } catch (e) {}"
SHOP_TITLE = "Edgefolio · " + UI["toolName"]["es"]
# los dos textos con candado de la vista previa (el resto del script y la nota de los formatos)
LOCKS = "() => [...document.querySelectorAll('#app i.fa-lock')].map(i => i.parentElement.textContent.trim())"
PINE_DESC = """() => { const n = [...document.querySelectorAll('#app strong')].find(x => x.textContent === 'Pine Script');
  return n.closest('div').nextElementSibling.textContent; }"""
HEAD_BUTTONS = "() => [...document.querySelectorAll('#app section section :is(button, a)')].map(b => b.textContent.trim())"
# El árbol: su botón de compra (el del aviso de las ramas cortadas), lo que dice ese aviso, el texto del árbol, la
# explicación abierta (su texto y sus botones, con su nombre) y lo que tiene el foco.
UNLOCK = re.compile("^(" + "|".join(re.escape(es(k)) for k in ("unlockBtn", "added")) + ")$")
TREE_SAYS = "t => { const s = document.querySelector('[data-tree-sec]'); return !!s && s.textContent.includes(t); }"
CTA_BAR = """() => { const i = document.querySelector('[data-tree-sec] i.fa-lock'); if (!i) return null;
  return [i.parentElement.querySelector('span').textContent, [...i.parentElement.querySelectorAll('button, a')].map(b => b.textContent.trim())]; }"""
TIP_NOW = """() => { const t = document.querySelector('[role=tooltip]'); if (!t) return null;
  return [t.querySelector('p').textContent, [...t.querySelectorAll('button')].map(b => [b.textContent.trim(), b.getAttribute('aria-label')])]; }"""
FOCUSED = "() => [document.activeElement.textContent.trim(), document.activeElement.getAttribute('aria-pressed')]"
# las «i» de los valores (su nombre) y la × de la explicación abierta
ARIA = """() => ({ infos: [...document.querySelectorAll('aside button[aria-label]')].map(b => b.getAttribute('aria-label')).sort(),
  close: (document.querySelector('[role=tooltip] button') || { getAttribute: () => null }).getAttribute('aria-label') })"""
CRAFTED_VALUES = ("d__close", "ema2__close", "macd__close")
# La explicación de cada indicador, por idioma (Explanation es la inglesa).
with open(ROOT / "catalogue" / "indicators.csv", encoding="utf-8", newline="") as f:
    EXPLAINED = {r["Key"]: {"en": r["Explanation"], **{k[12:]: v for k, v in r.items() if k.startswith("Explanation_")}}
                 for r in csv.DictReader(f)}
# «Sobre el indicador» de la ficha: su texto, su lang, su dir y la dirección en que se pinta.
ABOUT = """() => { const p = [...document.querySelectorAll('#app img[src$="TW_ICO.svg"]')].map(i => i.closest('div').querySelector('p')).find(Boolean);
  return p ? [p.textContent, p.getAttribute('lang'), p.getAttribute('dir'), getComputedStyle(p).direction] : null; }"""
OPEN_ROW = "() => { const s = document.querySelector(\"td[colspan='12'] span[style*='text-wrap']\"); return s && [s.textContent, s.getAttribute('lang')]; }"


def title_of(html: str) -> str:
    return re.search(r"<title>(.*?)</title>", html, re.S).group(1).strip()


def tab_title(row: dict, *more) -> str:
    return " · ".join([row["name"], row["ticker"], row["key"], row["interval"], *more, "Edgefolio"])


def serve(page, row: dict, text: str):
    """La vista previa de ``row``, la de la prueba (una rama cortada: el árbol tiene su aviso y su candado)."""
    page.route(re.compile(".*" + re.escape(row["preview"]) + "$"), lambda route: route.fulfill(body=text, content_type="text/plain"))


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
            # E12a: la explicación del indicador, en el idioma de la página (y con su lang y su dir), también al cambiarlo
            said = EXPLAINED[free["key"]]
            page.wait_for_function(f"t => (({ABOUT})() || [])[0] === t", arg=said["es"])
            assert page.evaluate(ABOUT) == [said["es"], "es", "ltr", "ltr"]
            page.evaluate("() => zt.setLanguage('ar')")
            page.wait_for_function(f"t => (({ABOUT})() || [])[0] === t", arg=said["ar"])
            assert page.evaluate(ABOUT) == [said["ar"], "ar", "rtl", "rtl"]
            page.evaluate("() => zt.setLanguage('es')")
            page.wait_for_function(f"t => (({ABOUT})() || [])[0] === t", arg=said["es"])
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

            # una sin traducir (un indicador nuevo del generador): la inglesa, dicha y de izquierda a derecha
            def english(route):
                response = route.fetch()
                route.fulfill(response=response, json={**response.json(), "ind_text": EXPLAINED[hourly["key"]]["en"],
                                                       "ind_lang": "en"})
            page.route(re.compile(".*/api/strategies/" + re.escape(hourly["id"]) + r"(\?.*)?$"), english)
            tab.goto(f"/s/{hourly['id']}?lang=ar")
            page.wait_for_function(f"t => (({ABOUT})() || [])[0] === t", arg=EXPLAINED[hourly["key"]]["en"])
            assert page.evaluate(ABOUT) == [EXPLAINED[hourly["key"]]["en"], "en", "auto", "ltr"]
            page.unroute(re.compile(".*/api/strategies/" + re.escape(hourly["id"]) + r"(\?.*)?$"))
            tab.goto("/?lang=es")

            # también en la fila desplegada de la Tabla de Pro (la misma que el title de su celda), y al cambiar de
            # idioma con la fila abierta, la de ese idioma en el sitio
            page.get_by_role("radio", name="Pro").click()
            page.wait_for_selector("tbody tr")
            page.locator("tbody tr").first.locator("td").nth(4).click()
            page.wait_for_function(f"() => !!({OPEN_ROW})()")
            cell = page.locator("tbody tr").first.locator("div[title]").first
            key = cell.locator("span").first.inner_text()
            assert page.evaluate(OPEN_ROW) == [EXPLAINED[key]["es"], "es"] == [cell.get_attribute("title"), "es"]
            page.evaluate("() => zt.setLanguage('fr')")
            page.wait_for_function(f"t => (({OPEN_ROW})() || [])[0] === t", arg=EXPLAINED[key]["fr"])
            assert page.locator("tbody tr").first.locator("div[title]").first.get_attribute("title") == EXPLAINED[key]["fr"]
            page.evaluate("() => zt.setLanguage('es')")
            page.wait_for_function(f"t => (({OPEN_ROW})() || [])[0] === t", arg=EXPLAINED[key]["es"])
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

            def tree_js(route):            # dos fallos, y después el de verdad
                asked.append(route.request.url[len(live.origin):])
                if len(asked) <= 2:
                    route.fulfill(status=500, content_type="text/plain", body="no")
                else:
                    route.continue_()

            page.route(re.compile(r".*/static/js/tree\.js(\?.*)?$"), tree_js)
            serve(page, paid, CRAFTED_PREVIEW)
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
            # y volver a su pestaña sin pulsarla: a la ficha, y Atrás del navegador; el aviso de la red, sin cerrarlo, se
            # va cuando llega (se quedaba encima del árbol)
            page.get_by_role("tab", name=UI["overviewTab"]["es"]).click()
            page.wait_for_function("() => location.pathname.endsWith('/tree') === false")
            page.go_back()
            unlock = page.locator("[data-tree-sec] button", has_text=UNLOCK)
            unlock.wait_for()
            assert asked[2:] == ["/static/js/tree.js?retry=2"] and alert.count() == 0

            # B31, de punta a punta: «Comprar para desbloquear» la añade y lo dice la cabecera; quitada con la
            # cabecera, el árbol vuelve a ofrecerlo (con una marca propia, seguía «Añadida al carrito») y la añade
            assert unlock.inner_text() == es("unlockBtn")
            unlock.click()
            page.wait_for_function(f"id => ({CART})().join() === id", arg=paid["id"])
            assert unlock.inner_text() == es("added")
            page.locator("#app section section button", has_text=UI["inCartBtn"]["es"]).click()
            page.wait_for_function(f"() => ({CART})().length === 0")
            page.wait_for_function("t => [...document.querySelectorAll('[data-tree-sec] button')].some(b => b.textContent === t)",
                                   arg=es("unlockBtn"))
            assert UI["addToCart"]["es"] in page.evaluate(HEAD_BUTTONS)
            unlock.click()
            page.wait_for_function(f"id => ({CART})().join() === id", arg=paid["id"])

            # la «i» de cada valor y la × de su explicación, en el idioma de la página (eran «What is …?» y «Close»)
            for lang in ("es", "ar"):
                if lang != "es":
                    page.evaluate("l => zt.setLanguage(l)", lang)
                said = sorted(text_of(lang, "whatIs").replace("{f}", f) for f in CRAFTED_VALUES)
                page.wait_for_function(f"s => JSON.stringify(({ARIA})().infos) === JSON.stringify(s)", arg=said)
                page.locator("aside button[aria-label]").first.click()
                page.wait_for_function("() => { const t = document.querySelector('[role=tooltip]'); return t && t.querySelector('button'); }")
                assert page.evaluate(ARIA) == {"infos": said, "close": CORE["dialogClose"][lang]}, lang
            assert tab.problems() == ["500 GET /static/js/tree.js", "500 GET /static/js/tree.js?retry=1"], tab.problems()
        finally:
            tab.close()


def test_a_strategy_the_account_has_says_so(real_app):
    """B29: con la sesión abierta, la ficha de una estrategia que ya es de la cuenta dice «Ya es tuya» en vez
    de «Añadir al carrito» (o «Descargar», en una gratis): su .pine si su enlace vale y es de la versión de
    hoy; si no, Mis estrategias (que da otro, o la actualización), sin recargar la página. El servidor la
    sigue presupuestando (decisión del dueño). Y el árbol dice lo mismo: su vista de visitante no la vende ni la
    pide otra vez («Comprar para desbloquear» la añadía al carrito); su botón lleva a la de propietario."""
    shop = of(real_app)
    free, paid, hourly = pick(real_app)
    other = next(r for r in rows(real_app, "paid=1&size=48")[::-1] if r["id"] not in (paid["id"], hourly["id"]))
    # sus scripts completos (la gratis no se pide sin el suyo; con uno que se lee, la vista de propietario del árbol
    # sale entera); la tienda de las pruebas es de toda la sesión: sólo se quita lo puesto
    made = []
    for row in (free, paid):
        script = shop.settings.strategies_dir / shop.catalogue.resolve(row["id"]).private_file
        if not script.exists():
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text(OWNED_SCRIPT, encoding="utf-8")
            made.append(script)
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

            # el árbol, como la cabecera: abre en la vista de propietario; en la de visitante, su aviso y el candado de
            # una rama dicen «Ya es tuya…» y su botón lleva a la de propietario, con el foco en ella; nunca al carrito
            # (lo hacía «Comprar para desbloquear») ni a pedir otra vez una gratis («Conseguirla gratis»)
            for row, first in ((paid, "cta1"), (free, "fCta1")):
                serve(page, row, CRAFTED_PREVIEW)
                tab.goto(f"/s/{row['id']}/tree")
                page.wait_for_function(TREE_SAYS, arg=es("ownFull"))
                visitor = page.get_by_role("button", name=es("visitor"), exact=True)
                visitor.click()
                page.wait_for_function(f"() => !!({CTA_BAR})()")
                assert page.evaluate(CTA_BAR) == [es(first) + es("ownedRest"), [es("ownedBtn")]], row["id"]
                page.locator("[data-tree-sec] button", has_text=es("ownedBtn")).press("Enter")
                page.wait_for_function(TREE_SAYS, arg=es("ownFull"))
                assert page.evaluate(FOCUSED) == [es("owner"), "true"], "el foco, en Propietario (el botón pulsado se va)"
                visitor.click()
                lock = page.locator(f'[data-tree-scroll] button[aria-label="{es("fPaid" if row is free else "paid")}"]').first
                lock.scroll_into_view_if_needed()
                page.wait_for_timeout(250)
                lock.click()
                page.wait_for_function("() => { const t = document.querySelector('[role=tooltip]'); return t && t.querySelector('button'); }")
                assert page.evaluate(TIP_NOW) == [es("ownedLock"), [["×", CORE["dialogClose"]["es"]], [es("ownedBtn"), None]]]
                page.locator("[role=tooltip] button", has_text=es("ownedBtn")).click()
                page.wait_for_function(TREE_SAYS, arg=es("ownFull"))
                assert page.evaluate(FOCUSED)[1] == "true" and page.locator("[role=dialog]").count() == 0
                assert page.evaluate(CART) == [], "una que ya es suya no va al carrito"
            assert tab.problems() == []
        finally:
            tab.close()
            for script in made:
                script.unlink()
