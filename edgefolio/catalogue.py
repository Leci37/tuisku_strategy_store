# -*- coding: utf-8 -*-
"""Las estrategias a la venta, leídas de catalogue/catalogue.csv: el único sitio de donde salen los precios.

A su lado: indicators.csv (qué es cada indicador, en los idiomas de la tienda, para la página de la estrategia),
bundles.json (los lotes y sus precios), release.json (de qué ejecución del generador es: entre cuántas estrategias
probadas se eligieron) y, si existen, since_release.csv: cuánto lleva cada una desde su publicación (id, pct,
as_of), y levels.json, los niveles de cada script (levels.py). Y de la vista previa publicada de cada una
(static/assets/previews/), la «Expiry date» de la cabecera de su script.
"""
from __future__ import annotations

import base64
import binascii
import csv
import json
import logging
import math
import re
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from functools import cached_property
from pathlib import Path

from .levels import load as load_levels
from .settings import GRADE_CUTOFFS, Settings

log = logging.getLogger(__name__)

TV_SCRIPTS = "https://www.tradingview.com/scripts/"
EXPIRY = re.compile(r"Expiry date:\s*(\d{4})/(\d{2})/(\d{2})")

# Columna del CSV -> (campo de la fila, tipo). Cualquiera puede faltar o estar vacía: la fila dice null.
NUMBERS = {
    "Net Profit_usd": ("np", float), "Net Profit_per": ("npp", float), "Total Closed Trades": ("tr", int),
    "Percent Profitable_per": ("w", float), "Profit Factor": ("pf", float), "Max Drawdown_usd": ("mdd", float),
    "Max Drawdown_per": ("mddp", float), "Avg Trade_usd": ("avg", float), "Avg Trade_per": ("avgp", float),
    "Avg # Bars in Trades": ("bars", float), "months_trained": ("m", int), "n_candles": ("cand", float),
    "Precision f1_per": ("prc", float), "Tree Deep": ("tdep", int),
    # operaciones por vela del backtest, como la escribe el generador: la maqueta del diseño, sin esa columna,
    # ponía operaciones por mes de entrenamiento, otra unidad bajo el mismo nombre
    "Trade Activity Per Candle": ("actv", float),
}


def b64url(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")


def unb64url(text: str) -> str:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4)).decode()


def number(raw, kind=float):
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return int(round(v)) if kind is int else v


def asset(path: str) -> str:
    """El catálogo guarda 'assets/...' relativo a static/; la página también corre en /s/<id>."""
    return "/static/" + path.lstrip("/") if path else ""


def grade(trades, cutoffs: tuple = GRADE_CUTOFFS) -> str:
    """Cuánta prueba tiene el backtest: sus operaciones cerradas contra los cortes de A, B y C (GRADE_CUTOFFS)."""
    t, (a, b, c) = trades or 0, cutoffs
    return "A" if t >= a else "B" if t >= b else "C" if t >= c else "D"


def script_expiry(path: Path):
    """La «Expiry date» de la cabecera de un script (``// ID_model: … Date Creation: … Expiry date: 2027/06/13``, la
    misma en su vista previa pública), o None sin ella. Desde ese día, a las 00:00 UTC, el script no abre operaciones
    (``isExpired = time >= expiryTime``)."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            head = f.read(4096)   # la cabecera son las primeras líneas
    except OSError:
        return None
    m = EXPIRY.search(head)
    try:
        return date(int(m[1]), int(m[2]), int(m[3])) if m else None
    except ValueError:
        return None


def read_release(path: Path) -> dict:
    """release.json, o {} sin él (un catálogo publicado con la forma de antes de los paquetes) o roto."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


