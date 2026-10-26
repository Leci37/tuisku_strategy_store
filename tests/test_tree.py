# -*- coding: utf-8 -*-
"""«Cómo decide» (static/js/tree.js, static/js/views/tree/ y static/trees/): sus datos, y la pestaña en un Chromium
de verdad con el kit del núcleo (``testing.mobile``, 0.28) sobre el catálogo de verdad (``real_app``).

- Cada patrón de las vistas previas publicadas se explica en los 8 idiomas: en y es en features.json, los otros
  seis en ``pat`` de ui.json (sólo 7 de los 22 de 2026-10 tenían explicación). Cada nombre de features.json dice
  de qué patrón es.
- Árbol | Bloques dicen cuál está puesta (aria-selected). La línea del patrón y el texto de cada explicación dicen
  su idioma (lang): la descripción de un indicador, fuera de es y en, es la inglesa, y en árabe va de izquierda a
  derecha (dir; si no, su punto final salta al principio). La línea del patrón va en la dirección de la página: en
  árabe, de derecha a izquierda aunque empiece por un nombre latino («WaveTrend…»).
- Un valor que el generador divide por el cierre (``macd__close``, sus entradas de 2026) lleva el nombre del suyo,
  con una nota, si es de un patrón de la estrategia: ``d`` es la %D del RSI estocástico y una distancia de precio
  en WaveTrend, y ``ema2`` es la media intermedia de la Triple EMA y una de 2 velas en TMA Overlay (cada una, con
  su nombre: ``d@Wave_Trend_Calculation``). Lo mismo en los ocho idiomas: el nombre traducido (``feat``) tampoco
  vale fuera de su patrón. Cada valor por el que pregunta una vista previa publicada, o que toma su bosque, tiene
  nombre (E12b: antes, 140 de 182 salían con su código), en los ocho idiomas.
- Las descripciones de los valores, también en pt, fr, de, zh, ar e hi (``featDesc``, E12a), salvo las de los
  patrones de 2026-10, en en y es: ésas salen en inglés, dicho (lang) y de izquierda a derecha.
- «Comprar para desbloquear» sigue al carrito (la propiedad ``inCart`` de la página; sin ella, como fuera) y
  añade la estrategia una sola vez; si ya es de la cuenta (``owned``), «Ver como propietario», que ni la compra ni
  la pide. La «i» de cada valor dice «¿Qué es …?» en el idioma de la página.
- El propietario: su script completo colorea los resultados con sus niveles (``buyThreshold``,
  ``sellThreshold``); «el árbol completo», sea cual sea el del bosque; si su script no llega, dónde bajarlo y nunca
  «Comprar». En una gratis, «pídela» y no «cómprala».
- El visitante (E9): con los niveles que publica la tienda (API #3: ``buy_at``, ``close_at``); sin ellos, ningún
  resultado dice Comprar, Vender ni Esperar: cada uno, su puntuación, sin las zonas de colores, y la pestaña dice
  por qué (``noLevels``). Nunca 0,55 y −0,9. Tampoco «Resultado del árbol»: su escala dice −1 y +1, y ella y los
  dos ejemplos van en gris; la ayuda de los valores y el pie de la explicación de un resultado, de la puntuación.
- En árabe, la escala de «Resultado del árbol» va de izquierda a derecha, como su barra, y el + de una
  puntuación sale delante de sus cifras, como el −.
- En el móvil, tocar una pregunta enseña su explicación aunque la página se mueva sola justo después.
"""
import json
import re
import sys

from zlecitool_core.testing import mobile

from edgefolio.settings import ROOT
from edgefolio.shop import of
from tests.test_mine import buy

sys.path.insert(0, str(ROOT / "tools"))
import design_update  # noqa: E402

FX = json.loads((ROOT / "static" / "trees" / "features.json").read_text(encoding="utf-8"))
UI = json.loads((ROOT / "static" / "trees" / "ui.json").read_text(encoding="utf-8"))
TREE_JS = (ROOT / "static" / "js" / "tree.js").read_text(encoding="utf-8")
OTHERS = ("pt", "fr", "de", "zh", "ar", "hi")
# «primer(o)» en los otros seis, como lo decía ownFull antes
FIRST = {"pt": "primeira", "fr": "premier", "de": "erste", "zh": "第一", "ar": "الأولى", "hi": "पहला"}
# Árbol | Bloques y los verbos de los resultados, en español: los de la vista (renderVals), no los de TEXT.
BLOCKS, BUY, SELL, WAIT = "Bloques", "Comprar", "Vender", "Esperar"
VERBS = (BUY, SELL, WAIT)
# La d de WaveTrend, una distancia de precio: la %D del RSI estocástico se llama d también.
WAVE_D = "d@Wave_Trend_Calculation"
# Los patrones cuyos valores ya tenían descripción antes de 2026-10: la suya, en los ocho idiomas (E12a); la de los
# demás (E12b), en en y es.
TRANSLATED = {"L_Vortex_Indicator", "L_Triple_EMA", "MACD_ULT_MTF", "Bollinger_RSI_Double_Strategy",
              "L_Chaikin_Money_Flow", "L_Money_Flow_Index", "L_Stochastic_RSI"}
