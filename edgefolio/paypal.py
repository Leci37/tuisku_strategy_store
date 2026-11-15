# -*- coding: utf-8 -*-
"""PayPal Orders v2: crear un pedido por un importe que calculó el servidor, cobrarlo y comprobar lo
que se pagó de verdad. FakePayPal hace de PayPal en local y en las pruebas.

Un cobro puede hacerse en PayPal sin que su respuesta llegue (un tiempo agotado, un reinicio): cada intento
siguiente contesta 422 ORDER_ALREADY_CAPTURED. Por eso el cobro lleva su PayPal-Request-Id (repetirlo da la
misma respuesta) y ``settled()`` pregunta a PayPal por el pedido: lo que de verdad cobró, si cobró."""
from __future__ import annotations

import secrets
from dataclasses import dataclass
from decimal import Decimal

import httpx

BASE_URLS = {"sandbox": "https://api-m.sandbox.paypal.com", "live": "https://api-m.paypal.com"}


@dataclass
class Capture:
    status: str          # COMPLETED cuando el dinero se movió
    amount: Decimal
    currency: str
    payer: str           # el correo (o el id) de quien pagó, para el recibo


@dataclass
class Created:
    id: str
    approve_url: str     # adonde va el navegador para aprobar el pago


class PayPalError(Exception):
    pass


def _send(call, url: str, **kw):
    """Una petición a PayPal; una que no llega o no vuelve (red, tiempo agotado) es un PayPalError, como un
    rechazo: hasta el 14-11-2026 era un 500 sin más."""
    try:
        return call(url, **kw)
    except httpx.HTTPError as e:
        raise PayPalError(f"PayPal no contestó: {type(e).__name__}") from e


def _capture_of(body: dict):
    """El cobro de un pedido de PayPal (su respuesta al cobrar, o el pedido entero), o None si no lo tiene."""
    try:
        cap = body["purchase_units"][0]["payments"]["captures"][0]
    except (KeyError, IndexError, TypeError):
        return None
    payer = body.get("payer", {})
    return Capture(cap["status"], Decimal(cap["amount"]["value"]), cap["amount"]["currency_code"],
                   payer.get("email_address") or payer.get("payer_id", ""))


class PayPalREST:
    def __init__(self, mode: str, client_id: str, secret: str, timeout: float = 20):
        self.base = BASE_URLS[mode]
        self.auth = (client_id, secret)
        self.timeout = timeout

    def _token(self) -> str:
        r = _send(httpx.post, f"{self.base}/v1/oauth2/token", auth=self.auth,
                  data={"grant_type": "client_credentials"}, timeout=self.timeout)
        if r.status_code != 200:
            raise PayPalError(f"PayPal no dejó entrar: {r.status_code}")
        return r.json()["access_token"]

    def create_order(self, total: Decimal, currency: str, reference: str, return_url: str,
                     cancel_url: str) -> Created:
        r = _send(httpx.post, f"{self.base}/v2/checkout/orders", timeout=self.timeout,
                  headers={"Authorization": f"Bearer {self._token()}"},
                  json={"intent": "CAPTURE",
                        "purchase_units": [{"reference_id": reference,
                                            "amount": {"currency_code": currency, "value": str(total)}}],
                        "payment_source": {"paypal": {"experience_context": {
                            "brand_name": "Edgefolio", "user_action": "PAY_NOW",
                            "shipping_preference": "NO_SHIPPING",
                            "return_url": return_url, "cancel_url": cancel_url}}}})
        if r.status_code not in (200, 201):
            raise PayPalError(f"PayPal no creó el pedido: {r.status_code} {r.text[:200]}")
        body = r.json()
        links = {link.get("rel"): link.get("href") for link in body.get("links", [])}
        # con payment_source, PayPal contesta 'payer-action'; el flujo de antes dice 'approve'
        approve = links.get("payer-action") or links.get("approve")
        if not approve:
            raise PayPalError("PayPal no dio el enlace para aprobar el pedido")
        return Created(body["id"], approve)

    def capture(self, order_id: str) -> Capture:
        # el mismo PayPal-Request-Id en cada intento: si el primero cobró, los siguientes reciben su respuesta
        r = _send(httpx.post, f"{self.base}/v2/checkout/orders/{order_id}/capture", timeout=self.timeout,
                  headers={"Authorization": f"Bearer {self._token()}", "Content-Type": "application/json",
                           "PayPal-Request-Id": f"edgefolio-capture-{order_id}"})
        if r.status_code not in (200, 201):
            raise PayPalError(f"PayPal no cobró: {r.status_code} {r.text[:200]}")
        cap = _capture_of(r.json())
        if cap is None:
            raise PayPalError("PayPal no dijo qué cobró")
        return cap

    def settled(self, order_id: str):
        """Lo que PayPal cobró de este pedido (su Capture: COMPLETED, PENDING…), o None si no cobró nada."""
        r = _send(httpx.get, f"{self.base}/v2/checkout/orders/{order_id}", timeout=self.timeout,
                  headers={"Authorization": f"Bearer {self._token()}"})
        if r.status_code != 200:
            raise PayPalError(f"PayPal no dio el pedido: {r.status_code} {r.text[:200]}")
        return _capture_of(r.json())


class FakePayPal:
    """Aprueba cada pedido por el importe exacto con que se creó (PAYPAL_MODE=fake)."""

    def __init__(self):
        self.orders = {}
        self.captured = {}   # lo cobrado, para settled()

    def create_order(self, total: Decimal, currency: str, reference: str, return_url: str,
                     cancel_url: str) -> Created:
        order_id = "FAKE-" + secrets.token_hex(6).upper()
        self.orders[order_id] = (total, currency)
        # de vuelta a la tienda, como hace PayPal cuando quien compra aprueba
        return Created(order_id, f"{return_url}?token={order_id}&PayerID=FAKE")

    def capture(self, order_id: str) -> Capture:
        if order_id not in self.orders:
            raise PayPalError("pedido desconocido")
        total, currency = self.orders[order_id]
        self.captured[order_id] = Capture("COMPLETED", total, currency, "buyer@example.com")
        return self.captured[order_id]

    def settled(self, order_id: str):
        return self.captured.get(order_id)
