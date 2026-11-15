# -*- coding: utf-8 -*-
"""Mis estrategias (con la sesión abierta): lo que la cuenta compró o descargó, sus enlaces, las
renovaciones y sus favoritas.

Es de la cuenta lo que hizo con la sesión abierta (``user_id``) y lo que se hizo sin cuenta con un
correo que la cuenta ha demostrado que es suyo (``proofs``); nunca lo que sólo coincide con el correo con
que se dio de alta, que el núcleo no comprueba.

Una gratis pedida con la sesión abierta sale en la cuenta si se mandó a su propio correo (``own``) o a uno de los
que ha demostrado; no si se mandó a cualquier otra dirección. Hasta el 2026-11-15, una cuenta veía (y renovaba) las
que pedía para cualquier dirección, sin abrir ningún correo.
"""
from __future__ import annotations

import math
import secrets
from datetime import timedelta, timezone
from typing import Iterable

from sqlalchemy import func, or_, select, update

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


def links_of(user_id: int, emails: Iterable[str], own: str = "") -> list:
    """Cada enlace que tiene la cuenta: los de pago de sus pedidos y sus descargas gratis. ``date`` es
    cuándo se hizo con la estrategia (el pedido o la primera descarga), no cuándo se hizo el enlace."""
    emails = sorted(set(emails))
    mine = Order.user_id == user_id
    if emails:
        mine = or_(mine, (Order.user_id.is_(None) & or_(Order.email.in_(emails), func.lower(Order.payer).in_(emails))))
    paid = db.session.execute(select(Download, Order.created_at).join(Order, Order.paypal_id == Download.paypal_id)
                              .where(Order.status == "PAID", mine)).all()
    asked = FreeClaim.user_id == user_id
    if own:
        asked = asked & FreeClaim.email.in_(sorted(set(emails) | {own.strip().lower()}))
    elif emails:
        asked = asked & FreeClaim.email.in_(emails)
    else:
        asked = None
    found = [asked] if asked is not None else []
    if emails:
        found.append(FreeClaim.user_id.is_(None) & FreeClaim.email.in_(emails))
    free = FreeClaim.query.filter(or_(*found)).all() if found else []
    out = [{"token": d.token, "item_key": d.item_key, "expires": d.expires_at, "count": d.count, "version": d.version,
            "paypal_id": d.paypal_id, "date": created, "kind": "paid"} for d, created in paid]
    out += [{"token": c.token, "item_key": c.item_key, "expires": c.expires_at, "count": c.count, "version": c.version,
             "paypal_id": "", "date": c.consent_at, "kind": "free", "email": c.email, "news": c.news} for c in free]
    return out


def owned(user_id: int, emails: Iterable[str], own: str = "") -> dict:
    """item_key -> cada enlace que tiene la cuenta para ella, el más nuevo el último."""
    groups = {}
    for link in sorted(links_of(user_id, emails, own), key=lambda r: r["expires"]):
        groups.setdefault(link["item_key"], []).append(link)
    return groups


def held(shop, user_id: int, emails: Iterable[str], own: str = "") -> set:
    """Las claves de lo que la cuenta tiene, para no vendérselo suelto (E8): lo de Mis estrategias cuyo enlace sirve o
    se puede renovar. No lo es (y se vende) lo que ya no se renueva (2026-11-15):
    - una gratis que pasó a ser de pago, con su enlace caducado o gastado (errNoLongerFree);
    - la v1 comprada de una estrategia caducada con una v2 publicada, que no va con la compra (errUpdateExpired).
    Hasta entonces, las dos daban errAlreadyOwned: ni se renovaban ni se podían comprar."""
    items, settings, now = shop.catalogue.items, shop.settings, utcnow()

    def still_hers(key, links):
        s, latest = items.get(key), links[-1]
        if s is None:
            return True
        if latest["expires"] > now and latest["count"] < settings.max_downloads and \
                s.serves(latest["version"], latest["kind"] == "paid"):
            return True                                        # su enlace sirve
        return s.price == 0 if latest["kind"] == "free" else s.serves(latest["version"])
    return {key for key, links in owned(user_id, emails, own).items() if still_hers(key, links)}


def update_of(s, latest: dict):
    """La versión nueva que se le da a quien tiene ``latest`` (su último enlace), o None. Gratis mientras la estrategia
    no ha caducado (la «Expiry date» de su script; decisión del dueño, 2026-10-26); después, no. Una gratis, siempre: se
    pide otra vez sin pagar."""
    if s.version <= latest["version"]:
        return None
    if latest["kind"] == "free":
        return s.version if s.price == 0 else None   # se pide otra vez sin pagar, mientras siga siendo gratis
    return s.version if s.serves(latest["version"]) else None


