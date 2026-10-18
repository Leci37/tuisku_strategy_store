# -*- coding: utf-8 -*-
"""Recorre la tienda en un navegador de verdad y guarda las capturas del README en docs/img/.

    PORT=5105 python app.py                 # en una terminal, con el .env de desarrollo (PAYPAL_MODE=fake,
                                            # DISCOUNT_CODES=demo20=0.20, sin SMTP: los correos, a <datos>/mail)
    python tools/screenshots.py             # en otra; lee el mismo .env para encontrar los correos

Lite → tres estrategias y un código en el carrito (uno que no vale, «demo20», y aplicarlo otra vez lo
deja) → Pro, sin «con PayPal» en inglés, con filtros (Esc cierra un desplegable), en tabla y en tarjetas
(el enlace al indicador, con su texto) → la página de una estrategia y «Cómo decide» → Pagar (PayPal de
prueba) → el tutorial de instalación → la página de gracias → descargar un script de pago → darse de alta
en el núcleo, confirmar el correo con el que se pagó (el enlace, del correo que el servidor dejó en
<datos>/mail) y Mis estrategias (cada fila, con sus enlaces) → el recorrido de bienvenida (Esc lo cierra)
→ comparar, «Crea tu pack» y una gratis por correo (Esc cierra cada uno; el correo vacío o mal escrito,
debajo del campo; la casilla de novedades, con el teclado) → la píldora de Comparar, dentro del carrito
de Lite y flotando en Pro, y «Solo GRATIS» con el teclado → Pro en español → árabe y español → la
tienda en un móvil (el carrito a 76 px del borde, Carrito no mueve la página, Buscar enfoca la búsqueda).
Es también la prueba de punta a punta: para en el primer paso que falla e informa de los errores de la
consola del navegador (también de la CSP). Las descargas necesitan los scripts de pago
(flask --app app edgefolio restore-scripts).

SHOP_URL (por defecto http://localhost:5105), CHROMIUM_PATH (un navegador) y OUT (por defecto docs/img).
"""
import email
import json
import os
import re
import sys
import time
from email import policy
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from zlecitool_core.config import load_env_file  # noqa: E402

load_env_file(ROOT / ".env")
BASE = os.environ.get("SHOP_URL", "http://localhost:5105").rstrip("/")
OUT = Path(os.environ.get("OUT") or ROOT / "docs" / "img")
MAIL = Path(os.environ.get("ZLECITOOL_DATA_DIR") or ROOT / "data") / "mail"
BUYER = "buyer@example.com"            # quien paga en el PayPal de prueba
ACCOUNT = "ana@example.com"            # la cuenta del núcleo con la que se entra después
PASSWORD = "probando-la-tienda-1"
STRATEGY = "AAPL_1Day_2CT0_8a979adf"   # la de la página de la estrategia y el árbol
UI = json.loads((ROOT / "i18n" / "ui.json").read_text(encoding="utf-8"))
RED = "rgb(192, 57, 43)"               # el borde del campo con un error (#c0392b)
problems = []

# Las píldoras de Comparar que se ven (la que dice «Comparar · N», no el botón de cada fila): si van
# fijas, si van dentro del carrito de Lite y, entonces, dónde acaba ella y dónde empieza la caja.
PILLS = """() => [...document.querySelectorAll('button')]
  .filter(b => b.querySelector('i.fa-code-compare') && /·\\s*\\d+\\s*$/.test(b.textContent) && b.getClientRects().length)
  .map(b => {
    const dock = b.closest('[data-sf-cart]'), box = dock && dock.querySelector(':scope > div');
    return { fixed: getComputedStyle(b).position === 'fixed', inDock: !!dock, bottom: b.getBoundingClientRect().bottom,
             boxTop: box ? box.getBoundingClientRect().top : null };
  })"""


def step(name):
    print(f"· {name}", flush=True)


