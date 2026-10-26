# -*- coding: utf-8 -*-
"""Los formatos hechos de un script Pine completo: el lector, las reglas en .md, el .py/.js beta y el zip."""
import io
import json
import os
import random
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

from edgefolio import formats
from edgefolio.catalogue import Catalogue
from edgefolio.settings import ROOT, STATIC

TWO_TREES = """//@version=5
strategy("Tuisku_NVDA_1Day_1ULT_cccc3333", overlay=true)
decision_tree_0_NVDA_1Day_cccc3333(ema3, ema12, histA_IsUpInt)=>
\tvar float ret = 0  // # DecisionTreeRegressor(criterion=friedman_mse, max_depth=3)
\tif( ema3 <= 1954.56 )
\t\tif( ema12 <= -30.33 )
\t\t\tif( ema3 <= 100.5 )
\t\t\t\tret := 1.000000 // buy
\t\t\tif( ema3 > 100.5 )
\t\t\t\tret := 0.600000
\t\tif( ema12 > -30.33 )
\t\t\tret := -0.950000 // sell
\tif( ema3 > 1954.56 )
\t\tif( histA_IsUpInt <= 0.5 )
\t\t\tret := 0.100000
\t\tif( histA_IsUpInt > 0.5 )
\t\t\tret := -0.300000
\t
    ret //return
decision_tree_1_NVDA_1Day_cccc3333(ema3)=>
\tvar float ret = 0
\tif( ema3 <= 50 )
\t\tret := 0.5
\tif( ema3 > 50 )
\t\tret := -0.5
    ret //return
plot(close)
float op_operation = (decision_tree_0_NVDA_1Day_cccc3333(ema3, ema12, histA_IsUpInt) + decision_tree_1_NVDA_1Day_cccc3333(ema3)) / 2
if (op_operation <= 0)
    strategy.cancel("x")
if (op_operation >= 0.55)
    strategy.entry("x", strategy.long)
if (op_operation <= -0.9)
    strategy.close("x", comment = "under Le1")
"""
ONE_TREE = TWO_TREES.replace(
    "(decision_tree_0_NVDA_1Day_cccc3333(ema3, ema12, histA_IsUpInt) + decision_tree_1_NVDA_1Day_cccc3333(ema3)) / 2",
    "decision_tree_0_NVDA_1Day_cccc3333(ema3, ema12, histA_IsUpInt)")
# The exits as every one of the 2,834 scripts has them (copied from a real one, comments left out).
EXITS = """
var float stop = na
var float limit1 = na
var float limit2 = na
percent2points(percent) =>
    strategy.position_avg_price * percent / 100 / syminfo.mintick

sl = percent2points(input(2.92, title="stop loss %%"))
tp1 = percent2points(input(1.12, title="take profit 1 %%"))
tp2 = percent2points(input(2.31, title="take profit 2 %%"))
tp3 = percent2points(input(3.91, title="take profit 3 %%"))
activateTrailingOnThirdStep = input(false,title="activate trailing on third stage (tp3 is amount, tp2 is offset level)")
log.info("Stop Loss (sl):", sl," Take Profit 1 (tp1):", tp1, " Take Profit 2 (tp2):", tp2," Take Profit 3 (tp3):", tp3)

curProfitInPts() =>
    if strategy.position_size > 0
        (high - strategy.position_avg_price) / syminfo.mintick
    else if strategy.position_size < 0
        (strategy.position_avg_price - low) / syminfo.mintick
    else
        0
calcStopLossPrice(OffsetPts) =>
    if strategy.position_size > 0
        strategy.position_avg_price - OffsetPts * syminfo.mintick
    else if strategy.position_size < 0
        strategy.position_avg_price + OffsetPts * syminfo.mintick
    else
        0
calcProfitTrgtPrice(OffsetPts) =>
    calcStopLossPrice(-OffsetPts)
getCurrentStage() =>
    var stage = 0
    if strategy.position_size == 0
        stage := 0
    if stage == 0 and strategy.position_size != 0
        stage := 1
    else if stage == 1 and curProfitInPts() >= tp1
        stage := 2
    else if stage == 2 and curProfitInPts() >= tp2
        stage := 3
    stage
stopLevel = -1.
profitLevel = calcProfitTrgtPrice(tp3)
curStage = getCurrentStage()
float op_operation = decision_tree_0_NVDA_1Day_cccc3333(ema3, ema12, histA_IsUpInt)
if (op_operation <= 0)
    if curStage == 1
        stopLevel := calcStopLossPrice(sl)
        strategy.exit("x", loss = sl, profit = tp3, comment = "sl or tp3")
    else if curStage == 2
        stopLevel := calcStopLossPrice(0)
        strategy.exit("x", stop = stopLevel, profit = tp3, comment = "breakeven or tp3")
    else if curStage == 3
        stopLevel := calcStopLossPrice(-tp1)
        strategy.exit("x", stop = stopLevel, profit = tp3, comment = "tp1 or tp3")
    else
        strategy.cancel("x")

FIXED_DOLLAR_AMOUNT  = 10000
positionSize = FIXED_DOLLAR_AMOUNT / close

if (op_operation >= 0.55)
    stop := close * 0.965
    limit1 := close * 1.03
    limit2 := close * 1.02
    strategy.entry("x", strategy.long, qty=positionSize, stop=stop, comment="in")
if (op_operation <= -0.9)
    strategy.close("x", comment = "under Le1")
"""
WITH_EXITS = ONE_TREE[:ONE_TREE.index("float op_operation")].replace(
    "overlay=true)", "overlay=true, margin_long=1000, margin_short=1000, pyramiding=1)") + EXITS.lstrip("\n")