# Los textos del árbol sin los niveles del script (E9), y la nota de un valor dividido por el cierre.
SCORED_TEXTS = ("relNote", "score", "results", "s3Score", "noLevels", "leadScore1", "leadScoreN", "hiEx", "loEx",
                "exHelpScore", "optTextScore", "leafFootScore")


def text_of(lang: str, key: str) -> str:
    """Un texto del árbol: los de en y es están en tree.js (TEXT), los de los otros seis en ui.json."""
    if lang in OTHERS:
        return UI[lang][key]
    block = TREE_JS[TREE_JS.index(f"  {lang}: {{"):]
    return re.search(rf"\b{key}: '((?:[^'\\]|\\.)*)'", block).group(1)


def es(key: str) -> str:
    return text_of("es", key)


def bases_of(src: str) -> list:
    return [b.strip() for b in re.search(r"^// Technical base pattern:(.*)$", src, re.M).group(1).split(",") if b.strip()]


def key_of(f: str, bases: list) -> str:
    """La clave de features.json con que la pestaña nombra el valor ``f`` en una estrategia de esos patrones, como
    keyOf de tree.js: la de su patrón (``d@Wave_Trend_Calculation``) y luego la suya, sólo si es de uno de ellos; uno
    dividido por el cierre, también sin ``__close``. '' si no tiene."""
    def own(e):
        return e is not None and (not e[4] or not bases or e[4] in bases)
    for g in ([f, f[:-len("__close")]] if f.endswith("__close") else [f]):
        for k in [f"{g}@{b}" for b in bases] + [g]:
            if own(FX["features"].get(k)):
                return k
    return ""


# Una vista previa de dos patrones, honda (el resultado de compra, cuatro pasos a la derecha) y con una rama
# cortada: d__close (de WaveTrend), ema2__close (de la Triple EMA) y macd__close (de ningún patrón suyo).
CRAFTED_PREVIEW = """// Technical base pattern: Wave_Trend_Calculation, L_Triple_EMA
// ID_model: TEST_1Day_1WAV_00000000 Date Creation: 2026/10/13 Expiry date: 2027/06/13
//@version=5
strategy("Tuisku_TEST_1Day_1WAV_00000000", overlay=true)
decision_tree_0_TEST_1Day_00000000(d__close, ema2__close, macd__close)=>
\tfloat ret = na  // # DecisionTreeRegressor(max_depth=4)
\tif( d__close <= 0.01 )
\t\tif( ema2__close <= 0.98 )
\t\t\tif( macd__close <= 0.03 )
\t\t\t\tif( d__close <= 0.005 )
\t\t\t\t\tret := 1.0 // buy
\t\t\t\tif( d__close > 0.005 )
\t\t\t\t\tret := 0.2
\t\t\tif( macd__close > 0.03 )
\t\t\t\tret := 0.1
\t\tif( ema2__close > 0.98 )
\t\t\tret := -0.2
\tif( d__close > 0.01 )
\t\tif( ema2__close <= 0.95 )
\t\t\tif( macd__close <= -0.03 )
\t\t\t\tret := -1 // sell
\t\t\tif( macd__close > -0.03 )
\t\t\t\tret := 0.3
\t\tif( ema2__close > 0.95 )
"""
# Los nombres de otros patrones, tal cual: ``d`` (del RSI estocástico) y ``macd`` (del MACD) en una de WaveTrend.
FOREIGN_PREVIEW = """// Technical base pattern: Wave_Trend_Calculation
decision_tree_0_TEST_1Day_00000000(d, macd)=>
\tfloat ret = na  // # DecisionTreeRegressor(max_depth=2)
\tif( d <= 0.5 )
\t\tret := 1.0
\tif( d > 0.5 )
\t\tif( macd <= 0.1 )
\t\t\tret := -1.0
\t\tif( macd > 0.1 )
\t\t\tret := 0.2
"""
# Un script completo de la plantilla de 2026 (niveles 0,8 y −0,5) con dos árboles; su vista previa, el primero.
OWNED_TREES = """// Technical base pattern: Bollinger_RSI_Double_Strategy
// ID_model: TEST_1Day_1BOL_11111111 Date Creation: 2026/10/13 Expiry date: 2027/06/13
//@version=5
strategy("Tuisku_TEST_1Day_1BOL_11111111", overlay=true)
decision_tree_0_TEST_1Day_11111111(BBlower__close, vrsi)=>
\tfloat ret = na  // # DecisionTreeRegressor(max_depth=2)
\tif( BBlower__close <= 0.97 )
\t\tif( vrsi <= 30 )
\t\t\tret := 0.7
\t\tif( vrsi > 30 )
\t\t\tret := 0.1
\tif( BBlower__close > 0.97 )
\t\tret := -0.6
\tret //return
"""
OWNED_SCRIPT = OWNED_TREES + """decision_tree_1_TEST_1Day_11111111(vrsi)=>
\tfloat ret = na  // # DecisionTreeRegressor(max_depth=1)
\tif( vrsi <= 50 )
\t\tret := 0.9
\tif( vrsi > 50 )
\t\tret := -1
\tret //return
float op_operation = (decision_tree_0_TEST_1Day_11111111(BBlower__close, vrsi) + decision_tree_1_TEST_1Day_11111111(vrsi)) / 2
buyThreshold = input.float(0.8, title="buy when the forest gives at least")
sellThreshold = input.float(-0.5, title="close when the forest gives at most")
if strategy.position_size == 0 and op_operation >= buyThreshold
    strategy.entry("x", strategy.long, comment = "in")
if strategy.position_size > 0 and op_operation <= sellThreshold
    strategy.close("x", comment = "out")
"""
# La plantilla de antes: los niveles, escritos en sus `if`; el `<= 0` que arma las salidas no cierra.
OLD_SCRIPT = """float op_operation = decision_tree_0_X(a)
if( op_operation >= 0.6 )
\tstrategy.entry("x", strategy.long)
if( op_operation <= 0 )
\tstrategy.exit("x", loss = sl)
if( op_operation <= -0.7 )
\tstrategy.close("x")
"""

