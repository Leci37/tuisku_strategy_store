# -*- coding: utf-8 -*-
"""La API del catálogo: filtros, orden, páginas y los recuentos del panel Pro, comprobados contra el
catálogo de verdad contando sus filas en Python a secas."""
import csv
import json
import math
import time
from decimal import Decimal

import pytest

from edgefolio.catalogue import TV_SCRIPTS, Catalogue, Strategy
from edgefolio.search import RANGES, track
from edgefolio.settings import ROOT
from edgefolio.shop import install
from tests.conftest import ROWS, TODAY, cart_id, strategy_id

ROW_FIELDS = {"id", "ticker", "interval", "key", "hash", "name", "ind", "index", "market", "price", "np", "npp", "tr",
              "w", "pf", "mdd", "mddp", "avg", "avgp", "bars", "m", "actv", "cand", "prc", "tdep", "release",
              "version", "profit", "candle", "icon", "preview", "thumb_profit", "thumb_candle", "grade", "live",
              "live_as_of", "is_new", "tv_symbol", "file", "ind_url", "ind_text", "ind_lang"}


@pytest.fixture(scope="module")
def rows():
    return [s.as_row() for s in Catalogue(ROOT / "catalogue" / "catalogue.csv")]


def get(client, query=""):
    r = client.get("/api/strategies?" + query)
    assert r.status_code == 200, r.text
    return r.json


def test_first_page(real_client, rows):
    body = get(real_client)
    assert body["total"] == len(rows) == body["counts"]["all"] > 0
    assert body["page"] == 1 and body["size"] == 25 and len(body["rows"]) == 25
    assert [r["np"] for r in body["rows"]] == sorted((r["np"] for r in rows), reverse=True)[:25]
    assert "hist" not in body and "options" not in body


def test_row_fields(real_client):
    row = get(real_client, "q=NVDA&size=1")["rows"][0]
    assert set(row) == ROW_FIELDS
    assert row["id"] == f"{row['ticker']}_{row['interval']}_{row['key']}_{row['hash']}"
    assert row["file"] == "Tuisku_" + row["id"] and row["tv_symbol"] == "NASDAQ:NVDA"
    for k in ("profit", "candle", "icon", "preview"):
        assert row[k].startswith("/static/assets/") and (ROOT / row[k][1:]).is_file(), k
    assert row["thumb_profit"] == f"/thumbs/{row['id']}_profit.webp"
    assert row["grade"] == ("A" if row["tr"] >= 100 else "B" if row["tr"] >= 50 else "C" if row["tr"] >= 25 else "D")
    assert row["live"] is None, "sin cifra desde la publicación hasta que la escriba el trabajo diario"


def test_grades_follow_the_cutoffs(real_client, rows):
    """E10: la nota dice cuánta prueba respalda el backtest: A desde 100 operaciones cerradas, B desde 50, C desde 25;
    D, menos (GRADE_CUTOFFS). La página los recibe para decirlos en su explicación. Con el catálogo de 2026-10
    (5–63 operaciones), B, C y D."""
    from edgefolio.catalogue import grade
    from edgefolio.settings import Settings
    assert [grade(t) for t in (100, 99, 50, 49, 25, 24, 0, None)] == ["A", "B", "B", "C", "C", "D", "D", "D"]
    assert [grade(t, (30, 20, 10)) for t in (30, 29, 20, 10, 9)] == ["A", "B", "B", "C", "D"]
    assert real_client.get("/api/config").json["grade_cutoffs"] == [100, 50, 25]
    served = {r["id"]: r["grade"] for r in get(real_client, "size=100")["rows"]}
    assert served == {r["id"]: grade(r["tr"]) for r in rows} and {"B", "C", "D"} <= set(served.values())
    # otros cortes, de la configuración: las notas cambian con ellos
    s = Strategy("X", "1Day", "1C00", "h", Decimal("9"), {"Total Closed Trades": "30"}, grade_cutoffs=(60, 40, 30))
    assert s.grade == "C" and Strategy("X", "1Day", "1C00", "h", Decimal("9"), {"Total Closed Trades": "30"}).grade == "C"
    graded = Catalogue(Settings(catalogue=ROOT / "catalogue" / "catalogue.csv", grade_cutoffs=(60, 40, 7)))
    assert {s.id: s.grade for s in graded} == {r["id"]: grade(r["tr"], (60, 40, 7)) for r in rows}
    assert "A" in {s.grade for s in graded}


