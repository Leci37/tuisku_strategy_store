# -*- coding: utf-8 -*-
"""El catálogo filtrado en el servidor: GET /api/strategies, /api/strategies/<id> y /api/bundles.

El panel Pro pide cada histograma y cada recuento de opciones en cada cambio, cada uno contado contra
«todos los demás filtros». Con 2.834 filas basta Python a secas si cada filtro es una máscara de bits
(un bit por fila): los recuentos son AND y popcount, nunca una vuelta por las filas.
"""
from __future__ import annotations

import math
import weakref
from datetime import date, timedelta
from typing import Optional

from .web import Refusal, invalid

# clave -> (campo de la fila, mínimo y máximo de la barra, escala logarítmica, barras): los deslizadores
# del panel Pro del diseño (§12).
RANGES = {
    "np": ("np", 200, 6_500_000, True, 36), "price": ("price", 0, 140, False, 36),
    "npp": ("npp", 0.1, 6500, True, 32), "trades": ("tr", 0, 2000, False, 32), "win": ("w", 0, 100, False, 32),
    "pf": ("pf", 1, 35_000, True, 32), "months": ("m", 0, 400, False, 32), "mlu": ("mdd", 0, 40_000, False, 32),
    "mlp": ("mddp", 0, 4, False, 32), "avg": ("avg", 1, 2_100_000, True, 32), "avgp": ("avgp", 0, 5000, False, 32),
    "bars": ("bars", 0, 8000, False, 32), "act": ("actv", 0, 3, False, 32), "candles": ("cand", 0, 500_000, False, 32),
    "prec": ("prc", 40, 100, False, 32), "tree": ("tdep", 1, 10, False, 10),
}
SELECTS = {"sym": "ticker", "tf": "interval", "ind": "key", "idx": "index", "rel": "release"}
SORTS = {"np": "np", "npp": "npp", "win": "w", "price": "price", "trades": "tr", "avg": "avg", "months": "m"}
# "hot" es el % de beneficio con los tickers por turnos: si no, la docena de variantes de un ticker
# llenaría la primera página, la cinta de tickers y el primer lote.
ORDERS = (*SORTS, "hot")
TABS = ("hot", "win", "stocks", "crypto", "new", "free")
INTERVALS = ("1Min", "3Min", "5Min", "15Min", "30Min", "1Hour", "2Hour", "4Hour", "1Day", "1Week")
EPS = 1e-6  # un tirador escrito como «200 $» tiene que dejar la fila de 199,9999 $ (la tolerancia del diseño)


def fraction(value: float, lo: float, hi: float, log: bool) -> float:
    if log:
        f = (math.log10(max(value, lo)) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))
    else:
        f = (value - lo) / (hi - lo)
    return min(1.0, max(0.0, f))


def to_mask(flags) -> int:
    """El bit i, puesto si pasa la fila i; hecho con una cadena porque desplazar en un bucle es cuadrático."""
    return int("".join(["1" if f else "0" for f in flags][::-1]) or "0", 2)


def masks_by(column: list) -> dict:
    """{valor: máscara de las filas que lo tienen}, en una pasada (None se deja fuera)."""
    n, groups = len(column), {}
    for i, v in enumerate(column):
        if v is not None:
            groups.setdefault(v, bytearray(b"0" * n))[n - 1 - i] = 49  # ord("1")
    return {v: int(buf, 2) for v, buf in groups.items()}


