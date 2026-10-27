# -*- coding: utf-8 -*-
"""Los otros formatos de una estrategia, hechos de su script Pine completo: las reglas en palabras
sencillas (.md), las versiones en Python y JavaScript de los árboles (.py, .js, beta) y el zip que los
lleva con el .pine. Lo que escriben (el producto que se entrega) va en inglés, como el script.

La fábrica escribe cada árbol como una función Pine `decision_tree_N_...(...) =>` de bloques
`if( feat <= v )` / `if( feat > v )` anidados que acaban en `ret := score // buy|sell`, y el script lee
`op_operation` de los árboles, compra con `op_operation >= X` y cierra con `op_operation <= Y`. Con
`op_operation <= 0` arma su orden de salida: un stop loss y un take profit (las entradas `sl`,
`tp1`..`tp3`, en % del precio de entrada) que pasan por tres etapas (getCurrentStage) según sube el precio.

La plantilla de la fábrica de 2026 lo escribe de otra forma, y también se lee: los umbrales son entradas
(`buyThreshold`, `sellThreshold`), compra con `op_operation >= buyThreshold` (y sólo desde `tradeFrom` y
hasta que caduca), cierra con `op_operation <= sellThreshold`, y las salidas (`slPercent`..`tp3Percent`)
van con la entrada y se mueven por etapas en cada vela mientras hay posición (`if strategy.position_size > 0`).
"""
from __future__ import annotations

import functools
import io
import json
import re
import textwrap
import zipfile
from dataclasses import dataclass, field
from typing import Optional, Union

from .settings import STATIC

NUM = r"(-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"
RE_TREE = re.compile(r"^decision_tree_(\d+)_\w*\s*\(([^)]*)\)\s*=>")
RE_LEAF = re.compile(r"^ret\s*:=\s*" + NUM + r"\s*(?://\s*(buy|sell)\b)?", re.I)
RE_LE = re.compile(r"^if\s*\(\s*(\w+)\s*<=\s*" + NUM + r"\s*\)")
RE_PARAMS = re.compile(r"DecisionTreeRegressor\(([^)]*)\)")
RE_COMBINE = re.compile(r"\bop_operation\s*=\s*(.+)")
RE_BUY = re.compile(r"^if\s*\(\s*op_operation\s*>=\s*" + NUM + r"\s*\)")
RE_LOW = re.compile(r"^if\s*\(\s*op_operation\s*<=\s*" + NUM + r"\s*\)")
RE_NAME = re.compile(r'^strategy\(\s*"([^"]+)"')
RE_BASES = re.compile(r"^// Technical base pattern:(.*)$", re.M)
RE_PYRAMIDING = re.compile(r"^strategy\(.*\bpyramiding\s*=\s*(\d+)")
RE_INPUT = re.compile(r"^(sl|tp1|tp2|tp3)\s*=\s*percent2points\(\s*input(?:\.float)?\(\s*" + NUM +
                      r'(?:.*?title\s*=\s*"([^"]*)")?')
RE_TRAIL = re.compile(r"^activateTrailingOnThirdStep\s*=\s*input(?:\.bool)?\(\s*(true|false)")
RE_STAGE_UP = re.compile(r"\bstage\s*==\s*(\d+)\s+and\s+curProfitInPts\(\)\s*>=\s*(\w+)")
RE_CUR_STAGE = re.compile(r"^(?:else\s+)?if\s+curStage\s*==\s*(\d+)")
RE_STOP_LEVEL = re.compile(r"^stopLevel\s*:=\s*calcStopLossPrice\(\s*(-?\w+(?:\.\d+)?)\s*\)")
RE_EXIT = re.compile(r"^strategy\.exit\((.*)\)")
RE_ENTRY_STOP = re.compile(r"^stop\s*:=\s*close\s*\*\s*" + NUM)
# La plantilla de 2026: umbrales y salidas como entradas, y las salidas puestas mientras hay posición.
RE_THRESHOLD = re.compile(r"^(buy|sell)Threshold\s*=\s*input(?:\.float)?\(\s*" + NUM)
RE_INPUT_PCT = re.compile(r"^(sl|tp1|tp2|tp3)Percent\s*=\s*input(?:\.float)?\(\s*" + NUM +
                          r'(?:.*?title\s*=\s*"([^"]*)")?')
