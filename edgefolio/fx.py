# -*- coding: utf-8 -*-
"""Los cambios del día (del BCE, por frankfurter.app) en <datos>/edgefolio/fx.json. Una vez al día los trae el reloj
del núcleo (la tarea ``fx_update`` de tool.json, a las 17:00 de Madrid, después de que publique el BCE;
edgefolio/tasks.py); a mano:

    flask --app app edgefolio fx-update

La tienda sólo los usa para enseñar «≈ importe» en la moneda de quien mira; PayPal cobra en dólares.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import httpx

URL = "https://api.frankfurter.app/latest?from=USD"
# El BCE no publica el riyal; está atado al dólar a 3,75 desde 1986.
PEGGED = {"SAR": 3.75}
# Lo que puede fallar al traerlos: la red, o una respuesta que no es la de siempre.
FAILURES = (httpx.HTTPError, KeyError, TypeError, ValueError)


def fetch() -> dict:
    r = httpx.get(URL, timeout=20, follow_redirects=True)
    r.raise_for_status()
    body = r.json()
    rates = {"USD": 1, **body["rates"], **PEGGED}
    return {"base": "USD", "date": body["date"], "rates": rates, "source": "ECB via frankfurter.app"}


def write(data: dict, path: Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)  # el servidor nunca lee medio fichero
