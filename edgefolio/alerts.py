# -*- coding: utf-8 -*-
"""Los avisos de las favoritas: un correo por persona cuando una estrategia que sigue tiene una versión
nueva, baja de precio o entra en un lote. Lo lanza el reloj del núcleo una vez al día (la tarea
``send_alerts`` de tool.json, edgefolio/tasks.py), no una petición; a mano, ``flask --app app edgefolio
send-alerts``.

Cada vuelta compara el catálogo con cómo era en la anterior (edgefolio_alert_state) y guarda cómo es
ahora: un cambio se avisa una vez. La primera vuelta sólo toma la foto: aún no hay con qué comparar. La foto
nueva se guarda antes de mandar nada: una vuelta que falla al guardarla no ha mandado ningún correo.

Los avisos van al correo de la cuenta sólo si la cuenta ha demostrado que es suyo (``proofs``): el
núcleo no lo comprueba al darse de alta, y nadie tiene que recibir correos porque otro se registrara
con su dirección y marcara unas casillas. Y nunca a una cuenta borrada (``privacy.closed``, núcleo 0.30).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Callable, Optional

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


def save_state(picture_now: dict, at=None):
    """La foto de ahora en lugar de la de antes; ``at``, la hora de la vuelta (la que tocaba, en una tarea). Sin
    ``commit``: lo guarda quien llama, con lo demás de la vuelta."""
    AlertState.query.delete()
    at = at or utcnow()
    db.session.add_all(AlertState(item_key=k, version=v["version"], price=v["price"], bundles=v["bundles"],
                                  updated_at=at) for k, v in picture_now.items())


def subscriptions() -> list:
    """Cada favorita con algún aviso encendido."""
    rows = Favourite.query.order_by(Favourite.user_id, Favourite.created_at).all()
    return [r for r in rows if any((r.alerts or {}).values())]


def run(shop, link: Callable, mail: Callable, at=None, before_commit: Optional[Callable[[dict], None]] = None) -> dict:
    """Manda lo que toca y guarda la foto nueva; devuelve las cuentas para el log. ``link(endpoint, **values)`` hace
    las direcciones de los correos (con la dirección pública: ``external_url(…, trusted_host_ok=False)``); ``mail``,
    el ``mail.send`` del núcleo; ``at``, cuándo tocaba la vuelta. ``before_commit(cuentas)`` apunta, en la misma
    transacción que la foto, lo que haga falta (la vez de la tarea: una repetición no manda nada otra vez)."""
    catalogue, texts = shop.catalogue, shop.texts
    now = picture(catalogue)
    before = state()
    if not before:
        result = {"first_run": True, "emails": 0, "unconfirmed": 0, "changes": 0}
        save_state(now, at)
        if before_commit is not None:
            before_commit(result)
        db.session.commit()
        return result
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
                  "url": link("edgefolio.strategy_page", strategy_id=s.id)}
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
    letters = []
    for email, lang, lines in per_person.values():
        if not lines:
            continue
        body = texts.get("mailAlertBody", lang, lines="\n".join("- " + line for line in lines),
                         mine=link("edgefolio.mine_page"))
        letters.append((email, texts.get("mailAlertSubject", lang), body))
    result = {"first_run": False, "emails": len(letters), "unconfirmed": len(unconfirmed), "changes": len(found)}
    # Un cambio no se repite mañana: ya está en la foto, como para todos. Primero se guarda (con la vez de la tarea);
    # los correos, después: si guardar falla (otra vuelta de la misma vez lo hizo antes), no sale ninguno dos veces
    save_state(now, at)
    if before_commit is not None:
        before_commit(result)
    db.session.commit()
    for email, subject, body in letters:
        mail(email, subject, body, kind="edgefolio-alert")
    return result