class Index:
    """Los valores por fila y las máscaras por valor de un catálogo, hechos una vez."""

    def __init__(self, catalogue):
        self.strategies = list(catalogue)
        rows = [s.summary for s in self.strategies]
        self.n = len(rows)
        self.everything = (1 << self.n) - 1
        self.values = {k: [r[field] for r in rows] for k, (field, *_) in RANGES.items()}
        self.bins = {}
        for k, (field, lo, hi, log, nbins) in RANGES.items():
            which = masks_by([None if v is None else min(nbins - 1, int(fraction(v, lo, hi, log) * nbins))
                              for v in self.values[k]])
            self.bins[k] = [which.get(i, 0) for i in range(nbins)]
        self.options = {}
        for k, field in SELECTS.items():
            self.options[k] = masks_by([r[field] for r in rows])
        self.labels = self._labels(rows)
        self.text = [" ".join((r["name"], r["ticker"], r["ind"], r["key"])).lower() for r in rows]
        self.free = to_mask(r["price"] == 0 for r in rows)
        self.crypto = to_mask(r["market"] == "crypto" for r in rows)
        self.order = {k: sorted(range(self.n), key=lambda i, f=field: (rows[i][f] is None, -(rows[i][f] or 0)))
                      for k, field in SORTS.items()}
        self.tickers = [r["ticker"] for r in rows]
        self.releases = [s.release_date for s in self.strategies]
        self._new = (None, 0)

    def _labels(self, rows) -> dict:
        names, icons, inds = {}, {}, {}
        for r in rows:
            # algunas filas de cripto llevan 'BINANCE:XRPUSD' como nombre: mejor uno de verdad, si alguna lo tiene
            if r["ticker"] not in names or (":" in names[r["ticker"]] and ":" not in r["name"]):
                names[r["ticker"]] = r["name"]
            icons.setdefault(r["ticker"], r["icon"])
            inds.setdefault(r["key"], r["ind"])
        return {"sym": {t: (f"{n} ({t})", icons[t]) for t, n in names.items()},
                "ind": {k: (f"{k} – {i}" if i else k, None) for k, i in inds.items()}}

    def new_mask(self, new_days: int) -> int:
        """Publicadas en los últimos NEW_DAYS días: se recalcula al cambiar el día, no en cada petición."""
        today = date.today()
        if self._new[0] != (today, new_days):
            since = today - timedelta(days=new_days)
            self._new = ((today, new_days), to_mask(d is not None and since <= d <= today for d in self.releases))
        return self._new[1]

    def range_mask(self, key: str, lo: Optional[float], hi: Optional[float]) -> int:
        lo_t = None if lo is None else lo - abs(lo) * EPS
        hi_t = None if hi is None else hi + abs(hi) * EPS
        return to_mask(v is not None and (lo_t is None or v >= lo_t) and (hi_t is None or v <= hi_t)
                       for v in self.values[key])

    def select_mask(self, key: str, values: list) -> int:
        m = 0
        for v in values:
            m |= self.options[key].get(v, 0)
        return m

    def text_mask(self, q: str) -> int:
        return to_mask(q in t for t in self.text)

    def option_list(self, key: str, within: int) -> list:
        values = list(self.options[key])
        if key == "tf":
            values.sort(key=lambda v: (INTERVALS.index(v) if v in INTERVALS else len(INTERVALS), v))
        else:
            values.sort(reverse=key == "rel")
        out = []
        for v in values:
            label, icon = self.labels.get(key, {}).get(v, (v, None))
            o = {"v": v, "label": label, "count": (within & self.options[key][v]).bit_count()}
            if icon:
                o["icon"] = icon
            out.append(o)
        return out


_indexes = weakref.WeakKeyDictionary()


def index_of(catalogue) -> Index:
    if catalogue not in _indexes:
        _indexes[catalogue] = Index(catalogue)
    return _indexes[catalogue]


TRUE, FALSE = ("1", "true", "yes", "on"), ("0", "false", "no", "off", "")


def flag(params, name: str) -> bool:
    raw = params.get(name)
    if raw is None:
        return False
    if raw.strip().lower() in TRUE:
        return True
    if raw.strip().lower() in FALSE:
        return False
    raise invalid(name)


def integer(params, name: str, default: int, lo: int, hi: Optional[int] = None) -> int:
    raw = params.get(name)
    if raw is None:
        return default
    try:
        v = int(raw)
    except ValueError:
        raise invalid(name) from None
    if v < lo or (hi is not None and v > hi):
        raise invalid(name)
    return v


def number_param(params, name: str) -> Optional[float]:
    raw = params.get(name)
    if raw is None or raw.strip() == "":
        return None
    try:
        v = float(raw)
    except ValueError:
        raise Refusal("errRequest", 400, field=name) from None
    if math.isnan(v) or math.isinf(v):
        raise Refusal("errRequest", 400, field=name)
    return v