def test_grade_cutoffs_from_the_environment(tmp_path):
    from edgefolio.settings import Settings
    assert Settings.from_env(tmp_path, {}).grade_cutoffs == (100, 50, 25)
    assert Settings.from_env(tmp_path, {"GRADE_CUTOFFS": "200, 80,20"}).grade_cutoffs == (200, 80, 20)
    for raw in ("100,50", "50,100,25", "100,50,0", "a,b,c", "100,50,50"):
        with pytest.raises(ValueError, match="GRADE_CUTOFFS"):
            Settings.from_env(tmp_path, {"GRADE_CUTOFFS": raw})


def test_rows_carry_their_indicator_page(real_client):
    """«CLAVE · indicador» en las fichas de Pro lleva a la página del indicador en TradingView, y al pasar
    por encima dice qué es: lo mismo que la página de la estrategia."""
    row = next(r for r in get(real_client, "q=1BOL&size=25&ind_lang=en")["rows"] if r["key"] == "1BOL")
    assert row["ind_url"] == "https://www.tradingview.com/script/uCV8I4xA-Bollinger-RSI-Double-Strategy-by-ChartArt-v1-1/"
    assert row["ind_text"].startswith("The Bollinger RSI Double Strategy combines") and row["ind_lang"] == "en"
    detail = real_client.get(f"/api/strategies/{row['id']}?ind_lang=en").json
    assert (detail["ind_url"], detail["ind_text"], detail["ind_lang"]) == (row["ind_url"], row["ind_text"], "en")
    # un indicador sin página propia (una combinación: «--» en indicators.csv) lleva a la lista de scripts
    combined = next(r for r in get(real_client, "q=2BB0&size=25")["rows"] if r["key"] == "2BB0")
    assert combined["ind_url"] == TV_SCRIPTS


def test_crypto_symbol_and_missing_values(real_client, rows):
    row = get(real_client, "tab=crypto&size=1")["rows"][0]
    assert row["market"] == "crypto" and row["tv_symbol"] == "BINANCE:" + row["ticker"]
    assert any(r["pf"] is None for r in rows), "an empty Profit Factor is null, not NaN or 0"


def test_search_text(real_client, rows):
    body = get(real_client, "q=  chaikin  &size=100")
    expected = [r for r in rows if "chaikin" in f"{r['name']} {r['ticker']} {r['ind']} {r['key']}".lower()]
    assert body["total"] == len(expected) > 0
    assert get(real_client, "q=1c00")["total"] == sum(r["key"] == "1C00" for r in rows)


def test_range_filter(real_client, rows):
    body = get(real_client, "np_min=1000&np_max=50000&win_min=60")
    assert body["total"] == sum(1000 <= r["np"] <= 50000 and r["w"] >= 60 for r in rows)
    assert all(1000 <= r["np"] <= 50000 for r in body["rows"])


def test_a_missing_value_fails_an_active_range(real_client, rows):
    assert get(real_client, "pf_min=1")["total"] == sum(r["pf"] is not None for r in rows) < len(rows)
    assert get(real_client, "pf_min=")["total"] == len(rows), "an empty bound is an open end"


def test_multi_select(real_client, rows):
    body = get(real_client, "sym=AMD&sym=NVDA&tf=1Day&size=100")
    assert body["total"] == sum(r["ticker"] in ("AMD", "NVDA") and r["interval"] == "1Day" for r in rows)
    assert {r["ticker"] for r in body["rows"]} == {"AMD", "NVDA"}
    assert get(real_client, "sym=")["total"] == 0, "present with nothing ticked: an empty list"
    rel = next(r["release"] for r in rows if r["index"] == "CRYPTO")
    assert get(real_client, f"idx=CRYPTO&rel={rel}")["total"] == sum(
        r["index"] == "CRYPTO" and r["release"] == rel for r in rows) > 0


