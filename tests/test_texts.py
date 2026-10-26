# -*- coding: utf-8 -*-
"""Los textos de la tienda en sus 8 idiomas (W2, 2026-10-26).

- E12a: cada indicador de ``catalogue/indicators.csv`` se explica en los 8 idiomas (``Explanation`` es la inglesa;
  ``Explanation_es``…``_hi``, las otras siete) y la API manda la del idioma de la petición (``ind_text``) y dice cuál es
  (``ind_lang``); sólo una que faltara saldría en inglés (``ind_lang`` = en), y la página la marcaría.
- E12d: el rango de la profundidad del árbol dice «Tree depth» en inglés.
- E12c: en árabe, un signo va delante de su cifra o detrás de su nombre latino, el % de %K delante de la K y una
  fórmula latina entera, de izquierda a derecha (una marca LRM o un aislamiento LRI…PDI; sin ella, el algoritmo bidi
  pinta «1−», «+VI», «K%»); en chino, la puntuación es la de ancho completo; en hindi, la frase acaba en «।».
- Los plurales árabes: lo que cuenta lleva la forma que pide el número (3–10, el plural: «9 صفقات»; 11–99, el
  singular: «36 صفقة»), también en la nota de cada estrategia (``gradeTip``), en sus operaciones (``tradesWord``), entre
  cuántas se eligieron (``riskTried``, por las probadas) y en los cortes de la nota (``gradeCuts``, por el de la A).
"""
import csv
import json
import re

from zlecitool_core.testing import mobile

from edgefolio.catalogue import Catalogue
from edgefolio.settings import ROOT
from tests.test_listing_page import CARDS, RISK, SEEN

UI = json.loads((ROOT / "i18n" / "ui.json").read_text(encoding="utf-8"))
TREES = json.loads((ROOT / "static" / "trees" / "ui.json").read_text(encoding="utf-8"))
LANGS = UI["_languages"]
with open(ROOT / "catalogue" / "indicators.csv", encoding="utf-8", newline="") as f:
    INDICATORS = list(csv.DictReader(f))
LRM, LRI, PDI = "\u200e", "\u2066", "\u2069"
AR = "\u0600-\u06ff"                  # las letras y los signos árabes


def explanations(row: dict) -> dict:
    return {"en": row["Explanation"], **{lang: row.get(f"Explanation_{lang}", "") for lang in LANGS if lang != "en"}}


