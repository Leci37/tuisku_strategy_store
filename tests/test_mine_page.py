# -*- coding: utf-8 -*-
"""Mis estrategias en un Chromium de verdad (el kit del núcleo, ``testing.mobile``) sobre el catálogo de verdad
(``real_app``).

- «¿Compraste sin cuenta?»: un correo vacío o mal escrito no se manda y lo dice bajo el campo (los textos del
  núcleo, el borde rojo, ``aria-invalid``), como la gratis; también el rechazo del servidor a la dirección. El
  campo se puede vaciar (antes volvía el correo de la cuenta), e Intro no manda mientras se compone (zh, hi).
- Mandado, «Hecho» se queda, también cuando el bloque salió por un enlace usado; y pedir un correo que la
  cuenta ya demostró lo dice un aviso, sin pedir nada al servidor (antes, el bloque se iba sin decir nada).
- Las favoritas esperan a API #15: sin ella, nada de «Pulsa el corazón…» (decía que no había ninguna).
- Una alerta o un ♥ que el servidor no guarda (la sesión se cerró en otra pestaña: 401) vuelven a como
  estaban, la favorita a su sitio, y el aviso dice por qué.
- «Añádela a TradingView» sólo sale con algo de la cuenta que instalar, como en Gracias con los enlaces
  escondidos (antes abría el tutorial sin estrategia: «strategy.pine» y TradingView sin símbolo).
- Una respuesta que llega bien pero con el cuerpo cortado (una navegación o la red la cortaron a medias) es «sin
  conexión», como no tener respuesta; antes era null, y leerlo (``m.items``) un TypeError en la consola. Y una que
  dijera «null» no rompe Mis estrategias.
"""
import json
from urllib.parse import quote

from zlecitool_core import testing
from zlecitool_core.testing import mobile

from edgefolio.settings import ROOT
from tests.conftest import outbox, proof_token, prove
from tests.test_mine import buy

UI = json.loads((ROOT / "i18n" / "ui.json").read_text(encoding="utf-8"))
TOUR_SEEN = "try { localStorage.setItem('edgefolio-tour-v1', '1'); } catch (e) {}"
FIELD = "section input[type=email]"
UNDER = "section label [role=alert]"          # lo que falla en la dirección, bajo el campo
NOTICE = "[role=status][data-ef-toast]"
BORDER = "s => getComputedStyle(document.querySelector(s)).borderTopColor"
RED = "rgb(192, 57, 43)"
# las favoritas como se ven: el nombre de cada fila y sus tres campanas (1 encendida, 0 apagada)
FAVS = """() => { const box = [...document.querySelectorAll('section > div')].find(d => d.querySelector('span > i.fa-heart'));
  return [...box.querySelectorAll(':scope > div')].map(r => [r.querySelector('button').textContent.trim(),
    [...r.querySelectorAll('span > button > i')].map(i => (i.className.includes('fa-solid') ? '1' : '0')).join('')]); }"""
SAME = "s => JSON.stringify((" + FAVS + ")()) === JSON.stringify(s)"


def asked(live) -> list:
    """Las peticiones de la prueba de un correo que llegaron al servidor."""
    return [r for r in live.requests if r[1].startswith("/api/mine/proofs")]


