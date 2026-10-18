# -*- coding: utf-8 -*-
"""Los cambios del día (del BCE, por frankfurter.app) en catalogue/fx.json. Una vez al día:

    flask --app app edgefolio fx-update      # p. ej. a las 17:00 CET, después de que publique el BCE

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


def fetch() -> dict:
    r = httpx.get(URL, timeout=20, follow_redirects=True)
    r.raise_for_status()
    body = r.json()
    rates = {"USD": 1, **body["rates"], **PEGGED}
    return {"base": "USD", "date": body["date"], "rates": rates, "source": "ECB via frankfurter.app"}


def write(data: dict, path: Path):
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)  # el servidor nunca lee medio fichero
