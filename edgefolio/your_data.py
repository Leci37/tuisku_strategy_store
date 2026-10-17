# -*- coding: utf-8 -*-
"""Tus datos (núcleo 0.30): lo que la tienda guarda de una cuenta, en «Descargar mis datos», y cómo se va
con «Borrar mi cuenta». Las páginas, el zip, la cola y la comprobación son del núcleo; aquí, lo de la tienda.

app.py registra ``export`` y ``erase`` con ``privacy.add_privacy``, y el núcleo las corre en el reloj de la
tienda (``zt_privacy``), sin la petición de nadie: la cuenta es ``subject.user_id``. Las dos pueden
repetirse, y ``erase`` no confirma: lo confirma el núcleo con el resto de su parte.

Es de la cuenta lo que hizo con la sesión abierta (``user_id``) y lo que se hizo sin cuenta con un correo
**demostrado**: el de la cuenta si lo demostró el núcleo (``subject.email``, desde la 0.26) y los que la
cuenta demostró aquí (``proofs``). Nunca lo que sólo coincide con un correo sin demostrar: darse de alta no
lo demuestra, y cualquiera podría registrarse con el de otra persona.

Al borrar la cuenta:

- **los pedidos se quedan** (``KEEP``): son el registro de una venta, que pide la ley fiscal (lo vendido,
  el importe, la fecha). Pierden quién los hizo: el correo, el de PayPal (``payer``) y el hash de la
  cookie del navegador que compró; los hechos con la sesión abierta siguen apuntando a la cuenta borrada,
  y sus enlaces de descarga, sin nadie que los vea, caducan solos;
- lo demás se va: sus descargas gratis, sus favoritas, las pruebas de sus correos y, de cada correo
  demostrado, su alta en las novedades y su fila en ``edgefolio_mailbox``.

Lo hecho sin cuenta con un correo demostrado se va también si otra cuenta demostró el mismo correo: es de
quien lo controla, que pidió borrarlo (y el núcleo comprueba que su correo no queda en ninguna fila de
nadie).
"""
from __future__ import annotations

from sqlalchemy import func, or_, select, update

from zlecitool_core.db import db

from .models import Download, EmailProof, Favourite, FreeClaim, Mailbox, Order, Subscriber

#: Lo que la ley obliga a guardar: los pedidos, sin correo, apuntando a la cuenta borrada.
KEEP = ("edgefolio_order",)


def proven_emails(subject) -> list:
    """Los correos que la cuenta ha demostrado: el suyo, si lo demostró el núcleo, y los de sus pruebas."""
    emails = {row.email for row in EmailProof.query.filter(EmailProof.user_id == subject.user_id,
                                                           EmailProof.verified_at.isnot(None))}
    if subject.email:
        emails.add(subject.email)
    return sorted({email.strip().lower() for email in emails if email and email.strip()})


def _orders_of(user_id: int, emails: list):
    """Sus pedidos: los que hizo con la sesión abierta y los hechos sin cuenta con uno de sus correos
    demostrados (el del pedido o el de quien pagó en PayPal), como los cuenta Mis estrategias."""
    mine = Order.user_id == user_id
    if emails:
        mine = or_(mine, Order.user_id.is_(None) & or_(func.lower(Order.email).in_(emails),
                                                       func.lower(Order.payer).in_(emails)))
    return mine


def _claims_of(user_id: int, emails: list):
    """Sus descargas gratis: las pedidas con la sesión abierta y las pedidas sin cuenta con uno de sus correos
    demostrados."""
    mine = FreeClaim.user_id == user_id
    if emails:
        mine = or_(mine, FreeClaim.user_id.is_(None) & func.lower(FreeClaim.email).in_(emails))
    return mine


def export(subject, out) -> None:
    """Lo de la cuenta en «Descargar mis datos», en ``edgefolio/`` del zip. ``out.rows`` deja fuera las
    columnas que parecen secretas: los enlaces (``token``), el hash de la cookie de quien compra
    (``buyer_hash``) y los de los enlaces de confirmar (``token_hash``)."""
    emails = proven_emails(subject)
    orders = _orders_of(subject.user_id, emails)
    out.rows("orders", Order.query.filter(orders).order_by(Order.created_at, Order.paypal_id))
    paid_links = Download.paypal_id.in_(select(Order.paypal_id).where(orders))
    out.rows("downloads", Download.query.filter(paid_links).order_by(Download.created_at, Download.item_key))
    out.rows("free_downloads", FreeClaim.query.filter(_claims_of(subject.user_id, emails))
             .order_by(FreeClaim.consent_at, FreeClaim.item_key))
    out.rows("favourites", Favourite.query.filter_by(user_id=subject.user_id).order_by(Favourite.created_at))
    out.rows("email_proofs", EmailProof.query.filter_by(user_id=subject.user_id).order_by(EmailProof.requested_at),
             exclude=("id",))
    out.rows("news", Subscriber.query.filter(func.lower(Subscriber.email).in_(emails)).order_by(Subscriber.email))
    out.rows("mailboxes", Mailbox.query.filter(func.lower(Mailbox.email).in_(emails)).order_by(Mailbox.email))


def erase(subject) -> None:
    """Lo de la cuenta, fuera; sus pedidos, sin quién los hizo (arriba). Sin ``commit``: lo confirma el
    núcleo, que después comprueba que no queda nada. Otra vez no cambia nada: los correos ya no están."""
    emails = proven_emails(subject)
    db.session.execute(update(Order).where(_orders_of(subject.user_id, emails))
                       .values(email="", payer="", buyer_hash="").execution_options(synchronize_session=False))
    FreeClaim.query.filter(_claims_of(subject.user_id, emails)).delete(synchronize_session=False)
    Favourite.query.filter_by(user_id=subject.user_id).delete(synchronize_session=False)
    if emails:
        Subscriber.query.filter(func.lower(Subscriber.email).in_(emails)).delete(synchronize_session=False)
        Mailbox.query.filter(func.lower(Mailbox.email).in_(emails)).delete(synchronize_session=False)
    # Las pruebas, lo último: hasta aquí dicen qué correos son suyos.
    EmailProof.query.filter_by(user_id=subject.user_id).delete(synchronize_session=False)