def test_free_paid_and_tabs(real_client, rows):
    free = sum(r["price"] == 0 for r in rows)
    assert get(real_client, "free=1")["total"] == get(real_client, "tab=free")["total"] == free
    assert get(real_client, "paid=1")["total"] == len(rows) - free
    assert get(real_client, "tab=stocks")["total"] == sum(r["market"] == "stocks" for r in rows)
    hot = get(real_client, "tab=hot")["rows"]
    assert len({r["ticker"] for r in hot}) == 25, "Hot takes the tickers in turns"
    best = {}
    for r in sorted(rows, key=lambda r: -r["npp"]):
        best.setdefault(r["ticker"], r["npp"])
    assert [r["npp"] for r in hot] == sorted(best.values(), reverse=True)[:25], "each ticker's best, by net profit %"
    assert [r["npp"] for r in get(real_client, "sort=npp")["rows"]] == sorted((r["npp"] for r in rows), reverse=True)[:25]
    win = get(real_client, "tab=win")["rows"]
    assert [r["w"] for r in win] == sorted((r["w"] for r in rows), reverse=True)[:25]
    by_price = get(real_client, "tab=hot&sort=price")["rows"]
    assert by_price[0]["price"] == max(r["price"] for r in rows), "an explicit sort wins over the tab's"


def test_every_tab_and_search_takes_the_tickers_in_turns_by_net_profit(real_client, rows):
    """Los turnos son los de lo que queda tras la pestaña o la búsqueda: primero el mejor de cada ticker,
    por % de beneficio; después el segundo de cada uno… (con los del catálogo entero, la pestaña Gratis
    salía con su mejor estrategia en el noveno puesto)."""
    for query in ("tab=free&size=100", "tab=stocks&size=100", "tab=hot&q=chaikin&size=100"):
        got = get(real_client, query)["rows"]
        assert got, query
        turn, seen = [], {}
        for r in got:
            seen[r["ticker"]] = seen.get(r["ticker"], -1) + 1
            turn.append(seen[r["ticker"]])
        assert turn == sorted(turn), f"{query}: los turnos, en orden"
        for t in set(turn):
            npp = [r["npp"] for r, k in zip(got, turn) if k == t]
            assert npp == sorted(npp, reverse=True), f"{query}: el turno {t} por % de beneficio"
    free = get(real_client, "tab=free&size=1")["rows"][0]
    assert free["npp"] == max(r["npp"] for r in rows if r["price"] == 0)


def test_new_tab_and_count(client):
    body = get(client, "tab=new")
    assert body["counts"] == {"all": len(ROWS), "new": 1}
    assert [r["id"] for r in body["rows"]] == [strategy_id(ROWS[2])] and body["rows"][0]["is_new"]
    assert body["rows"][0]["release"] == TODAY


def test_paging(real_client):
    one, two = get(real_client, "sort=trades&size=10"), get(real_client, "sort=trades&size=10&page=2")
    assert len(two["rows"]) == 10 and not {r["id"] for r in one["rows"]} & {r["id"] for r in two["rows"]}
    assert one["rows"][-1]["tr"] >= two["rows"][0]["tr"]
    assert get(real_client, "page=999")["rows"] == []
    r = real_client.get("/api/strategies?size=101")
    assert r.status_code == 400 and r.json == {"error": "errRequest", "field": "size"}


def test_bad_parameters(real_client):
    for query in ("sort=cheap", "tab=hidden", "np_min=lots", "win_max=nan"):
        r = real_client.get("/api/strategies?" + query)
        assert r.status_code == 400 and r.json["error"] == "errRequest", query


def bin_of(value, served):
    """La barra del histograma de ``value`` en la escala que mandó el servidor (``ranges``)."""
    lo, hi, log, n = served["min"], served["max"], served["log"], served["bins"]
    if log:
        f = (math.log10(max(value, lo)) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))
    else:
        f = (value - lo) / (hi - lo)
    return min(n - 1, int(min(1, max(0, f)) * n))


def test_histograms_count_every_other_filter(real_client, rows):
    # filtros que dejan estrategias en el catálogo de 2026-10 (con AAPL, TSLA y 5.000 $, los del de 2024, no
    # quedaba ninguna, y cada histograma esperado era todo ceros)
    body = get(real_client, "facets=1&sym=ADBE&sym=AMD&np_min=1000&win_max=80")
    passes = {"sym": lambda r: r["ticker"] in ("ADBE", "AMD"), "np": lambda r: r["np"] >= 1000,
              "win": lambda r: r["w"] <= 80}
    assert body["total"] == sum(all(p(r) for p in passes.values()) for r in rows) > 0
    fields = {k: v[0] for k, v in RANGES.items()}
    for key in RANGES:
        others = [r for r in rows if all(p(r) for k, p in passes.items() if k != key)]
        expected = [0] * RANGES[key][4]
        for r in others:
            if r[fields[key]] is not None:
                expected[bin_of(r[fields[key]], body["ranges"][key])] += 1
        assert sum(expected) > 0 and body["hist"][key] == expected, key
    assert body["ranges"]["np"]["bins"] == len(body["hist"]["np"]) == 36
    assert body["ranges"]["tree"]["bins"] == len(body["hist"]["tree"]) == 10