def strategies(catalogue, settings, params) -> dict:
    """Una página de estrategias; con facets=1, además cada histograma y cada recuento del panel Pro.
    ``params`` son los de la consulta (``get`` y ``getlist``, como los de Flask)."""
    ix = index_of(catalogue)
    q = params.get("q", "")
    if len(q) > 100:
        raise invalid("q")
    tab, sort = params.get("tab", ""), params.get("sort", "")
    free, paid, facets = flag(params, "free"), flag(params, "paid"), flag(params, "facets")
    page, size = integer(params, "page", 1, 1), integer(params, "size", 25, 1, 100)
    if tab and tab not in TABS:
        raise invalid("tab")
    if sort and sort not in ORDERS:
        raise invalid("sort")

    filters = []  # (nombre, máscara): cada recuento deja fuera el suyo
    query = q.strip().lower()
    if query:
        filters.append(("q", ix.text_mask(query)))
    if tab == "stocks":
        filters.append(("tab", ix.everything & ~ix.crypto))
    elif tab == "crypto":
        filters.append(("tab", ix.crypto))
    elif tab == "new":
        filters.append(("tab", ix.new_mask(settings.new_days)))
    elif tab == "free":
        filters.append(("tab", ix.free))
    if free:
        filters.append(("free", ix.free))
    if paid:
        filters.append(("paid", ix.everything & ~ix.free))
    for key in RANGES:
        lo, hi = number_param(params, f"{key}_min"), number_param(params, f"{key}_max")
        if lo is not None or hi is not None:
            filters.append((key, ix.range_mask(key, lo, hi)))
    for key in SELECTS:
        if key in params:  # presente con sólo valores vacíos: nada marcado, no pasa nada
            values = params.getlist(key)
            if any(len(v) > 200 for v in values):
                raise invalid(key)
            filters.append((key, ix.select_mask(key, [v for v in values if v])))

    # prefix[i] = AND de los filtros antes de i; suffix[i] = AND de los filtros desde i: «todos menos uno»
    # en dos AND
    prefix, suffix = [ix.everything], [ix.everything]
    for _, m in filters:
        prefix.append(prefix[-1] & m)
    for _, m in reversed(filters):
        suffix.append(suffix[-1] & m)
    suffix.reverse()
    passing = prefix[-1]

    order = sort or ("win" if tab == "win" else "hot" if tab else "np")
    bits = format(passing, f"0{ix.n}b")[::-1] if ix.n else ""
    if order == "hot":
        # los tickers por turnos entre lo que queda (el mejor de cada uno primero, por % de beneficio): con
        # los turnos del catálogo entero, una pestaña o una búsqueda salía en un orden sin sentido
        turn, seen = {}, {}
        for i in ix.order["npp"]:
            if bits[i] == "1":
                turn[i] = seen[ix.tickers[i]] = seen.get(ix.tickers[i], -1) + 1
        hits = sorted(turn, key=turn.get)
    else:
        hits = [i for i in ix.order[order] if bits[i] == "1"]
    start = (page - 1) * size
    body = {"total": len(hits), "page": page, "size": size,
            "rows": [catalogue.row(ix.strategies[i]) for i in hits[start:start + size]],
            "counts": {"all": ix.n, "new": ix.new_mask(settings.new_days).bit_count()}}

    if facets:
        positions = {name: i for i, (name, _) in enumerate(filters)}

        def others(name: str) -> int:
            i = positions.get(name)
            return passing if i is None else prefix[i] & suffix[i + 1]

        body["hist"] = {k: [(others(k) & b).bit_count() for b in ix.bins[k]] for k in RANGES}
        body["ranges"] = {k: {"min": lo, "max": hi, "log": log, "bins": n} for k, (_, lo, hi, log, n) in RANGES.items()}
        body["options"] = {k: ix.option_list(k, others(k)) for k in SELECTS}
    return body


def strategy(catalogue, strategy_id: str) -> dict:
    s = catalogue.resolve(strategy_id)
    if not s:
        raise Refusal("errUnknownStrategy", 404)
    return catalogue.detail(s)


def bundles(catalogue, settings) -> dict:
    # El «antes» de la tarjeta del pack sin nada elegido: PACK_SIZE estrategias al precio mediano de las de
    # pago, un pack típico (la media se inclinaría hacia las pocas caras; las cinco más caras lo
    # exagerarían). Con las estrategias elegidas, el presupuesto da el «antes» y el ahorro de ese pack.
    return {"bundles": [b.as_dict() for b in catalogue.bundles.values()],
            "pack": {"size": settings.pack_size, "price": float(settings.pack_price),
                     "was": float(settings.pack_size * catalogue.median_paid_price)}}
