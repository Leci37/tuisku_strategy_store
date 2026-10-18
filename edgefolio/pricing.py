# -*- coding: utf-8 -*-
"""Los precios y los descuentos, sólo en el servidor. El navegador manda ids, claves de lotes y un código.

Un carrito son estrategias sueltas, lotes (catalogue/bundles.json) y como mucho un «Crea tu pack»
(PACK_SIZE estrategias de pago por PACK_PRICE, o por la suma de sus precios si es menor: un pack de
estrategias baratas nunca cuesta más que comprarlas sueltas). Una estrategia que va en un lote elegido o en
el pack no se cobra otra vez suelta, y un carrito cuyos lotes (o un lote y el pack) comparten una estrategia
se rechaza (overlap): cada uno la cobraría.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from .settings import Settings

CENT = Decimal("0.01")
ZERO = Decimal("0")


def cents(value: Decimal) -> Decimal:
    return value.quantize(CENT, ROUND_HALF_UP)


@dataclass
class Quote:
    items: list            # [(Strategy, lo que se cobra)]: las sueltas
    subtotal: Decimal      # precios del catálogo: sueltas + lotes + pack
    discount_rate: Decimal
    total: Decimal
    code: str              # como se tecleó, en minúsculas ('' si no hay)
    code_status: str       # '' | 'applied' | 'invalid'
    bundles: list = field(default_factory=list)   # [(Bundle, lo que se cobra)]
    pack: tuple = None                             # ([Strategy], lo que se cobra) o None
    tier_rate: Decimal = ZERO
    code_rate: Decimal = ZERO
    tier_index: int = 0       # cuántos escalones por importe ha pasado el subtotal
    next_tier: dict = None    # {over, rate, missing} del siguiente; None si no queda (o no se aplica)

    @property
    def strategies(self) -> list:
        """Cada estrategia que se lleva quien compra, una vez: lo que guarda el pedido y para lo que hay enlace."""
        out = {s.key: s for s, _ in self.items}
        for b, _ in self.bundles:
            out.update((s.key, s) for s in b.items)
        if self.pack:
            out.update((s.key, s) for s in self.pack[0])
        return list(out.values())

    def lines(self) -> dict:
        return {
            "items": [{"id": s.id, "price": str(p)} for s, p in self.items],
            "bundles": [{"key": b.key, "price": str(p)} for b, p in self.bundles],
            "pack": pack_line(*self.pack) if self.pack else None,
        }

    def as_dict(self) -> dict:
        return {
            **self.lines(),
            "subtotal": str(self.subtotal),
            "tier_rate": str(self.tier_rate),
            "code_rate": str(self.code_rate),
            "discount_rate": str(self.discount_rate),
            "discount": str((self.subtotal - self.total).quantize(CENT)),
            "total": str(self.total),
            "code_status": self.code_status,
            "tier_index": self.tier_index,
            "next_tier": self.next_tier,
        }


def pack_line(strategies: list, price: Decimal, list_price: Decimal) -> dict:
    """El pack como lo enseña el carrito: `price`, lo que cobra este carrito por él (después del escalón o
    del código); `was`, sus estrategias sueltas; y `save`, lo que ahorra el pack por sí mismo frente a ellas,
    1 - list_price/was ("0" si nada): el escalón y el código se enseñan aparte."""
    was = sum((s.price for s in strategies), ZERO).quantize(CENT)
    save = (1 - list_price / was).quantize(CENT, ROUND_HALF_UP) if was > 0 and list_price < was else ZERO
    return {"ids": [s.id for s in strategies], "price": str(price), "was": str(was),
            "save": str(save) if save > 0 else "0"}


def ladder(subtotal: Decimal, settings: Settings) -> tuple:
    """(cuántos escalones ha pasado el subtotal, el siguiente), con la regla de tier_rate: un escalón vale
    sólo por encima de su umbral, así que con 160 $ justos al del 15 % aún le falta 0,01 $."""
    tiers = sorted(settings.tiers)  # el umbral más bajo, primero
    passed = sum(1 for over, _ in tiers if subtotal > over)
    if passed == len(tiers):
        return passed, None
    over, rate = tiers[passed]
    return passed, {"over": str(over), "rate": str(rate), "missing": str((over - subtotal + CENT).quantize(CENT))}


def tier_rate(subtotal: Decimal, settings: Settings) -> Decimal:
    for over, rate in settings.tiers:  # el umbral más alto, primero
        if subtotal > over:
            return rate
    return ZERO


def overlap(bundles: list, pack: list = ()) -> list:
    """Las estrategias que están a la vez en dos de los lotes elegidos, o en un lote y en el pack."""
    groups = [{s.key for s in b.items} for b in {b.key: b for b in bundles}.values()]
    groups.append({s.key for s in pack})
    seen, twice = set(), set()
    for keys in groups:
        twice |= seen & keys
        seen |= keys
    every = {s.key: s for b in bundles for s in b.items} | {s.key: s for s in pack}
    return [every[k] for k in sorted(twice)]


def quote(strategies: list, code: str, settings: Settings, bundles: list = (), pack: list = ()) -> Quote:
    """Una de cada estrategia y de cada lote; un código de precio único cambia el de cada suelta y, si no,
    el escalón por importe y el código se suman, con el tope de MAX_DISCOUNT: un total nunca llega a cero."""
    chosen = list({b.key: b for b in bundles}.values())
    pack = list({s.key: s for s in pack}.values())
    covered = {s.key for b in chosen for s in b.items} | {s.key for s in pack}
    loose = [s for s in {s.key: s for s in strategies}.values() if s.key not in covered]
    pack_price = min(settings.pack_price, sum((s.price for s in pack), ZERO)).quantize(CENT) if pack else ZERO
    fixed = sum((b.price for b in chosen), ZERO) + pack_price
    subtotal = (sum((s.price for s in loose), ZERO) + fixed).quantize(CENT)
    code = (code or "").strip().lower()
    if code and code in settings.flat_price_codes:
        # un precio de lanzamiento para las sueltas: los lotes y el pack ya son una oferta, sin escalón encima
        flat = settings.flat_price_codes[code].quantize(CENT)
        charged = [(s, min(flat, s.price)) for s in loose]
        total = (sum((p for _, p in charged), ZERO) + fixed).quantize(CENT)
        return Quote(charged, subtotal, ZERO, total, code, "applied", [(b, b.price) for b in chosen],
                     (pack, pack_price, pack_price) if pack else None)
    code_rate = settings.discount_codes.get(code, ZERO) if code else ZERO
    status = "" if not code else ("applied" if code in settings.discount_codes else "invalid")
    tier = tier_rate(subtotal, settings)
    rate = min(tier + code_rate, settings.max_discount)
    off = 1 - rate
    passed, upcoming = ladder(subtotal, settings)
    return Quote([(s, cents(s.price * off)) for s in loose], subtotal, rate, cents(subtotal * off), code, status,
                 [(b, cents(b.price * off)) for b in chosen], (pack, cents(pack_price * off), pack_price) if pack else None,
                 tier, code_rate, passed, upcoming)
