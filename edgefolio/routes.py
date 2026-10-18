# -*- coding: utf-8 -*-
"""Las páginas y la API de la tienda. Finas: el trabajo lo hacen los módulos de al lado, sin Flask.

Todo pide sesión sin hacer nada (el núcleo protege cada ruta); lo que usa quien entra sin cuenta (mirar
el catálogo, comprar, descargar con un enlace, la descarga gratis) va marcado con @public. Mis
estrategias y las favoritas, no: el núcleo manda a un navegador a /login?next=/mine y contesta 401
{"error": "errLoginRequired"} a un script.

Las páginas (/, /mine, /thanks, /s/<id>, /s/<id>/tree) son una sola plantilla: la página lee la ruta en
el navegador. Un rechazo es {"error": "<clave>"} (con "vars", "field", "items"… si hace falta), y la
página lo enseña traducido.
"""
from __future__ import annotations

from flask import Blueprint, Response, current_app, jsonify, redirect, render_template, request, send_file

from zlecitool_core import current_tool
from zlecitool_core.accounts import current_user
from zlecitool_core.http import external_url, public_base
from zlecitool_core.i18n import request_language
from zlecitool_core.mail import send as send_mail
from zlecitool_core.security import email_problem, public

from . import cli, downloads, free, media, mine, orders, proofs, search
from .settings import Settings
from .shop import install, of
from .web import Refusal, json_object, text_field, valid_email

bp = Blueprint("edgefolio", __name__)
cli.register(bp)

BUYER_COOKIE = "edgefolio_buyer"
PRIVATE = {"Cache-Control": "private, no-store"}
FOREVER = {"Cache-Control": "public, max-age=31536000, immutable"}


@bp.record_once
def _start(state):
    """La tienda de esta instalación, con la configuración del entorno, al registrar el blueprint."""
    app = state.app
    with app.app_context():
        data_dir = current_tool().data_dir
    install(app, Settings.from_env(data_dir, public_url=public_base()))


def shop():
    return of(current_app)


@bp.errorhandler(Refusal)
def _refused(refusal: Refusal):
    return jsonify(refusal.body()), refusal.status


def body() -> dict:
    return json_object(request.get_json(silent=True))


def signed_in():
    return current_user if current_user.is_authenticated else None


def user_id():
    user = signed_in()
    return user.id if user is not None else None


def link(endpoint: str, **values) -> str:
    """La dirección de un enlace que sale de la tienda (un correo, la vuelta de PayPal): con
    ZLECITOOL_PUBLIC_URL, nunca con la cabecera Host (sólo en desarrollo, sin ella)."""
    url = external_url(endpoint, trusted_host_ok=False, **values)
    if url is None:
        raise Refusal("errLater", 503)
    return url


def limited(name: str):
    """429 cuando esta IP ha gastado el límite ``name`` (shop.limits)."""
    if not shop().limits[name].hit(request.remote_addr or "unknown"):
        raise Refusal("errTooMany", 429)


def email_of(raw) -> str:
    return valid_email(raw, problem=email_problem)


# ── las páginas: una plantilla, la página lee la ruta ───────────────────────

def _page():
    return render_template("edgefolio/shop.html")


@bp.get("/")
@public
def index():
    return _page()


@bp.get("/thanks")
@public
def thanks():
    return _page()


def _strategy_page(strategy_id: str, tail: str = ""):
    """La página de una estrategia. Un id que no existe va a la tienda (el navegador no pide nada que dé
    404); un alias (el base64 de la tienda de antes), a la dirección de su id."""
    s = shop().catalogue.resolve(strategy_id)
    if s is None:
        return redirect("/", code=302)
    if s.id != strategy_id:
        return redirect(f"/s/{s.id}{tail}", code=301)
    return _page()


@bp.get("/s/<strategy_id>")
@public
def strategy_page(strategy_id):
    return _strategy_page(strategy_id)


@bp.get("/s/<strategy_id>/tree")
@public
def tree_page(strategy_id):
    return _strategy_page(strategy_id, "/tree")


@bp.get("/mine")
def mine_page():
    return _page()


# ── el catálogo ──────────────────────────────────────────────────────────────

