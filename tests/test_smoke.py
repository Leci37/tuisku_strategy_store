# -*- coding: utf-8 -*-
"""La prueba de humo: la tienda arranca sobre el núcleo y cumple su contrato.

testing.check_tool(app) es el contrato del núcleo hecho prueba (que cada página pide sesión salvo lo
@public, que cada texto está en los 8 idiomas, la barra, el pie, las cabeceras de seguridad…). Crece con
cada versión del núcleo: no se quita ni se rodea. Desde la 0.30 recibe ``privacy_sample``: lo de una cuenta
como lo de verdad (``sample``, en tests/test_privacy.py), con lo que exporta, borra la cuenta y comprueba que
no queda nada fuera de los pedidos (``keep``), y que ésos se quedan sin correo.
"""
from pathlib import Path

from zlecitool_core import load_ficha, testing

from tests.test_privacy import sample

ROOT = Path(__file__).resolve().parent.parent
FICHA = load_ficha(ROOT)


def test_the_tool_meets_the_core_contract(app):
    testing.check_tool(app, privacy_sample=sample)


def test_the_package_is_named_after_the_slug():
    assert FICHA.slug == "edgefolio" and (ROOT / FICHA.slug / "__init__.py").is_file()


def test_a_public_tool_that_sells_with_paypal_not_credits():
    assert not FICHA.is_business and not FICHA.ads and not FICHA.prices and FICHA.tour is None
    assert tuple(FICHA.wordmark) == ("Edge", "folio") and FICHA.name_key == "toolName"


def test_the_shop_is_public_and_my_strategies_asks_to_sign_in(app, client):
    for path in ("/", "/thanks", "/s/AAPL_1Day_1ADX_aaaa1111", "/s/AAPL_1Day_1ADX_aaaa1111/tree", "/api/config",
                 "/api/strategies?size=1", "/api/bundles", "/api/fx", "/api/me"):
        assert app.test_client().get(path).status_code == 200, path
    assert app.test_client().get("/mine").headers["location"] == "/login?next=/mine"


def test_the_page_in_the_language_of_the_shell(app):
    page = app.test_client().get("/?lang=ar").get_data(as_text=True)
    assert '<html lang="ar" dir="rtl"' in page and "استراتيجيات TradingView" in page
