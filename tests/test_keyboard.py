# -*- coding: utf-8 -*-
"""El teclado y los diálogos de la tienda en un Chromium de verdad (el kit del núcleo, ``testing.mobile``), sobre
el catálogo de verdad (``real_app``). Los diálogos (el recorrido, el tutorial de instalación, el pack, Comparar y
la gratis) son capas del diseño, no un <dialog>: static/js/lib/modal.js hace lo que haría showModal(). Al
abrirse, el foco entra; lo de detrás queda inert y Tab da la vuelta dentro; al cerrarse, el foco vuelve a quien
lo abrió; y, si lo enfocado desaparece dentro («Enviarme el enlace» al mandarlo), va a lo principal. Además: las
× dicen qué cierran o qué quitan, una imagen del recorrido se arrastra como el resto, Lite | Pro va con las
flechas, una fila de la Tabla se abre con el teclado, Esc en un desplegable de Pro devuelve el foco a su botón y
los buscadores enseñan el foco en su caja."""
import json
import re

from zlecitool_core.testing import mobile

DIALOG = "[role=dialog][aria-modal=true]"
ACTIVE_IN_DIALOG = "() => !!document.activeElement && !!document.activeElement.closest('[role=dialog]')"
ACTIVE_IS_MAIN = "() => !!document.activeElement && document.activeElement.matches('[role=dialog] [data-ef-focus]')"
ACTIVE_IS_OPENER = "() => document.activeElement === window.__opener"
LABEL = "() => (document.activeElement.getAttribute('aria-label') || document.activeElement.textContent || '').trim()"
SEARCH_BOX = """sel => { const l = document.querySelector(sel).closest('label'); return getComputedStyle(l).borderColor; }"""
BLUE = "rgb(9, 80, 227)"


def opened_with_enter(page, locator):
    """Enfoca ``locator``, lo recuerda como quien abre y pulsa Intro."""
    locator.focus()
    page.evaluate("() => { window.__opener = document.activeElement; }")
    page.keyboard.press("Enter")
    page.wait_for_selector(DIALOG)


def closed_with_escape(page):
    page.keyboard.press("Escape")
    page.wait_for_selector(DIALOG, state="detached")
    assert page.evaluate("() => document.querySelectorAll('[inert]').length") == 0, "lo de detrás sigue inert"


def drag(page, box, dx):
    """Arrastra con el ratón desde el centro de ``box``, dx píxeles."""
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + dx, y, steps=8)
    page.mouse.up()


def test_the_dialogs_of_lite_take_the_keyboard_and_give_it_back(real_app):
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            tab.goto("/")                    # la primera vez: el recorrido se abre solo
            page.wait_for_selector(DIALOG)
            page.wait_for_function(ACTIVE_IS_MAIN)
            assert page.evaluate("() => document.activeElement.textContent.trim()") == "Continuar"
            assert page.evaluate("() => document.querySelector('header.app-topbar').inert && "
                                 "!!document.querySelector('input[data-search]').closest('[inert]')"), "la página de detrás"
            for _ in range(3):               # × y «Continuar»: Tab no sale
                page.keyboard.press("Tab")
                assert page.evaluate(ACTIVE_IN_DIALOG)
            page.keyboard.press("Shift+Tab")
            assert page.evaluate(ACTIVE_IN_DIALOG)
            page.mouse.wheel(0, 900)
            page.wait_for_timeout(150)
            assert page.evaluate("() => window.scrollY") == 0, "la rueda movía la página de detrás"

            # B12: un arrastre con el ratón que empieza en la curva del paso 2 pasa de paso (no arrastra la imagen)
            page.locator(f"{DIALOG} [data-ef-focus]").click()
            page.wait_for_function("() => document.querySelector('[role=dialog]').innerText.includes('Paso 2 de 3')")
            drag(page, page.locator(f"{DIALOG} img").first.bounding_box(), -120)
            page.wait_for_function("() => document.querySelector('[role=dialog]').innerText.includes('Paso 3 de 3')")
            drag(page, page.locator(f"{DIALOG} img[alt=PayPal]").bounding_box(), 120)
            page.wait_for_function("() => document.querySelector('[role=dialog]').innerText.includes('Paso 2 de 3')")
            closed_with_escape(page)

            # «Ver tutorial» con el teclado: entra, y Esc lo devuelve al chip
            opened_with_enter(page, page.locator("[data-ef-bar=end] button").first)
            page.wait_for_function(ACTIVE_IS_MAIN)
            closed_with_escape(page)
            assert page.evaluate(ACTIVE_IS_OPENER)

            # B11: Lite | Pro, un solo alto de Tab y las flechas
            radios = "() => [...document.querySelectorAll('[data-ef-bar=start] [role=radio]')].map(b => [b.tabIndex, b.getAttribute('aria-checked')])"
            assert page.evaluate(radios) == [[0, "true"], [-1, "false"]]
            page.locator("[data-ef-bar=start] [role=radio]").first.focus()
            page.keyboard.press("ArrowRight")
            page.wait_for_function("() => document.activeElement.matches('[role=radio][aria-checked=true]') && "
                                   "document.activeElement.textContent.trim() === 'Pro'")
            assert page.evaluate(radios) == [[-1, "false"], [0, "true"]]
            page.keyboard.press("ArrowLeft")
            page.wait_for_function("() => document.activeElement.matches('[role=radio][aria-checked=true]') && "
                                   "document.activeElement.textContent.trim() === 'Lite'")

            # B10: el buscador enseña el foco en su caja
            page.wait_for_selector("input[data-search=lite]")
            page.wait_for_function("() => document.querySelectorAll('#app img').length > 0")
            assert page.evaluate(SEARCH_BOX, "input[data-search=lite]") != BLUE
            page.locator("input[data-search=lite]").focus()
            assert page.evaluate(SEARCH_BOX, "input[data-search=lite]") == BLUE

            # B5: la × de una explicación dice «Cerrar»
            page.locator("#app button[title]").filter(has_text="%").first.click()
            assert page.locator("[role=tooltip] button").get_attribute("aria-label") == "Cerrar"

            # B8: el selector del pack, con su buscador, y de vuelta al «+»
            opened_with_enter(page, page.locator("#app button", has_text=re.compile(r"^\+$")).first)
            page.wait_for_function("() => document.activeElement.matches('[role=dialog] input')")
            page.keyboard.press("Shift+Tab")         # del primero, al último: «Hecho»
            assert page.evaluate(LABEL) == "Hecho"
            closed_with_escape(page)
            assert page.evaluate(ACTIVE_IS_OPENER)

            # B5 y B8: Comparar, con sus × con nombre
            compare = page.locator("#app button[title=Comparar]")
            compare.nth(0).click()
            compare.nth(1).click()
            opened_with_enter(page, page.locator("#app button", has_text="Comparar ·"))
            page.wait_for_function(ACTIVE_IS_MAIN)
            assert page.evaluate(LABEL) == "Cerrar"
            removes = page.evaluate("() => [...document.querySelectorAll('[role=dialog] th button')].map(b => b.getAttribute('aria-label'))")
            assert len(removes) == 2 and all(re.match(r"^Quitar \S+ · \S+$", x) for x in removes), removes
            closed_with_escape(page)
            assert page.evaluate(ACTIVE_IS_OPENER)

            # C2: la gratis, mandada, deja el foco en «Volver a la tienda»; Esc, en «Descargar»
            page.route("**/api/free", lambda route: route.fulfill(status=200, content_type="application/json",
                                                                 body=json.dumps({"sent": True})))
            opened_with_enter(page, page.locator("#app button", has_text=re.compile(r"^\s*Descargar\s*$")).first)
            page.wait_for_function("() => document.activeElement.matches('[role=dialog] input[type=email]')")
            assert page.locator(f"{DIALOG} button").first.get_attribute("aria-label") == "Cerrar"
            page.keyboard.type("ana@example.com")
            page.keyboard.press("Enter")
            page.wait_for_function("() => document.activeElement.textContent.trim() === 'Volver a la tienda'")
            page.keyboard.press("Tab")
            assert page.evaluate(ACTIVE_IN_DIALOG), "el siguiente Tab, dentro del diálogo"
            closed_with_escape(page)
            assert page.evaluate(ACTIVE_IS_OPENER)
            assert tab.problems() == []
        finally:
            tab.close()