def test_the_proof_field_says_what_is_wrong_and_done_stays(real_app):
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(TOUR_SEEN)
            client = mobile.sign_in(tab)
            tab.goto("/mine")
            field, send = page.locator(FIELD), page.get_by_role("button", name=UI["sendLink"]["es"], exact=True)
            field.wait_for()
            assert field.input_value() == client.email and field.get_attribute("aria-invalid") == "false"
            empty, invalid = page.evaluate("() => [zt.t('errEmailRequired'), zt.t('errEmailInvalid')]")

            # C7: mal escrito, bajo el campo, sin mandar nada
            field.fill("no-es-un-correo")
            send.click()
            page.locator(UNDER).wait_for()
            assert page.locator(UNDER).inner_text() == invalid
            assert field.get_attribute("aria-invalid") == "true" and page.evaluate(BORDER, FIELD) == RED
            field.press("Backspace")                    # escribir lo quita
            assert page.locator(UNDER).count() == 0 and field.get_attribute("aria-invalid") == "false"
            # C8: el campo se vacía y se queda vacío (antes volvía el correo de la cuenta); vacío no se manda
            field.fill("x")
            field.press("Backspace")
            assert field.input_value() == ""
            field.type("o")
            assert field.input_value() == "o", "se pegaba al correo de la cuenta"
            field.fill("")
            send.click()
            page.locator(UNDER).wait_for()
            assert page.locator(UNDER).inner_text() == empty and field.input_value() == ""
            # C9: Intro mientras se compone (zh, hi) elige los caracteres: no manda
            field.fill("otra@example.com")
            field.dispatch_event("keydown", {"key": "Enter", "keyCode": 229, "isComposing": True})
            page.wait_for_timeout(300)
            assert asked(live) == []
            # el servidor rechaza la dirección: también bajo el campo, no en un aviso
            field.fill("ana,bob@example.com")
            with page.expect_response("**/api/mine/proofs") as refused:
                field.press("Enter")
            assert refused.value.status == 400
            page.locator(UNDER).wait_for()
            assert page.locator(UNDER).inner_text() == invalid and page.locator("[data-ef-toast]").count() == 0
            # Intro con una buena: «Hecho»
            field.fill("otra@example.com")
            field.press("Enter")
            page.get_by_text(UI["proofSent"]["es"]).wait_for()
            assert [m["to"] for m in outbox("otra@example.com")] == ["otra@example.com"]

            # C11: con el correo de la cuenta ya demostrado, el bloque sale por un enlace usado
            prove(client)
            used = proof_token(client.email)
            tab.goto(f"/mine?proof={used}")
            page.get_by_text(UI["errProofExpired"]["es"]).wait_for()
            page.get_by_text(UI["favEmpty"]["es"]).wait_for()       # API #15, con los correos demostrados, ya está
            assert field.input_value() == client.email
            before = len(asked(live))
            send.click()                                # el de la cuenta, ya demostrado: lo dice un aviso
            page.locator(NOTICE).wait_for()
            assert page.locator(NOTICE).inner_text().split("\n")[:2] == [UI["proofProvenTitle"]["es"], UI["proofProvenText"]["es"]]
            assert len(asked(live)) == before, "no se pide nada al servidor"
            assert field.count() == 1, "el bloque se queda, para escribir otro"
            field.fill("otra-mas@example.com")         # otro correo: el aviso de antes se va
            page.locator(NOTICE).wait_for(state="detached")
            send.click()
            page.get_by_text(UI["proofSent"]["es"]).wait_for()
            page.wait_for_timeout(300)
            assert page.get_by_text(UI["proofSent"]["es"]).count() == 1, "«Hecho» se iba con el bloque"
            assert [m["to"] for m in outbox("otra-mas@example.com")] == ["otra-mas@example.com"]
            assert tab.problems() == ["400 POST /api/mine/proofs"], tab.problems()
        finally:
            tab.close()