RE_BUY_INPUT = re.compile(r"^if\b.*\bop_operation\s*>=\s*buyThreshold\b")
RE_CLOSE_INPUT = re.compile(r"^if\b.*\bop_operation\s*<=\s*sellThreshold\b")
RE_IN_POSITION = re.compile(r"^if\s+strategy\.position_size\s*>\s*0\s*$")

BETA = ("BETA: generated automatically from the Pine script. Check its signals against the strategy "
        "running in TradingView before relying on them; the Pine script is the reference.")


@dataclass
class Leaf:
    raw: str
    sig: str  # buy, sell o '' (el comentario de la fábrica en la hoja)

    @property
    def value(self) -> float:
        return float(self.raw)


@dataclass
class Split:
    feat: str
    raw: str
    le: "Node"
    gt: "Node"


Node = Optional[Union[Leaf, Split]]  # None: una rama que no está en el texto (una vista previa cortada)


@dataclass
class Tree:
    index: int
    name: str
    inputs: list
    regressor: str
    root: Node
    missing: int = 0


@dataclass
class Stage:
    n: int
    reached_at: Optional[str]  # la entrada cuyo % tiene que alcanzar el máximo de la vela; None: desde la entrada
    stop: str                  # el argumento de calcStopLossPrice: 'sl' (debajo), '0' (en la entrada), '-tp1' (encima)
    profit: str                # la entrada del take profit, encima de la entrada


@dataclass
class Exits:
    pct: dict = field(default_factory=dict)       # entrada -> su valor por defecto en %, como está escrito ('2.92')
    titles: dict = field(default_factory=dict)    # entrada -> su título en TradingView ('stop loss')
    stages: list = field(default_factory=list)    # [Stage]; vacía si el código de las etapas no es el de la fábrica
    trailing: Optional[str] = None                # el valor por defecto de 'activate trailing', si el script lo tiene
    trailing_used: bool = False                   # si algo, aparte de su declaración, lo lee


@dataclass
class Script:
    name: str
    trees: list = field(default_factory=list)
    combine: str = "mean"          # cómo junta el script las puntuaciones: mean o sum
    buy: Optional[str] = None      # op_operation >= buy abre una posición larga
    close: Optional[str] = None    # op_operation <= close la cierra
    arm: Optional[str] = None      # op_operation <= arm pone o mueve la orden de salida (stop loss, take profit)
    exits: Optional[Exits] = None
    pyramiding: Optional[int] = None
    entry_stop: Optional[str] = None  # el stop de la orden de entrada = close * esto (un precio de entrada, no un stop loss)
    exits_always: bool = False     # las salidas van con la entrada y se mueven en cada vela con posición (plantilla de 2026)
    dated: bool = False            # sólo abre posiciones desde su fecha "trade from" y hasta que caduca
    bases: list = field(default_factory=list)  # «// Technical base pattern: A, B»: de qué patrón es cada nombre


def _lines(src: str) -> list:
    """(sangría, texto) de cada línea con algo; un tabulador cuenta 4, así valen tabuladores y espacios."""
    out = []
    for line in src.replace("\r", "").split("\n"):
        text = line.strip()
        if text:
            out.append((len(line.expandtabs(4)) - len(line.expandtabs(4).lstrip()), text))
    return out


