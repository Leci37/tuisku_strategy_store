# -*- coding: utf-8 -*-
"""Las escalas que pone el catálogo, en un Chromium de verdad (``testing.mobile`` del núcleo) sobre el catálogo
de verdad (``real_app``). Los rangos de Pro van del mínimo al máximo del catálogo (con las barras del diseño,
las del catálogo de 2024, las 143 estrategias de 2026-10 caían en un rincón), y la actividad por vela se
filtra con sus tres decimales. Las dos barras de la página de la estrategia («Backtest» y «Desde su
publicación») miden contra el mejor backtest del catálogo, el ``npp_max`` de /api/config: contra el 100 % del
diseño, los backtests de 0,03–0,44 % no se veían."""
import json
import re

from zlecitool_core.testing import mobile

from edgefolio.settings import ROOT
from edgefolio.shop import of

ES = {k: v["es"] for k, v in json.loads((ROOT / "i18n" / "ui.json").read_text(encoding="utf-8")).items()
      if isinstance(v, dict) and isinstance(v.get("es"), str)}
# Pro, sin el recorrido de bienvenida: lo que guarda el navegador de quien ya lo vio
PRO = "try { localStorage.setItem('edgefolio-tour-v1', '1'); localStorage.setItem('tuisku-sf-mode', 'pro'); } catch (e) {}"
# Las dos barras de la página de la estrategia: lo que llena cada una de su carril (las vistas no tienen
# ganchos; el estilo, por sus propiedades, que el navegador escribe a su manera)
BARS = """() => [...document.querySelectorAll('#app div')].filter(d => d.style.height === '8px' && d.style.overflow === 'hidden')
  .map(d => d.firstElementChild.getBoundingClientRect().width / d.getBoundingClientRect().width)"""
COUNT = "() => [...document.querySelectorAll('aside div')].find(d => d.style.fontSize === '26px').textContent.trim()"


def es(n) -> str:
    """Un extremo de una barra como lo escribe la caja en español (sin miles: son cifras pequeñas)."""
    return str(n).replace(".", ",")


def drawn(tab, label: str) -> dict:
    """Las cajas de mínimo y máximo de un rango de «Más filtros», abierto, y cuántas de sus barras tienen algo."""
    return tab.page.evaluate("""label => {
      const boxes = [...document.querySelectorAll('aside input')].filter(i => i.getAttribute('aria-label') === label);
      const hist = [...boxes[0].parentElement.parentElement.children].find(d => d.style.height === '40px');
      const bars = [...hist.children];
      return { lo: boxes[0].value, hi: boxes[1].value, bars: bars.length, filled: bars.filter(b => b.style.height !== '0px').length };
    }""", label)


def test_the_pro_ranges_and_the_strategy_bars_follow_the_catalogue(real_app, real_client):
    catalogue = of(real_app).catalogue
    by_npp = sorted((s for s in catalogue if s.numbers["npp"] is not None), key=lambda s: s.numbers["npp"])
    low, best = by_npp[0], by_npp[-1]
    top = best.numbers["npp"]
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        try:
            mobile.sign_in(tab)
            tab.context.add_init_script(PRO)
            with tab.page.expect_response(lambda r: "facets=1" in r.url) as facets:
                tab.goto("/")
            ranges = facets.value.json()["ranges"]

            tab.page.locator("aside button[aria-expanded]", has_text=ES["fClosedTrades"]).click()
            trades = drawn(tab, ES["fClosedTrades"])
            assert (trades["lo"], trades["hi"]) == (es(ranges["trades"]["min"]), es(ranges["trades"]["max"])), trades
            assert trades["filled"] > 5, f"las operaciones, repartidas por la barra y no en la primera: {trades}"

            tab.page.locator("aside button[aria-expanded]", has_text=ES["fActivity"]).click()
            act = drawn(tab, ES["fActivity"])
            assert (act["lo"], act["hi"]) == (es(ranges["act"]["min"]), es(ranges["act"]["max"])), act
            expected = real_client.get("/api/strategies?act_max=0.017").json["total"]
            box = tab.page.locator(f'aside input[aria-label="{ES["fActivity"]}"]').nth(1)
            box.fill("0,017")
            with tab.page.expect_request(lambda r: "act_max=0.017" in r.url):
                box.press("Enter")                    # con un decimal, se mandaba 0
            tab.page.wait_for_function(f"() => ({COUNT})() === '{expected}'")

            # la peor y la mejor del catálogo; a la peor, una cifra desde su publicación de −0,22 %
            def with_live(route):
                response = route.fetch()
                body = response.json()
                for row in body.get("rows", [body]):
                    if row.get("id") == low.id:
                        row["live"] = -0.22
                route.fulfill(response=response, json=body)

            tab.page.route(re.compile(r".*/api/strategies.*"), with_live)
            tab.goto(f"/s/{best.id}")
            tab.page.wait_for_function(f"() => ({BARS})().length === 2 && ({BARS})()[0] > 0.5")
            bt, since = tab.page.evaluate(BARS)
            assert abs(bt - 1) < 0.01 and since == 0, (bt, since)
            tab.goto(f"/s/{low.id}")
            tab.page.wait_for_function(f"() => ({BARS})().length === 2 && ({BARS})()[1] > 0")
            bt, since = tab.page.evaluate(BARS)
            assert abs(bt - max(0, low.numbers["npp"]) / top) < 0.01, (bt, low.numbers["npp"], top)
            assert abs(since - min(1, 0.22 / top)) < 0.01, since
            assert tab.problems() == []
        finally:
            tab.close()
