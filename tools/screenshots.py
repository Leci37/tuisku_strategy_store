# -*- coding: utf-8 -*-
"""Recorre la tienda en un navegador de verdad y guarda las capturas del README y de docs/FLUJO_USUARIO.md
en docs/img/.

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
tienda en un móvil (el carrito a 76 px del borde, Carrito no mueve la página, Buscar enfoca la búsqueda) →
las capturas en español de docs/FLUJO_USUARIO.md (edgefolio_es_*.png, cada una recortada a lo que enseña),
la última con la cuenta, después de comprar: la tarjeta dice «Ya es tuya» y no «Comprar».
Es también la prueba de punta a punta: para en el primer paso que falla e informa de los errores de la
consola del navegador (también de la CSP). Las descargas necesitan los scripts de pago
(flask --app app edgefolio restore-scripts).

SHOP_URL (por defecto http://localhost:5105), CHROMIUM_PATH (un navegador) y OUT (por defecto docs/img).
SHOP_URL con localhost, no con 127.0.0.1: sin ZLECITOOL_PUBLIC_URL el núcleo sólo ofrece las llaves de
acceso en localhost, y la captura de entrar (edgefolio_es_login.png) enseña el botón, como en producción.
Todas salen con una base de datos nueva; en otra vuelta, la cuenta ya ha confirmado el correo y la de esa
confirmación (edgefolio_mine_proof.png) no se repite.
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
STRATEGY = "SNOW_1Day_1BOL_7abec5de"   # la de la página de la estrategia y el árbol (catálogo de 2026-10)
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
    """Un texto de la tienda (i18n/ui.json), para buscarlo en la página como lo pinta; de uno con plurales
    ({one, other…}), el de muchos."""
    text = UI[key][lang]
    return text.get("other", "") if isinstance(text, dict) else text


def core_texts(page, *keys, lang="en"):
    """Textos del núcleo, del mismo diccionario que lee la página (/zt/i18n.json)."""
    return page.evaluate("([keys, lang]) => fetch('/zt/i18n.json').then(r => r.json()).then(d => keys.map(k => d[k][lang]))",
                         [list(keys), lang])


def two_symbols(page):
    """Los dos símbolos del filtro de Pro, del catálogo de hoy (API #2, contados con un 60 % de aciertos o más):
    los dos primeros de la lista que guardan dos estrategias o más cada uno. Así la lista y la tabla tienen
    filas, y en el desplegable se ven marcados sin bajarlo. Sus nombres, como los pinta el desplegable, y
    cuántas estrategias quedan con los dos filtros."""
    options = page.request.get(BASE + "/api/strategies?win_min=60&facets=1&size=1").json()["options"]["sym"]
    picked = [o for o in options if o["count"] >= 2][:2]
    expect(len(picked) == 2, f"no two symbols with two strategies or more at a 60% win rate: {options}")
    return [o["label"] for o in picked], sum(o["count"] for o in picked)


def all_of(n, lang="en"):
    """El pie de la lista de Pro con las ``n`` en una página («1–4 of 4»): la lista filtrada ya ha llegado."""
    return ui("rangeOf", lang).replace("{from}", "1").replace("{to}", str(n)).replace("{total}", str(n))


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


def new_page(browser, width, height, lang="en", tour_seen=True, touch=False):
    # touch: un móvil de verdad (pantalla táctil, la etiqueta viewport): sin el cursor en los campos
    ctx = browser.new_context(viewport={"width": width, "height": height}, accept_downloads=True, locale="en-US",
                              has_touch=touch, is_mobile=touch)
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

        step("Pro with filters: two symbols and a win rate of 60% or more")
        symbols, kept = two_symbols(page)
        panel = page.locator("aside").first
        # dispatched clicks: the sticky cart strip covers the panel's rows once the page has scrolled
        panel.get_by_text("Symbol", exact=True).dispatch_event("click")
        button(page, "Deselect all").dispatch_event("click")
        for name in symbols:
            panel.get_by_text(name, exact=True).dispatch_event("click")
        panel.get_by_text("Symbol", exact=True).dispatch_event("click")
        panel.get_by_text("Win Rate (%)", exact=True).dispatch_event("click")
        low = panel.locator("input").nth(-2)
        low.fill("60")
        low.press("Enter")
        page.get_by_text("Clear all").first.wait_for()
        page.get_by_text(all_of(kept), exact=True).wait_for()
        page.wait_for_timeout(1200)
        print(f"  {' and '.join(symbols)}, win rate 60% or more: {kept} strategies")
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
            confirm = page.get_by_role("button", name=f"Yes, {BUYER} is mine")
            confirm.wait_for()
            shot(page, "mine_proof", height=900)    # sólo con una cuenta nueva: en otra vuelta ya está confirmado
            confirm.click()
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

        spanish(browser)
        browser.close()

    report()
    return 1 if problems else 0


def crop(page, name, *parts, pad=12, fixed=False, within=None):
    """Una captura en español de docs/FLUJO_USUARIO.md, ``edgefolio_es_<name>.png``, recortada a lo que importa
    para que pese poco: la caja que junta ``parts`` (localizadores) con ``pad`` px de margen, dentro de la de
    ``within`` si se da (una tabla más ancha que su caja); sin ``parts``, la ventana tal como está. Lo de la
    página se mide desde arriba y sale de la página entera (la barra fija y la franja pegajosa del carrito, en
    su sitio); lo fijo (un diálogo), con ``fixed``, de la ventana."""
    if parts and not fixed:
        page.evaluate("window.scrollTo(0, 0)")
    page.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading = 'eager')")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(700)
    path = OUT / f"edgefolio_es_{name}.png"
    if parts:
        boxes = [x.bounding_box() for x in parts]
        expect(all(boxes), f"{name}: lo que se recorta no está en la página")
        x0, y0 = min(b["x"] for b in boxes) - pad, min(b["y"] for b in boxes) - pad
        x1, y1 = max(b["x"] + b["width"] for b in boxes) + pad, max(b["y"] + b["height"] for b in boxes) + pad
        x0, y0, x1 = max(0, x0), max(0, y0), min(page.viewport_size["width"], x1)
        if within:
            w = within.bounding_box()
            x0, x1 = max(x0, w["x"] - pad), min(x1, w["x"] + w["width"] + pad)
        if fixed:
            y1 = min(y1, page.viewport_size["height"])
        page.screenshot(path=str(path), full_page=not fixed, clip={"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0})
    else:
        page.screenshot(path=str(path))
    print(f"  saved {path.name} ({path.stat().st_size // 1024} KB)")


def sign_in(page, then="/mine"):
    """Entra con la cuenta del recorrido (ya dada de alta arriba) por la puerta del núcleo, y vuelve a ``then``."""
    page.goto(f"{BASE}/login?next={then}", wait_until="networkidle")
    page.locator("input[name=email]").fill(ACCOUNT)
    page.locator("input[name=password]").fill(PASSWORD)
    page.locator("form.account-form button[type=submit]").click()
    page.wait_for_url(lambda url: url.split("?")[0].endswith(then), timeout=20000)   # no /login?next=/mine
    page.wait_for_load_state("networkidle")


def spanish(browser):
    """Las capturas en español de docs/FLUJO_USUARIO.md, que cita la tienda en español: una por lo que cuenta
    cada pantalla, recortada a ello. Va la última y en sus propios navegadores: no cambia ninguna de arriba (el
    pedido que paga aquí, con el PayPal de prueba, se suma a Mis estrategias después de su captura)."""
    def es(key):
        return ui(key, "es")

    def get(page, path):
        return page.request.get(BASE + path).json()

    def smallest(page, *texts):
        """El elemento más pequeño de la página que contiene todos estos textos."""
        box = page.locator("div")
        for text in texts:
            box = box.filter(has=page.get_by_text(text, exact=True))
        return box.last

    showing = re.compile(r"^" + re.escape(es("showingN").split("{n}")[0]) + r"\d+ ")
    page = new_page(browser, 1366, 900, lang="es")
    page.goto(BASE + "/", wait_until="networkidle")
    page.get_by_text(showing).wait_for()

    # lo que se busca, del catálogo de hoy (por la API): una gratis, dos de pago de 59 US$ fuera de los packs,
    # el pack «Inicio en cripto» y los dos símbolos del filtro de Pro
    cfg = get(page, "/api/config")
    bundles = get(page, "/api/bundles")["bundles"]
    crypto = next(b for b in bundles if b["name_key"] == "bundleCrypto")
    in_bundles = {i for b in bundles for i in b["ids"]}
    free_id = get(page, "/api/strategies?free=1&sort=hot&size=1")["rows"][0]["id"]
    cheap = [r for r in get(page, "/api/strategies?paid=1&price_min=59&price_max=59&sort=hot&size=24")["rows"]
             if r["id"] not in in_bundles][:2]
    tape = get(page, "/api/strategies?paid=1&sort=hot&size=12")["rows"]
    expect(len(cheap) == 2 and tape, f"the catalogue has no two strategies of 59 US$ outside the bundles: {cheap}")
    symbols, kept = two_symbols(page)

    step("Spanish: the top bar and Lite")
    band = page.locator("[data-screen-label] > div").first           # la cinta, bajo la barra del núcleo
    band.get_by_text(f"{tape[0]['ticker']} · {tape[0]['key']}", exact=True).first.wait_for()
    crop(page, "bar", page.locator("header").first, band, pad=0)
    page.get_by_text(re.compile(r"^" + re.escape(es("tabNew")) + r" · \d+$")).wait_for()
    crop(page, "lite")

    step("Spanish: Build your pack, with «Inicio en cripto» in the cart")
    smallest(page, es("bundleCrypto"), es("addBundle")).locator("button").filter(has_text=es("addBundle")).click()
    page.wait_for_timeout(500)
    smallest(page, es("packTitle"), es("addPack")).locator("button").first.click()   # una casilla «+» lo abre
    picker = page.locator("[role=dialog]").first
    picker.wait_for()
    # las del pack, juntas arriba: lo que comparten sus tickers («USDT»), en el buscador del selector
    common = os.path.commonprefix([i.split("_")[0][::-1] for i in crypto["ids"]])[::-1]
    if common:
        picker.locator("input").fill(common)
    held = picker.locator("button").filter(has_text=es("inCartBtn"))
    held.nth(len(crypto["ids"]) - 1).wait_for()
    page.wait_for_timeout(600)
    expect(held.count() == len(crypto["ids"]), f"the pack picker: {held.count()} strategies «{es('inCartBtn')}»")
    crop(page, "pack_picker", picker, pad=16, fixed=True)
    esc_closes(page, "the pack picker")

    step("Spanish: Pro's cart strip, with the design's own cart")
    for r in cheap:
        page.goto(f"{BASE}/s/{r['id']}", wait_until="networkidle")
        button(page, es("addToCart")).first.click()
        button(page, es("inCartBtn")).first.wait_for()
    page.goto(BASE + "/", wait_until="networkidle")
    page.get_by_role("radio", name="Pro").click()
    page.get_by_text(es("shown")).wait_for()
    strip = page.locator("[data-sf-cart]").first
    strip.get_by_placeholder(es("codePh")).fill("demo20")
    button(strip, es("apply")).click()
    strip.get_by_text(es("codeOk"), exact=True).wait_for()
    # el siguiente tramo, de la configuración: cuenta por encima de su importe (53,01, no 53,00)
    subtotal = crypto["price"] + sum(r["price"] for r in cheap)
    over = min(float(t["over"]) for t in cfg["tiers"] if float(t["over"]) >= subtotal)
    missing = f"{over + 0.01 - subtotal:.2f}".replace(".", ",")
    page.wait_for_timeout(800)
    expect(missing in strip.inner_text(), f"the strip does not ask for {missing} more: {strip.inner_text()[:300]!r}")
    print(f"  {crypto['key']} + {cheap[0]['id']} + {cheap[1]['id']} + demo20: {missing} more")
    crop(page, "strip", strip, pad=0)

    step("Spanish: a paid order's thanks page, opened in another browser")
    button(page, es("checkout")).first.click()
    page.wait_for_url("**/thanks**", timeout=20000)
    page.get_by_text(es("downloadAll")).first.wait_for(timeout=20000)
    other = new_page(browser, 1366, 900, lang="es")
    other.goto(page.url, wait_until="networkidle")
    other.get_by_text(es("linksHiddenTitle")).wait_for(timeout=20000)
    expect(other.get_by_text(es("downloadAll")).count() == 0, "another browser sees the order's links")
    other.get_by_text(es("signInToDownload")).first.wait_for()
    # con la barra: sin sesión («Entrar»)
    crop(other, "thanks_other", other.locator("header").first, smallest(other, es("linksHiddenTitle"), es("backShop")),
         pad=16)
    other.context.close()
    page.keyboard.press("Escape")                                     # el tutorial de instalación

    step("Spanish: a free strategy's page and its email")
    page.goto(f"{BASE}/s/{free_id}", wait_until="networkidle")
    page.get_by_text(es("allResults")).first.wait_for()
    page.wait_for_timeout(1000)
    crop(page, "detail_free")
    button(page, es("download")).first.click()
    page.locator("[role=dialog] input[type=email]").fill("visitante@example.com")
    button(page, es("sendLink")).click()
    # su enlace vale DOWNLOAD_DAYS (API #1), con la forma de su número: «el enlace vale 7 días»
    days = cfg["download_days"]
    page.get_by_text(es("freeSent").replace("{days}", es("linkDays")["one" if days == 1 else "other"]
                                            .replace("{n}", str(days)))).first.wait_for()
    crop(page, "free_sent", page.locator("[role=dialog]").first, pad=16, fixed=True)
    esc_closes(page, "the free download")

    step("Spanish: a paid strategy's preview and formats, How it decides in Blocks")
    page.goto(f"{BASE}/s/{STRATEGY}", wait_until="networkidle")
    page.get_by_text(es("formatsNote")).first.wait_for()
    page.wait_for_timeout(1000)
    crop(page, "detail_preview", smallest(page, "Pine Script v5", es("formatsNote")))
    page.goto(f"{BASE}/s/{STRATEGY}/tree", wait_until="networkidle")
    # los textos del árbol son de su propio diccionario (static/js/tree.js), no de i18n/ui.json
    page.get_by_text("Resultado del árbol", exact=False).first.wait_for()
    tree = page.locator("section[data-tree-sec]")
    tree.get_by_role("tab", name="Bloques").click()
    page.wait_for_timeout(1200)
    crop(page, "tree_blocks", tree)

    step("Spanish: Pro with filters, the Symbol dropdown open")
    pro = new_page(browser, 1366, 900, lang="es")
    pro.context.add_init_script("try { localStorage.setItem('tuisku-sf-mode', 'pro'); } catch (e) {}")
    pro.goto(BASE + "/", wait_until="networkidle")
    pro.get_by_text(es("shown")).wait_for()
    panel = pro.locator("aside").first
    panel.get_by_text(es("fWinRate"), exact=True).dispatch_event("click")
    low = panel.locator("input").nth(-2)
    low.fill("60")
    low.press("Enter")
    pro.get_by_text(es("clearAll")).first.wait_for()
    panel.get_by_text(es("fSymbol"), exact=True).dispatch_event("click")
    button(pro, es("selNone")).dispatch_event("click")
    for name in symbols:
        panel.get_by_text(name, exact=True).dispatch_event("click")
    pro.get_by_text(all_of(kept, "es"), exact=True).wait_for()
    pro.wait_for_timeout(1200)
    crop(pro, "pro_filters", panel.locator(":scope > *").first, low, pro.locator("input[data-search]").first)

    step("Spanish: the Table, a row unfolded")
    pro.keyboard.press("Escape")
    pro.get_by_text(es("clearAll")).first.click()
    # la lista entera ya en la página: si no, se despliega una fila de la filtrada, que después baja
    panel.get_by_text(str(cfg["strategies"]), exact=True).first.wait_for()
    button(pro, es("viewTableTab")).click()
    table = pro.locator("table").first
    table.wait_for()
    pro.wait_for_load_state("networkidle")
    table.locator("tbody tr").first.locator("td").first.click()   # la primera celda: la tabla no se corre de lado
    pro.wait_for_timeout(1200)
    expect(table.locator("tbody tr").nth(1).get_by_text(es("overviewTab")).count() > 0, "the first row did not unfold")
    table.evaluate("t => { t.parentElement.scrollLeft = 0; }")
    # la cabecera, la fila desplegada y dos más, dentro de su tarjeta (la tabla es más ancha que ella)
    crop(pro, "table_row", table.locator("thead"), table.locator("tbody tr").nth(3),
         within=table.locator("xpath=../.."))

    step("Spanish: My strategies signed out, the core's login")
    door = new_page(browser, 1366, 900, lang="es")
    door.goto(BASE + "/mine", wait_until="networkidle")
    expect("/login?next=/mine" in door.url, door.url)
    form = door.locator("form.account-form")
    # la tarjeta del núcleo: la contraseña, el enlace por correo, la llave de acceso y el alta
    crop(door, "login", form.locator("xpath=ancestor::*[.//a[contains(@href, '/register')]][1]"), pad=16)

    step("Spanish: a phone, Pro and My strategies")
    phone = new_page(browser, 390, 844, lang="es", touch=True)
    phone.context.add_init_script("try { localStorage.setItem('tuisku-sf-mode', 'pro'); } catch (e) {}")
    phone.goto(BASE + "/", wait_until="networkidle")
    phone.get_by_text(es("shown")).wait_for()
    phone.wait_for_timeout(1000)
    crop(phone, "phone_pro")
    sign_in(phone)
    # la cuenta habla inglés (se dio de alta arriba, en inglés) y manda sobre la cookie: ?lang=es sólo cambia
    # esta página, no la cuenta
    phone.goto(BASE + "/mine?lang=es", wait_until="networkidle")
    phone.get_by_text(es("signedAs").replace("{e}", ACCOUNT)).first.wait_for()
    phone.wait_for_timeout(1000)
    crop(phone, "phone_mine")

    step("Spanish: Lite signed in, a strategy just bought says «Ya es tuya»")
    # la última: su pedido no sale en ninguna captura de arriba (Mis estrategias, en el móvil, ya está hecha)
    own = new_page(browser, 1366, 900, lang="es")
    sign_in(own, then="/")
    own.goto(BASE + "/?lang=es", wait_until="networkidle")      # la cuenta habla inglés (arriba)
    own.get_by_text(showing).wait_for()
    own.locator("a[data-ef-owned]").first.wait_for()             # Mis estrategias ya ha llegado: lo que compró arriba
    own.wait_for_timeout(600)
    buy = core_texts(own, "buy", lang="es")[0]                  # «Comprar», del diccionario del núcleo
    cards = own.locator("div.sf-hover2")
    # dos tarjetas de pago seguidas, en la misma fila, que la cuenta aún no tiene: se compra la primera
    seen = own.evaluate("""(buy) => [...document.querySelectorAll('div.sf-hover2')].map(c => ({
        top: Math.round(c.getBoundingClientRect().top), first: c.innerText.trim().split('\\n')[0],
        buy: [...c.querySelectorAll('button')].some(b => b.textContent.trim() === buy) }))""", buy)
    i = next((i for i in range(len(seen) - 1) if seen[i]["buy"] and seen[i + 1]["buy"]
              and seen[i]["top"] == seen[i + 1]["top"]), None)
    expect(i is not None, f"no two cards side by side that say «{buy}»: {seen}")
    card, neighbour = cards.nth(i), cards.nth(i + 1)
    button(card, buy).click()
    button(own, es("checkout")).first.click()                     # el PayPal de prueba: directo a Gracias
    own.wait_for_url("**/thanks**", timeout=20000)
    own.get_by_role("link", name=".pine").first.wait_for(timeout=20000)   # pagado, con la sesión: sus enlaces
    own.goto(BASE + "/?lang=es", wait_until="networkidle")
    own.get_by_text(showing).wait_for()
    owned = card.locator("a[data-ef-owned]")
    owned.wait_for()
    label = owned.inner_text().strip()
    expect(card.evaluate("c => c.innerText.trim().split('\\n')[0]") == seen[i]["first"],
           f"the cards moved: {seen[i]['first']!r} is not card {i} any more")
    expect(label.startswith(es("ownedYours") + " · ") and button(card, buy).count() == 0,
           f"the strategy just bought: {label!r}, «{buy}» {button(card, buy).count()}")
    expect(button(neighbour, buy).count() == 1, f"its neighbour does not say «{buy}»")
    print(f"  {seen[i]['first']}: {label!r}; {seen[i + 1]['first']}: {buy!r}")
    crop(own, "owned", card, neighbour)


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