PREVIEWS = sorted((STATIC / "assets" / "previews").glob("*.pine"))


def pine_as_python(src: str):
    """Each tree function translated line by line, independently of formats.parse, to check it against."""
    funcs, out = {}, None
    for line in src.replace("\r", "").split("\n"):
        head = re.match(r"^decision_tree_(\d+)_\w*\(", line)
        if head:
            out = ["def f(x):"]
            funcs[int(head.group(1))] = out
            continue
        if out is None or not line.strip():
            continue
        if not line[0].isspace():
            out = None
            continue
        pad = "    " * (len(line) - len(line.lstrip("\t")))
        text = line.strip()
        if m := re.match(r"^if\(\s*(\w+)\s*(<=|>)\s*(\S+)\s*\)", text):
            out.append(f'{pad}if x["{m.group(1)}"] {m.group(2)} {m.group(3)}:')
        elif m := re.match(r"^(?:var float )?ret\s*:?=\s*(\S+)", text):
            out.append(f"{pad}ret = {m.group(1)}")
    trees = {}
    for n, lines in funcs.items():
        scope = {}
        try:
            exec("\n".join(lines + ["    return ret"]), scope)
        except SyntaxError:  # un árbol que la vista previa corta por la mitad (cuando el primero es corto)
            continue
        trees[n] = scope["f"]
    return trees


def generated(script, title="t"):
    scope = {}
    exec(formats.to_python(script, title), scope)
    return scope


def samples(script, n=300, seed=7):
    """Bar values around every threshold, so every leaf is reached."""
    cuts = {}
    for tree in script.trees:
        for path, _ in formats.leaves(tree.root):
            for f, raw, _ in path:
                cuts.setdefault(f, set()).add(float(raw))
    rnd = random.Random(seed)
    for _ in range(n):
        yield {f: rnd.choice(sorted(c)) + rnd.choice((-1, 0, 0.001, 1)) * rnd.random() for f, c in cuts.items()}


def test_parses_trees_combination_and_thresholds():
    s = formats.parse(TWO_TREES)
    assert s.name == "Tuisku_NVDA_1Day_1ULT_cccc3333"
    assert [t.index for t in s.trees] == [0, 1] and s.combine == "mean"
    assert (s.buy, s.close) == ("0.55", "-0.9"), "the <= 0 block only manages exits; -0.9 closes"
    t = s.trees[0]
    assert t.inputs == ["ema3", "ema12", "histA_IsUpInt"] and t.missing == 0
    assert t.regressor == "criterion=friedman_mse, max_depth=3"
    assert [(leaf.raw, leaf.sig) for _, leaf in formats.leaves(t.root)] == [
        ("1.000000", "buy"), ("0.600000", ""), ("-0.950000", "sell"), ("0.100000", ""), ("-0.300000", "")]


