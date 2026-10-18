# -*- coding: utf-8 -*-
"""Los avisos de las favoritas: un correo por persona, en su idioma, con lo que cambió desde la vuelta
anterior; sólo a un correo que la cuenta ha demostrado que es suyo."""
import csv
import json

from edgefolio.shop import install
from tests.conftest import BUNDLES, ROWS, outbox, prove, signed, strategy_id

AAPL, MSFT, TSLA = strategy_id(ROWS[0]), strategy_id(ROWS[1]), strategy_id(ROWS[3])


def follow(client, item, **alerts_on):
    r = client.put(f"/api/favourites/{item}", json={"alerts": alerts_on})
    assert r.status_code == 200, r.get_data(as_text=True)


def account(app, email="ana@example.com", lang="es"):
    """Una cuenta con su correo demostrado y el idioma que eligió en la carcasa."""
    client = signed(app, email)
    client.post("/zt/lang", json={"lang": lang})
    prove(client)
    return client


def republish(app, settings, paypal, rows, bundles):
    """Lo que hacen publish.py y un cambio de bundles.json entre dos vueltas (y la tienda, al arrancar)."""
    with open(settings.catalogue, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    settings.bundles.write_text(json.dumps(bundles))
    install(app, settings, paypal)


def run(app):
    result = app.test_cli_runner().invoke(args=["edgefolio", "send-alerts"])
    assert result.exit_code == 0, result.output
    return result.output


def mails(to="ana@example.com"):
    return [m for m in outbox(to) if "Edgefolio:" in m["subject"]]


def test_the_first_run_only_takes_the_picture(app):
    ana = account(app)
    follow(ana, TSLA, pd=True)
    assert "primera vez" in run(app) and mails() == []
    assert "0 estrategias cambiaron; 0 correos" in run(app)


def test_changes_are_emailed_once_in_the_persons_language(app, settings, paypal):
    ana = account(app)
    follow(ana, TSLA, pd=True, bd=True)
    follow(ana, AAPL, nv=True)
    follow(ana, MSFT)                      # una favorita sin avisos no recibe nada
    run(app)
    rows = [dict(r, version="2" if r["ticker"] == "AAPL" else "1") for r in ROWS]
    rows[3]["Price"], rows[1]["Price"] = "40", "60"   # TSLA y MSFT, más baratas
    trio = {"key": "trio", "name_key": "bundleCrypto", "ids": [TSLA, strategy_id(ROWS[1])], "price": 90}
    republish(app, settings, paypal, rows, BUNDLES + [trio])
    assert "3 estrategias cambiaron; 1 correos" in run(app)   # AAPL versión, TSLA precio + lote, MSFT precio
    (mail,) = mails()
    assert mail["subject"] == "Edgefolio: novedades de tus estrategias favoritas"
    body = mail["body"]
    assert "Tesla (TSLA · 1C00): ahora $40.00, antes $50.00." in body
    assert "ahora está en el pack «" in body and "$90.00 por 2 estrategias" in body
    assert "Apple (AAPL · 1ADX): versión nueva, v2." in body
    assert "Microsoft" not in body, "no tiene ningún aviso encendido"
    assert f"http://localhost:5105/s/{TSLA}" in body and "/mine" in body
    assert "0 correos" in run(app), "el mismo cambio no se manda dos veces"


def test_a_price_rise_or_switched_off_alert_sends_nothing(app, settings, paypal):
    ana = account(app)
    follow(ana, TSLA, pd=False, nv=True)
    run(app)
    rows = [dict(r) for r in ROWS]
    rows[3]["Price"] = "40"
    republish(app, settings, paypal, rows, BUNDLES)
    assert "0 correos" in run(app)
    rows[3]["Price"] = "70"
    republish(app, settings, paypal, rows, BUNDLES)
    assert "0 correos" in run(app)


def test_in_the_language_of_the_page_and_only_to_a_proven_email(app, settings, paypal, monkeypatch):
    monkeypatch.setenv("ZLECITOOL_PUBLIC_URL", "https://shop.example")
    bo = account(app, "bo@example.com", lang="en")
    follow(bo, TSLA, pd=True)
    stranger = signed(app, "victim@example.com")      # alguien que se dio de alta con el correo de otro
    follow(stranger, TSLA, pd=True)
    run(app)
    rows = [dict(r) for r in ROWS]
    rows[3]["Price"] = "45"
    republish(app, settings, paypal, rows, BUNDLES)
    assert "1 correos; 1 cuentas sin el correo confirmado" in run(app)
    (mail,) = mails("bo@example.com")
    assert mail["subject"] == "Edgefolio: news about your favourite strategies"
    assert "Tesla (TSLA · 1C00): now $45.00, was $50.00. https://shop.example/s/" in mail["body"]
    assert mails("victim@example.com") == [], "sin demostrar el correo, ningún aviso"
