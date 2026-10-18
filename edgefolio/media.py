# -*- coding: utf-8 -*-
"""Las miniaturas de los gráficos (GET /thumbs/<raíz>.webp, para las tarjetas y las tablas) y los cambios
de moneda (GET /api/fx, para los precios «≈»).

Un gráfico PNG pesa unos 100 KB; una tarjeta necesita un WebP de 640 px de la décima parte. Cada uno se
hace la primera vez que se pide y se guarda en <datos>/edgefolio/thumbs: publicar un catálogo no tiene
que hacer 5.668. Y se vuelve a hacer cuando el gráfico es más nuevo que él: publicar un paquete reemplaza
un gráfico con el mismo nombre, y no sólo con ``flask edgefolio import`` (que vacía la carpeta), también con
``python catalogue/publish.py --package``, que no sabe dónde está.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Optional

try:
    from PIL import Image
except ImportError:  # la tienda sigue funcionando: el navegador recibe el PNG entero
    Image = None

WIDTH = 640
QUALITY = 80
STEM = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_+=-]{0,200}$")

_stems = {}


def charts(settings) -> set:
    """Los nombres de los gráficos que existen: las únicas raíces de las que se puede pedir miniatura."""
    folder = settings.static / "assets" / "charts"
    if folder not in _stems:
        _stems[folder] = {p.stem for p in folder.glob("*.png")} if folder.is_dir() else set()
    return _stems[folder]


def make_thumb(src: Path, dest: Path):
    with Image.open(src) as im:
        im.load()
        if im.width > WIDTH:
            im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA")
        dest.parent.mkdir(parents=True, exist_ok=True)
        # se escribe al lado y se renombra: dos primeras peticiones nunca sirven medio fichero
        fd, tmp = tempfile.mkstemp(dir=dest.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as f:
                im.save(f, "WEBP", quality=QUALITY, method=4)
            os.replace(tmp, dest)
        except BaseException:
            os.unlink(tmp)
            raise


def thumb(settings, stem: str) -> Optional[Path]:
    """La miniatura de ``stem`` (hecha si hace falta); None sin Pillow (vale el PNG). KeyError si no es
    un gráfico del catálogo."""
    if not STEM.match(stem) or stem not in charts(settings):
        raise KeyError(stem)
    if Image is None:
        return None
    dest = settings.thumbs_dir / f"{stem}.webp"
    src = settings.static / "assets" / "charts" / f"{stem}.png"
    try:
        # estricto: una hecha en el mismo instante que el gráfico (un disco de tiempos gruesos) se rehace una vez más
        fresh = dest.stat().st_mtime_ns > src.stat().st_mtime_ns
    except FileNotFoundError:  # sin miniatura; o sin el gráfico (--prune con la tienda en marcha): vale la que haya
        fresh = dest.is_file()
    if not fresh:
        make_thumb(src, dest)
    return dest


def fx(settings) -> dict:
    """Del dólar a las monedas locales; PayPal cobra siempre en dólares, esto sólo pinta el «≈». Los del
    día (``flask edgefolio fx-update``, en la carpeta de datos) o, sin ellos, los de ejemplo del repo."""
    path = settings.fx_today if Path(settings.fx_today).is_file() else settings.fx
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"base": "USD", "date": None, "rates": {"USD": 1}, "source": "none"}
    return {"base": data.get("base", "USD"), "date": data.get("date"), "rates": data.get("rates", {}),
            "source": data.get("source", "")}