def test_each_track_is_the_catalogues_own(real_client, rows):
    """Cada barra va del mínimo al máximo del catálogo, redondeados hacia fuera: las estrategias la llenan.
    Con las del diseño (las del catálogo de 2024), las 94 de 2026-10 caían en un rincón: 5–63 operaciones en
    la primera de 32 barras de 0–2000, y 23 por debajo del mínimo de «Beneficio neto (%)»."""
    body = get(real_client, "facets=1")
    for key, (field, *_) in RANGES.items():
        values = [r[field] for r in rows if r[field] is not None]
        served, hist = body["ranges"][key], body["hist"][key]
        assert sum(hist) == len(values), key
        if not values:
            continue
        lo, hi = served["min"], served["max"]
        assert lo <= min(values) and max(values) <= hi, key
        if served["log"]:
            assert math.log10(max(values) / min(values)) / math.log10(hi / lo) > 0.5, key
        else:
            assert (max(values) - min(values)) / (hi - lo) >= 1 / 3, key
        if len(set(values)) > 2:
            assert max(hist) < len(values), f"{key}: todas en una barra"


def test_tracks_are_round_and_logarithmic_only_over_two_orders_of_magnitude():
    """Con las cifras del catálogo de 2026-10: las operaciones (5–63), el beneficio neto (257,57–4.398,51 $ y
    0,03–0,44 %), el factor de beneficio, la actividad por vela y la tasa de acierto."""
    assert track([5, 63], 0, 2000, False) == (0, 70, False)
    assert track([0.03, 0.44], 0.1, 6500, True) == (0, 0.5, False)
    assert track([257.57, 4398.51], 200, 6_500_000, True) == (0, 5000, False)   # 17 veces: lineal
    assert track([1.094, 123.632], 1, 35_000, True) == (1, 200, True)           # 113 veces: logarítmica
    assert track([0.002, 0.238], 0, 3, False) == (0, 0.3, False)
    assert track([30.56, 100], 0, 100, False) == (30, 100, False)
    assert track([-120, None, 340], 0, 1, False) == (-200, 400, False)
    assert track([0.0001, 0.5], 0.1, 6500, True) == (0.0001, 0.5, True)
    assert track([0, 0.5], 0.1, 6500, True) == (0, 0.5, False), "un cero no cabe en una escala logarítmica"
    assert track([5, 5], 1, 10, False) == (5, 6, False), "un solo valor: una barra de un paso"
    assert track([None], 1, 10, False) == (1, 10, False), "sin valores, la del diseño"


def test_activity_is_trades_per_candle(real_client, rows):
    """«Actividad por vela» es la columna del generador (operaciones por vela del backtest), no las operaciones
    por mes de entrenamiento con que la suplía la maqueta del diseño."""
    with open(ROOT / "catalogue" / "catalogue.csv", newline="", encoding="utf-8") as f:
        column = {f"{r['ticker']}_{r['interval']}_{r['key_techs']}_{r['id_model']}": float(r["Trade Activity Per Candle"])
                  for r in csv.DictReader(f, delimiter="\t")}
    assert {r["id"]: r["actv"] for r in rows} == column
    assert get(real_client, "act_max=0.01")["total"] == sum(v <= 0.01 for v in column.values()) > 0
    # sin la columna, nada: 50 operaciones en 15 meses no son 3,33 operaciones por vela
    bare = Strategy("X", "1Hour", "1C00", "h", Decimal("9"), {"Total Closed Trades": "50", "months_trained": "15"})
    assert bare.numbers["actv"] is None and bare.numbers["tr"] == 50


def test_config_gives_the_best_backtest_for_the_bars_of_the_strategy_page(real_client, rows, client):
    assert real_client.get("/api/config").json["npp_max"] == max(r["npp"] for r in rows)
    assert client.get("/api/config").json["npp_max"] is None, "sin backtests, la página se queda con su 100 %"