PRO_TABLE = """(() => { localStorage.setItem('edgefolio-tour-v1', '1'); localStorage.setItem('tuisku-sf-mode', 'pro');
  localStorage.setItem('tuisku-sf-pview5', 'table'); })()"""


def test_pro_by_keyboard_rows_dropdowns_and_their_labels(real_app):
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(PRO_TABLE)
            # un enlace de descarga gastado vuelve con su aviso: su × dice «Cerrar» (B5)
            tab.goto("/?link=errDownloadLimit")
            page.wait_for_selector("[role=alert] button")
            assert page.locator("[role=alert] button").get_attribute("aria-label") == "Cerrar"
            page.locator("[role=alert] button").click()

            # B9 y B23: de la última cabecera, Tab llega a la primera fila; Intro la abre, un clic la cierra
            page.wait_for_selector("tbody tr")
            first = page.locator("tbody tr td:first-child button[aria-expanded]").first
            page.locator("thead button").last.focus()
            page.keyboard.press("Tab")
            assert page.evaluate("() => document.activeElement.matches('tbody button[aria-expanded]')")
            page.keyboard.press("Enter")
            page.wait_for_selector("td[colspan='12']")
            assert first.get_attribute("aria-expanded") == "true"
            first.click()                    # el botón y la fila: una sola vez, no dos
            page.wait_for_selector("td[colspan='12']", state="detached")
            assert first.get_attribute("aria-expanded") == "false"
            page.locator("tbody tr").first.locator("td").nth(4).click()   # con el ratón, la fila entera
            page.wait_for_selector("td[colspan='12']")

            # B8: Esc en un desplegable con el foco en su buscador lo devuelve a su botón
            symbol = page.locator("aside button[aria-expanded]").filter(has_text="Símbolo")
            symbol.focus()
            page.keyboard.press("Enter")
            page.keyboard.press("Tab")
            assert page.evaluate("() => document.activeElement.matches('aside input:not([aria-label])')")
            assert page.evaluate(SEARCH_BOX, "aside input:not([aria-label])") == BLUE      # B10
            page.keyboard.press("Escape")
            page.wait_for_function("() => document.activeElement.matches('aside button[aria-expanded=false]') && "
                                   "document.activeElement.textContent.includes('Símbolo')")

            # B5: la × de un filtro activo dice cuál quita
            page.keyboard.press("Enter")
            page.locator("aside button.sf-hover1").first.click()
            page.keyboard.press("Escape")
            chip = page.locator("section span > button[aria-label^='Quitar Símbolo: ']")
            chip.wait_for()
            page.locator("input[data-search=pro]").focus()
            assert page.evaluate(SEARCH_BOX, "input[data-search=pro]") == BLUE
            assert tab.problems() == []
        finally:
            tab.close()