def test_the_favourites_wait_for_the_account_and_come_back_when_refused(real_app):
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(TOUR_SEEN)
            client = mobile.sign_in(tab)
            ids = [r["id"] for r in client.get("/api/strategies?paid=1&size=3").json["rows"]]
            for sid in ids:
                assert client.put(f"/api/favourites/{sid}", json={"alerts": {}}).status_code == 200

            # C10: mientras no llega API #15, la lista de favoritas no dice que esté vacía
            held = []
            page.route("**/api/mine", lambda route: held.append(route))
            tab.goto("/mine")
            page.get_by_role("heading", name=UI["myStrategies"]["es"]).wait_for()
            page.wait_for_timeout(300)
            assert held and page.get_by_text(UI["favEmpty"]["es"]).count() == 0, "«Pulsa el corazón…» con favoritas"
            held[0].continue_()
            page.unroute("**/api/mine")
            page.wait_for_function("() => document.querySelectorAll('section span > button > i.fa-bell').length === 9")
            shown = page.evaluate(FAVS)
            assert [bells for _, bells in shown] == ["000"] * 3 and page.get_by_text(UI["favEmpty"]["es"]).count() == 0

            # C12: la sesión se cierra en otra pestaña (la misma cookie): el servidor no guarda nada (401)
            assert page.evaluate("() => fetch('/logout', {method: 'POST', headers: {Accept: 'application/json'}})"
                                 ".then(r => r.status)") == 200
            toast = page.locator("[role=alert][data-ef-toast]")
            bell = page.locator("section span > button", has_text=UI["alertPrice"]["es"]).nth(1)
            with page.expect_response(f"**/api/favourites/{ids[1]}") as put:
                bell.click()
            assert put.value.status == 401
            toast.wait_for()
            page.wait_for_function(SAME, arg=shown)
            heart = page.locator("section button[title=%s]" % json.dumps(UI["favourites"]["es"], ensure_ascii=False)).nth(1)
            with page.expect_response(f"**/api/favourites/{ids[1]}") as gone:
                heart.click()
            assert gone.value.status == 401
            page.wait_for_function(SAME, arg=shown)
            assert toast.count() == 1 and page.evaluate("() => zt.t('errLoginRequired')") in toast.inner_text()
            # la cuenta, como estaba
            again = testing.signed_in_client(real_app, email=client.email)
            favs = again.get("/api/mine").json["favourites"]
            assert [f["id"] for f in favs] == ids and all(not any(f["alerts"].values()) for f in favs)
            assert tab.problems() == [f"401 PUT /api/favourites/{ids[1]}", f"401 DELETE /api/favourites/{ids[1]}"], tab.problems()
        finally:
            tab.close()


def test_the_install_tutorial_waits_for_a_strategy_of_the_account(real_app):
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(TOUR_SEEN)
            client = mobile.sign_in(tab)
            install = page.get_by_role("button", name=UI["installTitle"]["es"], exact=True)
            # sin nada de la cuenta (API #15 ya llegó), ni el botón ni el tutorial de una estrategia que no hay
            tab.goto("/mine")
            page.get_by_text(UI["favEmpty"]["es"]).wait_for()
            assert install.count() == 0, "el tutorial sin estrategia: «strategy.pine», TradingView sin símbolo"
            # con una comprada, el tutorial es el suyo
            row = client.get("/api/strategies?paid=1&size=1").json["rows"][0]
            buy(client, [row["id"]])
            tab.goto("/mine")
            install.click()
            dialog = page.get_by_role("dialog")
            dialog.get_by_text(row["file"] + ".pine", exact=True).wait_for()
            page.keyboard.press("ArrowRight")
            page.keyboard.press("ArrowRight")
            assert f"Busca {row['ticker']} y elige el intervalo " in dialog.locator("p").inner_text()
            link = dialog.get_by_role("link", name=UI["instOpenTv"]["es"].format(sym=row["ticker"]))
            assert "?symbol=" + quote(row["tv_symbol"], safe="") + "&" in link.get_attribute("href")
            assert tab.problems() == []
        finally:
            tab.close()


def test_an_answer_cut_halfway_is_a_network_failure_not_a_script_error(real_app):
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(TOUR_SEEN)
            mobile.sign_in(tab)
            answer = {"body": '{"items": [{"id": '}
            page.route("**/api/mine", lambda route: route.fulfill(status=200, content_type="application/json",
                                                                  body=answer["body"]))
            tab.goto("/mine")
            toast = page.locator("[role=alert][data-ef-toast]")
            toast.wait_for()
            assert UI["errShopNetwork"]["es"] in toast.inner_text(), toast.inner_text()
            assert tab.problems() == [], tab.problems()
            # «null»: nada que enseñar, y nada en la consola
            answer["body"] = "null"
            with page.expect_response("**/api/mine"):
                tab.goto("/mine")
            page.wait_for_timeout(300)
            assert toast.count() == 0 and tab.problems() == [], tab.problems()
        finally:
            tab.close()