def test_options(real_client, rows):
    # (con NVDA de 1Hour, hasta que las horarias de acciones salieron del catálogo: ahora son de cripto)
    body = get(real_client, "facets=1&sym=XRPUSDT&tf=1Hour")
    sym = {o["v"]: o for o in body["options"]["sym"]}
    assert len(sym) == len({r["ticker"] for r in rows}), "every value is listed, even with a count of 0"
    assert sym["NVDA"]["label"].endswith("(NVDA)") and sym["NVDA"]["icon"] == "/static/assets/icons/NVDA_big.svg"
    assert sym["SOLUSDT"]["count"] == sum(r["ticker"] == "SOLUSDT" and r["interval"] == "1Hour" for r in rows) > 0
    tf = {o["v"]: o["count"] for o in body["options"]["tf"]}
    assert tf["1Day"] == sum(r["ticker"] == "XRPUSDT" and r["interval"] == "1Day" for r in rows) > 0
    ind = {o["v"]: o["label"] for o in body["options"]["ind"]}
    assert ind["1C00"] == "1C00 – Chaikin Money Flow (CMF)"
    assert [o["v"] for o in body["options"]["idx"]] == ["CRYPTO", "NASDAQ", "NYSE"]
    assert body["options"]["rel"][0]["v"] == max(r["release"] for r in rows)


def test_facets_are_fast(real_client):
    query = "facets=1&q=a&np_min=1000&win_max=95&sym=AAPL&sym=NVDA&sym=ETHUSDT&tf=1Day&tf=1Hour&ind=1C00&sort=win"
    best = min(timed(real_client, query) for _ in range(5))
    assert best < 0.150, f"{best * 1000:.0f} ms"
    assert min(timed(real_client, "facets=1") for _ in range(5)) < 0.150


def timed(client, query):
    t = time.perf_counter()
    get(client, query)
    return time.perf_counter() - t


def test_one_strategy(client, real_client):
    s = ROWS[0]
    by_id = client.get(f"/api/strategies/{strategy_id(s)}").json
    assert by_id == client.get(f"/api/strategies/{cart_id(s)}").json
    assert by_id["versions"] == [{"v": 1, "date": "2024-09-27", "note": ""}]
    assert client.get("/api/strategies/NOPE_1Day_X_0").json == {"error": "errUnknownStrategy"}
    detail = real_client.get("/api/strategies/ADBE_1Day_1C00_151aa3e7?ind_lang=en").json
    assert detail["ind_text"].startswith("The Chaikin") and detail["ind_url"].startswith("https://www.tradingview.com/")


def test_since_release_when_the_daily_job_has_run(app, client, settings, paypal):
    assert client.get("/api/config").json["since_release"] == 0, "sin cifras, la página no habla de ello"
    settings.since_release.write_text(f"id\tpct\tas_of\n{strategy_id(ROWS[0])}\t-3.25\t2026-10-04\n"
                                      f"{strategy_id(ROWS[2])}\t\t2026-10-04\nNOPE_1Day_X_0\t1.5\t2026-10-04\n")
    install(app, settings, paypal)   # la tienda, arrancada otra vez
    rows = {r["id"]: r for r in get(client, "size=10")["rows"]}
    assert rows[strategy_id(ROWS[0])]["live"] == -3.25 and rows[strategy_id(ROWS[0])]["live_as_of"] == "2026-10-04"
    assert rows[strategy_id(ROWS[1])]["live"] is None and rows[strategy_id(ROWS[2])]["live"] is None
    assert client.get("/api/config").json["since_release"] == 1, "las que tienen cifra (E11): vuelve sola"


def test_config_says_among_how_many_tried_strategies(real_client, client, app, settings, paypal):
    """E1: entre cuántas estrategias probadas se eligieron las del catálogo, de release.json (al lado de
    catalogue.csv): las de 2026-10, entre las 1.531 que escribió esa ejecución. Sin saberlo, null (la página no lo
    dice); y uno que no puede ser (menos que las que hay), tampoco."""
    release = json.loads((ROOT / "catalogue" / "release.json").read_text(encoding="utf-8"))
    real = real_client.get("/api/config").json
    assert real["tried"] == release["tried"] == 1531 and real["strategies"] == release["rows"] == 94
    assert client.get("/api/config").json["tried"] is None, "un catálogo sin release.json"
    release_json = settings.catalogue.parent / "release.json"
    for tried, served in ((9, 9), (3, None), ("9", None), (True, None)):
        release_json.write_text(json.dumps({"rows": 4, "tried": tried}))
        install(app, settings, paypal)
        assert client.get("/api/config").json["tried"] == served, tried