def test_markdown_rules_in_plain_words():
    md = formats.to_markdown(formats.parse(ONE_TREE), "Tuisku_NVDA")
    assert "1. If ema3 ≤ 100.5 and ema12 ≤ -30.33 → Buy (score 1.00)" in md, "repeated splits become one bound"
    assert "2. If 100.5 < ema3 ≤ 1954.56 and ema12 ≤ -30.33 → Buy (score 0.60)" in md, "0.60 ≥ 0.55: the script buys"
    assert "3. If ema3 ≤ 1954.56 and ema12 > -30.33 → Close (score -0.95)" in md, "-0.95 ≤ -0.9: it closes"
    assert "4. If ema3 > 1954.56 and histA_IsUpInt = 0 → Wait (score 0.10)" in md, "0/1 values read as yes/no"
    assert "- `ema3`: Slow average." in md, "los nombres de static/trees/features.json"
    assert "0.55 or more" in md and "-0.9 or less" in md
    # with several trees one leaf does not decide alone: the factory's labels are used
    md2 = formats.to_markdown(formats.parse(TWO_TREES), "Tuisku_NVDA")
    assert "→ Wait (score 0.60)" in md2 and "## Tree 2 of 2" in md2 and "average" in md2


# Una de WaveTrend y Triple EMA que pregunta por d__close (la distancia de WaveTrend dividida por el cierre),
# ema2__close (la media intermedia de la Triple EMA), macd__close (de un patrón que no es suyo) y d.
NAMED = """// Technical base pattern: Wave_Trend_Calculation, L_Triple_EMA
// ID_model: TEST_1Day_1WAV_00000000 Date Creation: 2026/10/13 Expiry date: 2027/06/13
//@version=5
strategy("Tuisku_TEST_1Day_1WAV_00000000", overlay=true)
decision_tree_0_TEST_1Day_00000000(d__close, ema2__close, macd__close, d)=>
\tfloat ret = na  // # DecisionTreeRegressor(max_depth=3)
\tif( d__close <= 0.01 )
\t\tif( ema2__close <= 0.5 )
\t\t\tret := 1.0 // buy
\t\tif( ema2__close > 0.5 )
\t\t\tif( d <= 3 )
\t\t\t\tret := 0.2
\t\t\tif( d > 3 )
\t\t\t\tret := 0.1
\tif( d__close > 0.01 )
\t\tif( macd__close <= 0.1 )
\t\t\tret := -1 // sell
\t\tif( macd__close > 0.1 )
\t\t\tret := 0.3
"""


def test_markdown_names_each_value_as_the_tree_does():
    """«Values used» del .md busca cada nombre como el árbol (static/js/tree.js, keyOf): el de un patrón de la
    estrategia (``d@Wave_Trend_Calculation``) antes que el suelto, éste sólo si es de uno de sus patrones, y el de un
    valor dividido por el cierre sin ``__close``, con la nota del árbol. Antes miraba sólo la clave tal cual:
    ``d__close`` salía sin nombre y ``d``, en una de WaveTrend, como la %D del RSI estocástico."""
    fx = json.loads((STATIC / "trees" / "features.json").read_text(encoding="utf-8"))["features"]
    tree_js = (STATIC / "js" / "tree.js").read_text(encoding="utf-8")
    assert f"relNote: '{formats.REL_NOTE}'" in tree_js, "la misma nota que el árbol en inglés"
    script = formats.parse(NAMED)
    assert script.bases == ["Wave_Trend_Calculation", "L_Triple_EMA"]
    md = formats.to_markdown(script, "Tuisku_TEST")
    wave, ema2, stoch_d = fx["d@Wave_Trend_Calculation"], fx["ema2"], fx["d"]
    assert f"- `d__close`: {wave[0]}. {wave[1]} {formats.REL_NOTE}" in md
    assert f"- `ema2__close`: {ema2[0]}. {ema2[1]} {formats.REL_NOTE}" in md
    assert f"- `d`: {wave[0]}. {wave[1]}\n" in md and stoch_d[0] not in md
    assert "- `macd__close`\n" in md, "el MACD no es de sus patrones: sin nombre, como en el árbol"
    # la misma pregunta en una del RSI estocástico: ahí d es la %D
    md = formats.to_markdown(formats.parse(NAMED.replace("Wave_Trend_Calculation, L_Triple_EMA", "L_Stochastic_RSI")), "T")
    assert f"- `d`: {stoch_d[0]}. {stoch_d[1]}\n" in md and f"- `d__close`: {stoch_d[0]}. {stoch_d[1]} {formats.REL_NOTE}" in md
    # sin la línea de los patrones (un script de antes), el nombre suelto, como el árbol
    assert formats.parse(TWO_TREES).bases == [] and "- `ema3`: Slow average." in formats.to_markdown(formats.parse(TWO_TREES), "T")