@dataclass(frozen=True)
class Strategy:
    ticker: str
    interval: str
    key_techs: str
    id_model: str
    price: Decimal
    row: dict = field(repr=False, compare=False)  # la fila entera del catálogo
    live: float = None        # % desde la publicación, de since_release.csv; None hasta que haya cifra
    live_as_of: str = None
    new_days: int = 30
    grade_cutoffs: tuple = GRADE_CUTOFFS
    expiry: date = None       # la «Expiry date» de su script publicado (su vista previa); None si no la dice
    ind_name: str = None      # el nombre de su indicador en indicators.csv; sin él, el de la fila del catálogo

    @property
    def id(self) -> str:
        """El id de la URL (/s/<id>) y la raíz del nombre de sus gráficos."""
        return f"{self.ticker}_{self.interval}_{self.key_techs}_{self.id_model}"

    @property
    def key(self) -> str:
        """El id que guardan los pedidos y los enlaces (y el del carrito de antes, sin base64)."""
        return f"{self.ticker} - {self.interval} - {self.key_techs} - {self.id_model}"

    @property
    def private_file(self) -> str:
        """El nombre del script de pago en STRATEGIES_DIR, el que le da la fábrica (pine_TW_b/)."""
        return b64url(f"{self.ticker}_{self.interval}_{self.key_techs}tuisku{self.id_model}") + ".pine"

    @property
    def download_name(self) -> str:
        """El .pine que se lleva quien compra: con el nombre del script en TradingView, el tutorial y el zip."""
        return f"{self.file}.pine"

    @property
    def file(self) -> str:
        """El nombre del script dentro de TradingView, y la base del nombre de cada formato."""
        return f"Tuisku_{self.id}"

    @property
    def market(self) -> str:
        return "crypto" if self.row.get("Index") == "CRYPTO" else "stocks"

    @property
    def tv_symbol(self) -> str:
        if self.market == "crypto":
            return f"BINANCE:{self.ticker}"
        return f"{self.row.get('Index') or 'NASDAQ'}:{self.ticker}"

    @property
    def grade(self) -> str:
        return grade(self.numbers["tr"], self.grade_cutoffs)

    @property
    def version(self) -> int:
        return number(self.row.get("version"), int) or 1

    @property
    def release(self) -> str:
        return (self.row.get("Release date") or "").strip()[:10]

    @property
    def release_date(self):
        try:
            return date.fromisoformat(self.release)
        except ValueError:
            return None

    @property
    def is_new(self) -> bool:
        d = self.release_date
        return bool(d) and date.today() - timedelta(days=self.new_days) <= d <= date.today()

    @property
    def expired(self) -> bool:
        """Si su script ya caducó (desde su «Expiry date», a las 00:00 UTC, no abre operaciones): su versión nueva
        deja de darse gratis a quien tiene una de antes (decisión del dueño, 2026-10-26)."""
        return self.expiry is not None and datetime.now(timezone.utc).date() >= self.expiry

    def serves(self, version: int, paid: bool = True) -> bool:
        """Si un enlace de la versión ``version`` (de pago; con ``paid=False``, de una gratis) da el script de hoy, el único
        que guarda la tienda. El de su versión, siempre; el de una de antes, mientras la estrategia no ha caducado (la
        versión nueva es gratis hasta su «Expiry date»; decisión del dueño, 2026-10-26); el de una gratis, siempre. Lo
        miran Mis estrategias, renovar (API #16) y la descarga (API #10): si no, el enlace de antes, aún válido, daría la
        versión nueva."""
        return not paid or version >= self.version or not self.expired

    @cached_property
    def numbers(self) -> dict:
        return {name: number(self.row.get(col), kind) for col, (name, kind) in NUMBERS.items()}

    @cached_property
    def summary(self) -> dict:
        """Los campos de la fila que no cambian mientras corre el servidor (is_new sí, a medianoche)."""
        r = self.row
        stems = {k: Path(r.get(col) or "").stem for k, col in (("profit", "path_stra"), ("candle", "path_candle"))}
        return {
            "id": self.id, "ticker": self.ticker, "interval": self.interval, "key": self.key_techs,
            "hash": self.id_model, "name": r.get("Name") or self.ticker, "ind": self.ind_name or r.get("Full Indicator Name") or "",
            "index": r.get("Index") or "", "market": self.market, "price": number(self.price) or 0,
            **self.numbers, "release": self.release, "version": self.version,
            "profit": asset(r.get("path_stra")), "candle": asset(r.get("path_candle")),
            "icon": asset(r.get("path_ico_big")), "preview": asset(r.get("pine_path_shadow")),
            "thumb_profit": f"/thumbs/{stems['profit']}.webp" if stems["profit"] else "",
            "thumb_candle": f"/thumbs/{stems['candle']}.webp" if stems["candle"] else "",
            "grade": self.grade, "tv_symbol": self.tv_symbol, "file": self.file,
        }

    def as_row(self) -> dict:
        return {**self.summary, "live": self.live, "live_as_of": self.live_as_of, "is_new": self.is_new}