def _tree(lines: list, start: int) -> Tree:
    head = RE_TREE.match(lines[start][1])
    name = lines[start][1].split("(", 1)[0]
    body = []
    for ind, text in lines[start + 1:]:
        if ind == 0:
            break
        body.append((ind, text))
    params = RE_PARAMS.search(body[0][1]) if body else None
    i = next((n for n, (_, text) in enumerate(body) if text.startswith("if")), len(body))
    missing = 0

    def node(ind):
        nonlocal i, missing
        if i >= len(body) or body[i][0] != ind:
            missing += 1
            return None
        text = body[i][1]
        m = RE_LEAF.match(text)
        if m:
            i += 1
            return Leaf(m.group(1), (m.group(2) or "").lower())
        m = RE_LE.match(text)
        if not m:
            missing += 1
            return None
        i += 1
        feat, raw = m.group(1), m.group(2)
        le = node(body[i][0] if i < len(body) and body[i][0] > ind else -1)
        gt = None
        if i < len(body) and body[i][0] == ind and re.match(r"^if\s*\(\s*" + feat + r"\s*>", body[i][1]):
            i += 1
            gt = node(body[i][0] if i < len(body) and body[i][0] > ind else -1)
        else:
            missing += 1
        return Split(feat, raw, le, gt)

    root = node(body[i][0]) if i < len(body) else None
    return Tree(int(head.group(1)), name, [p.strip() for p in head.group(2).split(",") if p.strip()],
                params.group(1).strip() if params else "", root, missing)


def _block(lines: list, n: int) -> list:
    """Las líneas anidadas bajo la línea n."""
    out = []
    for ind, text in lines[n + 1:]:
        if ind <= lines[n][0]:
            break
        out.append(text)
    return out


def _stages(block: list, ups: dict) -> list:
    """La orden de salida de cada etapa del bloque `op_operation <= arm`; [] si no se entiende cada etapa."""
    stages, n, stop = [], None, None
    for text in block:
        if m := RE_CUR_STAGE.match(text):
            n, stop = int(m.group(1)), None
        elif m := RE_STOP_LEVEL.match(text):
            stop = m.group(1)
        elif (m := RE_EXIT.match(text)) and n is not None:
            args = dict(re.findall(r"(\w+)\s*=\s*([\w.\-]+)", m.group(1)))
            level = args.get("loss") or (stop if args.get("stop") == "stopLevel" else None)
            if not level or "profit" not in args or (n > 1 and n not in ups):
                return []
            stages.append(Stage(n, ups.get(n), level, args["profit"]))
    return stages


def _exits(lines: list, arm_block: list) -> Optional[Exits]:
    exits = Exits()
    ups = {}
    for _, text in lines:
        if m := RE_INPUT.match(text) or RE_INPUT_PCT.match(text):
            exits.pct[m.group(1)] = m.group(2)
            exits.titles[m.group(1)] = (m.group(3) or m.group(1)).replace("%", "").strip()
        if m := RE_TRAIL.match(text):
            exits.trailing = m.group(1)
        elif "activateTrailingOnThirdStep" in text and not text.startswith("//"):
            exits.trailing_used = True
        if m := RE_STAGE_UP.search(text):
            ups[int(m.group(1)) + 1] = m.group(2)
    stages = _stages(arm_block, ups)
    known = all(s.profit in exits.pct and s.stop.lstrip("-") in exits.pct | {"0": ""} and
                (s.reached_at is None or s.reached_at in exits.pct) for s in stages)
    exits.stages = stages if known and [s.n for s in stages] == list(range(1, len(stages) + 1)) else []
    return exits if exits.pct else None