def test_python_matches_the_pine_trees_and_combines_them_like_the_script():
    script = formats.parse(TWO_TREES)
    py, pine = generated(script), pine_as_python(TWO_TREES)
    assert "BETA" in py["__doc__"] and "TradingView" in py["__doc__"]
    for x in samples(script):
        assert py["tree_0"](x) == pine[0](x) and py["tree_1"](x) == pine[1](x)
        assert py["score"](x) == pytest.approx((pine[0](x) + pine[1](x)) / 2)
    assert py["signal"]({"ema3": 10, "ema12": -40, "histA_IsUpInt": 0}) == "buy"      # (1 + 0.5) / 2
    assert py["signal"]({"ema3": 3000, "ema12": 0, "histA_IsUpInt": 1}) == "none"     # (-0.3 - 0.5) / 2
    assert py["INPUTS"] == ["ema3", "ema12", "histA_IsUpInt"]


@pytest.mark.skipif(not shutil.which("node"), reason="node is not installed")
def test_javascript_gives_the_same_scores(tmp_path):
    script = formats.parse(TWO_TREES)
    xs = list(samples(script, 100))
    (tmp_path / "s.mjs").write_text(formats.to_javascript(script, "t"))
    (tmp_path / "run.mjs").write_text("import * as s from './s.mjs';\n"
                                      f"const xs = {json.dumps(xs)};\n"
                                      "console.log(JSON.stringify(xs.map(x => [s.score(x), s.signal(x)])));\n")
    out = json.loads(subprocess.run(["node", str(tmp_path / "run.mjs")], capture_output=True, text=True,
                                    check=True).stdout)
    py = generated(script)
    assert out == [[pytest.approx(py["score"](x)), py["signal"](x)] for x in xs]


def test_every_preview_parses():
    assert len(PREVIEWS) == len(Catalogue(ROOT / "catalogue" / "catalogue.csv"))
    complete = 0
    for path in PREVIEWS:
        script = formats.parse(path.read_text(encoding="utf-8"))
        assert script.trees and any(leaf for _, leaf in formats.leaves(script.trees[0].root)), path.name
        complete += script.trees[0].missing == 0
    assert complete >= 5, "some previews hold a whole tree: those are checked leaf by leaf below"


def test_whole_previews_match_the_pine_leaf_by_leaf():
    checked = 0
    for path in PREVIEWS[::7] if len(PREVIEWS) > 700 else PREVIEWS:
        src = path.read_text(encoding="utf-8")
        script = formats.parse(src)
        if script.trees[0].missing:
            continue
        py, pine = generated(script), pine_as_python(src)
        for x in samples(script, 60):
            assert py["tree_0"](x) == pine[0](x), path.name
        checked += 1
    assert checked >= 5


def test_a_cut_preview_says_what_is_missing():
    path = next(p for p in PREVIEWS if formats.parse(p.read_text(encoding="utf-8")).trees[0].missing)
    script = formats.parse(path.read_text(encoding="utf-8"))
    assert "(not in this copy of the script)" in formats.to_markdown(script, "x")
    with pytest.raises(ValueError):  # a branch the preview does not have is never guessed
        for x in samples(script, 400):
            generated(script)["tree_0"](x)


