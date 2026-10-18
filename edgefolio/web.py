# -*- coding: utf-8 -*-
"""Lo que comparten las rutas, sin Flask: los rechazos (una clave del diccionario, nunca una frase), los
límites por dirección IP, la forma de lo que llega en el cuerpo JSON y la regla de los correos.

Un rechazo es ``Refusal("errAlgo", 400, field="email")``: las rutas lo contestan como
``{"error": "errAlgo", "field": "email"}``, la convención de las herramientas, y la página lo enseña
traducido. Lo que acompaña a la clave (``vars`` para el texto, ``items`` con lo que ya no se vende…) es
para la página, no para leerlo.
"""
from __future__ import annotations

import hashlib
import re
import threading
import time
from collections import deque
from email.utils import parseaddr
from typing import Any, Optional


class Refusal(Exception):
    """Lo que no se puede hacer, con su clave del diccionario y su código HTTP."""

    def __init__(self, key: str, status: int = 400, vars: Optional[dict] = None, **extra: Any):
        super().__init__(key)
        self.key, self.status, self.vars, self.extra = key, status, vars, extra

    def body(self) -> dict:
        out = {"error": self.key, **self.extra}
        if self.vars:
            out["vars"] = self.vars
        return out


def invalid(field: str) -> Refusal:
    """Un parámetro que no tiene la forma que se espera: ``field`` es su nombre, como lo manda la página
    ('email', 'size', 'alerts.nv'; 'body' cuando el cuerpo no es el objeto JSON que se espera)."""
    return Refusal("errRequest", 400, field=field)


def digest(token: str) -> str:
    """Los enlaces de un solo uso y la cookie de quien compra se guardan sólo como hash: una copia de la
    base de datos no abre nada."""
    return hashlib.sha256(token.encode()).hexdigest()


# ── el cuerpo JSON ───────────────────────────────────────────────────────────

def json_object(body: Any) -> dict:
    """El cuerpo, que tiene que ser un objeto JSON (un formulario de otra web no puede mandar uno)."""
    if not isinstance(body, dict):
        raise invalid("body")
    return body


def text_field(body: dict, name: str, max_length: int, default: Optional[str] = None) -> str:
    value = body.get(name, default)
    if value is None or not isinstance(value, str) or len(value) > max_length:
        raise invalid(name)
    return value


def list_field(body: dict, name: str, max_items: int, max_length: int = 200) -> list:
    value = body.get(name, [])
    if (not isinstance(value, list) or len(value) > max_items
            or any(not isinstance(v, str) or len(v) > max_length for v in value)):
        raise invalid(name)
    return value


def bool_field(body: dict, name: str, default: bool = False, prefix: str = "") -> bool:
    value = body.get(name, default)
    if not isinstance(value, bool):
        raise invalid(prefix + name)
    return value


# ── los correos ──────────────────────────────────────────────────────────────

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s.]+$")
# Lo que hace que un programa de correo lea otra cosa: una lista (, ;), un nombre o un comentario
# (< > ( ) "), una ruta o un grupo ([ ] :), un escape (\). Y los espacios (un salto de línea es una
# cabecera nueva: «Bcc:»).
NOT_IN_EMAIL = frozenset(',;<>()"[]:\\')


def valid_email(email: Any, problem=None) -> str:
    """La dirección, sin espacios y en minúsculas, o un rechazo. ``problem`` es la regla del núcleo
    (``security.email_problem``); esta, más estricta, es la de la tienda: sus correos llevan enlaces."""
    if not isinstance(email, str):
        raise Refusal("errEmailInvalid", 400, field="email")
    email = email.strip().lower()
    if (len(email) > 254 or email.count("@") != 1
            or any(c in NOT_IN_EMAIL or c.isspace() or not c.isprintable() for c in email)
            or parseaddr(email) != ("", email) or not EMAIL.match(email)
            or (problem is not None and problem(email))):
        raise Refusal("errEmailInvalid", 400, field="email")
    return email


# ── los límites por dirección IP ─────────────────────────────────────────────

class RateLimit:
    """Como mucho ``limit`` veces por clave en cualquier ventana de ``window`` segundos: una ventana que
    se desliza, en memoria. Es por proceso y empieza vacía al arrancar: basta para que un script no
    llene los buzones de nadie."""

    SWEEP_EVERY = 1000  # las veces entre dos limpiezas de las claves que se han callado

    def __init__(self, limit: int, window: float, clock=time.monotonic):
        self.limit, self.window, self.clock = limit, window, clock
        self.hits = {}
        self.calls = 0
        self.lock = threading.Lock()

    def hit(self, key: str) -> bool:
        """True (y cuenta) si ``key`` está por debajo del límite; False (y no cuenta) si no."""
        now = self.clock()
        with self.lock:
            self.calls += 1
            if self.calls % self.SWEEP_EVERY == 0:
                self.hits = {k: q for k, q in self.hits.items() if q and q[-1] > now - self.window}
            q = self.hits.setdefault(key, deque())
            while q and q[0] <= now - self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True