def parse(src: str) -> Script:
    lines = _lines(src)
    name = next((m.group(1) for _, t in lines if (m := RE_NAME.match(t))), "")
    script = Script(name, [_tree(lines, n) for n, (_, t) in enumerate(lines) if RE_TREE.match(t)])
    bases = RE_BASES.search(src.replace("\r", ""))
    script.bases = [b.strip() for b in bases.group(1).split(",") if b.strip()] if bases else []
    arm_block = []
    thresholds = {m.group(1): m.group(2) for _, t in lines if (m := RE_THRESHOLD.match(t))}
    for n, (ind, text) in enumerate(lines):
        if (m := RE_PYRAMIDING.match(text)) and script.pyramiding is None:
            script.pyramiding = int(m.group(1))
        m = RE_COMBINE.search(text)
        if m and "decision_tree_" in m.group(1) and not text.startswith("//"):
            expr = m.group(1)
            used = {int(x) for x in re.findall(r"decision_tree_(\d+)_", expr)}
            script.trees = [t for t in script.trees if t.index in used] or script.trees
            script.combine = "sum" if "+" in expr and "/" not in expr else "mean"
        if (m := RE_BUY.match(text)) and script.buy is None:
            script.buy = m.group(1)
            entry = _block(lines, n)
            stop = next((e.group(1) for t in entry if (e := RE_ENTRY_STOP.match(t))), None)
            if stop and any(t.startswith("strategy.entry(") and re.search(r"\bstop\s*=\s*stop\b", t) for t in entry):
                script.entry_stop = stop
        if RE_BUY_INPUT.match(text) and script.buy is None and "buy" in thresholds:
            script.buy = thresholds["buy"]
            script.dated = "tradeFrom" in text and "isExpired" in text
        if RE_CLOSE_INPUT.match(text) and script.close is None and "sell" in thresholds:
            if any("strategy.close" in s for s in _block(lines, n)):
                script.close = thresholds["sell"]
        if RE_IN_POSITION.match(text) and not arm_block:
            block = _block(lines, n)
            if any(RE_CUR_STAGE.match(s) for s in block) and any(s.startswith("strategy.exit(") for s in block):
                script.exits_always, arm_block = True, block
        if m := RE_LOW.match(text):
            block = _block(lines, n)
            if script.close is None and any("strategy.close" in s for s in block):
                script.close = m.group(1)
            if script.arm is None and any(s.startswith("strategy.exit(") for s in block):
                script.arm, arm_block = m.group(1), block
    script.exits = _exits(lines, arm_block)
    return script