# Lo que se ve de la pestaña: las dos pestañas de dentro, la línea del patrón (idioma, texto y dirección), cada caja
# (su código y lo que dice) y todo su texto.
SEEN = """() => {
  const sec = document.querySelector('[data-tree-sec]');
  if (!sec || !sec.querySelector('[data-tree-scroll] button, [data-blk-scroll] button')) return null;
  const boxes = {};
  sec.querySelectorAll('[data-tree-scroll] button[aria-label]').forEach(b => { boxes[b.getAttribute('aria-label')] = b.textContent.trim(); });
  return {
    tabs: [...sec.querySelectorAll('[role=tab]')].map(b => [b.textContent.trim(), b.getAttribute('aria-selected')]),
    about: [...sec.querySelectorAll('span[lang]')].map(s => [s.getAttribute('lang'), s.textContent, getComputedStyle(s).direction]),
    boxes, text: sec.textContent
  };
}"""
READY = f"() => !!({SEEN})()"
# El recuadro del propietario: los botones y enlaces junto a su texto.
OWNER_BOX = """text => {
  const span = [...document.querySelectorAll('[data-tree-sec] span')].find(s => s.textContent === text);
  if (!span) return null;
  return [...span.parentElement.querySelectorAll('button, a')].map(b => b.textContent.trim());
}"""
TIP = """() => { const t = document.querySelector('[role=tooltip]'); if (!t) return null;
  const p = t.querySelector('p'); return { title: t.querySelector('strong').textContent, lang: p.getAttribute('lang'), text: p.textContent,
  dir: p.getAttribute('dir'), direction: getComputedStyle(p).direction, cta: [...t.querySelectorAll('button')].map(b => b.textContent.trim()) }; }"""
CART = "() => { try { return (JSON.parse(localStorage.getItem('edgefolio-cart-v1')) || {}).cart || []; } catch (e) { return []; } }"
# Lo que tree.js hace con lo que le pasa la página, sin pintar: la etiqueta y dos clics de «Comprar para
# desbloquear» según inCart (lo que la página dice del carrito), la línea del patrón en francés (y sin su
# traducción: la inglesa, dicha), los nombres de otros patrones en tres idiomas, los niveles de un script completo y
# los del visitante: los que manda API #3 (buy_at, close_at) o, sin ellos, ninguno (scored).
UNIT = """async ([scripts, preview, foreign]) => {
  const { StrategyTree, levelsOf } = await import('/static/js/tree.js');
  const [fx, ui] = await Promise.all(['features', 'ui'].map(f => fetch('/static/trees/' + f + '.json').then(r => r.json())));
  const paid = { id: 'TEST_1Day_1WAV_00000000', ticker: 'TEST', price: 69 }, free = { ...paid, price: 0 };
  const shown = (props, texts = ui, src = preview) => {
    const tree = new StrategyTree({});
    tree.props = { embedded: true, lang: 'es', strategy: paid, ...props };
    Object.assign(tree, { _fx: fx, _ui: texts, setState: () => {}, follow: () => {} });
    tree.state = { ...tree.state, trees: tree.forest(src, tree.props.strategy) };
    return tree.renderVals();
  };
  const unlockWith = props => {
    let buys = 0;
    const v = shown({ ...props, onBuy: () => { buys++; } });
    v.unlock(); v.unlock();
    return [v.unlockLabel, buys];
  };
  return {
    none: unlockWith({}), out: unlockWith({ inCart: false }), in: unlockWith({ inCart: true }),
    free: unlockWith({ strategy: free, inCart: true }),
    owned: unlockWith({ owned: true }), ownedFree: unlockWith({ strategy: free, owned: true }),
    fr: shown({ lang: 'fr' }).abouts, untranslated: shown({ lang: 'fr' }, { ...ui, fr: { ...ui.fr, pat: {} } }).abouts,
    foreign: ['es', 'fr', 'ar'].map(lang => shown({ lang }, ui, foreign).nodes.filter(n => n.isDec).map(n => n.name)),
    levels: scripts.map(levelsOf),
    published: [{}, { buy_at: 0.15, close_at: -0.1 }, { buy_at: 0.15, close_at: null }].map(lv => {
      const v = shown({ strategy: { ...paid, ...lv } });
      return [v.scored, v.nodes.filter(n => n.isLeaf).map(n => n.verb).join()];
    })
  };
}"""


