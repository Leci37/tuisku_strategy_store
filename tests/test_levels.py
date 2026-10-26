# -*- coding: utf-8 -*-
"""Los niveles de cada script (edgefolio/levels.py): con qué puntuación compra y con cuál cierra, para que el árbol
del visitante diga comprar, vender o esperar. Se leen de cada script completo, sólo del que lleva el nombre de su
estrategia; ``flask --app app edgefolio levels`` los escribe en catalogue/levels.json desde STRATEGIES_DIR (la
importación de un paquete, en tests/test_release.py) y API #3 los manda (``buy_at``, ``close_at``).

Todo en carpetas temporales: el catalogue/levels.json del repo no se toca."""
import json
from decimal import Decimal

from edgefolio import levels
from edgefolio.catalogue import Catalogue, Strategy
from edgefolio.settings import ROOT
from edgefolio.shop import install
from tests.conftest import ROWS, strategy_id
from tests.test_formats import TEMPLATE_2026


def strategy(row) -> Strategy:
    return Strategy(row["ticker"], row["interval"], row["key_techs"], row["id_model"], Decimal(row["Price"]), row)


def script_of(strategy_id_: str, buy="0.6", sell="-0.9") -> str:
    """El script completo de la plantilla de 2026 de esa estrategia, con esos niveles."""
    src = TEMPLATE_2026.replace('buyThreshold = input.float(0.6,', f'buyThreshold = input.float({buy},')
    src = src.replace('sellThreshold = input.float(-0.9,', f'sellThreshold = input.float({sell},')
    first = src.index('strategy("') + len('strategy("')
    return src[:first] + "Tuisku_" + strategy_id_ + src[src.index('"', first):]


def run(app, *args):
    return app.test_cli_runner().invoke(args=["edgefolio", *args])


def test_a_script_gives_its_levels_only_when_it_is_its_strategys():
    sid = strategy_id(ROWS[0])
    assert levels.of_script(script_of(sid, "0.8", "-0.55"), sid) == ({"buy_at": 0.8, "close_at": -0.55}, "")
    # una copia de prueba: el script de otra estrategia (como los de la historia del repo en otra máquina)
    assert levels.of_script(script_of(strategy_id(ROWS[1])), sid) == (None, "other")
    # el suyo, pero sin decir con qué compra
    nothing = script_of(sid).replace("op_operation >= buyThreshold", "op_operation >= 2 * buyThreshold")
    assert levels.of_script(nothing, sid) == (None, "none")
    # la plantilla de antes: los niveles, escritos en sus if
    old = (f'//@version=5\nstrategy("Tuisku_{sid}", overlay=true)\nfloat op_operation = decision_tree_0_X(a)\n'
           'if( op_operation >= 0.55 )\n\tstrategy.entry("x", strategy.long)\nif( op_operation <= -0.9 )\n'
           '\tstrategy.close("x")\n')
    assert levels.of_script(old, sid) == ({"buy_at": 0.55, "close_at": -0.9}, "")
    # el nombre que se compara es el de la estrategia en TradingView (Strategy.file)
    assert all(levels.title_of(s.id) == s.file for s in Catalogue(ROOT / "catalogue" / "catalogue.csv"))


def test_the_file_reads_back_and_leaves_out_what_is_not_a_level(tmp_path):
    path = tmp_path / "levels.json"
    found = {"B_1Day_X_2": {"buy_at": 0.7, "close_at": None}, "A_1Day_X_1": {"buy_at": 0.6, "close_at": -0.9}}
    levels.write(path, found)
    text = path.read_text(encoding="utf-8")
    assert text.splitlines()[1].startswith('  "A_1Day_X_1"'), "una estrategia por línea, por orden"
    assert levels.load(path) == found and not list(tmp_path.glob(".*.tmp"))
    path.write_text(json.dumps({"A": {"buy_at": "0.6"}, "B": {"buy_at": True}, "C": {"close_at": -0.9},
                                "D": {"buy_at": 0.5, "close_at": "nan"}, "E": [0.6], "F": {"buy_at": 0.5}}))
    assert levels.load(path) == {"A": {"buy_at": 0.6, "close_at": None}, "F": {"buy_at": 0.5, "close_at": None}}
    path.write_text("{")
    assert levels.load(path) == {} and levels.load(tmp_path / "no-está.json") == {}


def test_the_command_writes_the_levels_of_the_published_catalogue(app, settings, client, paypal):
    private = settings.strategies_dir
    aapl, msft, nvda, tsla = (strategy(r) for r in ROWS)
    (private / aapl.private_file).write_text(script_of(aapl.id, "0.8", "-0.55"), encoding="utf-8")
    (private / msft.private_file).write_text(script_of(nvda.id), encoding="utf-8")   # una copia de otra
    # la gratis, NVDA, no tiene script; TSLA tiene el de conftest, sin niveles ni nombre
    result = run(app, "levels")
    assert result.exit_code == 0, result.output
    assert "catalogue/levels.json: 1 de 4 estrategias con los niveles de su script" in result.output
    assert "1 sin su script" in result.output and "1 cuyo script no dice con qué compra" not in result.output
    assert "2 cuyo script es el de otra estrategia" in result.output and "reinicia la tienda" in result.output
    assert levels.load(settings.levels) == {aapl.id: {"buy_at": 0.8, "close_at": -0.55}}

    # API #3 los manda, cuando la tienda arranca otra vez; sin ellos, null
    assert client.get(f"/api/strategies/{aapl.id}").json["buy_at"] is None, "la tienda en marcha sigue con lo de antes"
    install(app, settings, paypal)
    detail = client.get(f"/api/strategies/{aapl.id}").json
    assert (detail["buy_at"], detail["close_at"]) == (0.8, -0.55)
    other = client.get(f"/api/strategies/{msft.id}").json
    assert (other["buy_at"], other["close_at"]) == (None, None)
    assert "buy_at" not in client.get("/api/strategies?size=10").json["rows"][0], "sólo en la ficha (API #3)"


def test_with_no_script_of_its_own_the_command_leaves_the_file_alone(app, settings):
    """Con las copias de prueba de otra máquina, un fichero vacío borraría los niveles de verdad."""
    private = settings.strategies_dir
    for r in ROWS:
        (private / strategy(r).private_file).write_text(script_of("ZZZ_1Day_1ULT_00000000"), encoding="utf-8")
    settings.levels.write_text('{\n  "AAPL_1Day_1ADX_aaaa1111": {"buy_at": 0.8, "close_at": -0.55}\n}\n')
    before = settings.levels.read_bytes()
    result = run(app, "levels")
    assert result.exit_code != 0 and "4 cuyo script es el de otra estrategia" in result.output
    assert "no se toca" in result.output and settings.levels.read_bytes() == before
