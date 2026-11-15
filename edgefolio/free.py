# -*- coding: utf-8 -*-
"""Las estrategias gratis, para un correo: el enlace va por correo y nunca en la respuesta, así que la
dirección es de verdad. Las novedades son una casilla aparte: se apuntan sólo si se marca, y sólo
cuentan cuando la persona lo confirma desde el correo (doble opt-in del RGPD).

Lo que se cuenta por dirección se cuenta y se apunta con la fila de la dirección bloqueada (``lock_address``): diez
peticiones a la vez no pasan todas el recuento antes de apuntarse. Se cuenta de dos maneras (2026-11-15):

- DAILY_CLAIMS al día por dirección **y por quien pide** (la cuenta o la IP): hasta entonces eran 10 por dirección
  de cualquiera, y cualquiera, sin cuenta, dejaba a otra persona sin sus gratis del día pidiendo 10 con su correo;
- ADDRESS_DAILY_CLAIMS al día por dirección, de todos: lo que puede llegar a un buzón.
"""
from __future__ import annotations

import secrets
from datetime import timedelta
from typing import Optional

from sqlalchemy import func, update

from zlecitool_core.db import db, utcnow

from .models import FreeClaim, Mailbox, Subscriber
from .web import Refusal, digest

DAILY_CLAIMS = 10            # por correo y por quien pide
ADDRESS_DAILY_CLAIMS = 20    # por correo, de todos: el buzón
NEWS_CONFIRM_DAYS = 30       # lo que vale el enlace que confirma las novedades


def lock_address(email: str):
    """Bloquea la fila de la dirección hasta el ``commit``: en SQLite, la primera escritura de la
    transacción toma el candado de escritura; en Postgres, el UPDATE bloquea la fila. Lo que se lea
    después ya ve lo que apuntaron las peticiones de antes."""
    now = utcnow()
    dialect = db.session.get_bind().dialect.name
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    db.session.execute(insert(Mailbox).values(email=email, first_seen_at=now, last_seen_at=now)
                       .on_conflict_do_nothing(index_elements=["email"]))
    db.session.execute(update(Mailbox).where(Mailbox.email == email).values(last_seen_at=now))


def claims_since(email: str, since, requester_hash: Optional[str] = None) -> int:
    q = db.session.query(func.count(FreeClaim.token)).filter(FreeClaim.email == email, FreeClaim.consent_at >= since)
    if requester_hash is not None:
        q = q.filter(FreeClaim.requester_hash == requester_hash)
    return q.scalar()


def add_claim(email: str, key: str, news: bool, lang: str, days: int, version: int = 1,
              consent_at=None, user_id: Optional[int] = None, daily_limit: Optional[int] = None,
              requester: Optional[str] = None) -> Optional[str]:
    """El token de la descarga nueva; None si ``daily_limit`` y ``requester`` (quien pide) ya pidió tantas para esta
    dirección en el último día, o si la dirección ya recibió ADDRESS_DAILY_CLAIMS de todos. Recuento y alta, de una
    vez (la fila de la dirección, bloqueada)."""
    token, now = secrets.token_urlsafe(24), utcnow()
    who = digest(requester) if requester else None
    db.session.commit()  # lo que hubiera abierto, cerrado: la escritura de abajo es la primera
    lock_address(email)
    day = now - timedelta(days=1)
    if daily_limit is not None and (claims_since(email, day, who if who else None) >= daily_limit
                                    or claims_since(email, day) >= ADDRESS_DAILY_CLAIMS):
        db.session.rollback()
        return None
    db.session.add(FreeClaim(token=token, user_id=user_id, email=email, item_key=key, news=bool(news),
                             consent_at=consent_at or now, expires_at=now + timedelta(days=days), count=0,
                             version=version, lang=lang, requester_hash=who))
    db.session.commit()
    return token