def test_zip_holds_the_script_and_every_format():
    data = formats.build_zip(ONE_TREE, "Tuisku_NVDA_1Day_1ULT_cccc3333", "help@example.com")
    z = zipfile.ZipFile(io.BytesIO(data))
    stem = "Tuisku_NVDA_1Day_1ULT_cccc3333"
    assert sorted(z.namelist()) == sorted([f"{stem}.pine", f"{stem}.md", f"{stem}.py", f"{stem}.js", "README.txt"])
    assert z.read(f"{stem}.pine").decode() == ONE_TREE
    assert "Beta" in z.read("README.txt").decode() or "BETA" in z.read("README.txt").decode()
    assert "help@example.com" in z.read("README.txt").decode()
    assert "BETA" in z.read(f"{stem}.js").decode()


def test_a_script_without_trees_still_gets_its_zip():
    z = zipfile.ZipFile(io.BytesIO(formats.build_zip('//@version=5\nstrategy("x")\n', "x")))
    assert "No decision trees" in z.read("x.md").decode()
    scope = {}
    exec(z.read("x.py").decode(), scope)
    assert scope["signal"]({}) == "none"


def test_parses_the_exits():
    s = formats.parse(WITH_EXITS)
    assert (s.buy, s.arm, s.close) == ("0.55", "0", "-0.9") and s.pyramiding == 1 and s.entry_stop == "0.965"
    e = s.exits
    assert e.pct == {"sl": "2.92", "tp1": "1.12", "tp2": "2.31", "tp3": "3.91"}
    assert e.titles == {"sl": "stop loss", "tp1": "take profit 1", "tp2": "take profit 2", "tp3": "take profit 3"}
    assert [(x.n, x.reached_at, x.stop, x.profit) for x in e.stages] == [
        (1, None, "sl", "tp3"), (2, "tp1", "0", "tp3"), (3, "tp2", "-tp1", "tp3")]
    assert [formats.stop_pct(x, e) for x in e.stages] == ["-2.92", "0", "1.12"]
    assert (e.trailing, e.trailing_used) == ("false", False), "declared, read by nothing"
    assert formats.parse(ONE_TREE).arm is None and formats.parse(ONE_TREE).exits is None, "its <= 0 only cancels"


def test_markdown_says_what_the_script_does_with_the_score_and_the_exits():
    md = formats.to_markdown(formats.parse(WITH_EXITS), "Tuisku_NVDA")
    for line in (
            "- **0.55 or more: Buy.** It opens a long position (only one at a time: a buy signal while a position "
            "is open adds nothing).",
            "- **Above 0 and below 0.55: Wait.** No new order; an open position keeps the exits it already has.",
            "- **0 or less: arm the exits.** With a position open, it places or moves its stop loss and take profit "
            "(see Exits); with no position, it cancels any pending order.",
            "- **-0.9 or less: Close.** It closes the whole position at market.",
            "stop loss 2.92 %, take profit 1 1.12 %, take profit 2 2.31 %, take profit 3 3.91 %.",
            "1. From the bar the position opens: a stop loss 2.92 % below the entry price and a take profit "
            "3.91 % above it.",
            "2. Once a bar's high has reached 1.12 % above the entry price (take profit 1): a stop at the entry "
            "price (break-even) and a take profit 3.91 % above it.",
            "3. Once a later bar's high has reached 2.31 % above the entry price (take profit 2): a stop 1.12 % "
            "above the entry price (that gain is kept) and a take profit 3.91 % above it.",
            "Until the first such bar after the entry the position has no stop loss and no take profit",
            "nothing in the script reads it: there is no trailing stop, whatever it is set to.",
            "it is not a stop loss"):
        assert line in md, line
    # each leaf by what the script does with its score: >= 0.55, (0, 0.55), (-0.9, 0], <= -0.9
    for rule in ("→ Buy (score 1.00)", "→ Buy (score 0.60)", "→ Wait (score 0.10)", "→ Arm the exits (score -0.30)",
                 "→ Close (score -0.95)"):
        assert rule in md, rule
    assert "Buy, Wait, Arm the exits and Close are what the script does" in md


