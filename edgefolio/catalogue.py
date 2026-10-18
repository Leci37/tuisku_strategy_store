# -*- coding: utf-8 -*-
"""Las estrategias a la venta, leídas de catalogue/catalogue.csv: el único sitio de donde salen los precios.

A su lado: indicators.csv (qué es cada indicador, para la página de la estrategia), bundles.json (los
lotes y sus precios) y, si existe, since_release.csv, que escribe el trabajo diario.
"""
from __future__ import annotations

import base64
import binascii
import csv
import json
import logging
import math
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from decimal import Decimal
from functools import cached_property
from pathlib import Path

from .settings import Settings

log = logging.getLogger(__name__)

TV_SCRIPTS = "https://www.tradingview.com/scripts/"

# Columna del CSV -> (campo de la fila, tipo). Cualquiera puede faltar o estar vacía: la fila dice null.
NUMBERS = {
    "Net Profit_usd": ("np", float), "Net Profit_per": ("npp", float), "Total Closed Trades": ("tr", int),
    "Percent Profitable_per": ("w", float), "Profit Factor": ("pf", float), "Max Drawdown_usd": ("mdd", float),
    "Max Drawdown_per": ("mddp", float), "Avg Trade_usd": ("avg", float), "Avg Trade_per": ("avgp", float),
    "Avg # Bars in Trades": ("bars", float), "months_trained": ("m", int), "n_candles": ("cand", float),
    "Precision f1_per": ("prc", float), "Tree Deep": ("tdep", int),
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


def grade(trades) -> str:
    """Cuánta prueba tiene el backtest: los cortes del diseño (aún por acordar)."""
    t = trades or 0
    return "A" if t >= 300 else "B" if t >= 100 else "C" if t >= 30 else "D"


@dataclass(frozen=True)
class Strategy:
    ticker: str
    interval: str
    key_techs: str
    id_model: str
    price: Decimal
    row: dict = field(repr=False, compare=False)  # la fila entera del catálogo
    live: float = None        # % desde la publicación, del trabajo diario; None hasta que corra
    live_as_of: str = None
    new_days: int = 30

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
        return grade(self.numbers["tr"])

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

    @cached_property
    def numbers(self) -> dict:
        out = {name: number(self.row.get(col), kind) for col, (name, kind) in NUMBERS.items()}
        out["actv"] = out["tr"] / out["m"] if out["tr"] is not None and out["m"] else None
        return out

    @cached_property
    def summary(self) -> dict:
        """Los campos de la fila que no cambian mientras corre el servidor (is_new sí, a medianoche)."""
        r = self.row
        stems = {k: Path(r.get(col) or "").stem for k, col in (("profit", "path_stra"), ("candle", "path_candle"))}
        return {
            "id": self.id, "ticker": self.ticker, "interval": self.interval, "key": self.key_techs,
            "hash": self.id_model, "name": r.get("Name") or self.ticker, "ind": r.get("Full Indicator Name") or "",
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
                              bundles=path.parent / "bundles.json", since_release=path.parent / "since_release.csv")
        live = {r.get("id"): r for r in read_table(source.since_release)}
        self.items = {}   # por clave: lo que guardan los pedidos y los enlaces
        self.by_id = {}
        with open(source.catalogue, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                s = Strategy(row["ticker"], row["interval"], row["key_techs"], row["id_model"],
                             Decimal(row["Price"]).quantize(Decimal("0.01")), row, new_days=source.new_days)
                if s.id in live:
                    s = replace(s, live=number(live[s.id].get("pct")), live_as_of=live[s.id].get("as_of") or None)
                if s.key not in self.items:
                    self.items[s.key] = s
                    self.by_id[s.id] = s
        self.indicators = {}
        for r in read_table(source.indicators):
            lower = {k.strip().lower(): v for k, v in r.items() if k}
            if clean(lower.get("key")):
                self.indicators[clean(lower["key"])] = {
                    "ind_text": clean(lower.get("explanation")),
                    "ind_url": clean(lower.get("traderview url indicator")) or TV_SCRIPTS,
                    "ind_author": clean(lower.get("author")),
                }
        self.bundles = self._bundles(source.bundles)

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

    def row(self, s: Strategy) -> dict:
        """La fila de una lista: la de la estrategia y su indicador (la página de TradingView a la que lleva
        «CLAVE · indicador» en las fichas de Pro, y su explicación al pasar por encima)."""
        ind = self.indicators.get(s.key_techs, {})
        return {**s.as_row(), "ind_text": ind.get("ind_text", ""), "ind_url": ind.get("ind_url", TV_SCRIPTS)}

    def detail(self, s: Strategy) -> dict:
        ind = self.indicators.get(s.key_techs, {})
        versions = [{"v": v, "date": s.release if v == s.version else None, "note": ""}
                    for v in range(s.version, 0, -1)]
        return {**self.row(s), "ind_author": ind.get("ind_author", ""), "versions": versions}
