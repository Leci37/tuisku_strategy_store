# -*- coding: utf-8 -*-
"""La configuración de la tienda, del entorno: ni un secreto ni un código de descuento en el código.

Lo común (la sesión, la base de datos, el correo, la dirección pública, los idiomas) es del núcleo y
se configura con sus variables (CONTRATO.md del núcleo, §3). Lo propio de la tienda:

PAYPAL_MODE           fake (por defecto: sin PayPal, para trabajar en local y en las pruebas) | sandbox | live
PAYPAL_CLIENT_ID      el id público de la app REST de PayPal
PAYPAL_CLIENT_SECRET  sólo en el servidor
STRATEGIES_DIR        la carpeta privada con los .pine de pago (por defecto <datos>/edgefolio/strategies)
DISCOUNT_CODES        pares código=porcentaje: "spring20=0.20,partner40=0.40"
FLAT_PRICE_CODES      pares código=precio que ponen un mismo precio a cada estrategia suelta: "launch=0.99"
MAX_DISCOUNT          el tope del descuento por importe más el del código juntos (0.70)
DOWNLOAD_DAYS         lo que vale un enlace de descarga, en días (7)
MAX_DOWNLOADS         las descargas de cada enlace (10)
PACK_SIZE, PACK_PRICE «Crea tu pack»: cuántas estrategias y por cuánto (5 por 249)
NEW_DAYS              los días que una estrategia sale en «Nuevas» desde que se publicó (30)
CONTACT_EMAIL         la dirección que la página da para los problemas (sales@tuisku.eu)

Con PayPal de verdad (sandbox o live) hace falta ZLECITOOL_PUBLIC_URL: el enlace de vuelta de PayPal se
hace con ella y nunca con la cabecera Host, que la escribe quien pide.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Mapping, Optional

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
CATALOGUE = ROOT / "catalogue"

# El descuento por importe del pedido, como lo aplicaba la página de antes: más de 2.500 $ → 70 %…
DEFAULT_TIERS = ((Decimal("2500"), Decimal("0.70")), (Decimal("1000"), Decimal("0.40")),
                 (Decimal("500"), Decimal("0.25")), (Decimal("290"), Decimal("0.20")),
                 (Decimal("160"), Decimal("0.15")))
PAYPAL_MODES = ("fake", "sandbox", "live")


def _pairs(raw: str) -> dict:
    out = {}
    for part in (raw or "").split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            if k.strip():
                out[k.strip().lower()] = Decimal(v.strip())
    return out


@dataclass
class Settings:
    paypal_mode: str = "fake"
    paypal_client_id: str = ""
    paypal_client_secret: str = ""
    currency: str = "USD"
    # Lo privado y lo que se hace solo, dentro de la carpeta de datos de la herramienta.
    strategies_dir: Path = Path("data") / "edgefolio" / "strategies"
    thumbs_dir: Path = Path("data") / "edgefolio" / "thumbs"
    fx_today: Path = Path("data") / "edgefolio" / "fx.json"  # lo escribe flask edgefolio fx-update
    # Lo publicado, en el repo.
    catalogue: Path = CATALOGUE / "catalogue.csv"
    indicators: Path = CATALOGUE / "indicators.csv"
    bundles: Path = CATALOGUE / "bundles.json"
    fx: Path = CATALOGUE / "fx.json"           # cambios de ejemplo, hasta que haya los del día
    since_release: Path = CATALOGUE / "since_release.csv"
    static: Path = STATIC
    discount_codes: dict = field(default_factory=dict)
    flat_price_codes: dict = field(default_factory=dict)
    max_discount: Decimal = Decimal("0.70")
    tiers: tuple = DEFAULT_TIERS
    download_days: int = 7
    max_downloads: int = 10
    pack_size: int = 5
    pack_price: Decimal = Decimal("249")
    new_days: int = 30
    contact_email: str = "sales@tuisku.eu"

    @classmethod
    def for_data_dir(cls, data_dir: Path, **values) -> "Settings":
        """Los de por defecto con las carpetas privadas dentro de ``data_dir``."""
        data_dir = Path(data_dir)
        values.setdefault("strategies_dir", data_dir / "strategies")
        values.setdefault("thumbs_dir", data_dir / "thumbs")
        values.setdefault("fx_today", data_dir / "fx.json")
        return cls(**values)

    @classmethod
    def from_env(cls, data_dir: Path, environ: Optional[Mapping[str, str]] = None,
                 public_url: Optional[str] = None) -> "Settings":
        """La de esta instalación. ``public_url`` es ``ZLECITOOL_PUBLIC_URL`` (la lee el núcleo)."""
        e = (environ if environ is not None else os.environ).get
        s = cls.for_data_dir(
            data_dir,
            paypal_mode=(e("PAYPAL_MODE") or "fake").strip().lower(),
            paypal_client_id=e("PAYPAL_CLIENT_ID") or "",
            paypal_client_secret=e("PAYPAL_CLIENT_SECRET") or "",
            discount_codes=_pairs(e("DISCOUNT_CODES") or ""),
            flat_price_codes=_pairs(e("FLAT_PRICE_CODES") or ""),
            max_discount=Decimal(e("MAX_DISCOUNT") or "0.70"),
            download_days=int(e("DOWNLOAD_DAYS") or "7"),
            max_downloads=int(e("MAX_DOWNLOADS") or "10"),
            pack_size=int(e("PACK_SIZE") or "5"),
            pack_price=Decimal(e("PACK_PRICE") or "249"),
            new_days=int(e("NEW_DAYS") or "30"),
            contact_email=(e("CONTACT_EMAIL") or "sales@tuisku.eu").strip(),
        )
        if e("STRATEGIES_DIR"):
            s.strategies_dir = Path(e("STRATEGIES_DIR"))
        if s.paypal_mode not in PAYPAL_MODES:
            raise ValueError(f"PAYPAL_MODE es fake, sandbox o live, no {s.paypal_mode!r}")
        if s.paypal_mode != "fake" and not (s.paypal_client_id and s.paypal_client_secret):
            raise ValueError("fuera de PAYPAL_MODE=fake hacen falta PAYPAL_CLIENT_ID y PAYPAL_CLIENT_SECRET")
        if s.paypal_mode != "fake" and not public_url:
            # Sin ella, el enlace de vuelta de PayPal se haría con la cabecera Host, que elige quien pide.
            raise ValueError("con PAYPAL_MODE=sandbox o live hace falta ZLECITOOL_PUBLIC_URL, la dirección de la "
                             "tienda: ZLECITOOL_PUBLIC_URL=https://edgefolio.tuisku.eu")
        return s
