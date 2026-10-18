# -*- coding: utf-8 -*-
"""Mis estrategias (con la sesión abierta): lo que la cuenta compró o descargó, sus enlaces, las
renovaciones y sus favoritas.

Es de la cuenta lo que hizo con la sesión abierta (``user_id``) y lo que se hizo sin cuenta con un
correo que la cuenta ha demostrado que es suyo (``proofs``); nunca lo que sólo coincide con el correo con
que se dio de alta, que el núcleo no comprueba.
"""
from __future__ import annotations

import math
import secrets
from datetime import timedelta, timezone
from typing import Iterable

from sqlalchemy import func, or_, select

from zlecitool_core.db import db, utcnow

from .free import add_claim
from .models import Download, Favourite, FreeClaim, Order
from .web import Refusal, bool_field, invalid, json_object

ALERT_KEYS = ("nv", "pd", "bd")  # una versión nueva, una bajada de precio, en un lote


def iso(dt, date_only: bool = False) -> str:
    d = dt.replace(tzinfo=timezone.utc)
    return d.date().isoformat() if date_only else d.isoformat(timespec="seconds")


def strategy_or_404(catalogue, item_id: str):
    s = catalogue.resolve(item_id)
    if not s:
        raise Refusal("errUnknownStrategy", 404)
    return s


def links_of(user_id: int, emails: Iterable[str]) -> list:
    """Cada enlace que tiene la cuenta: los de pago de sus pedidos y sus descargas gratis. ``date`` es
    cuándo se hizo con la estrategia (el pedido o la primera descarga), no cuándo se hizo el enlace."""
    emails = sorted(set(emails))
    mine = Order.user_id == user_id
    if emails:
        mine = or_(mine, (Order.user_id.is_(None) & or_(Order.email.in_(emails), func.lower(Order.payer).in_(emails))))
    paid = db.session.execute(select(Download, Order.created_at).join(Order, Order.paypal_id == Download.paypal_id)
                              .where(Order.status == "PAID", mine)).all()
    free_mine = FreeClaim.user_id == user_id
    if emails:
        free_mine = or_(free_mine, FreeClaim.user_id.is_(None) & FreeClaim.email.in_(emails))
    free = FreeClaim.query.filter(free_mine).all()
    out = [{"token": d.token, "item_key": d.item_key, "expires": d.expires_at, "count": d.count, "version": d.version,
            "paypal_id": d.paypal_id, "date": created, "kind": "paid"} for d, created in paid]
    out += [{"token": c.token, "item_key": c.item_key, "expires": c.expires_at, "count": c.count, "version": c.version,
             "paypal_id": "", "date": c.consent_at, "kind": "free", "email": c.email, "news": c.news} for c in free]
    return out


def owned(user_id: int, emails: Iterable[str]) -> dict:
    """item_key -> cada enlace que tiene la cuenta para ella, el más nuevo el último."""
    groups = {}
    for link in sorted(links_of(user_id, emails), key=lambda r: r["expires"]):
        groups.setdefault(link["item_key"], []).append(link)
    return groups


def entry(settings, s, links: list) -> dict:
    """La fila de una estrategia: la compra es la primera (su fecha y su pedido, aunque se comprara otra
    vez o se renovara el enlace); el enlace, el último."""
    now = utcnow()
    latest, first = links[-1], min(links, key=lambda x: x["date"])
    valid = latest["expires"] > now and latest["count"] < settings.max_downloads
    url = f"/api/download/{latest['token']}"
    return {"id": s.id, "kind": latest["kind"], "date": iso(first["date"], True), "at": iso(first["date"]),
            "order": first["paypal_id"] or None, "expires": iso(latest["expires"]),
            "days_left": max(0, math.ceil((latest["expires"] - now).total_seconds() / 86400)), "valid": valid,
            "url": url if valid else None, "zip": f"{url}?format=zip" if valid else None,
            "version": latest["version"], "update": s.version if s.version > latest["version"] else None,
            "row": s.as_row()}


