# -*- coding: utf-8 -*-
"""Demostrar que un correo es de una cuenta, para ver en Mis estrategias lo comprado o descargado sin
cuenta con ese correo.

El núcleo no comprueba el correo de quien se da de alta: si Mis estrategias enseñara los pedidos cuyo
correo es el de la cuenta, cualquiera podría registrarse con el de quien compró y llevarse sus enlaces.
Así que lo hecho con la sesión abierta es de la cuenta (``user_id``), y lo hecho sin ella sólo se le
enseña cuando la cuenta ha demostrado su correo:

1. POST /api/mine/proofs {email} manda a esa dirección <ZLECITOOL_PUBLIC_URL>/mine?proof=<token>
   (PROOF_HOURS, un solo uso, sólo para la cuenta que lo pidió).
2. Esa página pregunta de quién es (POST /api/mine/proofs/peek {token} -> {email}, sin gastar nada) y
   sólo confirma cuando la persona pulsa: POST /api/mine/proofs/confirm {token}. Un lector de correo que
   abre el enlace (para mirarlo) no confirma nada.
"""
from __future__ import annotations

import secrets
from datetime import timedelta
from typing import List, Optional

from sqlalchemy import update

from zlecitool_core.db import db, utcnow

from .models import EmailProof
from .web import digest

PROOF_HOURS = 24
#: Direcciones sin confirmar que puede tener pendientes una cuenta: el formulario no sirve para llenar
#: buzones ajenos.
MAX_PENDING = 5
#: Un correo de confirmación a la misma dirección, como mucho cada tanto (un doble clic, una impaciencia).
RESEND_SECONDS = 60


def proven(user_id: Optional[int]) -> List[str]:
    """Los correos que la cuenta ha demostrado que son suyos."""
    if user_id is None:
        return []
    rows = EmailProof.query.filter(EmailProof.user_id == user_id, EmailProof.verified_at.isnot(None))
    return sorted(r.email for r in rows)


def is_proven(user_id: Optional[int], email: str) -> bool:
    return bool(user_id is not None and email and EmailProof.query.filter(
        EmailProof.user_id == user_id, EmailProof.email == email, EmailProof.verified_at.isnot(None)).first())


def request(user_id: int, email: str) -> Optional[str]:
    """El token del enlace que hay que mandar a ``email``, o None si no hay que mandar nada: la dirección
    ya es suya, se le acaba de mandar uno o la cuenta tiene demasiadas pendientes."""
    now = utcnow()
    row = EmailProof.query.filter_by(user_id=user_id, email=email).first()
    if row is not None and row.verified_at is not None:
        return None
    if row is not None and row.token_hash and row.requested_at > now - timedelta(seconds=RESEND_SECONDS):
        return None
    if row is None:
        pending = EmailProof.query.filter(EmailProof.user_id == user_id, EmailProof.verified_at.is_(None),
                                          EmailProof.expires_at > now).count()
        if pending >= MAX_PENDING:
            return None
        row = EmailProof(user_id=user_id, email=email)
        db.session.add(row)
    token = secrets.token_urlsafe(32)
    row.token_hash, row.requested_at, row.expires_at = digest(token), now, now + timedelta(hours=PROOF_HOURS)
    db.session.commit()
    return token


def forget(user_id: int, token: str):
    """Un enlace que no se pudo mandar: deja de valer."""
    db.session.execute(update(EmailProof).where(EmailProof.user_id == user_id,
                                                EmailProof.token_hash == digest(token)).values(token_hash=""))
    db.session.commit()


def _pending(user_id: int, token: str) -> Optional[EmailProof]:
    if not token or len(token) > 200:
        return None
    return EmailProof.query.filter(EmailProof.user_id == user_id, EmailProof.token_hash == digest(token),
                                   EmailProof.verified_at.is_(None), EmailProof.expires_at > utcnow()).first()


def peek(user_id: int, token: str) -> Optional[str]:
    """De qué correo es un enlace de esta cuenta que aún vale, sin gastarlo."""
    row = _pending(user_id, token)
    return row.email if row else None


def confirm(user_id: int, token: str) -> Optional[str]:
    """El correo que queda demostrado, una vez; None si el enlace es de otra cuenta, usado o viejo."""
    row = _pending(user_id, token)
    if row is None:
        return None
    done = db.session.execute(update(EmailProof).where(
        EmailProof.id == row.id, EmailProof.verified_at.is_(None)).values(verified_at=utcnow(), token_hash="")).rowcount
    db.session.commit()
    return row.email if done == 1 else None