@bp.get("/api/config")
@public
def config():
    """Lo que la página necesita para pintar precios y enlaces: nunca un secreto ni un código."""
    s = shop().settings
    return jsonify({"mode": s.paypal_mode, "currency": s.currency, "max_discount": str(s.max_discount),
                    "tiers": [{"over": str(o), "rate": str(r)} for o, r in s.tiers],
                    "pack": {"size": s.pack_size, "price": str(s.pack_price)},
                    "download_days": s.download_days, "max_downloads": s.max_downloads,
                    "new_days": s.new_days, "contact_email": s.contact_email,
                    "strategies": len(shop().catalogue)})


@bp.get("/api/strategies")
@public
def strategies():
    return jsonify(search.strategies(shop().catalogue, shop().settings, request.args))


@bp.get("/api/strategies/<strategy_id>")
@public
def strategy(strategy_id):
    return jsonify(search.strategy(shop().catalogue, strategy_id))


@bp.get("/api/bundles")
@public
def bundles():
    return jsonify(search.bundles(shop().catalogue, shop().settings))


@bp.get("/api/fx")
@public
def fx():
    return jsonify(media.fx(shop().settings))


@bp.get("/thumbs/<stem>.webp")
@public
def thumb(stem):
    try:
        path = media.thumb(shop().settings, stem)
    except KeyError:
        return jsonify({"error": "errNotFound"}), 404
    if path is None:
        return redirect(f"/static/assets/charts/{stem}.png", code=307)
    response = send_file(path, mimetype="image/webp", conditional=True)
    response.headers.update(FOREVER)
    return response


# ── comprar ──────────────────────────────────────────────────────────────────

@bp.post("/api/quote")
@public
def quote():
    return jsonify(orders.priced(shop(), orders.cart_of(request.get_json(silent=True))).as_dict())


@bp.post("/api/orders")
@public
def create_order():
    """El pedido de PayPal. El navegador recibe (o conserva) la cookie de quien compra: sólo él ve los
    enlaces del recibo, además de la cuenta que compra con la sesión abierta."""
    cart = orders.cart_of(request.get_json(silent=True))
    buyer = orders.buyer_token(request.cookies.get(BUYER_COOKIE))
    user = signed_in()
    created = orders.create(shop(), cart, buyer, return_url=link("edgefolio.thanks"),
                            cancel_url=link("edgefolio.index", checkout="cancel"),
                            user_id=user.id if user else None, email=user.email if user else "")
    response = jsonify(created)
    response.set_cookie(BUYER_COOKIE, buyer, max_age=orders.BUYER_DAYS * 86400, path="/", httponly=True,
                        samesite="Lax", secure=bool(current_app.config.get("SESSION_COOKIE_SECURE", True)))
    return response


@bp.post("/api/orders/<paypal_id>/capture")
@public
def capture(paypal_id):
    order = orders.capture(shop(), paypal_id, on_paid=_email_receipt)
    uid = user_id()
    see = orders.may_see_links(order, request.cookies.get(BUYER_COOKIE), uid, proofs.proven(uid))
    return jsonify(orders.receipt(shop(), order, see))


def _email_receipt(order):
    """En el idioma de la página que cobra. Sin dirección pública que dar (producción sin
    ZLECITOOL_PUBLIC_URL) no sale: lo pagado ya está pagado, y la página de gracias lo enseña igual."""
    mine = external_url("edgefolio.mine_page", trusted_host_ok=False)
    if mine is None:
        current_app.logger.warning("Recibo sin mandar: falta ZLECITOOL_PUBLIC_URL | pedido=%s", order.paypal_id)
        return
    orders.email_receipt(shop(), order, request_language(), mine, send_mail)


# ── descargar ────────────────────────────────────────────────────────────────

def _attachment(data: bytes, mimetype: str, name: str) -> Response:
    return Response(data, mimetype=mimetype,
                    headers={**PRIVATE, "Content-Disposition": f'attachment; filename="{name}"'})


# Antes que /<token>: "all" nunca es un token.
def _opened_in_the_browser() -> bool:
    """Un enlace de descarga abierto en la pestaña (un clic en la página, el enlace de un correo), no pedido
    por un script: entonces un rechazo vuelve a la tienda, no a una página con el JSON."""
    if request.headers.get("Sec-Fetch-Dest") == "document":
        return True
    return request.accept_mimetypes.best_match(["application/json", "text/html"]) == "text/html"


def _download(make):
    try:
        return make()
    except Refusal as refusal:
        if not _opened_in_the_browser():
            raise
        # a Mis estrategias, que da un enlace nuevo; sin sesión, a la tienda: el aviso, traducido allí
        where = "/mine" if signed_in() else "/"
        return redirect(f"{where}?link={refusal.key}", code=303)