def listing(shop, user_id: int, email: str, emails: list, proof_needed: bool) -> dict:
    catalogue, items = shop.catalogue, []
    for key, links in owned(user_id, emails).items():
        s = catalogue.resolve(key)
        if s:  # una estrategia que salió del catálogo ya no tiene nada que enseñar ni que descargar
            items.append(entry(shop.settings, s, links))
    items.sort(key=lambda e: e["at"], reverse=True)  # lo último, arriba (también del mismo día)
    favourites = []
    for fav in Favourite.query.filter_by(user_id=user_id).order_by(Favourite.created_at):
        s = catalogue.resolve(fav.item_key)
        if s:
            favourites.append({"id": s.id, "alerts": fav.alerts, "row": s.as_row()})
    return {"email": email, "emails": emails, "proof_needed": proof_needed, "items": items,
            "favourites": favourites}


def renew(shop, user_id: int, emails: list, item_id: str) -> dict:
    """Un enlace nuevo si el de antes caducó o se gastó, o para una versión nueva; si no, la misma fila:
    el botón no sirve para reiniciar el límite de un enlace que funciona."""
    s = strategy_or_404(shop.catalogue, item_id)
    links = owned(user_id, emails).get(s.key)
    if not links:
        raise Refusal("errNotOwned", 404)
    settings = shop.settings
    current = entry(settings, s, links)
    if current["valid"] and not current["update"]:
        return current
    latest = links[-1]
    if latest["kind"] == "paid":
        db.session.add(Download(token=secrets.token_urlsafe(24), paypal_id=latest["paypal_id"], item_key=s.key,
                                expires_at=utcnow() + timedelta(days=settings.download_days), count=0,
                                version=s.version))
        db.session.commit()
    else:
        # La renovada guarda la hora de la primera petición: no cuenta para el límite del día.
        first = min(x["date"] for x in links if x["kind"] == "free")
        news = any(x.get("news") for x in links if x["kind"] == "free")
        add_claim(latest["email"], s.key, news, "", settings.download_days, s.version, consent_at=first,
                  user_id=user_id)
    return entry(settings, s, owned(user_id, emails)[s.key])


def script_path(shop, user_id: int, emails: list, item_id: str):
    """El script completo para quien lo tiene (la vista de propietario del árbol)."""
    s = strategy_or_404(shop.catalogue, item_id)
    if s.key not in owned(user_id, emails):
        raise Refusal("errNotOwned", 404)
    path = shop.settings.strategies_dir / s.private_file
    if not path.is_file():
        raise Refusal("errFileMissing", 404, item=s.key)
    return path


def alerts_of(body: dict) -> dict:
    """Los avisos de una favorita, como los manda la página: {"alerts": {"nv": true, …}}."""
    raw = body.get("alerts", {})
    if not isinstance(raw, dict):
        raise invalid("alerts")
    return {k: bool_field(json_object(raw), k, prefix="alerts.") for k in ALERT_KEYS}


def set_favourite(shop, user_id: int, email: str, lang: str, item_id: str, alerts: dict) -> dict:
    s = strategy_or_404(shop.catalogue, item_id)
    fav = db.session.get(Favourite, (user_id, s.key))
    if fav is None:
        fav = Favourite(user_id=user_id, item_key=s.key, created_at=utcnow())
        db.session.add(fav)
    fav.alerts, fav.email, fav.lang = dict(alerts), email, lang
    db.session.commit()
    return {"id": s.id, "alerts": dict(alerts), "row": s.as_row()}


def delete_favourite(shop, user_id: int, item_id: str) -> dict:
    s = strategy_or_404(shop.catalogue, item_id)
    Favourite.query.filter_by(user_id=user_id, item_key=s.key).delete()
    db.session.commit()
    return {"id": s.id, "deleted": True}