def test_other_exit_values_and_a_trailing_input_that_is_used():
    src = WITH_EXITS.replace("input(2.92,", "input(1.5,").replace(
        '        strategy.cancel("x")',
        '        strategy.cancel("x")\nif activateTrailingOnThirdStep\n    strategy.exit("t", trail_points = tp3)')
    s = formats.parse(src)
    assert s.exits.pct["sl"] == "1.5" and s.exits.trailing_used
    md = formats.to_markdown(s, "x")
    assert "a stop loss 1.5 % below the entry price" in md and "see the Pine script for what it changes" in md
    assert generated(s)["TRAILING_STOP"] is None and generated(s)["STOP_LOSS_PCT"] == 1.5
    odd = WITH_EXITS.replace("stopLevel := calcStopLossPrice(0)", "stopLevel := low")  # not the factory's code
    md = formats.to_markdown(formats.parse(odd), "x")
    assert formats.parse(odd).exits.stages == [] and "see the Pine script for how" in md and "Stage" not in md


def test_python_and_javascript_carry_the_exits_as_data_not_simulated():
    script = formats.parse(WITH_EXITS)
    py = generated(script)
    assert (py["BUY_AT"], py["ARM_EXITS_AT"], py["CLOSE_AT"]) == (0.55, 0, -0.9)
    assert (py["STOP_LOSS_PCT"], py["TAKE_PROFIT_1_PCT"], py["TAKE_PROFIT_2_PCT"], py["TAKE_PROFIT_3_PCT"]) == (
        2.92, 1.12, 2.31, 3.91)
    assert py["STAGES"] == [{"stage": 1, "from_high_pct": None, "stop_pct": -2.92, "take_profit_pct": 3.91},
                            {"stage": 2, "from_high_pct": 1.12, "stop_pct": 0, "take_profit_pct": 3.91},
                            {"stage": 3, "from_high_pct": 2.31, "stop_pct": 1.12, "take_profit_pct": 3.91}]
    assert py["TRAILING_STOP"] is False and "NOT simulated" in py["__doc__"]
    signals = {round(py["score"](x), 2): py["signal"](x) for x in samples(script)}
    assert signals == {1.0: "buy", 0.6: "buy", 0.1: "none", -0.3: "arm_exits", -0.95: "close"}
    none = generated(formats.parse('//@version=5\nstrategy("x")\n'))
    assert none["STAGES"] == [] and none["STOP_LOSS_PCT"] is None and none["ARM_EXITS_AT"] is None
    if shutil.which("node"):
        js = formats.to_javascript(script, "t")
        assert "NOT simulated" in js and 'export const STOP_LOSS_PCT = 2.92;' in js
        out = subprocess.run(["node", "--input-type=module", "-e",
                              js + "\nconsole.log(JSON.stringify([STAGES, TRAILING_STOP, ARM_EXITS_AT, "
                                   "signal({ema3: 3000, ema12: 0, histA_IsUpInt: 1})]));"],
                             capture_output=True, text=True, check=True).stdout
        assert json.loads(out) == [py["STAGES"], False, 0, "arm_exits"]


@pytest.fixture(scope="module")
def paid_scripts(tmp_path_factory):
    """Los scripts de pago: los de STRATEGIES_DIR si los hay; si no, los de la historia del repo
    (``flask edgefolio restore-scripts`` hace lo mismo); sin ninguno de los dos, la prueba se salta."""
    if os.environ.get("STRATEGIES_DIR") and Path(os.environ["STRATEGIES_DIR"]).is_dir():
        return Path(os.environ["STRATEGIES_DIR"])
    import click

    from edgefolio.cli import restore
    folder = tmp_path_factory.mktemp("strategies")
    try:
        if restore(folder) <= 0:
            pytest.skip("la historia del repo no tiene los scripts de pago")
    except (click.ClickException, OSError) as e:
        pytest.skip(f"los scripts de pago no están en esta máquina ({e})")
    return folder


def test_every_paid_script_has_its_exits_understood(paid_scripts):
    from edgefolio.catalogue import Catalogue
    seen = 0
    for s in Catalogue(ROOT / "catalogue" / "catalogue.csv"):
        path = paid_scripts / s.private_file
        if not path.is_file():
            continue
        script = formats.parse(path.read_text(encoding="utf-8", errors="replace"))
        assert script.buy and script.close and (script.arm is not None or script.exits_always), s.id
        assert len(script.exits.stages) == 3 and not script.exits.trailing_used, s.id
        seen += 1
    if not seen:  # los de la historia del repo son de un catálogo anterior
        pytest.skip("los scripts de pago de este catálogo no están en esta máquina (STRATEGIES_DIR)")
    assert seen == len(Catalogue(ROOT / "catalogue" / "catalogue.csv")), "cada estrategia del catálogo tiene su script"


