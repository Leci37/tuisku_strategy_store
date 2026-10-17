# -*- coding: utf-8 -*-
"""La tienda aislada: datos, base de datos y secreto temporales (testing.isolated() del núcleo), sobre un
catálogo pequeño de cuatro estrategias, con PayPal de prueba y sin un solo correo de verdad.

``app`` es la tienda con ese catálogo; ``client``, alguien sin cuenta (con su token CSRF, como lo pone
csrf.js en el navegador); ``signed(app, email)``, una cuenta del núcleo con la sesión abierta; y
``real_client``, la tienda con el catálogo de verdad (2.834 estrategias), sus lotes y sus gráficos.
"""
import csv
import json
import re
from datetime import date
from decimal import Decimal

import pytest

from zlecitool_core import testing

from edgefolio.catalogue import Strategy, b64url
from edgefolio.paypal import FakePayPal
from edgefolio.settings import ROOT, Settings
from edgefolio.shop import install

TODAY = date.today().isoformat()

ROWS = [  # tres de pago y una gratis
    {"Price": "79", "ticker": "AAPL", "interval": "1Day", "key_techs": "1ADX", "id_model": "aaaa1111", "Name": "Apple",
     "Release date": "2024-09-27"},
    {"Price": "93", "ticker": "MSFT", "interval": "1Hour", "key_techs": "2BB0", "id_model": "bbbb2222",
     "Name": "Microsoft", "Release date": "2024-09-27"},
    {"Price": "0", "ticker": "NVDA", "interval": "1Day", "key_techs": "1ULT", "id_model": "cccc3333", "Name": "Nvidia",
     "Release date": TODAY},
    {"Price": "50", "ticker": "TSLA", "interval": "1Day", "key_techs": "1C00", "id_model": "dddd4444", "Name": "Tesla",
     "Release date": "2024-10-14"},
]
# "duo": AAPL + MSFT (172 $) por 150 $
BUNDLES = [{"key": "duo", "name_key": "bundleTop", "ids": ["AAPL_1Day_1ADX_aaaa1111", "MSFT_1Hour_2BB0_bbbb2222"],
            "price": 150}]


def cart_id(row: dict) -> str:
    """El id que ponía en el carrito la tienda de antes: el base64url de 'TICKER - INTERVAL - KEY - ID'."""
    return b64url(f"{row['ticker']} - {row['interval']} - {row['key_techs']} - {row['id_model']}")


def strategy_id(row: dict) -> str:
    """El id de la tienda nueva y de /s/<id>."""
    return f"{row['ticker']}_{row['interval']}_{row['key_techs']}_{row['id_model']}"


def visitor(app, ip=None):
    """Alguien sin cuenta, con el token CSRF de la página (csrf.js lo pone en cada POST del navegador)."""
    client = app.test_client()
    if ip:
        client.environ_base["REMOTE_ADDR"] = ip
    client.environ_base["HTTP_X_CSRFTOKEN"] = testing.csrf_token_of(client.get("/"))
    return client


def signed(app, email=""):
    """Una cuenta del núcleo con la sesión abierta y su token CSRF (la crea si no existe)."""
    return testing.signed_in_client(app, email=email)


def prove(client, email=None) -> str:
    """Lo que hace una persona para que su cuenta vea lo que compró sin ella: pide el enlace, lo abre desde
    su correo (la página dice de qué correo es) y lo confirma. Da el correo demostrado."""
    email = (email or client.email).strip().lower()
    assert client.post("/api/mine/proofs", json={"email": email}).json == {"sent": True}
    token = proof_token(email)
    assert client.post("/api/mine/proofs/peek", json={"token": token}).json == {"email": email}
    r = client.post("/api/mine/proofs/confirm", json={"token": token})
    assert r.status_code == 200 and r.json == {"email": email}, r.get_data(as_text=True)
    return email


def proof_token(email: str) -> str:
    """El token del último enlace de confirmación mandado a ``email``."""
    body = outbox(email)[-1]["body"]
    return re.search(r"/mine\?proof=([\w-]+)", body).group(1)


def outbox(to=None) -> list:
    """Los correos que la tienda «mandó» (no sale ninguno): {to, subject, body}. De uno con su versión en HTML
    (los del núcleo, como el adiós de una cuenta borrada), su texto."""
    out = [{"to": str(m["To"]), "subject": str(m["Subject"]),
            "body": m.get_body(preferencelist=("plain",)).get_content()} for m in testing.mail_outbox()]
    return [m for m in out if to is None or m["to"] == to]


def link_in(body: str, pattern: str) -> str:
    """El primer enlace del correo que encaja con ``pattern``."""
    return re.search(r"https?://\S*" + pattern + r"\S*", body).group(0)


@pytest.fixture
def settings(tmp_path):
    cat = tmp_path / "catalogue"
    cat.mkdir()
    with open(cat / "catalogue.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(ROWS[0]), delimiter="\t")
        w.writeheader()
        w.writerows(ROWS)
    (cat / "indicators.csv").write_text("key\texplanation\n")
    (cat / "bundles.json").write_text(json.dumps(BUNDLES))
    (cat / "fx.json").write_text((ROOT / "catalogue" / "fx.json").read_text())
    private = tmp_path / "strategies"
    private.mkdir()
    for row in ROWS:  # los de pago, con el nombre que les da la fábrica
        if Decimal(row["Price"]) > 0:
            s = Strategy(row["ticker"], row["interval"], row["key_techs"], row["id_model"], Decimal(row["Price"]), row)
            (private / s.private_file).write_text(f"//@version=5\nstrategy(\"{s.key}\")\n")
    return Settings(catalogue=cat / "catalogue.csv", indicators=cat / "indicators.csv", bundles=cat / "bundles.json",
                    fx=cat / "fx.json", fx_today=tmp_path / "fx-today.json", since_release=cat / "since_release.csv",
                    strategies_dir=private, thumbs_dir=tmp_path / "thumbs",
                    discount_codes={"spring20": Decimal("0.20"), "big60": Decimal("0.60")},
                    flat_price_codes={"launch": Decimal("0.99")})


@pytest.fixture
def paypal():
    return FakePayPal()


@pytest.fixture
def app(tmp_path, settings, paypal):
    with testing.isolated(tmp_path / "zt"):
        from app import create_app
        application = testing.prepare(create_app())
        install(application, settings, paypal)
        yield application


@pytest.fixture
def shop(app):
    from edgefolio.shop import of
    return of(app)


@pytest.fixture
def client(app):
    return visitor(app)


@pytest.fixture
def ids():
    return [cart_id(r) for r in ROWS]


@pytest.fixture(scope="session")
def real_app(tmp_path_factory):
    """La tienda con el catálogo de verdad (2.834 estrategias), sus lotes y sus gráficos."""
    tmp = tmp_path_factory.mktemp("real")
    with testing.isolated(tmp / "zt"):
        from app import create_app
        application = testing.prepare(create_app())
        install(application, Settings.for_data_dir(tmp / "data"), FakePayPal())
        yield application


@pytest.fixture
def real_client(real_app):
    return visitor(real_app)
