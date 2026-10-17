# -*- coding: utf-8 -*-
"""Los avisos de las favoritas: un correo por persona cuando una estrategia que sigue tiene una versión
nueva, baja de precio o entra en un lote. Lo lanza el trabajo diario (``flask --app app edgefolio
send-alerts``, desde cron), no una petición.

Cada vuelta compara el catálogo con cómo era en la anterior (edgefolio_alert_state) y guarda cómo es
ahora: un cambio se avisa una vez. La primera vuelta sólo toma la foto: aún no hay con qué comparar.

Los avisos van al correo de la cuenta sólo si la cuenta ha demostrado que es suyo (``proofs``): el
núcleo no lo comprueba al darse de alta, y nadie tiene que recibir correos porque otro se registrara
con su dirección y marcara unas casillas. Y nunca a una cuenta borrada (``privacy.closed``, núcleo 0.30).
"""
from __future__ import annotations

from decimal import Decimal

from zlecitool_core.db import db, utcnow
from zlecitool_core.privacy import closed

from . import proofs
from .models import AlertState, Favourite

# el interruptor (como lo guarda la página) -> lo que cambió
ALERTS = {"nv": "version", "pd": "price", "bd": "bundle"}


def money(value) -> str:
    return f"${Decimal(value):,.2f}"


def picture(catalogue) -> dict:
    """{clave: {version, price, bundles}} de cada estrategia ahora."""
    bundles_of = {}
    for b in catalogue.bundles.values():
        for s in b.items:
            bundles_of.setdefault(s.key, []).append(b.key)
    return {s.key: {"version": s.version, "price": str(s.price), "bundles": sorted(bundles_of.get(s.key, []))}
            for s in catalogue}


def changes(before: dict, now: dict) -> dict:
    """{clave: {'version': v, 'price': (antes, ahora), 'bundle': [claves]}} de lo nuevo desde ``before``."""
    out = {}
    for key, cur in now.items():
        old = before.get(key)
        if not old:
            continue  # nueva en el catálogo: nadie la puede seguir todavía
        found = {}
        if cur["version"] > old["version"]:
            found["version"] = cur["version"]
        if Decimal(cur["price"]) < Decimal(old["price"]):
            found["price"] = (old["price"], cur["price"])
        added = [b for b in cur["bundles"] if b not in old["bundles"]]
        if added:
            found["bundle"] = added
        if found:
            out[key] = found
    return out


def state() -> dict:
    return {r.item_key: {"version": r.version, "price": r.price, "bundles": list(r.bundles)}
            for r in AlertState.query.all()}


def save_state(picture_now: dict):
    AlertState.query.delete()
    now = utcnow()
    db.session.add_all(AlertState(item_key=k, version=v["version"], price=v["price"], bundles=v["bundles"],
                                  updated_at=now) for k, v in picture_now.items())
    db.session.commit()


def subscriptions() -> list:
    """Cada favorita con algún aviso encendido."""
    rows = Favourite.query.order_by(Favourite.user_id, Favourite.created_at).all()
    return [r for r in rows if any((r.alerts or {}).values())]


def run(shop, base_url: str, mail) -> dict:
    """Manda lo que toca y guarda la foto nueva; devuelve las cuentas para el log. ``base_url`` es la
    dirección pública de la tienda (los enlaces de los correos); ``mail``, el ``mail.send`` del núcleo."""
    catalogue, texts = shop.catalogue, shop.texts
    now = picture(catalogue)
    before = state()
    if not before:
        save_state(now)
        return {"first_run": True, "emails": 0, "unconfirmed": 0, "changes": 0}
    found = changes(before, now)
    per_person = {}  # user_id -> (correo, idioma, [líneas])
    unconfirmed = set()
    subs = subscriptions()
    # Entre «Borrar mi cuenta» y la parte de la tienda (núcleo 0.30) pasan minutos: sus favoritas siguen
    # aquí, y su correo no recibe nada más.
    gone = closed({sub.user_id for sub in subs})
    for sub in subs:
        news = found.get(sub.item_key)
        s = catalogue.items.get(sub.item_key)
        if not news or not s or sub.user_id in gone:
            continue
        if not proofs.is_proven(sub.user_id, sub.email):
            unconfirmed.add(sub.user_id)
            continue
        lang = sub.lang or "en"
        common = {"name": s.row.get("Name", s.ticker), "ticker": s.ticker, "code": s.key_techs,
                  "url": f"{base_url}/s/{s.id}"}
        lines = per_person.setdefault(sub.user_id, (sub.email, lang, []))[2]
        for switch, what in ALERTS.items():
            if not sub.alerts.get(switch) or what not in news:
                continue
            if what == "version":
                lines.append(texts.get("mailAlertNew", lang, version=news["version"], **common))
            elif what == "price":
                was, price = news["price"]
                lines.append(texts.get("mailAlertPrice", lang, price=money(price), was=money(was), **common))
            else:
                for key in news["bundle"]:
                    b = catalogue.bundles[key]
                    lines.append(texts.get("mailAlertBundle", lang, bundle=texts.get(b.name_key, lang),
                                           price=money(b.price), n=len(b.items), **common))
    sent = 0
    for email, lang, lines in per_person.values():
        if not lines:
            continue
        body = texts.get("mailAlertBody", lang, lines="\n".join("- " + line for line in lines),
                         mine=f"{base_url}/mine")
        mail(email, texts.get("mailAlertSubject", lang), body, kind="edgefolio-alert")
        sent += 1
    # Un cambio no se repite mañana: ya está en la foto, como para todos.
    save_state(now)
    return {"first_run": False, "emails": sent, "unconfirmed": len(unconfirmed), "changes": len(found)}
