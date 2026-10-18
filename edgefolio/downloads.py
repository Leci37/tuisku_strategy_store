# -*- coding: utf-8 -*-
"""Los scripts completos sólo salen del servidor por un enlace que dio la tienda, de un pedido pagado o
de una descarga gratis.

GET /api/download/<token>               el .pine; con ?format=zip, además las reglas en .md y el .py/.js beta
GET /api/download/all?t=<tok>&t=<tok>   el .pine de cada enlace válido, en un zip (la página de gracias)

Cada fichero enviado gasta una de las MAX_DOWNLOADS del enlace, con un único UPDATE condicional antes de
mandar nada: dos peticiones a la vez por la última descarga no pasan las dos.
"""
from __future__ import annotations

import io
import zipfile

from sqlalchemy import select, update

from zlecitool_core.db import db, utcnow

from . import formats
from .models import Download, FreeClaim, Order
from .web import Refusal

MAX_TOKENS = 100


def find_link(token: str):
    """El enlace (de pago, con el pedido pagado, o gratis), o None."""
    if not token or len(token) > 64:
        return None
    paid = db.session.execute(select(Download, Order.status).join(Order, Order.paypal_id == Download.paypal_id)
                              .where(Download.token == token)).first()
    if paid is not None and paid[1] == "PAID":
        return paid[0]
    return db.session.get(FreeClaim, token)


def checked(shop, token: str):
    """(estrategia, ruta) de un enlace que vale; si no, el rechazo que tiene que ver la persona. No gasta."""
    settings = shop.settings
    link = find_link(token)
    if link is None:
        raise Refusal("errLinkNotFound", 404)
    if link.expires_at < utcnow():
        raise Refusal("errLinkExpired", 410, vars={"e": settings.contact_email})
    if link.count >= settings.max_downloads:
        raise Refusal("errDownloadLimit", 429)
    strategy = shop.catalogue.resolve(link.item_key)
    if not strategy:
        raise Refusal("errStrategyGone", 404)
    path = settings.strategies_dir / strategy.private_file
    if not path.is_file():
        raise Refusal("errFileMissing", 404, item=strategy.key)
    return strategy, path


def claim_download(token: str, max_downloads: int) -> bool:
    """Gasta una descarga de un enlace que vale (de pago o gratis) con un UPDATE condicional: de dos
    peticiones que se disputan la última, sólo una se la lleva; leer y después escribir dejaría pasar a
    las dos."""
    now = utcnow()
    paid = select(Order.paypal_id).where(Order.status == "PAID")
    done = db.session.execute(update(Download).where(
        Download.token == token, Download.count < max_downloads, Download.expires_at > now,
        Download.paypal_id.in_(paid)).values(count=Download.count + 1)).rowcount
    if not done:
        done = db.session.execute(update(FreeClaim).where(
            FreeClaim.token == token, FreeClaim.count < max_downloads, FreeClaim.expires_at > now)
            .values(count=FreeClaim.count + 1)).rowcount
    db.session.commit()
    return done == 1


def spend(shop, token: str):
    """Se lleva una descarga del enlace o, si otra petición se llevó la última, el rechazo que toca."""
    if not claim_download(token, shop.settings.max_downloads):
        checked(shop, token)  # puede haber caducado entretanto: 410
        raise Refusal("errDownloadLimit", 429)


def one(shop, token: str, fmt: str = "pine"):
    """(bytes, tipo, nombre) de un enlace: el .pine o, con ``fmt="zip"``, el zip con sus formatos."""
    strategy, path = checked(shop, token)
    src = path.read_bytes()
    if fmt == "zip":
        stem = strategy.file
        data = formats.build_zip(src.decode("utf-8", errors="replace"), stem, shop.settings.contact_email)
        spend(shop, token)
        return data, "application/zip", f"{stem}.zip"
    spend(shop, token)
    return src, "text/plain; charset=utf-8", strategy.download_name


def all_in_one(shop, tokens: list):
    """(bytes, nombre) del zip con el .pine de cada enlace que vale. El mismo script por dos enlaces se
    manda (y se gasta) una vez. Sin ninguno, el primer rechazo."""
    files, first_error = {}, None
    for token in list(dict.fromkeys(tokens))[:MAX_TOKENS]:
        try:
            strategy, path = checked(shop, token)
            if strategy.download_name in files:
                continue
            data = path.read_bytes()
            spend(shop, token)
        except Refusal as e:
            first_error = first_error or e
            continue
        files[strategy.download_name] = data
    if not files:
        raise first_error or Refusal("errLinkNotFound", 404)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue(), "edgefolio-strategies.zip"