def first_tree(src: str) -> str:
    """El primer árbol de un script, el que pinta la pestaña."""
    lines = src.split("\n")
    at = next(k for k, line in enumerate(lines) if line.startswith("decision_tree_"))
    body = []
    for line in lines[at + 1:]:
        if line and not line[0].isspace():
            break
        body.append(line)
    return "\n".join(body)


def chosen(catalogue) -> dict:
    """Las de la prueba, del catálogo que haya: «real», de pago y de MACD, cuya vista previa pregunta por
    signal__close y macd__close y está cortada; «crafted» y «owned», otras dos de pago (la prueba pone sus
    vistas previas); «free», una gratis."""
    out = {}
    for s in catalogue:
        r = s.summary
        src = (ROOT / r["preview"].lstrip("/")).read_text(encoding="utf-8")
        tree = first_tree(src)
        macd = re.search(r"^// Technical base pattern: *MACD_ULT_MTF *$", src, re.M)
        if r["price"] == 0:
            out.setdefault("free", s)
        elif "real" not in out and macd and "if( signal__close <=" in tree and "if( macd__close <=" in tree \
                and "//return" not in tree:
            out["real"] = s
        elif "crafted" not in out:
            out["crafted"] = s
        elif "owned" not in out:
            out["owned"] = s
    assert set(out) == {"real", "crafted", "owned", "free"}, sorted(out)
    return out


def serve_preview(tab, strategy, text: str):
    """La vista previa de ``strategy``, la de la prueba."""
    tab.page.route(re.compile(".*" + re.escape(strategy.summary["preview"]) + "$"),
                   lambda route: route.fulfill(body=text, content_type="text/plain"))


def publish_levels(tab, strategy, buy, close):
    """API #3 de ``strategy`` con estos niveles, como la manda la tienda cuando catalogue/levels.json los tiene."""
    def fulfill(route):
        response = route.fetch()
        route.fulfill(response=response, json={**response.json(), "buy_at": buy, "close_at": close})
    tab.page.route(re.compile(".*/api/strategies/" + re.escape(strategy.id) + "$"), fulfill)


# Lo de la columna de los valores: sus botones y cuántas zonas de colores pintan los deslizadores.
ASIDE = """() => { const a = document.querySelector('aside'); if (!a) return null;
  return { text: a.textContent, buttons: [...a.querySelectorAll('button')].map(b => b.textContent.trim()).filter(t => t.length > 1),
           zones: [...a.querySelectorAll('span')].filter(s => s.style.opacity !== '' && s.style.top === '3px').length }; }"""


# «Resultado del árbol»: su escala (cada extremo, con dónde empieza y acaba; la barra y su fondo), sus dos ejemplos (texto,
# color y fondo) y si el signo de la puntuación se pinta delante de sus cifras (null si no lleva signo).
OUTPUT = """() => { const box = document.querySelector('aside > div'); if (!box) return null;
  const gauge = box.querySelector('[data-tree-gauge]'), bar = gauge.children[0], value = box.querySelector('strong + span');
  const rect = el => { const r = el.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.right)]; };
  const node = [...value.childNodes].find(n => n.nodeType === 3 && /\\d/.test(n.data));
  const at = i => { const r = document.createRange(); r.setStart(node, i); r.setEnd(node, i + 1); return r.getBoundingClientRect().left; };
  const sign = node.data.search(/[+−-]/), digit = node.data.search(/\\d/);
  return { labels: [...gauge.children[1].children].map(s => [s.textContent, ...rect(s)]), bar: rect(bar),
           gradient: getComputedStyle(bar).backgroundImage, value: value.textContent,
           buttons: [...box.querySelectorAll('button')].map(b => [b.textContent.trim(), getComputedStyle(b).color, getComputedStyle(b).backgroundColor]),
           signFirst: sign < 0 ? null : at(sign) < at(digit) }; }"""
TIP_TEXT = "() => { const t = document.querySelector('[role=tooltip]'); return t ? t.textContent : null; }"
NEUTRAL, GREEN, RED = "rgb(22, 38, 58)", "rgb(21, 128, 61)", "rgb(192, 57, 43)"


# La caja cuyo código empieza por arg[0] dice arg[1] (para until).
LEAF_SAYS = "(seen, arg) => Object.entries(seen.boxes).some(([k, t]) => k.startsWith(arg[0]) && t.startsWith(arg[1]))"


def wait_tree(tab) -> dict:
    tab.page.wait_for_function(READY, timeout=15000)
    return tab.page.evaluate(SEEN)


def until(tab, check: str, arg=None) -> dict:
    """Lo que se ve, cuando cumple ``check`` (JavaScript: ``(seen, arg) => …``, sobre lo de SEEN)."""
    tab.page.wait_for_function(f"([arg]) => {{ const seen = ({SEEN})(); return !!seen && ({check})(seen, arg); }}",
                               arg=[arg], timeout=15000)
    return tab.page.evaluate(SEEN)


def says(tab, text: str) -> dict:
    """Lo que se ve, cuando la pestaña dice ``text``."""
    return until(tab, "(seen, t) => seen.text.includes(t)", text)


