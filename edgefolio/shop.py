# -*- coding: utf-8 -*-
"""Lo que la tienda tiene cargado mientras corre: la configuración, el catálogo (con su índice de
búsqueda), PayPal (el de verdad o el de prueba), los límites por IP y los textos de sus correos.

Uno por app, en ``app.extensions["edgefolio"]``. Lo monta ``routes`` al registrar el blueprint, con la
configuración del entorno; las pruebas lo cambian con ``install(app, settings, paypal)``.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from . import search
from .catalogue import Catalogue
from .paypal import FakePayPal, PayPalREST
from .settings import ROOT, Settings
from .web import RateLimit

EXTENSION = "edgefolio"
DICTIONARY = ROOT / "i18n" / "ui.json"

# Correos de confirmación (de una dirección, del alta en las novedades) que puede pedir una IP en una
# ventana: PROOF_LIMIT en PROOF_WINDOW segundos. Y las descargas gratis: FREE_LIMIT en FREE_WINDOW.
PROOF_LIMIT, PROOF_WINDOW = 10, 600
FREE_LIMIT, FREE_WINDOW = 20, 3600


class Texts:
    """Los textos de los correos en un idioma dado, leídos del diccionario de la herramienta
    (i18n/ui.json, las claves mail*): el trabajo diario de los avisos no tiene petición, así que no
    puede preguntar al núcleo el idioma. Un idioma que falta va al inglés; {nombre} se rellena aquí."""

    PLACEHOLDER = re.compile(r"\{(\w+)\}")

    def __init__(self, path: Path = DICTIONARY):
        self.data = json.loads(Path(path).read_text(encoding="utf-8"))

    def get(self, key: str, lang: str, **values) -> str:
        entry = self.data[key]
        text = entry.get(lang) or entry["en"]
        if isinstance(text, dict):  # una forma de plural, como la lee t() en el navegador
            text = text.get("other", "")
        return self.PLACEHOLDER.sub(lambda m: str(values[m[1]]) if m[1] in values else m[0], text)


_catalogues = {}


def load_catalogue(settings: Settings) -> Catalogue:
    """El catálogo de esos ficheros, leído una vez por proceso mientras no cambien (varias apps en el
    mismo proceso, como las pruebas, no lo leen y lo indexan cada una)."""
    paths = (settings.catalogue, settings.indicators, settings.bundles, settings.since_release)
    stamp = tuple((str(p), hashlib.sha1(p.read_bytes()).hexdigest() if p.is_file() else None) for p in map(Path, paths))
    key = (stamp, settings.new_days)
    if key not in _catalogues:
        if len(_catalogues) > 8:
            _catalogues.clear()
        _catalogues[key] = Catalogue(settings)
    return _catalogues[key]


@dataclass
class Shop:
    settings: Settings
    paypal: object = None
    catalogue: Catalogue = None
    texts: Texts = None
    limits: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.catalogue is None:
            self.catalogue = load_catalogue(self.settings)
        search.index_of(self.catalogue)  # hecho ya: el primero que llega no lo espera
        if self.paypal is None:
            s = self.settings
            self.paypal = (FakePayPal() if s.paypal_mode == "fake" else
                           PayPalREST(s.paypal_mode, s.paypal_client_id, s.paypal_client_secret))
        if self.texts is None:
            self.texts = Texts()
        self.limits = {"proof": RateLimit(PROOF_LIMIT, PROOF_WINDOW), "free": RateLimit(FREE_LIMIT, FREE_WINDOW)}


def install(app, settings: Settings, paypal=None, catalogue: Optional[Catalogue] = None) -> Shop:
    """Pone (o cambia) la tienda de la app: lo hace el arranque y, con otra configuración, las pruebas."""
    shop = Shop(settings, paypal=paypal, catalogue=catalogue)
    app.extensions[EXTENSION] = shop
    return shop


def of(app) -> Shop:
    return app.extensions[EXTENSION]
