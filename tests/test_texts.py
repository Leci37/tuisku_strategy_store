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
- Lo que cuenta un ajuste (los días y las descargas de un enlace, DOWNLOAD_DAYS y MAX_DOWNLOADS; las estrategias de un
  pack, PACK_SIZE) o el catálogo (las de un lote): cada cuenta con su clave y su forma (``linkDays``,
  ``linkDownloads``), en los correos (el recibo, la gratis, los avisos) y en la página (la fila de confianza, Gracias,
  el aviso de un pack): en árabe, con 1, 2, 3, 11 y 100; en los demás, con 1 y con 7. Antes, cada texto valía sólo para
  los 7 días y las 10 descargas de hoy.
- Revisión de W2: la explicación de cada indicador dice lo que calcula su código en el generador
  (``TW_pines_script/pines_script/*.py``) y no promete nada (antes, 1TMA hablaba de una media triangular con bandas, y
  1BOL, 1WIL y 1ULT de señales «fiables» y «precisas»); una combinada nombra sólo lo que usa (``Key Combination``); y
  una misma cosa lleva la misma palabra en la explicación, en el árbol y en sus variables (el momentum, el envolvente).
- La API manda la explicación en el idioma que pide la página (``?ind_lang=``) sin tocar la cookie del idioma
  (``?lang=`` la cambia: el núcleo lo toma por la dirección de una página en un idioma).
"""
import csv
import json
import re

from zlecitool_core.testing import mobile

from edgefolio.catalogue import Catalogue
from edgefolio.search import Index
from edgefolio.settings import ROOT
from tests.conftest import outbox
from tests.test_free import claim, free_file  # noqa: F401 (free_file es un fixture)
from tests.test_listing_page import CARDS, RISK, SEEN
from tests.test_receipt import pay

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
        r = client.get(f"/api/strategies?q=1BOL&size=1&ind_lang={lang}")
        listed = r.json["rows"][0]
        detail = client.get(f"/api/strategies/{listed['id']}?ind_lang={lang}").json
        assert (listed["ind_text"], listed["ind_lang"]) == (detail["ind_text"], detail["ind_lang"]) == (said[lang], lang)
        # sin tocar la cookie del idioma: con ?lang=, cada lista de una pestaña en otro idioma cambiaba el de la visita
        # siguiente
        assert not [c for c in r.headers.getlist("Set-Cookie") if c.startswith("zt_lang=")], r.headers.getlist("Set-Cookie")
    # sin ?ind_lang=, el de la petición: ?lang= (como una página), o el del navegador (Accept-Language) si no hay cookie
    # ni cuenta; uno que la tienda no habla no cuenta
    assert real_app.test_client().get("/api/strategies?q=1BOL&size=1&lang=fr").json["rows"][0]["ind_lang"] == "fr"
    german = real_app.test_client().get("/api/strategies?q=1BOL&size=1&ind_lang=xx",
                                        headers={"Accept-Language": "de-DE,de;q=0.9"}).json
    assert german["rows"][0]["ind_lang"] == "de" and german["rows"][0]["ind_text"] == said["de"]


# Lo que una explicación no puede decir en una tienda de estrategias con backtest: promesas («fiable», «preciso», «da
# oportunidades»). Por idioma, la raíz.
PROMISES = {"en": r"reliab|accura|powerful|profit|better insight|more informed|suitable for|opportunit",
            "es": r"fiable|precis|rentab|oportunidad", "pt": r"fiáve|precis|rentáve|oportunidade",
            "fr": r"fiable|précis|rentab|opportunit", "de": r"zuverlässig|genauer|profitab|Gelegenheit|chance",
            "zh": r"可靠|准确|机会", "ar": r"موثوق|أدق|فرص", "hi": r"भरोसेमंद|सटीक|मौक़े|मौके"}


def test_the_explanations_say_what_the_code_computes_and_promise_nothing():
    """Cada explicación, de lo que calcula su indicador en el generador (TW_pines_script/pines_script/*.py) y de cómo
    se lee, sin prometer nada. 1TMA es TMA_Overlay.py: cuatro medias suavizadas (SMMA) de 21, 50, 100 y 200 velas, la
    media de 2 velas, el three-line strike y las envolventes; ni una media triangular ni bandas."""
    for row in INDICATORS:
        for lang, said in explanations(row).items():
            assert not re.search(PROMISES[lang], said, re.I), (row["Key"], lang, said)
    tma = next(r for r in INDICATORS if r["Key"] == "1TMA")
    en = tma["Explanation"]
    assert all(x in en for x in ("SMMA", "21, 50, 100 and 200", "2-bar", "three-line strike", "engulfing")), en
    assert "band" not in en.lower()
    assert not [v for v in tma.values() if re.search("riangula|triangulaire|dreieckig|三角|المثلث|ट्रायंगुलर", v)], tma
    assert tma["Full Indicator Name"] == "TMA Overlay"
    # 1ULT: la segunda media (50) y el resaltado de las velas que cruzan una media son opcionales en el script
    # (doma2 y spc, apagados): «puede añadir», no «dibuja»
    ult = next(r for r in INDICATORS if r["Key"] == "1ULT")["Explanation"]
    assert "can add a second one over 50 bars" in ult and "It can also highlight the bars" in ult, ult


def test_a_combination_names_only_what_it_uses():
    """«Key Combination» nombra sólo indicadores que la combinación usa (su «Associated Function», la de
    TW_tech_Class.py): 2MM0 es MA Cross + Money Flow Index y decía 1M00|1SMA (Smart Money Concepts); 2BB0, Bollinger
    Bands + Bull Bear Power, decía 1B00|1BOL (Bollinger RSI Double Strategy). Una parte sin clave propia en el catálogo
    se deja fuera. Y la explicación de una combinada lleva, en cada idioma, la de cada parte que tiene clave."""
    functions = {r["Key"]: {f.strip() for f in r["Associated Function"].split(",")} for r in INDICATORS}
    by_key = {r["Key"]: r for r in INDICATORS}
    for row in INDICATORS:
        parts = row["Key Combination"].split("|")
        assert all(p in functions and functions[p] <= functions[row["Key"]] for p in parts), (row["Key"], parts)
        if not row["Key"].startswith("2"):
            continue
        for lang, said in explanations(row).items():
            for p in parts:
                part = explanations(by_key[p])[lang]
                # (en alemán, la segunda va detrás de «Außerdem», con el verbo delante: sólo se mira la primera)
                if lang != "de" or said.startswith("Dieser kombinierte Indikator vereint zwei Indikatoren. " + part):
                    assert part[1:] in said, (row["Key"], lang, p)   # [1:]: «El indicador…» es «Además, el indicador…»
        assert "Additionally, The" not in row["Explanation"] and "Außerdem gilt" not in row["Explanation_de"]


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


def test_the_indicator_is_named_like_its_explanation_and_link(tmp_path):
    """El nombre que se enseña sale de indicators.csv, como la explicación y el enlace: la fila del catálogo trae el
    del generador, que puede quedarse atrás (1ICH decía «Ichimoku Oscillator» y su código es la nube). Sin nombre en
    indicators.csv, el de la fila. Y con él se busca y se filtra."""
    folder = tmp_path / "catalogue"
    folder.mkdir()
    (folder / "catalogue.csv").write_text((ROOT / "catalogue" / "catalogue.csv").read_text(encoding="utf-8"), encoding="utf-8")
    with open(folder / "indicators.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Key", "Full Indicator Name", "Explanation"])
        w.writeheader()
        w.writerow({"Key": "1BOL", "Full Indicator Name": "Bollinger Bands and RSI", "Explanation": "In English."})
        w.writerow({"Key": "1MAD", "Full Indicator Name": "", "Explanation": "In English."})
    catalogue = Catalogue(folder / "catalogue.csv")
    bol = next(x for x in catalogue if x.key_techs == "1BOL")
    mad = next(x for x in catalogue if x.key_techs == "1MAD")
    assert bol.row["Full Indicator Name"] == "Bollinger RSI Double Strategy"
    assert catalogue.row(bol)["ind"] == catalogue.detail(bol)["ind"] == "Bollinger Bands and RSI"
    assert catalogue.row(mad)["ind"] == mad.row["Full Indicator Name"] == "Madrid Moving Average Ribbon"
    index = Index(catalogue)
    assert index.labels["ind"]["1BOL"][0] == "1BOL – Bollinger Bands and RSI"
    assert any("bollinger bands and rsi" in t for t in index.text)


def test_each_indicator_links_to_what_its_code_computes():
    """El enlace y el autor de cada indicador son los de su script en TradingView, el que lista el generador como
    fuente (``TW_pines_script/pines_script/_links.txt``): 1MAC es el CM_MacD_Ult_MTF de ChrisMoody (llevaba a la
    estrategia MACD + SMA 200 de ChartArt), 1SMA el de LuxAlgo (llevaba a la estrategia de Uncle Sam) y 1ICH, cuyo
    código es la nube de Ichimoku de TradingView (``ichimoku_cloud.py``), la nube y no el oscilador. Un solo dominio
    para todos los idiomas: es.tradingview.com enseña TradingView en español a todos. (Una combinada no tiene página:
    «--», y lleva a la lista de scripts.)"""
    by_key = {r["Key"]: r for r in INDICATORS}
    assert (by_key["1MAC"]["Author"], by_key["1MAC"]["Traderview URL Indicator"]) == (
        "ChrisMoody", "https://www.tradingview.com/script/OQx7vju0-MacD-Custom-Indicator-Multiple-Time-Frame-All-Available-Options/")
    assert by_key["1SMA"]["Traderview URL Indicator"] == "https://www.tradingview.com/script/CnB3fSph-Smart-Money-Concepts-SMC-LuxAlgo/"
    assert (by_key["1ICH"]["Full Indicator Name"], by_key["1ICH"]["Traderview URL Indicator"]) == (
        "Ichimoku Cloud", "https://www.tradingview.com/scripts/ichimokuclouds/")
    assert by_key["1KON"]["Author"] == "manboto"
    pages = {r["Key"]: r["Traderview URL Indicator"] for r in INDICATORS if not r["Key"].startswith("2")}
    assert all(u.startswith("https://www.tradingview.com/") for u in pages.values()), pages
    assert {r["Traderview URL Indicator"] for r in INDICATORS if r["Key"].startswith("2")} == {"--"}


# Lo que dice cada número de un enlace (días, descargas) y de un lote (estrategias), en cada idioma: en árabe, el
# dual de 2, el plural de 3 a 10 y el singular de 11 a 99 y de 100 (en genitivo: van tras «لمدة», «حتى» y «مقابل»).
COUNTED = {
    "ar": {1: ("يوم واحد", "تنزيل واحد", "مقابل استراتيجية واحدة"), 2: ("يومين", "تنزيلين", "مقابل استراتيجيتين"),
           3: ("3 أيام", "3 تنزيلات", "مقابل 3 استراتيجيات"), 11: ("11 يومًا", "11 تنزيلًا", "مقابل 11 استراتيجية"),
           100: ("100 يوم", "100 تنزيل", "مقابل 100 استراتيجية")},
    "es": {1: ("1 día", "1 descarga", "por 1 estrategia."), 7: ("7 días", "7 descargas", "por 7 estrategias.")},
    "en": {1: ("1 day", "1 download", "for 1 strategy."), 7: ("7 days", "7 downloads", "for 7 strategies.")},
    "pt": {1: ("1 dia", "1 download", "por 1 estratégia."), 7: ("7 dias", "7 downloads", "por 7 estratégias.")},
    "fr": {1: ("1 jour", "1 téléchargement", "pour 1 stratégie."), 7: ("7 jours", "7 téléchargements", "pour 7 stratégies.")},
    "de": {1: ("1 Tag", "1 Download", "für 1 Strategie."), 7: ("7 Tage", "7 Downloads", "für 7 Strategien.")},
    "zh": {1: ("1 天", "1 次", "1 个策略共"), 7: ("7 天", "7 次", "7 个策略共")},
    "hi": {1: ("1 दिन", "1 डाउनलोड", "1 रणनीति $"), 7: ("7 दिन", "7 डाउनलोड", "7 रणनीतियाँ $")},
}
# Y cómo lo dice la frase de los enlaces del recibo y de la gratis, con las dos cuentas en su sitio.
LINKS_LINE = {"ar": "لمدة {days} وحتى {downloads}", "es": "{days} y hasta {downloads}", "en": "{days} and up to {downloads}",
              "pt": "{days} e até {downloads}", "fr": "{days} et ", "de": "{days} und für bis zu {downloads}",
              "zh": "{days}", "hi": "{days} "}


def test_the_mails_count_days_downloads_and_strategies_in_the_form_of_each_number(app, client, settings, shop,
                                                                                  free_file):
    """El recibo y la gratis dicen los días y las descargas de sus enlaces (DOWNLOAD_DAYS, MAX_DOWNLOADS: ajustes) y
    el aviso de un lote, sus estrategias, con la forma que pide cada número (el núcleo la elige con n). Antes, en
    árabe, «{n} أيام» y «{m} تنزيلات» sólo valían de 3 a 10, y en los demás idiomas «1 days»."""
    sent = 0
    for lang, cases in COUNTED.items():
        for n, (days, downloads, strategies) in cases.items():
            settings.download_days = settings.max_downloads = n
            before = len(outbox("buyer@example.com"))      # quien paga en el PayPal de prueba
            pay(client, {"items": ["AAPL_1Day_1ADX_aaaa1111"]}, lang=lang)
            mails = outbox("buyer@example.com")
            assert len(mails) == before + 1, (lang, n)
            body = mails[-1]["body"]
            line = LINKS_LINE[lang].format(days=days, downloads=downloads)
            assert days in body and downloads in body and line in body, (lang, n, body)
            if lang in ("ar", "es"):     # (la gratis tiene un tope por dirección y por hora)
                sent += 1
                assert claim(client, email=f"n{sent}@example.com", lang=lang).status_code == 200
                body = outbox(f"n{sent}@example.com")[-1]["body"]
                assert days in body and downloads in body and line in body, (lang, n, body)
            with app.app_context():
                alert = shop.texts.get("mailAlertBundle", lang, name="Tesla", ticker="TSLA", code="1C00", bundle="Duo",
                                       price="$90.00", n=n, url="u")
            assert strategies in alert, (lang, n, alert)
    settings.download_days, settings.max_downloads = 7, 10


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


# Una misma cosa, con la misma palabra en la explicación del indicador, en el árbol (lo que es el patrón) y en sus
# variables: el momentum (MACD, WaveTrend, Squeeze) y el envolvente (TMA Overlay); en árabe, el nombre del ADX y la
# barra del Williams Vix Fix (عمود, la barra de un histograma; شريط es la cinta de Madrid).
TERMS = {"pt": ("impulso", "engolfo"), "fr": ("momentum", "avalement"), "de": ("momentum", "engulfing"),
         "zh": ("动能", "吞没"), "ar": ("زخم", "ابتلاع"), "hi": ("मोमेंटम", "एनगल्फ़िंग")}
OTHER_WORDS = {"fr": ("élan",), "de": ("Schwung",), "hi": ("गति",)}


def test_one_word_for_each_thing_in_the_indicator_and_its_tree():
    explained = {row["Key"]: explanations(row) for row in INDICATORS}
    for lang, (momentum, engulfing) in TERMS.items():
        tree = TREES[lang]
        moving = [tree["pat"]["MACD_ULT_MTF"], tree["featDesc"]["hist"], tree["featDesc"]["val"],
                  tree["pat"]["Wave_Trend_Calculation"], explained["1MAC"][lang], explained["1WAV"][lang],
                  explained["1SQU"][lang]]
        assert all(momentum in text.lower() for text in moving), (lang, [t for t in moving if momentum not in t.lower()])
        assert not [t for t in moving for word in OTHER_WORDS.get(lang, ()) if word in t], lang
        candles = [tree["pat"]["TMA_Overlay"], tree["feat"]["bullishEngulfingInt"], tree["feat"]["bearishEngulfingInt"],
                   explained["1TMA"][lang], explained["1CAN"][lang]]
        assert all(engulfing in text.lower() for text in candles), (lang, [t for t in candles if engulfing not in t.lower()])
    ar = TREES["ar"]
    assert ar["featDesc"]["adx"].startswith("مؤشر متوسط الاتجاه:") and "(مؤشر متوسط الاتجاه)" in explained["1ADX"]["ar"]
    assert ar["feat"]["colInt"].startswith("عمود ") and "العمود" in ar["featDesc"]["colInt"]


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


def test_arabic_links_and_packs_count_with_the_right_form_in_the_page(real_app):
    """En la página, lo que cuenta un ajuste: la fila de confianza bajo «Pagar» (DOWNLOAD_DAYS, MAX_DOWNLOADS), la nota
    de los enlaces en Gracias y el aviso de un pack que no vale (PACK_SIZE). Antes, «الروابط لمدة 7 أيام وحتى 10
    تنزيلات» llevaba sus números escritos, y con otros ajustes decía «11 أيام» o «2 تنزيلات»."""
    rows = real_app.test_client().get("/api/strategies?paid=1&size=2").json["rows"]
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            cart = json.dumps({"cart": [rows[0]["id"]], "bundles": [], "packIds": [], "code": "", "applied": ""})
            page.add_init_script(SEEN + "try { localStorage.setItem('edgefolio-cart-v1', %s); } catch (e) {}" % json.dumps(cart))

            def config(route):
                response = route.fetch()
                route.fulfill(response=response, json={**response.json(), "download_days": 11, "max_downloads": 2})
            page.route(re.compile(r".*/api/config$"), config)
            page.route(re.compile(r".*/api/quote$"),
                       lambda route: route.fulfill(status=400, json={"error": "errPackSize", "vars": {"n": 5}}))
            tab.goto("/?lang=ar")
            page.get_by_text("الروابط لمدة 11 يومًا وحتى تنزيلين").wait_for()
            page.locator("[data-ef-toast]").wait_for()
            # con 5 (el PACK_SIZE de siempre), el plural; sin la cuenta, la forma «other»: «5 استراتيجية»
            assert "تحتاج الباقة إلى 5 استراتيجيات مدفوعة مختلفة بالضبط." in page.locator("[data-ef-toast]").inner_text()
            assert tab.problems() == ["400 POST /api/quote"], tab.problems()
        finally:
            tab.close()
        for days, downloads, note in ((2, 11, "كل رابط صالح لمدة يومين وحتى 11 تنزيلًا."),
                                      (1, 100, "كل رابط صالح لمدة يوم واحد وحتى 100 تنزيل.")):
            tab = mobile.open_page(chromium, live, "laptop")
            page = tab.page
            try:
                body = json.dumps({"order_id": "FAKE-AR", "status": "PAID", "total": "146.00", "currency": "USD",
                                   "payer": "b•••@example.com", "valid_days": days, "max_downloads": downloads,
                                   "download_all": "/api/download/all?t=x", "links_hidden": False, "paid_now": False,
                                   "downloads": [{**r, "url": "/api/download/x", "zip": "/api/download/x?format=zip"}
                                                 for r in rows]})
                page.add_init_script(SEEN)
                page.route("**/api/orders/*/capture",
                           lambda route: route.fulfill(status=200, content_type="application/json", body=body))
                tab.goto("/thanks?token=FAKE-AR&lang=ar")
                page.get_by_text(note).wait_for()
                assert tab.problems() == []
            finally:
                tab.close()


def pack_of(size: int):
    """API #4 (los lotes y el pack) con otro PACK_SIZE (el servidor sigue con el suyo: sólo cambia lo que la página
    dice)."""
    def config(route):
        response = route.fetch()
        cfg = response.json()
        route.fulfill(response=response, json={**cfg, "pack": {**cfg["pack"], "size": size}})
    return config


def test_the_pack_says_its_size_and_counts_what_is_left_in_its_form(real_app):
    """«Arma tu pack» dice su tamaño (PACK_SIZE, de API #1), no un 5 escrito en el texto, y cuántas faltan con la forma
    que pide su número (en árabe, «اختر اثنتين أخريين» con 2)."""
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        for lang, size, said in (("ar", 2, "اختر اثنتين أخريين · 2 مقابل "), ("es", 7, "Elige 7 más · 7 por "),
                                 ("ar", 1, "اختر واحدة أخرى · 1 مقابل ")):
            tab = mobile.open_page(chromium, live, "laptop")
            page = tab.page
            try:
                page.add_init_script(SEEN)

                page.route(re.compile(r".*/api/bundles$"), pack_of(size))
                tab.goto(f"/?lang={lang}")
                page.get_by_text(re.compile("^" + re.escape(said))).wait_for()
                assert tab.problems() == [], tab.problems()
            finally:
                tab.close()


def test_a_combined_indicator_is_named_like_its_tree_names_it():
    """El nombre de una combinada es el de sus partes como lo dice la pestaña «Cómo decide» (las funciones de su
    script sin «L_» ni guiones bajos, unidas por « + »): «Bull Bear Power + Triple EMA», no el del generador,
    «Bull_Bear_Power & Triple_EMA Combined»."""
    for row in INDICATORS:
        assert "_" not in row["Full Indicator Name"], row["Key"]
        if row["Key"].startswith("2"):
            parts = [f.strip().split(".")[-1] for f in row["Associated Function"].split(",")]
            assert row["Full Indicator Name"] == " + ".join(p.replace("L_", "", 1).replace("_", " ") for p in parts), row["Key"]


def test_a_bundle_list_that_wraps_never_ends_a_line_with_its_dot(real_app):
    """La lista de tickers de un lote va en una línea de izquierda a derecha dentro de la tarjeta; si se parte, el
    punto se queda con el ticker que le sigue. En árabe, el que acababa la primera línea quedaba junto al que la
    separa del recuento: «SNOW · ADBE · META · AMD · · 5 استراتيجيات»."""
    with mobile.serve(real_app) as live, mobile.browser() as chromium:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            page.add_init_script(SEEN)
            tab.goto("/?lang=ar")
            span = page.locator("span[dir=ltr]", has_text=re.compile(r"·")).first
            span.wait_for()
            # el último carácter que no es un espacio de cada línea (por la altura de cada letra)
            ends = span.evaluate("""el => {
                const node = el.firstChild, text = node.textContent, range = document.createRange(), lines = [];
                for (let i = 0; i < text.length; i++) {
                    range.setStart(node, i); range.setEnd(node, i + 1);
                    const r = range.getClientRects()[0];
                    if (!r || !text[i].trim()) continue;
                    const top = Math.round(r.top);
                    if (!lines.length || Math.abs(lines[lines.length - 1].top - top) > 4) lines.push({ top, last: text[i] });
                    else lines[lines.length - 1].last = text[i];
                }
                return lines.map(l => l.last);
            }""")
            assert len(ends) >= 2, f"la lista no se parte a este ancho: la prueba no prueba nada ({ends})"
            assert "·" not in ends, ends
            assert tab.problems() == [], tab.problems()
        finally:
            tab.close()