def pinned(tab, target) -> dict:
    """La explicación que deja abierta un clic en ``target`` (la que lleva su ×). Antes, el botón a la vista: el
    navegador avisa de un desplazamiento en el cuadro siguiente, y el de Playwright al hacer clic cerraría la
    explicación recién abierta, como el de una persona."""
    target.scroll_into_view_if_needed()
    tab.page.wait_for_timeout(250)
    target.click()
    tab.page.wait_for_function("() => { const t = document.querySelector('[role=tooltip]'); return t && t.querySelector('button'); }")
    tab.page.wait_for_timeout(450)     # lo que tarda el marco en seguir el camino (follow)
    return tab.page.evaluate(TIP)


def close_tip(tab):
    tab.page.locator("[role=tooltip] button").first.click()
    tab.page.wait_for_function("() => !document.querySelector('[role=tooltip]')")


def box(seen: dict, code: str) -> str:
    """Lo que dice la caja cuyo código empieza por ``code``."""
    return next(text for label, text in seen["boxes"].items() if label.startswith(code))


def test_every_published_pattern_is_explained_and_every_name_says_its_pattern():
    bases = set()
    for path in sorted((ROOT / "static" / "assets" / "previews").glob("*.pine")):
        m = re.search(r"^// Technical base pattern:(.*)$", path.read_text(encoding="utf-8"), re.M)
        assert m, path.name
        bases |= {b.strip() for b in m.group(1).split(",") if b.strip()}
    for b in sorted(bases):
        en, es_ = (FX["patterns"].get(b) or ["", ""])[:2]
        assert en and es_, f"{b}: sin explicación en static/trees/features.json"
        missing = [lg for lg in OTHERS if not UI[lg].get("pat", {}).get(b)]
        assert not missing, f"{b}: sin explicación en {missing} (static/trees/ui.json, pat)"
    for lg in OTHERS:
        assert set(UI[lg]["pat"]) == set(FX["patterns"]), lg
        for key in ("ownFull", "ownFail", "fOwnSignIn", "fOwnNotYours", "ownedRest", "ownedLock", "ownedBtn", "whatIs"):
            assert UI[lg].get(key), (lg, key)
        # el propietario elige cualquier árbol del bosque: «el árbol completo», no «el primero»
        assert FIRST[lg] not in UI[lg]["ownFull"], (lg, UI[lg]["ownFull"])
    # la «i» de cada valor dice cuál es, en los 8 idiomas
    assert all("{f}" in text_of(lg, "whatIs") for lg in ("en", "es") + OTHERS)
    # el quinto campo: sin él, el d__close de WaveTrend saldría como la %D del RSI estocástico; y la clave de un nombre
    # que usan dos patrones lleva el suyo
    wrong = {f: e[4:] for f, e in FX["features"].items() if len(e) != 5 or e[4] not in FX["patterns"]
             or ("@" in f and f.split("@")[1] != e[4])}
    assert not wrong, wrong
    # cada valor, con su nombre en los otros seis idiomas; su descripción, en los de los siete patrones de antes (E12a)
    for lg in OTHERS:
        assert set(UI[lg]["feat"]) == set(FX["features"]) and all(UI[lg]["feat"].values()), lg
        desc = UI[lg]["featDesc"]
        assert set(desc) <= set(FX["features"]) and all(desc.values()), lg
        missing = [k for k, e in FX["features"].items() if e[4] in TRANSLATED and k not in desc]
        assert not missing, (lg, missing)
        assert all(UI[lg].get(key) for key in SCORED_TEXTS), lg
    assert all(text_of(lg, key) for lg in ("en", "es") for key in SCORED_TEXTS)
    assert all("{n}" in text_of(lg, "leadScoreN") for lg in ("en", "es") + OTHERS)
    # y lo que leen las vistas del árbol lo da tree.js (tests/test_page_code.py mira sólo views/*.js)
    values, texts = design_update.used_values(ROOT / "static" / "js" / "views" / "tree")
    given, _ = design_update.given_values(ROOT)
    assert not values - given and not texts, sorted(values - given)


def test_every_value_a_published_preview_asks_about_has_its_name():
    """E12b: cada valor por el que pregunta una vista previa publicada, y cada uno que toma su bosque (la firma de sus
    árboles: el del propietario pregunta por ellos), tiene nombre y descripción de su patrón. Un catálogo nuevo con
    un valor sin nombre falla aquí: se escribe en static/trees/features.json (en, es y su patrón, de lo que calcula
    el generador) y su nombre, en ui.json (feat, los otros seis idiomas)."""
    asked, taken = set(), set()
    for path in sorted((ROOT / "static" / "assets" / "previews").glob("*.pine")):
        src = path.read_text(encoding="utf-8")
        bases = bases_of(src)
        asked |= {(f, path.name) for f in re.findall(r"if\(\s*(\w+)\s*<=", src) if not key_of(f, bases)}
        signature = re.search(r"^decision_tree_\d+_\w*\(([^)]*)\)\s*=>", src, re.M).group(1)
        taken |= {(f.strip(), path.name) for f in signature.split(",") if f.strip() and not key_of(f.strip(), bases)}
    assert not asked, f"{len(asked)} valores sin nombre: {sorted(asked)[:10]}"
    assert not taken, f"{len(taken)} valores sin nombre: {sorted(taken)[:10]}"