def expect(ok, what):
    """Una comprobación del recorrido: si no se cumple, para aquí y dice qué esperaba."""
    if not ok:
        raise AssertionError(what)


def ui(key, lang="en"):
    """Un texto de la tienda (i18n/ui.json), para buscarlo en la página como lo pinta."""
    return UI[key][lang]


def core_texts(page, *keys, lang="en"):
    """Textos del núcleo, del mismo diccionario que lee la página (/zt/i18n.json)."""
    return page.evaluate("([keys, lang]) => fetch('/zt/i18n.json').then(r => r.json()).then(d => keys.map(k => d[k][lang]))",
                         [list(keys), lang])


def esc_closes(page, what):
    """Una sola pulsación de Esc cierra lo que hay encima: no queda ningún diálogo."""
    expect(page.locator("[role=dialog]").count() > 0, f"{what}: no estaba abierto")
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    expect(page.locator("[role=dialog]").count() == 0, f"{what}: Esc no lo cerró")
    print(f"  Esc closes {what}")


def tab_to(page, selector, limit=150):
    """Tab hasta que el foco llega a ``selector`` (alcanzable con el teclado); falla si no llega."""
    for _ in range(limit):
        page.keyboard.press("Tab")
        if page.evaluate("s => !!(document.activeElement && document.activeElement.matches(s))", selector):
            return
    raise AssertionError(f"Tab no llega a {selector}")


def space_toggles(page, selector):
    """Con el foco en ``selector``, Espacio cambia su aria-checked (y otra vez lo deja como estaba)."""
    get = f"document.querySelector({json.dumps(selector)}).getAttribute('aria-checked')"
    before = page.evaluate(get)
    page.keyboard.press("Space")
    page.wait_for_timeout(300)
    after = page.evaluate(get)
    expect({before, after} == {"true", "false"}, f"Espacio no cambia {selector}: {before} → {after}")
    page.keyboard.press("Space")
    page.wait_for_timeout(300)
    expect(page.evaluate(get) == before, f"Espacio otra vez no deja {selector} como estaba")
    print(f"  Tab reaches {selector}; Space: {before} → {after} → {before}")


def shot(page, name, height=None, full=False):
    """Primero las imágenes perezosas; después, los ``height`` px de arriba (o la página entera)."""
    # desde arriba: la barra es fija, y una captura entera hecha con la página bajada la pinta en medio
    page.evaluate("window.scrollTo(0, 0); document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading = 'eager')")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(700)
    path = OUT / f"edgefolio_{name}.png"
    if height:
        page.screenshot(path=str(path), full_page=True, clip={"x": 0, "y": 0, "width": page.viewport_size["width"],
                                                               "height": height})
    else:
        page.screenshot(path=str(path), full_page=full)
    print(f"  saved {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")


def emailed_link(to: str, pattern: str, after: float) -> str:
    """El enlace del correo más nuevo a ``to`` que el servidor dejó en <datos>/mail después de ``after``."""
    for _ in range(40):
        for path in sorted(MAIL.glob("*.eml"), key=lambda p: p.stat().st_mtime, reverse=True):
            if path.stat().st_mtime < after:
                break
            msg = email.message_from_bytes(path.read_bytes(), policy=policy.default)
            if msg["To"] == to:
                found = re.search(r"https?://\S+" + pattern + r"\S*", msg.get_content())
                if found:
                    return found.group(0)
        time.sleep(0.25)
    raise SystemExit(f"ningún correo a {to} en {MAIL}: ¿es la carpeta de datos del servidor?")


def button(page, text):
    """A button by its visible text: the icon fonts' glyphs end up in the accessible name, so
    get_by_role(name=..., exact=True) would not match."""
    return page.locator("button", has_text=re.compile(r"^\s*" + re.escape(text) + r"\s*$"))