@functools.lru_cache(maxsize=1)
def feature_names() -> dict:
    """El nombre y la descripción en inglés de cada valor de indicador que usa la fábrica, y su patrón
    (static/trees/features.json; la clave de un nombre que usan dos patrones lleva el suyo:
    d@Wave_Trend_Calculation)."""
    try:
        data = json.loads((STATIC / "trees" / "features.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {k: (v[0], v[1], v[4] if len(v) > 4 else "") for k, v in data.get("features", {}).items() if len(v) >= 2}


# La nota de un valor que el generador divide por el cierre (BBlower__close), la del árbol (tree.js, relNote).
REL_NOTE = "As the model sees it: divided by the close of the candle."


def feature_label(feat: str, bases: list) -> tuple:
    """(nombre, descripción) en inglés del valor ``feat`` en un script de esos patrones, buscados como los busca
    el árbol (static/js/tree.js, keyOf): la clave de su patrón (``d@Wave_Trend_Calculation``) y luego la suya, sólo
    si es de uno de ellos; uno dividido por el cierre (``macd__close``), también sin ``__close``, con la nota.
    Sin nombre, ("", "")."""
    names = feature_names()
    for g in ([feat, feat[:-len("__close")]] if feat.endswith("__close") else [feat]):
        for key in [f"{g}@{b}" for b in bases] + [g]:
            e = names.get(key)
            if e and (not e[2] or not bases or e[2] in bases):
                return e[0], e[1] + (" " + REL_NOTE if g != feat else "")
    return "", ""


def is_flag(feat: str, raw: str) -> bool:
    """Los valores 0/1 de la fábrica acaban en Int: un corte entre 0 y 1 sólo pregunta sí o no."""
    return feat.endswith("Int") and 0 < float(raw) < 1


def leaves(node: Node, path=()):
    """(condiciones, hoja) de cada hoja, en el orden en que las escribe el script."""
    if node is None:
        yield path, None
    elif isinstance(node, Leaf):
        yield path, node
    else:
        yield from leaves(node.le, path + ((node.feat, node.raw, "le"),))
        yield from leaves(node.gt, path + ((node.feat, node.raw, "gt"),))


def features(script: Script) -> list:
    seen = {}
    for tree in script.trees:
        for path, _ in leaves(tree.root):
            seen.update((f, None) for f, _, _ in path)
    return list(seen)


def plain(path) -> str:
    """Las condiciones de un camino, una por valor: los cortes repetidos de un valor se juntan en un rango."""
    bounds = {}
    for feat, raw, way in path:
        lo, hi = bounds.get(feat, (None, None))
        if way == "le" and (hi is None or float(raw) < float(hi)):
            hi = raw
        if way == "gt" and (lo is None or float(raw) > float(lo)):
            lo = raw
        bounds[feat] = (lo, hi)
    parts = []
    for feat, (lo, hi) in bounds.items():
        if is_flag(feat, lo or hi):
            parts.append(f"{feat} = {1 if lo is not None else 0}")
        elif lo is not None and hi is not None:
            parts.append(f"{lo} < {feat} ≤ {hi}")
        else:
            parts.append(f"{feat} ≤ {hi}" if hi is not None else f"{feat} > {lo}")
    return " and ".join(parts) or "always"


ACTIONS = {"buy": "Buy", "sell": "Sell", "": "Wait"}
ARM = "Arm the exits"


def action(leaf: Leaf, script: Script) -> str:
    """Lo que hace el script cuando decide esta hoja. Con un árbol, la puntuación de la hoja es la del
    script, y sus umbrales lo dicen; los comentarios buy/sell de la fábrica (a ±0,7) no son lo que hace el
    script. Con varios árboles una hoja no decide sola: la etiqueta de la fábrica es la mejor pista."""
    if len(script.trees) == 1 and script.buy:
        v = leaf.value
        if v >= float(script.buy):
            return "Buy"
        if script.close and v <= float(script.close):
            return "Close"
        return ARM if script.arm is not None and v <= float(script.arm) else "Wait"
    return ACTIONS[leaf.sig]


def stop_pct(stage: Stage, exits: Exits) -> str:
    """Dónde está el stop de la etapa, en % por encima (+) o por debajo (-) del precio de entrada:
    calcStopLossPrice(x) lo pone x puntos por debajo, así que 'sl' es debajo, '0' en la entrada y '-tp1' encima."""
    if stage.stop == "0":
        return "0"
    return exits.pct[stage.stop[1:]] if stage.stop.startswith("-") else "-" + exits.pct[stage.stop]


def _stage_line(stage: Stage, exits: Exits) -> str:
    stop = stop_pct(stage, exits)
    where = ("a stop at the entry price (break-even)" if stop == "0" else
             f"a stop {stop} % above the entry price (that gain is kept)" if not stop.startswith("-") else
             f"a stop loss {stop[1:]} % below the entry price")
    when = ("From the bar the position opens" if stage.reached_at is None else
            f"Once {'a' if stage.n == 2 else 'a later'} bar's high has reached {exits.pct[stage.reached_at]} % "
            f"above the entry price ({exits.titles[stage.reached_at]})")
    return f"{stage.n}. {when}: {where} and a take profit {exits.pct[stage.profit]} % above it."


def how_it_decides(script: Script) -> list:
    """Lo que hace el script con su puntuación, como lo hace su código Pine (uno o varios árboles)."""
    n = len(script.trees)
    out = [(f"On every bar, each of the {n} decision trees gives a score between -1 and 1, and the script "
            f"takes their {'sum' if script.combine == 'sum' else 'average'}." if n > 1 else
            "On every bar, the decision tree gives a score between -1 and 1.")]
    if not script.buy:
        return out
    out[0] += " At the bar's close the script acts on it; the orders it sends are filled from the next bar on:"
    one = "only one at a time: a buy signal while a position is open adds nothing" if script.pyramiding == 1 else ""
    out += ["", f"- **{script.buy} or more: Buy.** It opens a long position" + (f" ({one})." if one else ".")
            + (" Its stop loss and take profit go with the entry order (see Exits)." if script.exits_always else "")
            + (" Only from the script's \"trade from\" date (an input) and until the script expires."
               if script.dated else "")]
    low = [x for x in (script.arm, script.close) if x is not None]
    out.append(f"- **Above {max(low, key=float) if low else '-1'} and below {script.buy}: Wait.** No new order"
               + ("; an open position keeps the exits it already has." if script.arm is not None or script.exits_always
                  else "."))
    if script.arm is not None:
        out.append(f"- **{script.arm} or less: {ARM.lower()}.** With a position open, it places or moves its "
                   "stop loss and take profit (see Exits); with no position, it cancels any pending order.")
    if script.close:
        out.append(f"- **{script.close} or less: Close.** It closes the whole position at market.")
    out += ["", "It only ever buys (long positions); it never sells short."]
    if script.entry_stop:
        pct = f"{float(script.entry_stop) * 100:g}"
        out += ["", f"The entry order carries `stop = close × {script.entry_stop}`. For a buy order that is a "
                    f"stop-entry price ({pct} % of the close, below the price at that moment), so the order is "
                    "filled on the next bar; it is not a stop loss."]
    return out


def exits_section(script: Script) -> list:
    exits = script.exits
    if not exits or (script.arm is None and not script.exits_always):
        return []
    values = ", ".join(f"{exits.titles[k]} {v} %" for k, v in exits.pct.items())
    out = ["## Exits", "", f"The exits are inputs of the script, in % of the entry price (in TradingView: the "
                           f"strategy's Settings, Inputs tab): {values}."]
    if exits.stages and script.exits_always:
        out += ["", f"The exit order moves through {len(exits.stages)} stages:", ""]
        out += [_stage_line(stage, exits) for stage in exits.stages]
        out += ["", "The stop loss and the take profit are sent with the entry order, so they act from the bar "
                    "the position opens. At every bar's close, while a position is open, the stage is updated "
                    "(one step at most per bar) and the exit order is moved to that stage's stop; it stays in "
                    "force until it is filled, moved, or the position is closed."]
    elif exits.stages:
        out += ["", f"The exit order moves through {len(exits.stages)} stages:", ""]
        out += [_stage_line(stage, exits) for stage in exits.stages]
        out += ["", "The stage is updated on every bar, one step at most per bar, but the exit order is only "
                    f"placed or moved on a bar whose score is {script.arm} or less. Until the first such bar after "
                    "the entry the position has no stop loss and no take profit; once placed, the order stays "
                    f"in force while the score is above {script.arm} again, until it is filled, moved, or the "
                    "position is closed."]
    elif script.exits_always:
        out += ["", "While a position is open, the script places or moves its exit order with them (see the "
                    "Pine script for how)."]
    else:
        out += ["", f"On a bar whose score is {script.arm} or less, the script places or moves its exit order "
                    "with them (see the Pine script for how)."]
    if exits.trailing is not None:
        state = "on" if exits.trailing == "true" else "off"
        out += ["", f"The script also has an input \"activate trailing on third stage\" ({state} by default)"
                + (", but nothing in the script reads it: there is no trailing stop, whatever it is set to."
                   if not exits.trailing_used else "; see the Pine script for what it changes.")]
    return out + [""]


def to_markdown(script: Script, title: str) -> str:
    n = len(script.trees)
    out = [f"# {title}: the rules in plain words", "",
           f"Generated from the Pine script of {script.name or title} (Edgefolio). The Pine script is the "
           "product and the reference; this file explains what it decides, for people and for AI assistants.", ""]
    labels = ("Buy, Wait, " + (f"{ARM} " if script.arm is not None else "") + "and Close"
              if script.close else "Buy and Wait")
    out += ["## How it decides", "", *how_it_decides(script), "",
            "Each rule below is one leaf of a tree: when every condition holds, the tree gives that score. "
            + (f"{labels} are what the script does with that score, as above."
               if len(script.trees) == 1 and script.buy else
               "Buy and Sell mark the leaves the factory labelled as strong signals; Wait is any other leaf."), ""]
    out += exits_section(script)
    used = features(script)
    if used:
        out += ["## Values used", ""]
        for f in used:
            label, text = feature_label(f, script.bases)
            out.append(f"- `{f}`" + (f": {label}. {text}" if label else ""))
        out.append("")
    if not script.trees:
        out += ["No decision trees were found in this script.", ""]
    for tree in script.trees:
        rules = list(leaves(tree.root))
        out += [f"## Tree {tree.index + 1} of {n}" if n > 1 else "## The tree", ""]
        if tree.regressor:
            out += [f"DecisionTreeRegressor({tree.regressor})", ""]
        for k, (path, leaf) in enumerate(rules, 1):
            if leaf is None:
                out.append(f"{k}. If {plain(path)} → (not in this copy of the script)")
            else:
                out.append(f"{k}. If {plain(path)} → {action(leaf, script)} (score {leaf.value:.2f})")
        out.append("")
    return "\n".join(out)


def _code(node: Node, depth: int, lang: str) -> list:
    pad = ("    " if lang == "py" else "  ") * depth
    if node is None:
        return [pad + ('raise ValueError("this branch is not in the source script")' if lang == "py" else
                       'throw new Error("this branch is not in the source script");')]
    if isinstance(node, Leaf):
        return [pad + (f"return {node.raw}" if lang == "py" else f"return {node.raw};")]
    if lang == "py":
        return ([f'{pad}if x["{node.feat}"] <= {node.raw}:'] + _code(node.le, depth + 1, lang) +
                [f"{pad}else:"] + _code(node.gt, depth + 1, lang))
    return ([f'{pad}if (x["{node.feat}"] <= {node.raw}) {{'] + _code(node.le, depth + 1, lang) +
            [f"{pad}}} else {{"] + _code(node.gt, depth + 1, lang) + [f"{pad}}}"])


def _header(title: str) -> list:
    return [f"{title}: the decision trees of the Pine script as functions.", "", *textwrap.wrap(BETA, 100), "",
            "Each tree function takes the indicator values of one bar (name -> number, computed as the Pine",
            "script computes them; see the .md for what each one is) and returns that tree's score. score()",
            "combines the trees as the script does and signal() applies the script's thresholds. TradingView",
            "keeps the previous bar's score when a value is na; these functions expect numbers.", "",
            "The price exits (stop loss, take profits and their stages: the constants below) are NOT simulated:",
            "they act on the prices after the entry, which one bar's indicator values do not tell. They are",
            "here as data; TradingView applies them when it runs the Pine script."]


PCT_NAMES = {"sl": "STOP_LOSS_PCT", "tp1": "TAKE_PROFIT_1_PCT", "tp2": "TAKE_PROFIT_2_PCT",
             "tp3": "TAKE_PROFIT_3_PCT"}


def _constants(script: Script, lang: str) -> list:
    """BUY_AT, ARM_EXITS_AT, CLOSE_AT y las salidas como datos, en Python o en JavaScript."""
    none, start, end = ("None", "", "") if lang == "py" else ("null", "export const ", ";")
    exits = script.exits

    def const(name, value, note=""):
        return f"{start}{name} = {value if value is not None else none}{end}" + (f"  # {note}" if lang == "py" and
                                                                                  note else f" // {note}" if note else "")
    out = [const("BUY_AT", script.buy, "opens a long position when score() is at least this"),
           const("ARM_EXITS_AT", script.arm, "the exits go with the entry and are kept while a position is open"
                 if script.exits_always else "at most this: places or moves the stop loss and take profit"),
           const("CLOSE_AT", script.close, "closes the position when score() is at most this"), ""]
    out.append(("# " if lang == "py" else "// ") + "The exits, in % of the entry price (the script's inputs). "
               "Not simulated here.")
    for key, name in PCT_NAMES.items():
        out.append(const(name, exits.pct.get(key) if exits else None, exits.titles.get(key, "") if exits else ""))
    rows = []
    for stage in exits.stages if exits and (script.arm is not None or script.exits_always) else []:
        reached = exits.pct[stage.reached_at] if stage.reached_at else none
        rows.append(f'    {{"stage": {stage.n}, "from_high_pct": {reached}, "stop_pct": {stop_pct(stage, exits)}, '
                    f'"take_profit_pct": {exits.pct[stage.profit]}}},')
    mark = "# " if lang == "py" else "// "
    out += [f"{mark}Each stage: from when (the bar's high, in % above the entry price; {none}: from the entry),",
            f"{mark}then its stop and its take profit, in % from the entry price (- below, + above)."]
    out += [f"{start}STAGES = [", *rows, f"]{end}"] if rows else [f"{start}STAGES = []{end}"]
    trailing = "false" if lang == "js" else "False"
    note = ("the 'activate trailing' input exists but the script never reads it: no trailing stop"
            if exits and exits.trailing is not None and not exits.trailing_used else "")
    if exits and exits.trailing_used:
        trailing, note = none, "the script uses its 'activate trailing' input: see the Pine script"
    out += [const("TRAILING_STOP", trailing, note), ""]
    return out


def to_python(script: Script, title: str) -> str:
    out = ['"""' + "\n".join(_header(title)) + '\n"""', "", *_constants(script, "py"),
           f"INPUTS = {json.dumps(features(script))}", ""]
    for tree in script.trees:
        out += ["", f"def tree_{tree.index}(x):", f'    """{tree.name}"""'] + _code(tree.root, 1, "py") + [""]
    calls = " + ".join(f"tree_{t.index}(x)" for t in script.trees) or "0.0"
    joined = calls if script.combine == "sum" else f"({calls}) / {max(len(script.trees), 1)}"
    out += ["", "def score(x):", f"    return {joined}", "", "",
            "def signal(x):",
            '    """buy, close, arm_exits or none: what the script does with the score (the exits themselves',
            '    are not simulated)."""',
            "    s = score(x)",
            "    if BUY_AT is not None and s >= BUY_AT:", '        return "buy"',
            "    if CLOSE_AT is not None and s <= CLOSE_AT:", '        return "close"',
            "    if ARM_EXITS_AT is not None and s <= ARM_EXITS_AT:", '        return "arm_exits"',
            '    return "none"', ""]
    return "\n".join(out)


def to_javascript(script: Script, title: str) -> str:
    out = ["/*"] + [(" * " + line).rstrip() for line in _header(title)] + [" */", "", *_constants(script, "js"),
           f"export const INPUTS = {json.dumps(features(script))};", ""]
    for tree in script.trees:
        out += [f"// {tree.name}", f"export function tree{tree.index}(x) {{"] + _code(tree.root, 1, "js") + ["}", ""]
    calls = " + ".join(f"tree{t.index}(x)" for t in script.trees) or "0"
    joined = calls if script.combine == "sum" else f"({calls}) / {max(len(script.trees), 1)}"
    out += ["export function score(x) {", f"  return {joined};", "}", "",
            "// buy, close, arm_exits or none: what the script does with the score (the exits are not simulated).",
            "export function signal(x) {", "  const s = score(x);",
            '  if (BUY_AT !== null && s >= BUY_AT) return "buy";',
            '  if (CLOSE_AT !== null && s <= CLOSE_AT) return "close";',
            '  if (ARM_EXITS_AT !== null && s <= ARM_EXITS_AT) return "arm_exits";', '  return "none";', "}", ""]
    return "\n".join(out)


def readme(stem: str, title: str, contact: str) -> str:
    return "\n".join([
        f"{title} - Edgefolio", "",
        f"{stem}.pine   The strategy for TradingView: the product.",
        f"{stem}.md     The rules in plain words, generated from every tree of the script (handy for AI assistants).",
        f"{stem}.py     Python version of the trees. {BETA}",
        f"{stem}.js     JavaScript version of the trees. Beta as well, same caveat.", "",
        "Add it to TradingView:",
        f"1. Open {stem}.pine and copy all of it.",
        "2. Sign in to TradingView (the free plan works; on an intraday chart of a stock the strategy needs the",
        "   exchange's full real-time data, a paid plan: with Cboe BZX data only it trades differently).",
        "3. Open the chart of the strategy's symbol and interval.",
        "4. Open the Pine Editor, paste the script and click \"Save\".",
        "5. Click \"Add to chart\" and look at the Strategy Tester.", "",
        "Past results do not guarantee future results. Trading involves significant risk.",
        f"Questions: {contact}", ""])


def build_zip(src: str, stem: str, contact: str = "sales@tuisku.ai") -> bytes:
    """El .zip que descarga quien compra: el script y los formatos hechos de él."""
    script = parse(src)
    title = script.name or stem
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{stem}.pine", src)
        z.writestr(f"{stem}.md", to_markdown(script, title))
        z.writestr(f"{stem}.py", to_python(script, title))
        z.writestr(f"{stem}.js", to_javascript(script, title))
        z.writestr("README.txt", readme(stem, title, contact))
    return buf.getvalue()
