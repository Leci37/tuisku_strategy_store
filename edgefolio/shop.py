# -*- coding: utf-8 -*-
"""Lo que la tienda tiene cargado mientras corre: la configuración, el catálogo (con su índice de
búsqueda), PayPal (el de verdad o el de prueba), los límites por IP y los textos de sus correos.

Uno por app, en ``app.extensions["edgefolio"]``. Lo monta ``routes`` al registrar el blueprint, con la
configuración del entorno; las pruebas lo cambian con ``install(app, settings, paypal)``.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from zlecitool_core.i18n import in_language
from zlecitool_core.i18n import t as core_text

from . import search
from .catalogue import Catalogue
from .paypal import FakePayPal, PayPalREST
from .settings import ROOT, Settings
from .web import RateLimit

log = logging.getLogger(__name__)

EXTENSION = "edgefolio"
DICTIONARY = ROOT / "i18n" / "ui.json"

# Correos de confirmación (de una dirección, del alta en las novedades) que puede pedir una IP en una
# ventana: PROOF_LIMIT en PROOF_WINDOW segundos. Y las descargas gratis: FREE_LIMIT en FREE_WINDOW.
PROOF_LIMIT, PROOF_WINDOW = 10, 600
FREE_LIMIT, FREE_WINDOW = 20, 3600
# Códigos de descuento que no valen que puede probar una IP en una ventana: el presupuesto dice si uno vale, y sin
# tope se adivinaban (300 en un segundo, 14-11-2026). Pasado, ningún código se mira hasta que la ventana corre.
CODE_LIMIT, CODE_WINDOW = 20, 3600
# Correos de «Confirma tu correo» a una misma dirección (de cualquier cuenta) en una ventana: una cuenta nueva no
# cuesta nada, y cada 61 segundos salía otro a la misma dirección ajena (14-11-2026).
PROOF_TO_LIMIT, PROOF_TO_WINDOW = 5, 86400


class Texts:
    """Los textos de los correos en un idioma dado, el de quien los recibe, leídos del diccionario de la
    herramienta (i18n/ui.json, las claves mail*): el trabajo diario de los avisos no tiene petición. Un
    idioma que falta va al inglés; {nombre} se rellena aquí, y la forma de un texto que cuenta (n) la elige
    el núcleo."""

    PLACEHOLDER = re.compile(r"\{(\w+)\}")

    def __init__(self, path: Path = DICTIONARY):
        self.data = json.loads(Path(path).read_text(encoding="utf-8"))

    def get(self, key: str, lang: str, **values) -> str:
        entry = self.data[key]
        text = entry.get(lang) or entry["en"]
        if isinstance(text, dict):
            # un texto que cuenta: la forma la elige el núcleo con n, con las reglas de cada idioma (CONTRATO, «Un
            # texto que cuenta algo»; en árabe, 2 lleva el dual, de 3 a 10 el plural y de 11 a 99 el singular), en
            # el idioma de quien lo recibe (in_language, también sin petición: el trabajo de los avisos). Sólo con
            # n: lo demás se rellena aquí, porque el núcleo no admite un nombre como {code} (el de los avisos), que
            # es también el del idioma en su Dictionary.text
            counted = {"n": values["n"]} if "n" in values else {}
            with in_language(lang if lang in entry else "en"):
                text = core_text(key, **counted)
        return self.PLACEHOLDER.sub(lambda m: str(values[m[1]]) if m[1] in values else m[0], text)


_catalogues = {}


def load_catalogue(settings: Settings) -> Catalogue:
    """El catálogo de esos ficheros, leído una vez por proceso mientras no cambien (varias apps en el
    mismo proceso, como las pruebas, no lo leen y lo indexan cada una)."""
    paths = (settings.catalogue, settings.indicators, settings.bundles, settings.since_release, settings.levels,
             Path(settings.catalogue).parent / "release.json")
    stamp = tuple((str(p), hashlib.sha1(p.read_bytes()).hexdigest() if p.is_file() else None) for p in map(Path, paths))
    # la carpeta static: de sus vistas previas sale la caducidad de cada script
    key = (stamp, settings.new_days, tuple(settings.grade_cutoffs), str(settings.static))
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
        self.limits = {"proof": RateLimit(PROOF_LIMIT, PROOF_WINDOW), "free": RateLimit(FREE_LIMIT, FREE_WINDOW),
                       "code": RateLimit(CODE_LIMIT, CODE_WINDOW), "proof_to": RateLimit(PROOF_TO_LIMIT, PROOF_TO_WINDOW)}
        log.info("Tienda en marcha | paypal=%s estrategias=%s lotes=%s", self.settings.paypal_mode, len(self.catalogue),
                 len(self.catalogue.bundles))


def install(app, settings: Settings, paypal=None, catalogue: Optional[Catalogue] = None) -> Shop:
    """Pone (o cambia) la tienda de la app: lo hace el arranque y, con otra configuración, las pruebas."""
    shop = Shop(settings, paypal=paypal, catalogue=catalogue)
    app.extensions[EXTENSION] = shop
    return shop


def of(app) -> Shop:
    return app.extensions[EXTENSION]