@dataclass(frozen=True)
class Bundle:
    key: str
    name_key: str          # la clave de su nombre en el diccionario
    items: tuple           # Strategy, ...
    price: Decimal

    @property
    def was(self) -> Decimal:
        return sum((s.price for s in self.items), Decimal("0"))

    def as_dict(self) -> dict:
        return {"key": self.key, "name_key": self.name_key, "ids": [s.id for s in self.items],
                "price": number(self.price), "was": number(self.was)}


def read_table(path: Path) -> list:
    """Un CSV pequeño, separado por comas o por tabuladores (indicators.csv, lo primero; las pruebas, lo segundo)."""
    if not path or not path.is_file():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        head = f.readline()
        f.seek(0)
        return list(csv.DictReader(f, delimiter="\t" if "\t" in head else ","))


def clean(value) -> str:
    v = (value or "").strip()
    return "" if v in ("--", "-") else v


class Catalogue:
    def __init__(self, source):
        """source: los Settings, o la ruta de catalogue.csv con sus compañeros al lado."""
        if not isinstance(source, Settings):
            path = Path(source)
            source = Settings(catalogue=path, indicators=path.parent / "indicators.csv",
                              bundles=path.parent / "bundles.json", since_release=path.parent / "since_release.csv",
                              levels=path.parent / "levels.json")
        # indicators.csv es de la tienda: el nombre de cada indicador, su página y su autor y la explicación, revisados
        # con el código del generador. Se lee antes que el catálogo para que el nombre que se enseña salga de él, el
        # mismo de la explicación y del enlace (la fila del catálogo trae el del generador, que puede quedarse atrás)
        self.indicators = {}
        for r in read_table(source.indicators):
            lower = {k.strip().lower(): v for k, v in r.items() if k}
            if clean(lower.get("key")):
                # la explicación, en inglés («Explanation») y en cada idioma con su columna («Explanation_es»…)
                texts = {"en": clean(lower.get("explanation")),
                         **{k.split("_", 1)[1]: clean(v) for k, v in lower.items() if k.startswith("explanation_")}}
                self.indicators[clean(lower["key"])] = {
                    "ind_name": clean(lower.get("full indicator name")),
                    "ind_texts": {lang: text for lang, text in texts.items() if text},
                    "ind_url": clean(lower.get("traderview url indicator")) or TV_SCRIPTS,
                    "ind_author": clean(lower.get("author")),
                }
        live = {r.get("id"): r for r in read_table(source.since_release)}
        self.items = {}   # por clave: lo que guardan los pedidos y los enlaces
        self.by_id = {}
        with open(source.catalogue, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                s = Strategy(row["ticker"], row["interval"], row["key_techs"], row["id_model"],
                             Decimal(row["Price"]).quantize(Decimal("0.01")), row, new_days=source.new_days,
                             grade_cutoffs=source.grade_cutoffs,
                             ind_name=self.indicators.get(row["key_techs"], {}).get("ind_name") or None)
                if s.id in live:
                    s = replace(s, live=number(live[s.id].get("pct")), live_as_of=live[s.id].get("as_of") or None)
                preview = (row.get("pine_path_shadow") or "").strip()
                if preview:
                    s = replace(s, expiry=script_expiry(Path(source.static) / preview))
                if s.key not in self.items:
                    self.items[s.key] = s
                    self.by_id[s.id] = s
        # cuántas tienen cifra desde su publicación: sin ninguna, la página no habla de ello
        self.since_release = sum(1 for s in self.items.values() if s.live is not None)
        # release.json va siempre al lado de catalogue.csv (publish.py). Entre cuántas estrategias probadas se
        # eligieron, si el generador lo dijo; uno que no puede ser (menos que las que hay) no se cuenta
        tried = read_release(Path(source.catalogue).parent / "release.json").get("tried")
        self.tried = tried if type(tried) is int and tried >= len(self.items) > 0 else None
        self.bundles = self._bundles(source.bundles)
        self.levels = load_levels(source.levels)

    def _bundles(self, path: Path) -> dict:
        """Los lotes de bundles.json que siguen siendo lo que prometen. Uno que perdió una estrategia, o que ya
        no cuesta menos que sus estrategias sueltas, se deja fuera entero (y va al log): vender lo que queda de
        él al precio de antes sería otro lote distinto del anunciado."""
        if not path or not path.is_file():
            return {}
        out = {}
        for b in json.loads(path.read_text(encoding="utf-8")):
            ids = b.get("ids", [])
            items = [self.resolve(i) for i in ids]
            gone = [i for i, s in zip(ids, items) if not s]
            if gone or not items:
                log.error("lote %s fuera: %s", b.get("key"),
                          f"no están en el catálogo: {', '.join(gone)}" if gone else "no tiene estrategias")
                continue
            bundle = Bundle(b["key"], b.get("name_key", b["key"]), tuple(items),
                            Decimal(str(b["price"])).quantize(Decimal("0.01")))
            if bundle.price >= bundle.was:
                log.error("lote %s fuera: su precio, %s, no es menor que el de sus estrategias, %s", bundle.key,
                          bundle.price, bundle.was)
                continue
            out[bundle.key] = bundle
        return out

    @cached_property
    def median_paid_price(self) -> Decimal:
        prices = sorted(s.price for s in self.items.values() if s.price > 0)
        if not prices:
            return Decimal("0")
        mid = len(prices) // 2
        return prices[mid] if len(prices) % 2 else ((prices[mid - 1] + prices[mid]) / 2).quantize(Decimal("0.01"))

    @cached_property
    def best_npp(self):
        """El mejor % de beneficio de los backtests del catálogo (None si ninguno lo tiene): la escala de las
        barras «Backtest» y «Desde su publicación» de la página de la estrategia."""
        return max((s.numbers["npp"] for s in self if s.numbers["npp"] is not None), default=None)

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items.values())

    def resolve(self, item_id: str):
        """Vale el id (AAPL_1Day_1C00_ac87f0dc), la clave 'T - I - K - H' o su base64 del carrito de antes."""
        if item_id in self.by_id:
            return self.by_id[item_id]
        if item_id in self.items:
            return self.items[item_id]
        try:
            return self.items.get(unb64url(item_id))
        except (binascii.Error, UnicodeDecodeError, ValueError):
            return None

    def explanation(self, s: Strategy, lang: str) -> tuple:
        """(texto, idioma) de la explicación del indicador de ``s`` en ``lang``; sin ella, la inglesa, y su idioma lo
        dice (la página la marca con lang="en" sólo entonces)."""
        texts = self.indicators.get(s.key_techs, {}).get("ind_texts", {})
        if texts.get(lang):
            return texts[lang], lang
        return (texts["en"], "en") if texts.get("en") else ("", lang)

    def row(self, s: Strategy, lang: str = "en") -> dict:
        """La fila de una lista: la de la estrategia y su indicador (la página de TradingView a la que lleva
        «CLAVE · indicador» en las fichas de Pro, y su explicación al pasar por encima, en ``lang``: el idioma de
        la petición; ``ind_lang``, el de la explicación)."""
        text, text_lang = self.explanation(s, lang)
        return {**s.as_row(), "ind_text": text, "ind_lang": text_lang,
                "ind_url": self.indicators.get(s.key_techs, {}).get("ind_url", TV_SCRIPTS)}

    def detail(self, s: Strategy, lang: str = "en") -> dict:
        """La de una estrategia (API #3): la fila, el autor del indicador, sus versiones y los niveles de su script,
        con los que el árbol del visitante dice comprar, vender o esperar (null si la tienda no los tiene)."""
        ind = self.indicators.get(s.key_techs, {})
        versions = [{"v": v, "date": s.release if v == s.version else None, "note": ""}
                    for v in range(s.version, 0, -1)]
        levels = self.levels.get(s.id, {})
        return {**self.row(s, lang), "ind_author": ind.get("ind_author", ""), "versions": versions,
                "buy_at": levels.get("buy_at"), "close_at": levels.get("close_at")}