@bp.get("/api/download/all")
@public
def download_all():
    def make():
        data, name = downloads.all_in_one(shop(), request.args.getlist("t"))
        return _attachment(data, "application/zip", name)
    return _download(make)


@bp.get("/api/download/<token>")
@public
def download(token):
    def make():
        data, mimetype, name = downloads.one(shop(), token, request.args.get("format", "pine"))
        return _attachment(data, mimetype, name)
    return _download(make)


# ── gratis, por correo ───────────────────────────────────────────────────────

@bp.post("/api/free")
@public
def free_claim():
    b = body()
    item = text_field(b, "id", 200)
    s = shop().catalogue.resolve(item)
    if not s:
        raise Refusal("errUnknownStrategy", 400)
    if s.price != 0:
        raise Refusal("errNotFree", 400)
    email = email_of(b.get("email"))
    news = b.get("news", False)
    if not isinstance(news, bool):
        raise Refusal("errRequest", 400, field="news")
    limited("free")
    return jsonify(free.claim(shop(), s, email, news, request_language(), link, send_mail, user_id=user_id()))


@bp.get("/api/news/confirm")
@public
def confirm_news():
    """El enlace del correo de la descarga gratis: desde ahora, a esa dirección se le pueden mandar novedades."""
    token = request.args.get("token", "")
    done = free.confirm_news(token) if 0 < len(token) <= 200 else None
    return redirect("/?news=confirmed" if done else "/?news=expired", code=303)


# ── quién es ─────────────────────────────────────────────────────────────────

@bp.get("/api/me")
@public
def me():
    user = signed_in()
    return jsonify({"email": user.email if user else None})


# ── Mis estrategias (con sesión) ─────────────────────────────────────────────

def _proven():
    return proofs.proven(current_user.id)


@bp.get("/api/mine")
def my_strategies():
    emails = _proven()
    return jsonify(mine.listing(shop(), current_user.id, current_user.email, emails,
                                proof_needed=current_user.email not in emails))


@bp.post("/api/mine/renew")
def renew():
    item = text_field(body(), "id", 200)
    return jsonify(mine.renew(shop(), current_user.id, _proven(), item))


@bp.get("/api/mine/<item_id>/script")
def script(item_id):
    path = mine.script_path(shop(), current_user.id, _proven(), item_id)
    return Response(path.read_text(encoding="utf-8", errors="replace"), mimetype="text/plain",
                    headers=PRIVATE)


@bp.post("/api/mine/proofs")
def ask_proof():
    """Manda el enlace que demuestra que un correo es de esta cuenta. La misma respuesta siempre: no dice
    si con ese correo se compró algo."""
    b = body()
    email = email_of(b.get("email") or current_user.email)
    limited("proof")
    token = proofs.request(current_user.id, email)
    if token:
        texts, lang = shop().texts, request_language()
        url = external_url("edgefolio.mine_page", trusted_host_ok=False, proof=token)
        if url is None:
            proofs.forget(current_user.id, token)
            raise Refusal("errLater", 503)
        send_mail(email, texts.get("mailProofSubject", lang),
                  texts.get("mailProofBody", lang, link=url, account=current_user.email, hours=proofs.PROOF_HOURS),
                  kind="edgefolio-proof")
    return jsonify({"sent": True})


@bp.post("/api/mine/proofs/peek")
def peek_proof():
    """De qué correo es el enlace, para que la página pregunte; el enlace sigue valiendo. Uno usado,
    caducado o de otra cuenta no es de nadie ({"email": null}): una respuesta, no un error."""
    token = text_field(body(), "token", 200, default="")
    return jsonify({"email": proofs.peek(current_user.id, token)})


@bp.post("/api/mine/proofs/confirm")
def confirm_proof():
    token = text_field(body(), "token", 200, default="")
    email = proofs.confirm(current_user.id, token)
    if not email:
        raise Refusal("errProofExpired", 400)
    return jsonify({"email": email})


@bp.put("/api/favourites/<item_id>")
def put_favourite(item_id):
    raw = request.get_json(silent=True)
    alerts_on = mine.alerts_of(json_object({} if raw is None and not request.data else raw))
    return jsonify(mine.set_favourite(shop(), current_user.id, current_user.email, request_language(), item_id,
                                      alerts_on))


@bp.delete("/api/favourites/<item_id>")
def delete_favourite(item_id):
    return jsonify(mine.delete_favourite(shop(), current_user.id, item_id))