TEMPLATE_2026 = ONE_TREE[:ONE_TREE.index("float op_operation")].replace(
    "overlay=true)", "overlay=true, margin_long=1000, margin_short=1000, pyramiding=1)") + """
slPercent = input.float(2.92, title="stop loss %")
tp1Percent = input.float(1.12, title="take profit 1 %")
tp2Percent = input.float(2.31, title="take profit 2 %")
tp3Percent = input.float(3.91, title="take profit 3 %")
buyThreshold = input.float(0.6, title="buy when the forest gives at least")
sellThreshold = input.float(-0.9, title="close when the forest gives at most")
tradeFrom = input.time(timestamp("2024-10-30T00:00:00+00:00"), title="trade from")
sl = percent2points(slPercent)
tp1 = percent2points(tp1Percent)
tp2 = percent2points(tp2Percent)
tp3 = percent2points(tp3Percent)
expiryTime = timestamp("2027-04-13T00:00:00+00:00")
isExpired = time >= expiryTime
getCurrentStage() =>
    var stage = 0
    if strategy.position_size == 0
        stage := 0
    if stage == 0 and strategy.position_size != 0
        stage := 1
    else if stage == 1 and curProfitInPts() >= tp1
        stage := 2
    else if stage == 2 and curProfitInPts() >= tp2
        stage := 3
    stage
stopLevel = -1.
curStage = getCurrentStage()
float op_operation = decision_tree_0_NVDA_1Day_cccc3333(ema3, ema12, histA_IsUpInt)
if strategy.position_size > 0
    if curStage == 1
        stopLevel := calcStopLossPrice(sl)
        strategy.exit("x", "x", loss = sl, profit = tp3, comment = "sl or tp3")
    else if curStage == 2
        stopLevel := calcStopLossPrice(0)
        strategy.exit("x", "x", stop = stopLevel, profit = tp3, comment = "breakeven or tp3")
    else if curStage == 3
        stopLevel := calcStopLossPrice(-tp1)
        strategy.exit("x", "x", stop = stopLevel, profit = tp3, comment = "tp1 or tp3")
FIXED_DOLLAR_AMOUNT = 10000
positionSize = FIXED_DOLLAR_AMOUNT / close
if strategy.position_size == 0 and time >= tradeFrom and not isExpired and op_operation >= buyThreshold
    strategy.entry("x", strategy.long, qty = positionSize, comment = "in")
    entryTicks = close / syminfo.mintick / 100
    strategy.exit("x", "x", loss = slPercent * entryTicks, profit = tp3Percent * entryTicks, comment = "sl or tp3")
if strategy.position_size > 0 and op_operation <= sellThreshold
    strategy.close("x", comment = "under Le1")
"""


def test_the_2026_template_is_read_with_its_inputs_and_its_exits_kept_while_in_position():
    # The factory's 2026 scripts: thresholds as inputs, exits sent with the entry and moved in stages while a
    # position is open. Read as the old template, the leaves were labelled by the factory's +-0.7 comments.
    script = formats.parse(TEMPLATE_2026)
    assert (script.buy, script.close, script.arm, script.exits_always, script.dated) == ("0.6", "-0.9", None, True, True)
    assert script.exits.pct == {"sl": "2.92", "tp1": "1.12", "tp2": "2.31", "tp3": "3.91"}
    assert [(s.n, s.reached_at, s.stop, s.profit) for s in script.exits.stages] == [
        (1, None, "sl", "tp3"), (2, "tp1", "0", "tp3"), (3, "tp2", "-tp1", "tp3")]
    md = formats.to_markdown(script, "t")
    assert "**0.6 or more: Buy.**" in md and "**-0.9 or less: Close.**" in md and "## Exits" in md
    assert "sent with the entry order" in md and "trade from" in md
    py = formats.to_python(script, "t")
    assert "BUY_AT = 0.6" in py and "CLOSE_AT = -0.9" in py and '"stage": 3' in py
