# -*- coding: utf-8 -*-
"""Los niveles de cada script: con qué puntuación del bosque compra (``buyThreshold``) y con cuál cierra
(``sellThreshold``). El generador los elige para cada modelo, así que cada script tiene los suyos.

El árbol del visitante («Cómo decide») sólo tiene la vista previa pública, que se corta antes de esas líneas: sin
ellos no puede decir qué hace el script con un resultado. La tienda los publica en catalogue/levels.json, junto al
catálogo, leídos de cada script completo como los lee edgefolio/formats.py: los escribe la importación de un paquete
(release.py) y, para el catálogo ya publicado, ``flask --app app edgefolio levels`` desde STRATEGIES_DIR. API #3 los
manda (``buy_at``, ``close_at``).

Sólo vale el script de la propia estrategia, el que lleva su nombre (``strategy("Tuisku_<id>")``, Strategy.file): uno
que dice ser de otra (una copia de prueba, como las de la historia del repo) se deja fuera, y se dice.

Sin Flask: el comando (cli.py) sólo pasa la configuración y enseña el resumen.
"""
from __future__ import annotations

import json
import logging
import math
import os
from pathlib import Path
from typing import Iterable, Optional

from . import formats

log = logging.getLogger(__name__)

FILE = "levels.json"   # al lado de catalogue.csv


def title_of(strategy_id: str) -> str:
    """El nombre del script en TradingView, el que le pone la fábrica (Strategy.file)."""
    return f"Tuisku_{strategy_id}"


def number(raw) -> Optional[float]:
    if isinstance(raw, bool):
        return None
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def of_script(src: str, strategy_id: str) -> tuple:
    """(niveles, por qué no): {buy_at, close_at} del script ``src`` si es el de la estrategia ``strategy_id``; si no,
    None y por qué: «other» (es el de otra) o «none» (no dice con qué compra)."""
    script = formats.parse(src)
    if script.name != title_of(strategy_id):
        return None, "other"
    buy = number(script.buy)
    if buy is None:
        return None, "none"
    return {"buy_at": buy, "close_at": number(script.close)}, ""


def collect(items: Iterable) -> tuple:
    """Los niveles (id → {buy_at, close_at}) y el recuento de ``items``: (id de la estrategia, el texto de su script
    completo, o None si no está)."""
    found, count = {}, {"levels": 0, "missing": 0, "other": 0, "none": 0}
    for strategy_id, src in items:
        if src is None:
            count["missing"] += 1
            continue
        levels, why = of_script(src, strategy_id)
        if levels is None:
            count[why] += 1
        else:
            found[strategy_id] = levels
            count["levels"] += 1
    return found, count


def dumps(levels: dict) -> bytes:
    """Una estrategia por línea y por orden: un cambio de niveles se lee en el diff del repo."""
    lines = [f"  {json.dumps(k)}: {json.dumps(v, sort_keys=True)}" for k, v in sorted(levels.items())]
    return ("{\n" + ",\n".join(lines) + ("\n" if lines else "") + "}\n").encode("utf-8")


def write(path: Path, levels: dict):
    """Al lado y renombrado: la tienda que arranca mientras tanto nunca lee medio fichero."""
    path = Path(path)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_bytes(dumps(levels))
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def load(path) -> dict:
    """id → {buy_at, close_at} de catalogue/levels.json ({} si no está). Una entrada que no vale se deja fuera, y va al
    log: sin niveles, el árbol del visitante enseña la puntuación de cada resultado, nunca unos que no son del script."""
    path = Path(path) if path else None
    if path is None or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        log.error("%s no se lee: %s", path, e)
        return {}
    out, bad = {}, []
    for strategy_id, v in (data.items() if isinstance(data, dict) else ()):
        buy = number(v.get("buy_at")) if isinstance(v, dict) else None
        close = number(v.get("close_at")) if isinstance(v, dict) else None
        if buy is None or (v.get("close_at") is not None and close is None):
            bad.append(str(strategy_id))
            continue
        out[str(strategy_id)] = {"buy_at": buy, "close_at": close}
    if bad or not isinstance(data, dict):
        log.error("%s: entradas que no valen, fuera: %s", path, ", ".join(bad) or "no es un objeto")
    return out


def summary(count: dict, total: int) -> str:
    """Lo que dicen la importación y el comando: cuántas tienen sus niveles y por qué no los demás."""
    out = f"catalogue/{FILE}: {count['levels']} de {total} estrategias con los niveles de su script"
    why = [(count["missing"], "sin su script"),
           (count["other"], "cuyo script es el de otra estrategia (¿una copia de prueba?)"),
           (count["none"], "cuyo script no dice con qué compra")]
    said = [f"{n} {text}" for n, text in why if n]
    if said:
        out += "; " + ", ".join(said) + ": en su árbol, el visitante ve la puntuación de cada resultado"
    return out