def entry(settings, s, links: list) -> dict:
    """La fila de una estrategia: la compra es la primera (su fecha y su pedido, aunque se comprara otra
    vez o se renovara el enlace); el enlace, el último."""
    now = utcnow()
    latest, first = links[-1], min(links, key=lambda x: x["date"])
    # el de una versión de antes, con la estrategia caducada, ya no vale: daría el script de hoy (downloads.checked)
    valid = (latest["expires"] > now and latest["count"] < settings.max_downloads
             and s.serves(latest["version"], latest["kind"] == "paid"))
    url = f"/api/download/{latest['token']}"
    return {"id": s.id, "kind": latest["kind"], "date": iso(first["date"], True), "at": iso(first["date"]),
            "order": first["paypal_id"] or None, "expires": iso(latest["expires"]),
            "days_left": max(0, math.ceil((latest["expires"] - now).total_seconds() / 86400)), "valid": valid,
            "url": url if valid else None, "zip": f"{url}?format=zip" if valid else None,
            "version": latest["version"], "update": update_of(s, latest), "row": s.as_row()}


def listing(shop, user_id: int, email: str, emails: list, proof_needed: bool) -> dict:
    catalogue, items = shop.catalogue, []
    for key, links in owned(user_id, emails, email).items():
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


def renew(shop, user_id: int, emails: list, item_id: str, own: str = "") -> dict:
    """Un enlace nuevo si el de antes caducó o se gastó, o para una versión nueva; si no, la misma fila:
    el botón no sirve para reiniciar el límite de un enlace que funciona. Una versión nueva de una de pago que ya
    caducó no se da (403 ``errUpdateExpired``): la tienda guarda un script por estrategia, el de hoy, así que un
    enlace nuevo de la de antes también la daría."""
    s = strategy_or_404(shop.catalogue, item_id)
    links = owned(user_id, emails, own).get(s.key)
    if not links:
        raise Refusal("errNotOwned", 404)
    settings = shop.settings
    current = entry(settings, s, links)
    latest = links[-1]
    if latest["kind"] == "free":
        if s.price > 0:
            # pasó a ser de pago: su enlace sirve hasta que caduca, y uno nuevo se compra (2026-11-15; hasta entonces se
            # renovaba siempre, también en sus versiones nuevas)
            raise Refusal("errNoLongerFree", 403)
    elif not s.serves(latest["version"]):
        raise Refusal("errUpdateExpired", 403)
    if current["valid"] and not current["update"]:
        return current
    if latest["kind"] == "paid":
        # dos «Pedir un enlace nuevo» a la vez (un doble clic) daban dos enlaces: 20 descargas (2026-11-15). Con la fila
        # del pedido bloqueada (la escritura de abajo, la primera de la transacción: en SQLite, el candado de
        # escritura; en Postgres, la fila), se mira otra vez si ya hay uno que sirve
        db.session.commit()
        db.session.execute(update(Order).where(Order.paypal_id == latest["paypal_id"]).values(status=Order.status))
        now = utcnow()
        fresh = Download.query.filter(Download.paypal_id == latest["paypal_id"], Download.item_key == s.key,
                                      Download.expires_at > now, Download.count < settings.max_downloads,
                                      Download.version >= s.version).first()
        if fresh is None:
            db.session.add(Download(token=secrets.token_urlsafe(24), paypal_id=latest["paypal_id"], item_key=s.key,
                                    expires_at=now + timedelta(days=settings.download_days), count=0,
                                    version=s.version))
        db.session.commit()
    else:
        # La renovada guarda la hora de la primera petición: no cuenta para el límite del día.
        first = min(x["date"] for x in links if x["kind"] == "free")
        news = any(x.get("news") for x in links if x["kind"] == "free")
        add_claim(latest["email"], s.key, news, "", settings.download_days, s.version, consent_at=first,
                  user_id=user_id, unless_valid=settings.max_downloads)
    return entry(settings, s, owned(user_id, emails, own)[s.key])


def script_path(shop, user_id: int, emails: list, item_id: str, own: str = ""):
    """El script completo para quien lo tiene (la vista de propietario del árbol). Es el de hoy: a quien tiene una versión
    de antes de una que ya caducó, no (sería la versión nueva, como su enlace: ``Strategy.serves``)."""
    s = strategy_or_404(shop.catalogue, item_id)
    links = owned(user_id, emails, own).get(s.key)
    if not links:
        raise Refusal("errNotOwned", 404)
    if not s.serves(links[-1]["version"], links[-1]["kind"] == "paid"):
        raise Refusal("errUpdateExpired", 403)
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