def texts(value):
    """Las cadenas de un texto (o de un plural, o de un diccionario anidado)."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from texts(v)


def in_language(lang: str) -> list:
    """(dónde, texto) de cada texto de ``lang``: la tienda, la pestaña del árbol y las explicaciones de los indicadores."""
    out = [(f"i18n {k}", t) for k, v in UI.items() if not k.startswith("_") for t in texts(v.get(lang))]
    out += [(f"trees {lang}", t) for t in texts(TREES.get(lang, {}))]
    out += [(f"indicators {r['Key']}", explanations(r)[lang]) for r in INDICATORS]
    return out


def bidi_hazards(text: str) -> list:
    """Lo que el algoritmo bidi pinta al revés en un párrafo árabe (lo aislado con LRI…PDI ya va bien)."""
    t = re.sub(LRI + ".*?" + PDI, "", text)
    found = re.findall(r"(?:^|[\s(" + AR + r"،:])[+\-−]\d", t)                     # «من −1»: «1−»
    found += re.findall(r"[A-Za-z][+\-−](?=$|[\s)" + AR + r"،.:؛])", t)            # «VI+ (…»: «+VI»
    found += re.findall(r"(?:^|[\s(" + AR + r"])%[A-Za-z]", t)                     # «خط %K»: «K%»
    found += re.findall(r"(?:^|[\s(" + AR + r":،])\d+(?:\.\d+)?\s*[×÷*/+\-−]\s*[A-Za-z]", t)  # «3 × ema1 − …»
    return found


def test_every_indicator_explains_itself_in_the_8_languages():
    keys = {r["Key"] for r in INDICATORS}
    sold = {s.key_techs for s in Catalogue(ROOT / "catalogue" / "catalogue.csv")}
    assert sold <= keys, f"indicadores del catálogo sin explicación: {sorted(sold - keys)}"
    for row in INDICATORS:
        said = explanations(row)
        assert all(said.values()), (row["Key"], [lang for lang, t in said.items() if not t])
        assert len(set(said.values())) == len(LANGS), (row["Key"], "una sin traducir")
        # la árabe empieza por una palabra árabe y la china y la hindi acaban como acaban sus frases
        assert re.match("[" + AR + "]", said["ar"]) and said["zh"].endswith("。") and said["hi"].endswith("।"), row["Key"]


def test_the_api_explains_each_indicator_in_the_language_asked(real_app):
    row = next(r for r in INDICATORS if r["Key"] == "1BOL")
    said = explanations(row)
    client = real_app.test_client()
    for lang in LANGS:
        listed = client.get(f"/api/strategies?q=1BOL&size=1&lang={lang}").json["rows"][0]
        detail = client.get(f"/api/strategies/{listed['id']}?lang={lang}").json
        assert (listed["ind_text"], listed["ind_lang"]) == (detail["ind_text"], detail["ind_lang"]) == (said[lang], lang)
    # sin ?lang=, el de la petición: el del navegador (Accept-Language), si no hay cookie ni cuenta (?lang= deja la
    # suya, como en una página: por eso, otro navegador)
    german = real_app.test_client().get("/api/strategies?q=1BOL&size=1", headers={"Accept-Language": "de-DE,de;q=0.9"}).json
    assert german["rows"][0]["ind_lang"] == "de" and german["rows"][0]["ind_text"] == said["de"]


def test_an_untranslated_explanation_is_english_and_says_so(tmp_path):
    """Un indicador nuevo del generador, aún sin su traducción a un idioma: la inglesa, y ind_lang lo dice."""
    folder = tmp_path / "catalogue"
    folder.mkdir()
    (folder / "catalogue.csv").write_text((ROOT / "catalogue" / "catalogue.csv").read_text(encoding="utf-8"), encoding="utf-8")
    with open(folder / "indicators.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Key", "Explanation", "Explanation_es"])
        w.writeheader()
        w.writerow({"Key": "1BOL", "Explanation": "In English.", "Explanation_es": "En español."})
    catalogue = Catalogue(folder / "catalogue.csv")
    s = next(x for x in catalogue if x.key_techs == "1BOL")
    assert [(catalogue.row(s, lang)["ind_text"], catalogue.row(s, lang)["ind_lang"]) for lang in ("es", "en", "ar")] == [
        ("En español.", "es"), ("In English.", "en"), ("In English.", "en")]
    other = next(x for x in catalogue if x.key_techs != "1BOL")
    assert (catalogue.row(other, "ar")["ind_text"], catalogue.detail(other, "ar")["ind_lang"]) == ("", "ar")


def test_arabic_draws_signs_names_and_formulas_the_right_way_round():
    found = [(where, text, bidi_hazards(text)) for where, text in in_language("ar") if bidi_hazards(text)]
    assert not found, found[:5]
    # y lo que la revisión tuvo que marcar sigue marcado
    assert TREES["ar"]["sellEnd"] == f"بيع {LRM}−1" and TREES["ar"]["buyEnd"] == f"شراء {LRM}+1"
    assert TREES["ar"]["feat"]["k"] == f"خط {LRM}%K" and TREES["ar"]["feat"]["diPlus"].startswith(f"DI+{LRM}")


def test_the_tree_depth_range_says_tree_depth():
    """E12d: el rango de Pro dice «Tree depth» en inglés. «Tree Deep» es el nombre de la columna del catálogo (el
    contrato con el generador), que no se enseña."""
    assert UI["fTreeDepth"]["en"] == "Tree depth"
    assert "Tree Deep" not in [t for v in UI.values() if isinstance(v, dict) for t in texts(v)]


def test_chinese_and_hindi_punctuation():
    cjk = "[一-鿿]"
    half = [(w, t) for w, t in in_language("zh") if re.search(cjk + r"[,:;?!()]|[,:;?!()]" + cjk, t)]
    assert not half, half[:5]
    # «你», el trato de toda la tienda; ningún «您»
    assert not [(w, t) for w, t in in_language("zh") if "您" in t]
    period = [(w, t) for w, t in in_language("hi") if re.search(r"[ऀ-ॿ]\.(\s|$)", t)]
    assert not period, period[:5]


def test_arabic_counts_take_the_form_their_number_asks_for():
    forms = ("zero", "one", "two", "few", "many", "other")
    for key in ("gradeTip", "tradesWord", "riskTried", "gradeCuts", "nStrategies"):
        assert set(UI[key]["ar"]) == set(forms), key
    assert "{n} صفقات" in UI["gradeTip"]["ar"]["few"] and "{n} صفقة" in UI["gradeTip"]["ar"]["many"]
    assert (UI["tradesWord"]["ar"]["few"], UI["tradesWord"]["ar"]["many"]) == ("صفقات", "صفقة")
    assert "{m} استراتيجيات" in UI["riskTried"]["ar"]["few"] and "{m} استراتيجية" in UI["riskTried"]["ar"]["many"]
    assert "{a} صفقات" in UI["gradeCuts"]["ar"]["few"] and "{a} صفقة" in UI["gradeCuts"]["ar"]["other"]
    for key, few, many in (("rulesN", "قواعد", "قاعدة"), ("visible", "نتائج", "نتيجة"), ("complete", "نتائج", "نتيجة"),
                           ("paidN", "فروع", "فرعًا"), ("ctaN", "فروع", "فرعًا"), ("fPaidN", "فروع", "فرعًا"),
                           ("fCtaN", "فروع", "فرعًا")):
        entry = TREES["ar"][key]
        assert set(entry) == set(forms) and few in entry["few"] and many in entry["many"], key
    # en español, «1 operación» y «2 operaciones»
    assert UI["tradesWord"]["es"] == {"one": "operación", "other": "operaciones"}
    assert UI["gradeTip"]["es"]["one"].startswith("Muestra: {n} operación cerrada.")


def few(n: int) -> bool:
    """La forma de 3–10 (y 103–110…) del árabe."""
    return 3 <= n % 100 <= 10


# Las operaciones de cada ficha de Lite: su número y la palabra que lo sigue.
TRADES = """() => [...document.querySelectorAll('#app button')].map(b => [b.querySelector('strong'), b])
  .filter(([s, b]) => s && b.querySelector('i.fa-circle-question') && /^\\d+$/.test(s.textContent))
  .map(([s, b]) => [s.textContent, b.textContent.slice(s.textContent.length).trim()])"""


def test_arabic_lite_counts_with_the_right_form(real_app):
    ar = {k: v["ar"] for k, v in UI.items() if not k.startswith("_")}
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(SEEN)
            tried = {"n": 1531, "cuts": [100, 50, 25]}

            def config(route):
                response = route.fetch()
                route.fulfill(response=response, json={**response.json(), "tried": tried["n"], "grade_cutoffs": tried["cuts"]})
            page.route(re.compile(r".*/api/config$"), config)
            tab.goto("/?lang=ar")
            page.wait_for_function(f"() => ({TRADES})().length > 5")
            cards = page.evaluate(TRADES)
            assert {few(int(n)) for n, _ in cards} == {True, False}, "la primera página tiene de las dos"
            assert all(word == (ar["tradesWord"]["few"] if few(int(n)) else ar["tradesWord"]["many"]) for n, word in cards), cards
            tips = [tip for _, tip, _ in page.evaluate(CARDS)]
            for tip in tips:
                n = int(re.search(r"\d+", tip).group(0))
                form = ar["gradeTip"]["few" if few(n) else "many"].replace("{n}", str(n))
                assert tip.startswith(form) and ar["gradeCuts"]["other"].replace("{a}", "100").replace("{b}", "50").replace(
                    "{c}", "25") in tip, tip
            # entre cuántas se eligieron: 1531, en singular; 1503, en plural
            m = page.evaluate("() => new Intl.NumberFormat('ar-u-nu-latn').format(1531)")
            assert f"من بين {m} استراتيجية جرى" in page.evaluate(RISK)[0], page.evaluate(RISK)
            tried.update(n=1503, cuts=[10, 5, 3])
            tab.goto("/?lang=ar")
            page.wait_for_function(f"() => ({RISK})().length && ({RISK})()[0].includes('استراتيجيات جرى')")
            # y los cortes de la nota, con una A desde 10: «10 صفقات»
            page.wait_for_function(f"() => ({CARDS})().length > 0")
            assert all("A: 10 صفقات فأكثر" in tip for _, tip, _ in page.evaluate(CARDS))
            assert tab.problems() == []
        finally:
            tab.close()
