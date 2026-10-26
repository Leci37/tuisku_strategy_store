# -*- coding: utf-8 -*-
"""Lo que la tienda dice de su catálogo (las decisiones del dueño del 2026-10-26), en un Chromium de verdad (el kit
del núcleo, ``testing.mobile``) sobre el catálogo de verdad.

- E1: el aviso de sobreajuste de Lite y de Pro dice entre cuántas estrategias probadas se eligieron las del
  catálogo (``tried`` de release.json, por API #1) y que sus cifras son de datos que los modelos no vieron. Sin
  saberlo, no lo dice.
- E10: la explicación de la nota (su ``title``) dice desde cuántas operaciones es cada letra (GRADE_CUTOFFS).
- E11: «Desde su publicación» no sale (las fichas de Lite, la caja y la barra de la ficha, Comparar) mientras
  ninguna estrategia tiene cifra; la caja de la ficha es entonces la del backtest. Con una cifra (since_release.csv)
  vuelve sola: en esa, su cifra y hasta cuándo; en las demás, «—» y que aún no se ha medido.
"""
import json
import shutil

import pytest

from zlecitool_core import testing
from zlecitool_core.testing import mobile

from edgefolio.paypal import FakePayPal
from edgefolio.settings import ROOT, Settings
from edgefolio.shop import install

UI = json.loads((ROOT / "i18n" / "ui.json").read_text(encoding="utf-8"))
ES = {k: v["es"] for k, v in UI.items() if isinstance(v, dict) and isinstance(v.get("es"), str)}
SEEN = "try { localStorage.setItem('edgefolio-tour-v1', '1'); localStorage.setItem('tuisku-sf-mode', 'lite'); } catch (e) {}"
SNOW, AMD = "SNOW_1Day_1BOL_7abec5de", "AMD_1Day_1M00_c7520cc7"
# Las vistas no tienen ganchos: el aviso de sobreajuste (el del triángulo), la nota de cada ficha de Lite (con lo
# que la sigue: «Desde su publicación …», o los botones si no sale), la caja de las barras de la ficha y las filas
# de Comparar.
RISK = """() => [...document.querySelectorAll('#app [role=note]')].filter(n => n.querySelector('.fa-triangle-exclamation'))
  .map(n => n.querySelector('span').textContent)"""
CARDS = """() => [...document.querySelectorAll('#app span[title]')].filter(s => s.style.cursor === 'help')
  .map(b => [b.parentElement.parentElement.innerText.split('\\n')[0], b.title, b.nextElementSibling.textContent.trim()])"""
BOX = """() => { const bars = [...document.querySelectorAll('#app div')].filter(d => d.style.height === '8px' && d.style.overflow === 'hidden');
  if (!bars.length) return null; const box = bars[0].parentElement;
  return { bars: bars.length, head: box.firstElementChild.firstElementChild.textContent,
           labels: [...box.children].filter(d => d.style.justifyContent === 'space-between').map(d => d.firstElementChild.textContent),
           notes: [...box.children].filter(d => d.tagName === 'SPAN').map(s => s.textContent) }; }"""
COMPARED = "() => [...document.querySelectorAll('[role=dialog] tr')].map(tr => tr.firstElementChild).filter(c => c.tagName === 'TD').map(c => c.textContent)"
PCT = "x => new Intl.NumberFormat('es-ES', { style: 'percent', minimumFractionDigits: 2, maximumFractionDigits: 2, signDisplay: 'exceptZero' }).format(x / 100)"
DAY = "iso => new Intl.DateTimeFormat('es-ES', { dateStyle: 'medium' }).format(new Date(iso + 'T12:00:00'))"
CUTS = " " + ES["gradeCuts"].format(a="100", b="50", c="25")


def compare_two(page) -> list:
    """Las dos primeras fichas de Lite, a Comparar: las filas del diálogo."""
    buttons = page.locator(f"#app button[title='{ES['compare']}']")
    buttons.nth(0).click()
    buttons.nth(1).click()
    page.locator("#app button", has_text=ES["compare"]).last.click()
    page.wait_for_selector("[role=dialog] tr td")
    rows = page.evaluate(COMPARED)
    page.keyboard.press("Escape")
    return rows