def test_the_tree_tab_its_names_languages_cart_and_owner_views(real_app):
    shop = of(real_app)
    pick = chosen(shop.catalogue)
    real, crafted, owned, free = (pick[k].id for k in ("real", "crafted", "owned", "free"))
    script = shop.settings.strategies_dir / pick["owned"].private_file
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(OWNED_SCRIPT, encoding="utf-8")
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        try:
            client = mobile.sign_in(tab)
            buy(client, [real, owned])          # la de «real», sin su script en la tienda (errFileMissing)
            serve_preview(tab, pick["crafted"], CRAFTED_PREVIEW)
            serve_preview(tab, pick["owned"], OWNED_TREES)

            # comprada, pero su script no llega: el propietario ve dónde bajarlo, nunca «Comprar»
            tab.goto(f"/s/{real}/tree")
            seen = wait_tree(tab)
            assert [s for _, s in seen["tabs"][-2:]] == ["true", "false"], seen["tabs"]
            assert seen["about"] == [["es", FX["patterns"]["MACD_ULT_MTF"][1], "ltr"]], seen["about"]
            assert box(seen, "if( signal__close <=").startswith(FX["features"]["signal"][2]), seen["boxes"]
            assert box(seen, "if( macd__close <=").startswith(FX["features"]["macd"][2]), seen["boxes"]
            text = says(tab, es("ownFail"))["text"]
            assert es("unlockBtn") not in text and es("ownNotYours") not in text
            assert tab.page.evaluate(OWNER_BOX, es("ownFail")) == [es("download")]
            tip = pinned(tab, tab.page.locator(f'[data-tree-scroll] button[aria-label="{es("paid")}"]').first)
            assert tip and tip["text"] == es("ownFail") and tip["cta"] == ["×", es("download")], tip
            close_tip(tab)
            tab.page.get_by_role("tab", name=BLOCKS, exact=True).click()
            until(tab, "seen => seen.tabs.slice(-2).map(t => t[1]).join() === 'false,true'")
            tab.page.get_by_role("tab", name=es("treeTab"), exact=True).click()

            # en árabe: su explicación del patrón; la descripción de un indicador, en inglés, dicho y de izquierda
            # a derecha (en una página de derecha a izquierda, su punto final saltaba al principio)
            tab.goto(f"/s/{real}/tree?lang=ar")
            seen = wait_tree(tab)
            assert seen["about"] == [["ar", UI["ar"]["pat"]["MACD_ULT_MTF"], "rtl"]], seen["about"]
            assert box(seen, "if( signal__close <=").startswith(UI["ar"]["feat"]["signal"]), seen["boxes"]
            assert UI["ar"]["noLevels"] in seen["text"], "sin los niveles del script, lo dice"
            # la escala de «Resultado del árbol» va de izquierda a derecha, como su barra (antes, en árabe, el extremo de
            # venta quedaba bajo el verde); el + de la puntuación, delante de sus cifras, como el − (antes, «0.89+»)
            out = tab.page.evaluate(OUTPUT)
            (low, low_left, _), _, (high, _, high_right) = out["labels"]
            assert (low, high) == ("−1", "+1") and (low_left, high_right) == tuple(out["bar"]), out
            assert out["value"].lstrip("\u200e").startswith("+") and out["signFirst"] is True, out
            info = UI["ar"]["whatIs"].replace("{f}", "signal__close")
            tip = pinned(tab, tab.page.locator(f'button[aria-label="{info}"]'))
            assert tip and tip["lang"] == "ar" and tip["title"] == UI["ar"]["feat"]["signal"], tip
            assert not tip["dir"] and tip["direction"] == "rtl", tip
            assert tip["text"] == UI["ar"]["featDesc"]["signal"] + " " + UI["ar"]["relNote"], tip
            close_tip(tab)
            # la línea de WaveTrend en árabe empieza por un nombre latino: va de derecha a izquierda, como la página
            # (con dir="auto" salía de izquierda a derecha); y los nombres, también en árabe, sólo los de su patrón
            both = ("Wave_Trend_Calculation", "L_Triple_EMA")
            tab.goto(f"/s/{crafted}/tree?lang=ar")
            seen = wait_tree(tab)
            assert seen["about"] == [["ar", UI["ar"]["pat"][b], "rtl"] for b in both], seen["about"]
            assert box(seen, "if( d__close <=").startswith(UI["ar"]["feat"][WAVE_D]), seen["boxes"]
            assert box(seen, "if( ema2__close <=").startswith(UI["ar"]["feat"]["ema2"]), seen["boxes"]
            info = UI["ar"]["whatIs"].replace("{f}", "d__close")
            tip = pinned(tab, tab.page.locator(f'button[aria-label="{info}"]'))
            assert tip and tip["lang"] == "en" and tip["title"] == UI["ar"]["feat"][WAVE_D], tip
            assert tip["dir"] == "ltr" and tip["direction"] == "ltr", tip
            assert tip["text"] == FX["features"][WAVE_D][1] + " " + text_of("en", "relNote"), tip
            close_tip(tab)

            # un nombre, sólo el de un patrón de la estrategia; «Comprar para desbloquear», una vez
            tab.goto(f"/s/{crafted}/tree?lang=es")
            seen = wait_tree(tab)
            assert box(seen, "if( d__close <=").startswith(FX["features"][WAVE_D][2]), \
                "la d de WaveTrend, no la %D del RSI estocástico"
            # sin los niveles del script: la puntuación de cada resultado, sin colores de compra ni de venta, y por qué
            assert all(box(seen, f"ret := {v}").startswith(es("score")) for v in ("1.000000", "-0.200000")), seen["boxes"]
            assert es("noLevels") in seen["text"] and not [t for t in seen["boxes"].values() if t.startswith(VERBS)]
            aside = tab.page.evaluate(ASIDE)
            assert aside["buttons"][:2] == [es("hiEx"), es("loEx")] and aside["zones"] == 0, aside
            assert es("exHelpScore") in aside["text"] and es("s3Score") in tab.page.evaluate("document.body.textContent")
            # «Resultado del árbol» tampoco: su escala, −1 y +1 (sin «Venta» ni «Compra») y en gris, como los dos ejemplos;
            # la ayuda de los valores, a qué resultado llega (no qué haría); la explicación de un resultado, su puntuación
            out = tab.page.evaluate(OUTPUT)
            assert [t for t, _, _ in out["labels"]] == ["−1", "0", "+1"] and out["gradient"] == "none", out
            assert {c for _, c, _ in out["buttons"]} == {NEUTRAL}, out
            assert es("optTextScore") in aside["text"] and UI["es"]["optText"] not in aside["text"]
            assert box(seen, "if( macd__close <=").startswith("macd__close"), seen["boxes"]
            assert box(seen, "if( ema2__close <=").startswith(FX["features"]["ema2"][2]), seen["boxes"]
            assert [lang for lang, _, _ in seen["about"]] == ["es", "es"], seen["about"]
            info = es("whatIs").replace("{f}", "ema2__close")
            tip = pinned(tab, tab.page.locator(f'button[aria-label="{info}"]'))
            assert tip and tip["lang"] == "es" and tip["text"] == FX["features"]["ema2"][3] + " " + es("relNote"), tip
            close_tip(tab)
            # (después de esa explicación: con la página desplazada hasta el resultado, la × de aquélla quedaba encima de
            # otro valor, que abría la suya al cerrarla)
            leaf = tab.page.locator('[data-tree-scroll] button[aria-label^="ret := 1.0"]')
            leaf.scroll_into_view_if_needed()
            tab.page.wait_for_timeout(250)     # desplazarse cierra la explicación: antes, a la vista
            leaf.hover()
            tab.page.wait_for_function("() => !!document.querySelector('[role=tooltip]')")
            tip = tab.page.evaluate(TIP_TEXT)
            assert tip.startswith(es("score") + " +1,00") and es("leafFootScore") in tip, tip
            tab.page.mouse.move(1, 1)
            tab.page.wait_for_function("() => !document.querySelector('[role=tooltip]')")
            tab.page.get_by_role("button", name=es("unlockBtn"), exact=True).click()
            tab.page.wait_for_function(f"() => ({CART})().includes('{crafted}')")
            tab.page.locator("[data-tree-sec] button", has_text=re.compile(
                "^(" + re.escape(es("unlockBtn")) + "|" + re.escape(es("added")) + ")$")).click()
            tab.page.wait_for_timeout(300)
            assert tab.page.evaluate(CART).count(crafted) == 1, "un segundo clic no la quita"
            unit = tab.page.evaluate(UNIT, [[OWNED_SCRIPT, OLD_SCRIPT, CRAFTED_PREVIEW], CRAFTED_PREVIEW, FOREIGN_PREVIEW])
            assert unit["none"] == [es("unlockBtn"), 2] and unit["out"] == [es("unlockBtn"), 2], unit
            assert unit["in"] == [es("added"), 0], unit
            assert unit["free"] == [es("fBtn"), 2], "una gratis abre su diálogo cada vez"
            assert unit["owned"] == unit["ownedFree"] == [es("ownedBtn"), 0], "la de la cuenta, ni al carrito ni al diálogo"
            assert unit["fr"] == [{"text": UI["fr"]["pat"][b], "lang": "fr", "dir": None} for b in both], unit["fr"]
            assert unit["untranslated"] == [{"text": FX["patterns"][b][0], "lang": "en", "dir": "ltr"} for b in both]
            assert unit["foreign"] == [[FX["features"][WAVE_D][2], "macd"], [UI["fr"]["feat"][WAVE_D], "macd"],
                                       [UI["ar"]["feat"][WAVE_D], "macd"]], \
                ("un nombre traducido tampoco vale fuera de su patrón", unit["foreign"])
            assert unit["levels"] == [{"buy": 0.8, "close": -0.5}, {"buy": 0.6, "close": -0.7},
                                      {"buy": 0.55, "close": -0.9}], unit["levels"]
            assert unit["published"] == [[True, ",".join([es("score")] * 6)],
                                         [False, ",".join((BUY, BUY, WAIT, SELL, SELL, BUY))],
                                         [False, ",".join((BUY, BUY, WAIT, WAIT, WAIT, BUY))]], unit["published"]

            # el propietario, con los niveles de su script (0,8 y −0,5); el visitante, sin los que publica la tienda,
            # con la puntuación de cada resultado
            tab.goto(f"/s/{owned}/tree")
            seen = says(tab, es("ownFull"))
            assert "primer" not in es("ownFull")
            assert box(seen, "ret := 0.700000").startswith(WAIT) and box(seen, "ret := -0.600000").startswith(SELL)
            assert box(seen, "if( BBlower__close <=").startswith(FX["features"]["BBlower"][2])
            tab.page.locator("[data-tree-sec] button", has_text=re.compile("^2$")).click()
            seen = says(tab, es("treeOf").replace("{n}", "2"))
            assert box(seen, "ret := 0.900000").startswith(BUY) and box(seen, "ret := -1.000000").startswith(SELL)
            assert tab.page.evaluate(OWNER_BOX, es("ownFull")) == [es("download")], "el árbol 2, completo también"
            tab.page.get_by_role("button", name=es("visitor"), exact=True).click()
            seen = until(tab, LEAF_SAYS, ["ret := 0.700000", es("score")])
            assert box(seen, "ret := -0.600000").startswith(es("score")), "nunca 0,55 y −0,9 para el visitante"
            assert es("noLevels") in seen["text"]
            # con los que publica la tienda (0,6 y −0,5): ni los del propietario ni los de 2024
            publish_levels(tab, pick["owned"], 0.6, -0.5)
            tab.goto(f"/s/{owned}/tree")
            says(tab, es("ownFull"))
            tab.page.get_by_role("button", name=es("visitor"), exact=True).click()
            seen = until(tab, LEAF_SAYS, ["ret := 0.700000", BUY])
            verbs = [next((w for w in VERBS if box(seen, f"ret := {v}").startswith(w)), None)
                     for v in ("0.700000", "0.100000", "-0.600000")]
            assert verbs == [BUY, WAIT, SELL], seen["boxes"]
            aside = tab.page.evaluate(ASIDE)
            assert es("noLevels") not in seen["text"] and aside["zones"] > 0
            # con ellos, «Resultado del árbol» es el del diseño: venta y compra en su escala, verde y rojo en los ejemplos
            out = tab.page.evaluate(OUTPUT)
            assert [t for t, _, _ in out["labels"]] == [es("sellEnd"), "0", es("buyEnd")] and "gradient" in out["gradient"]
            assert [c for _, c, _ in out["buttons"]][:2] == [GREEN, RED], out
            assert UI["es"]["optText"] in aside["text"] and es("optTextScore") not in aside["text"]

            # una gratis que la cuenta no tiene: pedirla, no comprarla
            tab.goto(f"/s/{free}/tree")
            wait_tree(tab)
            tab.page.get_by_role("button", name=es("owner"), exact=True).click()
            says(tab, es("fOwnNotYours"))
            assert tab.page.evaluate(OWNER_BOX, es("fOwnNotYours")) == [es("fBtn")]
            assert tab.problems() == [f"404 GET /api/mine/{real}/script"], "sólo el script que falta, a propósito"
        finally:
            tab.close()
            script.unlink()
        # sin sesión, la gratis dice con qué entrar y que se pide
        tab = mobile.open_page(chromium, live, "laptop")
        try:
            tab.context.add_cookies([{"name": "zt_consent", "value": "none", "domain": "127.0.0.1", "path": "/"}])
            tab.goto(f"/s/{free}/tree")
            wait_tree(tab)
            tab.page.get_by_role("button", name=es("owner"), exact=True).click()
            says(tab, es("fOwnSignIn"))
            assert tab.page.evaluate(OWNER_BOX, es("fOwnSignIn")) == [es("signIn"), es("fBtn")]
            assert tab.problems() == []
        finally:
            tab.close()