def new_page(browser, width, height, lang="en", tour_seen=True):
    ctx = browser.new_context(viewport={"width": width, "height": height}, accept_downloads=True, locale="en-US")
    # el idioma es el de la carcasa (su cookie); el aviso de cookies, ya contestado
    ctx.add_cookies([{"name": "zt_lang", "value": lang, "url": BASE}, {"name": "zt_consent", "value": "none", "url": BASE}])
    # el recorrido de bienvenida sale una vez por navegador; cada contexto de aquí es un navegador nuevo
    if tour_seen:
        ctx.add_init_script("try { localStorage.setItem('edgefolio-tour-v1', '1'); } catch (e) {}")
    page = ctx.new_page()
    # con la dirección del recurso: «Failed to load resource» no dice cuál
    page.on("console", lambda m: problems.append(f"{m.type}: {m.text} [{m.location.get('url', '')}]") if m.type == "error" else None)
    page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
    return page


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        launch = {"executable_path": os.environ["CHROMIUM_PATH"]} if os.environ.get("CHROMIUM_PATH") else {}
        browser = p.chromium.launch(**launch)
        page = new_page(browser, 1366, 900)

        step("Lite: three strategies and a code in the cart")
        page.goto(BASE + "/", wait_until="networkidle")
        page.get_by_text(re.compile(r"^Showing \d+ of ")).wait_for()
        buy = button(page, "Buy")
        for _ in range(3):
            buy.first.click()
            page.wait_for_timeout(300)
        page.get_by_text("Have a code?", exact=True).click()
        code = page.get_by_placeholder("Code")
        code.fill("nope")                                   # uno que no vale: lo dice junto al campo
        button(page, "Apply").click()
        page.get_by_text(ui("codeBad"), exact=True).wait_for()
        code.fill("demo20")
        button(page, "Apply").click()
        page.get_by_text(ui("codeOk"), exact=True).wait_for()
        page.get_by_text("−35%").first.wait_for()  # 15% for over $160 + 20% for the code, priced by the server
        button(page, "Apply").click()                      # otra vez: el código se queda aplicado
        page.wait_for_timeout(800)
        expect(page.get_by_text(ui("codeOk"), exact=True).count() == 1, "Apply again dropped the code's message")
        expect(page.get_by_text("−35%").count() > 0, "Apply again dropped the discount")
        crossed = page.evaluate("""() => [...document.querySelectorAll('[data-sf-cart] *')].filter(e =>
            getComputedStyle(e).textDecorationLine.includes('line-through') && e.textContent.trim()).map(e => e.textContent.trim())""")
        expect(len(crossed) == 1, f"the crossed-out subtotal: {crossed}")
        print(f"  {ui('codeBad')!r}, then {ui('codeOk')!r}, kept on Apply again; crossed out {crossed[0]}")
        shot(page, "lite", height=1480)

        step("Pro")
        page.get_by_role("radio", name="Pro").click()
        page.get_by_text("strategies shown").wait_for()
        # en inglés el precio ya es en dólares, los que cobra PayPal: sin la nota «You pay … with PayPal»
        strip = page.locator("[data-sf-cart]").first.inner_text()
        expect(ui("payNote").split("{amount}")[1].strip() not in strip, "English Pro shows the payNote")
        shot(page, "pro", height=1480)

        step("Pro with filters: two symbols and a win rate of 90% or more")
        panel = page.locator("aside").first
        # dispatched clicks: the sticky cart strip covers the panel's rows once the page has scrolled
        panel.get_by_text("Symbol", exact=True).dispatch_event("click")
        button(page, "Deselect all").dispatch_event("click")
        for name in ("Apple (AAPL)", "NVIDIA Corporation (NVDA)"):
            panel.get_by_text(name, exact=True).dispatch_event("click")
        panel.get_by_text("Symbol", exact=True).dispatch_event("click")
        panel.get_by_text("Win Rate (%)", exact=True).dispatch_event("click")
        low = panel.locator("input").nth(-2)
        low.fill("90")
        low.press("Enter")
        page.get_by_text("Clear all").first.wait_for()
        page.wait_for_timeout(1200)
        shot(page, "pro_filters", height=1300)
        panel.get_by_text("Symbol", exact=True).dispatch_event("click")   # un desplegable abierto: Esc lo cierra
        button(page, "Deselect all").wait_for()
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        expect(button(page, "Deselect all").count() == 0, "Esc did not close the Symbol dropdown")
        print("  Esc closes the filter dropdown")
        button(page, "Table").click()
        page.locator("table").first.wait_for()
        shot(page, "table", height=1100)
        # en tarjetas (la misma lista, ya cargada), «CLAVE · indicador» lleva a la página del indicador y
        # enseña su texto al pasar por encima
        button(page, "Cards").click()
        page.locator("a[dir=auto][target=_blank]").filter(has_text="·").first.wait_for()
        links = page.evaluate("""() => [...document.querySelectorAll('a[dir=auto][target=_blank]')]
            .filter(a => a.textContent.includes('·')).map(a => ({ href: a.href, title: a.title, text: a.textContent.trim() }))""")
        expect(links, "no indicator link in the cards")
        bad = [x for x in links if not re.search(r"tradingview\.com/scripts?/", x["href"]) or not x["title"].strip()]
        expect(not bad, f"indicator links without a TradingView page or text: {bad[:3]}")
        print(f"  {len(links)} cards: {links[0]['text']} → {links[0]['href']}")
        page.get_by_text("Clear all").first.click()
        button(page, "Rows").click()

        step("Strategy page and How it decides")
        page.goto(f"{BASE}/s/{STRATEGY}", wait_until="networkidle")
        page.get_by_text("Backtest results", exact=False).first.wait_for()
        shot(page, "strategy", height=1700)
        page.get_by_role("button", name="How it decides").first.click()
        page.get_by_text("Tree output", exact=False).first.wait_for()
        page.wait_for_timeout(1200)
        shot(page, "tree", height=1480)

        step("Checkout with the fake PayPal")
        page.goto(BASE + "/", wait_until="networkidle")
        page.get_by_role("button", name="Checkout").first.click()
        page.wait_for_url("**/thanks**", timeout=20000)
        page.get_by_text("Download all").first.wait_for(timeout=20000)
        page.wait_for_timeout(800)
        shot(page, "install")                       # the install tutorial opens the first time
        page.keyboard.press("Escape")
        shot(page, "thanks", height=1000)

        step("Download one paid file")
        with page.expect_download() as dl:
            page.get_by_role("link", name=".pine").first.click()
        d = dl.value
        first = Path(d.path()).read_text(errors="replace").splitlines()[0][:60]
        print(f"  {d.suggested_filename}: {first}")

        step("My strategies: an account of the core, and the email paid with, confirmed")
        page.goto(BASE + "/mine", wait_until="networkidle")
        assert "/login?next=/mine" in page.url, page.url        # Mis estrategias pide la sesión del núcleo
        for door in ("/register?next=/mine", "/login?next=/mine"):   # la cuenta, nueva o la de otra vuelta
            page.goto(BASE + door, wait_until="networkidle")
            page.locator("input[name=email]").fill(ACCOUNT)
            page.locator("input[name=password]").fill(PASSWORD)
            page.locator("form.account-form button[type=submit]").click()
            page.wait_for_load_state("networkidle")
            if page.url.rstrip("/").endswith("/mine"):
                break
            # en otra vuelta la cuenta ya existe: el núcleo rechaza el alta con un 400, buscado, y se entra
            problems[:] = [x for x in problems if not ("status of 400" in x and BASE + "/register" in x)]
        page.get_by_text(f"Signed in as {ACCOUNT}").first.wait_for()
        offer = page.get_by_text("Bought without an account?")
        pine = page.get_by_role("link", name=".pine")
        pine.or_(offer).first.wait_for()
        # se compró sin cuenta: confirmar ese correo. En otra vuelta ya está confirmado (las compras salen) y
        # el servidor no manda otro enlace; la oferta sigue, por el correo de la propia cuenta
        if offer.count() and not pine.count():
            asked = time.time() - 1
            page.locator("input[type=email]").fill(BUYER)
            button(page, "Send me the link").click()
            page.get_by_text("Check that inbox", exact=False).wait_for()
            page.goto(emailed_link(BUYER, r"/mine\?proof=", asked), wait_until="networkidle")
            page.get_by_role("button", name=f"Yes, {BUYER} is mine").click()
        page.get_by_role("link", name=".pine").first.wait_for()
        # cada fila: .pine y .zip mientras el enlace vale (si no, «Pedir un enlace nuevo»), y su ficha y su
        # árbol, /s/<id> y /s/<id>/tree
        mine_rows = page.evaluate("""([sheet, tree, renew]) => [...document.querySelectorAll('a')]
            .filter(a => a.textContent.trim() === sheet).map(a => {
              const box = a.parentElement, as = [...box.querySelectorAll('a')];
              const href = t => { const x = as.find(y => y.textContent.trim() === t); return x ? x.getAttribute('href') : null; };
              return { sheet: a.getAttribute('href'), tree: href(tree), pine: href('.pine'), zip: href('.zip'),
                       renew: [...box.querySelectorAll('button')].some(b => b.textContent.trim() === renew) };
            })""", [ui("overviewTab"), ui("howItDecides"), ui("newLink")])
        expect(mine_rows, "My strategies: no row with a Fact sheet link")
        for r in mine_rows:
            sid = r["sheet"][3:] if r["sheet"].startswith("/s/") else ""
            expect(sid and "/" not in sid and r["tree"] == f"/s/{sid}/tree", f"My strategies row links: {r}")
            expect((r["pine"] and r["zip"]) or r["renew"], f"My strategies row without .pine/.zip or a new link: {r}")
        print(f"  {len(mine_rows)} rows, each with .pine/.zip, Fact sheet and How it decides: {mine_rows[0]['sheet']}")
        shot(page, "mine", height=900)

        step("The welcome tour, the first time")
        tour = new_page(browser, 1366, 900, tour_seen=False)
        tour.goto(BASE + "/", wait_until="networkidle")
        tour.get_by_text("Step 1 of 3").wait_for()
        shot(tour, "tour")
        seen = "localStorage.getItem('edgefolio-tour-v1')"
        expect(tour.evaluate(seen) is None, "the tour was already marked as seen")
        esc_closes(tour, "the welcome tour")
        expect(tour.evaluate(seen) == "1", "Esc closed the tour without remembering it")

        step("Compare three strategies")
        lite = new_page(browser, 1366, 900)
        lite.goto(BASE + "/", wait_until="networkidle")
        lite.get_by_text(re.compile(r"^Showing \d+ of ")).wait_for()
        for i in (1, 2, 3):
            lite.locator("button[title=Compare]").nth(i).click()
        lite.locator("button", has_text=re.compile(r"Compare")).last.click()
        lite.locator("[role=dialog]").first.wait_for()
        shot(lite, "compare")
        esc_closes(lite, "compare")

        step("Build your pack")
        lite.get_by_text(re.compile(r"^Showing \d+ of ")).wait_for()
        button(lite, "Add pack").click()
        lite.locator("[role=dialog]").first.wait_for()
        esc_closes(lite, "the pack picker")
        button(lite, "Add pack").click()
        rows = lite.locator("[role=dialog] button").filter(has_text=re.compile(r"%"))
        for i in range(5):
            rows.nth(i).click()
        lite.wait_for_timeout(600)
        shot(lite, "pack")
        button(lite, "Done").click()

        step("A free strategy, sent by email")
        lite.goto(BASE + "/", wait_until="networkidle")
        lite.get_by_text("Free", exact=True).first.click()
        lite.wait_for_timeout(1200)
        button(lite, "Download").first.click()
        field = lite.locator("[role=dialog] input[type=email]")
        alert = lite.locator("[role=dialog] [role=alert]")
        required, invalid = core_texts(lite, "errEmailRequired", "errEmailInvalid")
        # lo que falla en el correo sale debajo del campo, con los textos del núcleo y el borde en rojo
        field.press("Enter")
        alert.wait_for()
        expect(alert.inner_text().strip() == required, f"empty email: {alert.inner_text()!r}, not {required!r}")
        field.fill("bad@")
        field.press("Enter")
        lite.wait_for_timeout(300)
        expect(alert.inner_text().strip() == invalid, f"'bad@': {alert.inner_text()!r}, not {invalid!r}")
        border = field.evaluate("e => getComputedStyle(e).borderTopColor")
        expect(border == RED, f"the field's border with an error: {border}")
        shot(lite, "free_error")
        field.press_sequentially("x")                       # escribir lo quita
        lite.wait_for_timeout(300)
        expect(alert.count() == 0, "typing did not clear the email error")
        border = field.evaluate("e => getComputedStyle(e).borderTopColor")
        expect(border != RED, "typing did not clear the red border")
        print(f"  {required!r}, {invalid!r} under the field, red border; typing clears them")
        field.fill("visitor@example.com")
        tab_to(lite, "[role=dialog] [role=checkbox]", limit=10)   # la casilla de novedades, con el teclado
        space_toggles(lite, "[role=dialog] [role=checkbox]")
        button(lite, "Send me the link").click()
        lite.get_by_text("Check your inbox", exact=False).first.wait_for()
        shot(lite, "free")
        print("  " + emailed_link("visitor@example.com", r"/api/download/", time.time() - 30)[:60])
        esc_closes(lite, "the free download")

        step("The Compare pill: inside Lite's cart, floating in Pro; Only FREE with the keyboard")
        dock = new_page(browser, 1366, 900)
        dock.goto(BASE + "/", wait_until="networkidle")
        dock.get_by_text(re.compile(r"^Showing \d+ of ")).wait_for()
        button(dock, "Buy").first.click()
        for i in (0, 1):
            dock.locator("button[title=Compare]").nth(i).click()
        dock.wait_for_timeout(600)
        pills = dock.evaluate(PILLS)
        expect(len(pills) == 1, f"Lite with a cart: {len(pills)} Compare pills")
        pill = pills[0]
        expect(pill["inDock"] and not pill["fixed"] and pill["bottom"] <= pill["boxTop"] + 0.5,
               f"Lite's pill is not in the cart, above the box: {pill}")
        print(f"  Lite: one pill in the cart, above the box ({pill['bottom']:.0f} <= {pill['boxTop']:.0f})")
        dock.get_by_role("radio", name="Pro").click()
        dock.get_by_text("strategies shown").wait_for()
        dock.wait_for_timeout(600)
        pills = dock.evaluate(PILLS)
        expect(len(pills) == 1 and pills[0]["fixed"] and not pills[0]["inDock"], f"Pro's Compare pill: {pills}")
        print("  Pro: one floating pill")
        dock.evaluate("document.activeElement && document.activeElement.blur()")
        tab_to(dock, "aside [role=switch]")
        space_toggles(dock, "aside [role=switch]")

        step("Pro in Spanish: the price in euros, and what PayPal charges")
        es_pro = new_page(browser, 1366, 900, lang="es")
        es_pro.context.add_init_script("try { localStorage.setItem('tuisku-sf-mode', 'pro'); } catch (e) {}")
        es_pro.goto(BASE + "/", wait_until="networkidle")
        es_pro.get_by_text(ui("shown", "es")).wait_for()
        add = button(es_pro, ui("addToCart", "es"))
        for _ in range(2):
            add.first.click()
            es_pro.wait_for_timeout(300)
        note = ui("payNote", "es").split("{amount}")[1].strip()       # «con PayPal»
        es_pro.locator("[data-sf-cart]").first.get_by_text(note, exact=False).wait_for()
        print("  " + es_pro.locator("[data-sf-cart]").first.get_by_text(note, exact=False).inner_text())
        shot(es_pro, "pro_es", height=1000)

        step("Arabic, right to left, and Spanish")
        ar = new_page(browser, 1366, 900, lang="ar")
        ar.goto(BASE + "/", wait_until="networkidle")
        ar.wait_for_timeout(1500)
        shot(ar, "arabic", height=1100)
        es = new_page(browser, 1366, 900, lang="es")
        es.goto(f"{BASE}/s/{STRATEGY}", wait_until="networkidle")
        es.wait_for_timeout(1500)
        shot(es, "spanish", height=1100)

        step("A phone")
        phone = new_page(browser, 390, 844)
        phone.goto(BASE + "/", wait_until="networkidle")
        phone.get_by_text(re.compile(r"^Showing \d+ of ")).wait_for()
        shot(phone, "phone")
        # con algo en el carrito y una en comparar: el carrito flota 76 px sobre el borde (encima de la
        # barra de abajo) y la píldora va dentro, encima de la caja
        button(phone, "Buy").first.click()
        phone.locator("button[title=Compare]").first.click()
        phone.wait_for_timeout(800)
        geo = phone.evaluate("() => ({ bottom: document.querySelector('[data-sf-cart]').getBoundingClientRect().bottom, ih: innerHeight })")
        expect(abs(geo["bottom"] - (geo["ih"] - 76)) <= 1, f"the phone's cart dock: bottom {geo['bottom']}, not {geo['ih'] - 76}")
        pills = phone.evaluate(PILLS)
        expect(len(pills) == 1 and pills[0]["inDock"] and not pills[0]["fixed"] and pills[0]["bottom"] <= pills[0]["boxTop"] + 0.5,
               f"the phone's Compare pill: {pills}")
        print(f"  dock bottom {geo['bottom']:.0f} = {geo['ih']} - 76, the pill inside it, above the box")
        shot(phone, "phone_cart")
        bar = phone.locator("nav").filter(has_text=ui("navShop")).filter(has_text=ui("navMine"))
        phone.evaluate("window.scrollTo(0, 900)")
        phone.wait_for_timeout(300)
        y = phone.evaluate("scrollY")
        bar.locator("button").filter(has_text=re.compile(r"^\s*" + re.escape(ui("cart")))).click()   # ya en la tienda: no se mueve
        phone.wait_for_timeout(700)
        expect(abs(phone.evaluate("scrollY") - y) <= 1, f"Cart moved the page: {y} → {phone.evaluate('scrollY')}")
        button(bar, ui("searchSmall")).click()
        phone.wait_for_timeout(700)
        expect(phone.evaluate("!!document.activeElement.matches('input[data-search]')"), "Search did not focus the search")
        print(f"  Cart keeps scrollY {y:.0f}; Search focuses input[data-search]")
        phone.goto(f"{BASE}/s/{STRATEGY}/tree", wait_until="networkidle")
        phone.get_by_text("Tree output", exact=False).first.wait_for()
        phone.wait_for_timeout(1200)
        # what the phone shows once scrolled to the tree: a full-page shot would draw the fixed bottom bar mid-page
        phone.get_by_text("Tree output", exact=False).first.scroll_into_view_if_needed()
        phone.evaluate("window.scrollBy(0, -90)")
        phone.wait_for_timeout(600)
        phone.screenshot(path=str(OUT / "edgefolio_phone_tree.png"))
        print("  saved edgefolio_phone_tree.png")
        browser.close()

    report()
    return 1 if problems else 0


def report():
    print(f"console errors: {len(problems)}")
    for line in problems[:20]:
        print("  ", line[:200])


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        report()                    # también cuando un paso falla: un error de la consola suele ser la causa
        raise