@pytest.fixture(scope="module")
def figures_app(tmp_path_factory):
    """El catálogo de verdad con una cifra desde su publicación, la de SNOW (since_release.csv), y sin release.json:
    no se sabe entre cuántas probadas se eligieron."""
    tmp = tmp_path_factory.mktemp("figures")
    folder = tmp / "catalogue"
    folder.mkdir()
    for name in ("catalogue.csv", "indicators.csv", "bundles.json", "fx.json"):
        shutil.copy(ROOT / "catalogue" / name, folder / name)
    (folder / "since_release.csv").write_text(f"id,pct,as_of\n{SNOW},1.23,2026-10-25\n", encoding="utf-8")
    settings = Settings.for_data_dir(tmp / "data", catalogue=folder / "catalogue.csv", indicators=folder / "indicators.csv",
                                     bundles=folder / "bundles.json", fx=folder / "fx.json",
                                     since_release=folder / "since_release.csv")
    with testing.isolated(tmp / "zt"):
        from app import create_app
        application = testing.prepare(create_app())
        install(application, settings, FakePayPal())
        yield application


def test_the_catalogue_says_among_how_many_tried_and_hides_what_it_has_not_measured(real_app):
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(SEEN)
            tab.goto("/")
            # E1: 94 estrategias elegidas entre 1.531 (en español, «1531»: los miles de cuatro cifras van sin punto)
            said = ES["riskText"] + " " + ES["riskTried"].replace("{n}", "94").replace(
                "{m}", page.evaluate("() => new Intl.NumberFormat('es-ES').format(1531)"))
            page.wait_for_function(f"s => ({RISK})()[0] === s", arg=said)
            # E10 y E11: cada nota dice sus cortes, y tras ella ya no sale «Desde su publicación —»
            page.wait_for_function(f"() => ({CARDS})().length > 0")
            cards = page.evaluate(CARDS)
            assert all(tip.endswith(CUTS) and after == "" for _, tip, after in cards), cards
            assert ES["sinceRelease"] not in page.locator("#app").inner_text()
            rows = compare_two(page)
            assert rows == [ES["fNetProfitPct"], ES["fWinRate"], ES["fClosedTrades"], ES["fAvgProfitUsd"], ES["sortPrice"]]

            page.get_by_role("radio", name="Pro").click()
            page.wait_for_function(f"s => ({RISK})()[0] === s", arg=said)

            # la ficha: la caja es la del backtest, sin el resultado real que no hay
            tab.goto(f"/s/{SNOW}")
            page.wait_for_function(f"() => ({BOX})() !== null")
            assert page.evaluate(BOX) == {"bars": 1, "head": ES["colBacktest"], "labels": [ES["npPct"]], "notes": []}
            assert ES["sinceRelease"] not in page.locator("#app").inner_text()
            assert tab.problems() == []
        finally:
            tab.close()


def test_since_release_comes_back_with_a_figure(figures_app):
    with mobile.serve(figures_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(SEEN)
            tab.goto("/")
            page.wait_for_function(f"() => ({CARDS})().some(c => c[2].startsWith({json.dumps(ES['sinceRelease'])}))")
            cards = [[ticker, after] for ticker, _, after in page.evaluate(CARDS)]
            figure, unknown = f"{ES['sinceRelease']} {page.evaluate(PCT, 1.23)}", f"{ES['sinceRelease']} —"
            assert ["SNOW", figure] in cards and ["AMD", unknown] in cards, cards
            assert sorted(set(after for _, after in cards)) == sorted([figure, unknown]), cards
            assert page.evaluate(RISK) == [ES["riskText"]], "sin release.json no se sabe entre cuántas: no lo dice"
            assert ES["sinceRelease"] in compare_two(page)

            tab.goto(f"/s/{SNOW}")
            page.wait_for_function(f"() => ({BOX})() !== null && ({BOX})().bars === 2")
            assert page.evaluate(BOX) == {"bars": 2, "head": ES["liveVsBacktest"], "labels": [ES["colBacktest"], ES["sinceRelease"]],
                                          "notes": [ES["liveAsOf"].replace("{date}", page.evaluate(DAY, "2026-10-25"))]}
            tab.goto(f"/s/{AMD}")
            page.wait_for_function(f"() => ({BOX})() !== null && ({BOX})().bars === 2")
            assert page.evaluate(BOX)["notes"] == [ES["liveUnknown"]]
            assert tab.problems() == []
        finally:
            tab.close()