def test_on_a_phone_a_tapped_question_keeps_its_explanation_while_the_page_moves(real_app):
    crafted = chosen(of(real_app).catalogue)["crafted"]
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "phone")
        try:
            mobile.sign_in(tab)
            serve_preview(tab, crafted, CRAFTED_PREVIEW)
            tab.goto(f"/s/{crafted.id}/tree")
            wait_tree(tab)
            frame = tab.page.locator("[data-tree-scroll]")
            # el árbol sigue el camino de la compra más fuerte, cuatro pasos a la derecha; se vuelve al principio
            tab.page.wait_for_function("() => document.querySelector('[data-tree-scroll]').scrollLeft > 0")
            frame.scroll_into_view_if_needed()
            frame.evaluate("el => { el.scrollLeft = 0; }")
            tab.page.wait_for_timeout(250)
            # un toque (sin que Playwright mueva nada antes) en la pregunta de la otra rama: los deslizadores de
            # encima cambian (el navegador sube la página para dejar la caja donde estaba) y el camino acaba fuera
            # de la vista (el marco se va hacia allí)
            question = tab.page.locator('[data-tree-scroll] button[aria-label^="if( ema2__close <= 0.95"]').bounding_box()
            area = frame.bounding_box()
            assert area["x"] <= question["x"] and question["x"] + question["width"] <= area["x"] + area["width"], (question, area)
            assert tab.page.evaluate("() => matchMedia('(hover: none)').matches")
            tab.page.touchscreen.tap(question["x"] + question["width"] / 2, question["y"] + question["height"] / 2)
            tab.page.wait_for_function("() => document.querySelector('[data-tree-scroll]').scrollLeft > 0")
            tab.page.wait_for_timeout(600)
            tip = tab.page.evaluate(TIP)
            assert tip and tip["title"] == FX["features"]["ema2"][2], f"la explicación se cerró al moverse la página: {tip}"
            assert tab.problems() == []
        finally:
            tab.close()