def claim(shop, strategy, email: str, news: bool, lang: str, links, mail, user_id: Optional[int] = None,
          requester: Optional[str] = None) -> dict:
    """La descarga gratis de ``strategy`` para ``email``. ``links`` hace las direcciones de los correos
    (``links(endpoint, **values)``) y ``mail`` los manda (el ``mail.send`` del núcleo). ``requester``: quién la pide
    («u:<cuenta>» o «ip:<red>»), para el tope del día."""
    if strategy.price != 0:
        raise Refusal("errNotFree", 400)
    if not (shop.settings.strategies_dir / strategy.private_file).is_file():
        raise Refusal("errFileMissing", 404, item=strategy.key)
    settings, texts = shop.settings, shop.texts
    days = settings.download_days
    # sin dirección pública que dar (producción sin ZLECITOOL_PUBLIC_URL), antes de apuntar nada: una
    # descarga cuyo correo no puede salir no cuenta ni deja un enlace que funcione
    mine = links("edgefolio.mine_page")
    token = add_claim(email, strategy.key, news, lang, days, strategy.version, user_id=user_id,
                      daily_limit=DAILY_CLAIMS, requester=requester)
    if token is None:
        raise Refusal("errFreeDaily", 429)
    # la suscripción pendiente se apunta con el correo que lleva su enlace
    confirm = secrets.token_urlsafe(24) if news and not news_confirmed(email) else None
    what = {"name": strategy.row.get("Name") or strategy.ticker, "ticker": strategy.ticker,
            "interval": strategy.interval}
    pine = links("edgefolio.download", token=token)
    # los días y las descargas de un enlace son ajustes: cada cuenta, con la forma que pide su número
    counts = {"days": texts.get("linkDays", lang, n=days),
              "downloads": texts.get("linkDownloads", lang, n=settings.max_downloads)}
    text = texts.get("mailFreeBody", lang, **what, **counts, pine=pine, zip=pine + "?format=zip", mine=mine)
    if confirm:
        text += "\n" + texts.get("mailNewsConfirm", lang, link=links("edgefolio.confirm_news", token=confirm))
    mail(email, texts.get("mailFreeSubject", lang, **what), text, kind="edgefolio-free")
    if confirm:
        request_news(email, "free", lang, token=confirm)
    return {"sent": True}


# ── las novedades ────────────────────────────────────────────────────────────

def news_confirmed(email: str) -> bool:
    row = db.session.get(Subscriber, email)
    return bool(row and row.news and row.confirmed_at is not None)


def request_news(email: str, source: str, lang: str, token: Optional[str] = None) -> Optional[str]:
    """Sólo cuando se marcó la casilla y salió el correo con el enlace. La fila queda pendiente
    (``confirmed_at`` vacío) hasta que se abre el enlace: nadie se apunta porque otro teclee su dirección.
    Da el token de ese enlace, o None si la dirección ya está confirmada. Una petición nueva cambia el
    token: vale el enlace del último correo."""
    token = token or secrets.token_urlsafe(24)
    row = db.session.get(Subscriber, email)
    if row is not None and row.news and row.confirmed_at is not None:
        return None
    if row is None:
        row = Subscriber(email=email)
        db.session.add(row)
    row.news, row.consent_at, row.source, row.lang = True, utcnow(), source, lang
    row.token_hash, row.confirmed_at = digest(token), None
    db.session.commit()
    return token


def confirm_news(token: str, days: int = NEWS_CONFIRM_DAYS) -> Optional[str]:
    """El correo cuya suscripción pendiente confirma el enlace, una vez; None si es usado, viejo o inventado."""
    if not token:
        return None
    since = utcnow() - timedelta(days=days)
    done = db.session.execute(update(Subscriber).where(
        Subscriber.token_hash == digest(token), Subscriber.news.is_(True), Subscriber.confirmed_at.is_(None),
        Subscriber.consent_at > since).values(confirmed_at=utcnow(), token_hash="")
        .returning(Subscriber.email)).first()
    db.session.commit()
    return done[0] if done else None


def subscribers() -> list:
    """A quién se le pueden mandar novedades: sólo las filas confirmadas."""
    rows = Subscriber.query.filter(Subscriber.news.is_(True), Subscriber.confirmed_at.isnot(None)) \
        .order_by(Subscriber.confirmed_at)
    return [{"email": r.email, "lang": r.lang, "source": r.source, "consent_at": r.consent_at,
             "confirmed_at": r.confirmed_at} for r in rows]
