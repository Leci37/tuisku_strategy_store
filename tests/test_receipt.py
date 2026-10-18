# -*- coding: utf-8 -*-
"""El recibo por correo (la «factura por correo» de la fila de confianza bajo el botón de pagar): sale una
vez, cuando el pago entra, en el idioma de la página que cobra."""
from edgefolio import routes
from tests.conftest import outbox

AAPL, TSLA = "AAPL_1Day_1ADX_aaaa1111", "TSLA_1Day_1C00_dddd4444"


def receipts():
    return [m for m in outbox() if "Edgefolio" in m["subject"] and ("order" in m["subject"] or "pedido" in m["subject"])]


def pay(client, body, lang="en"):
    order = client.post("/api/orders", json=body)
    assert order.status_code == 200, order.get_data(as_text=True)
    order_id = order.json["id"]
    return order_id, client.post(f"/api/orders/{order_id}/capture", headers={"Accept-Language": lang})


def test_the_payer_gets_a_receipt_in_the_pages_language(client):
    order_id, r = pay(client, {"items": [AAPL, TSLA]}, lang="es")
    assert r.status_code == 200
    [mail] = receipts()
    assert mail["to"] == "buyer@example.com"                 # quien paga en el PayPal de prueba
    assert mail["subject"] == f"Tu pedido de Edgefolio {order_id}"
    body = mail["body"]
    assert "- Apple (AAPL · 1ADX · 1Day): 79.00 USD" in body and "- Tesla (TSLA · 1C00 · 1Day): 50.00 USD" in body
    assert "Total pagado con PayPal: 129.00 USD" in body and "/mine" in body and "7 días" in body


def test_a_bundle_is_one_line_and_a_retry_sends_nothing_more(client):
    order_id, _ = pay(client, {"bundles": ["duo"]})
    assert client.post(f"/api/orders/{order_id}/capture").status_code == 200   # otra vez (un fallo de red)
    [mail] = receipts()
    assert mail["subject"] == f"Your Edgefolio order {order_id}"
    assert "(2): 150.00 USD" in mail["body"] and "Total paid with PayPal: 150.00 USD" in mail["body"]


def test_without_a_public_address_the_payment_still_goes_through(client, monkeypatch):
    order_id = client.post("/api/orders", json={"items": [AAPL]}).json["id"]
    # la dirección pública falta al cobrar (la vuelta de PayPal ya estaba hecha)
    monkeypatch.setattr(routes, "external_url", lambda *a, **k: None)
    r = client.post(f"/api/orders/{order_id}/capture")
    assert r.status_code == 200 and r.json["status"] == "PAID" and receipts() == []
