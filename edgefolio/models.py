# -*- coding: utf-8 -*-
"""Las tablas de la tienda, en la base de datos común (la del núcleo), todas con el prefijo edgefolio_.

Las cuentas son las del núcleo (core_user): una fila que es de alguien apunta a core_user.id y nunca
lee ni escribe esa tabla. Quien compra sin cuenta deja su pedido sin user_id; ese pedido se le enseña a
una cuenta sólo cuando la cuenta ha demostrado que el correo del pedido es suyo (EmailProof): el núcleo
no comprueba el correo de quien se da de alta, y cualquiera podría registrarse con el de otra persona.

Los enlaces de un solo uso (la confirmación de las novedades, la de un correo) se guardan sólo como hash.
"""
from __future__ import annotations

from zlecitool_core.db import db, utcnow


class Order(db.Model):
    """Un pedido de PayPal: lo que se compró, el total que calculó el servidor y cómo acabó."""

    __tablename__ = "edgefolio_order"

    paypal_id = db.Column(db.String(64), primary_key=True)
    #: La cuenta que compró con la sesión abierta; vacío si se compró sin cuenta.
    user_id = db.Column(db.Integer, db.ForeignKey("core_user.id"), nullable=True, index=True)
    items = db.Column(db.JSON, nullable=False)                    # las claves de las estrategias
    code = db.Column(db.String(64), nullable=False, default="")   # el código aplicado
    total = db.Column(db.String(20), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    status = db.Column(db.String(10), nullable=False, default="CREATED")   # CREATED, PAID, FAILED
    payer = db.Column(db.String(254), nullable=False, default="")          # lo que dice PayPal
    #: El correo de la cuenta que compró o, sin cuenta, el de PayPal (en minúsculas).
    email = db.Column(db.String(254), nullable=False, default="", index=True)
    lines = db.Column(db.JSON, nullable=False)                    # lo cobrado, línea a línea
    #: SHA-256 de la cookie del navegador que hizo el pedido: sólo él ve los enlaces del recibo.
    buyer_hash = db.Column(db.String(64), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)


class Download(db.Model):
    """Un enlace de descarga de una estrategia de un pedido pagado (y los que lo renuevan)."""

    __tablename__ = "edgefolio_download"

    token = db.Column(db.String(64), primary_key=True)
    paypal_id = db.Column(db.String(64), db.ForeignKey("edgefolio_order.paypal_id"), nullable=False, index=True)
    item_key = db.Column(db.String(200), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    count = db.Column(db.Integer, nullable=False, default=0)
    version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)


class FreeClaim(db.Model):
    """Una estrategia gratis mandada a un correo: el enlace va en el correo, nunca en la respuesta."""

    __tablename__ = "edgefolio_free_claim"

    token = db.Column(db.String(64), primary_key=True)
    #: La cuenta que la pidió con la sesión abierta; vacío si se pidió sin cuenta.
    user_id = db.Column(db.Integer, db.ForeignKey("core_user.id"), nullable=True, index=True)
    email = db.Column(db.String(254), nullable=False, index=True)
    item_key = db.Column(db.String(200), nullable=False)
    news = db.Column(db.Boolean, nullable=False, default=False)   # si marcó la casilla de novedades
    consent_at = db.Column(db.DateTime, nullable=False)          # cuándo la pidió
    expires_at = db.Column(db.DateTime, nullable=False)
    count = db.Column(db.Integer, nullable=False, default=0)
    version = db.Column(db.Integer, nullable=False, default=1)
    lang = db.Column(db.String(8), nullable=False, default="")


class Subscriber(db.Model):
    """Quien pidió las novedades: sólo cuenta cuando lo confirma desde el correo (doble opt-in)."""

    __tablename__ = "edgefolio_subscriber"

    email = db.Column(db.String(254), primary_key=True)
    news = db.Column(db.Boolean, nullable=False, default=True)
    consent_at = db.Column(db.DateTime, nullable=False)          # cuándo marcó la casilla
    source = db.Column(db.String(20), nullable=False)
    lang = db.Column(db.String(8), nullable=False, default="")
    token_hash = db.Column(db.String(64), nullable=False, default="", index=True)
    confirmed_at = db.Column(db.DateTime, nullable=True)         # vacío hasta que confirma


class Favourite(db.Model):
    """Las favoritas de una cuenta, con sus avisos (versión nueva, bajada de precio, en un lote)."""

    __tablename__ = "edgefolio_favourite"

    user_id = db.Column(db.Integer, db.ForeignKey("core_user.id"), primary_key=True)
    item_key = db.Column(db.String(200), primary_key=True)
    alerts = db.Column(db.JSON, nullable=False)
    #: El correo de la cuenta y el idioma de la página al guardarla: a dónde y en qué idioma van sus avisos
    #: (el trabajo diario no tiene petición ni puede leer core_user).
    email = db.Column(db.String(254), nullable=False, default="")
    lang = db.Column(db.String(8), nullable=False, default="en")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)


class AlertState(db.Model):
    """Cómo era cada estrategia en la última vuelta de los avisos: un cambio se avisa una vez."""

    __tablename__ = "edgefolio_alert_state"

    item_key = db.Column(db.String(200), primary_key=True)
    version = db.Column(db.Integer, nullable=False)
    price = db.Column(db.String(20), nullable=False)
    bundles = db.Column(db.JSON, nullable=False)                  # las claves de los lotes en que está
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow)


class EmailProof(db.Model):
    """Que una cuenta ha demostrado que un correo es suyo: abrió el enlace que se le mandó y lo confirmó.

    Hasta entonces la fila espera con el hash de ese enlace (``verified_at`` vacío). Una cuenta ve los
    pedidos y las descargas gratis hechos sin cuenta con un correo sólo cuando ese correo está aquí,
    confirmado, y es suyo.
    """

    __tablename__ = "edgefolio_email_proof"
    __table_args__ = (db.UniqueConstraint("user_id", "email", name="edgefolio_email_proof_user_email"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("core_user.id"), nullable=False, index=True)
    email = db.Column(db.String(254), nullable=False, index=True)
    token_hash = db.Column(db.String(64), nullable=False, default="", index=True)
    requested_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified_at = db.Column(db.DateTime, nullable=True)


class Mailbox(db.Model):
    """Una fila por dirección a la que la tienda escribe. No guarda más que cuándo: sirve para que lo que
    se cuenta por dirección (las descargas gratis de un día) se cuente y se apunte de una vez, también
    con varias peticiones a la vez y varios procesos (se bloquea su fila, en SQLite y en Postgres)."""

    __tablename__ = "edgefolio_mailbox"

    email = db.Column(db.String(254), primary_key=True)
    first_seen_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    last_seen_at = db.Column(db.DateTime, nullable=False, default=utcnow)
