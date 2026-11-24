# -*- coding: utf-8 -*-
"""Los logs de la tienda (la ronda de logs, 15-11-2026; docs/tecnico/LOGS.md): un error deja su línea, un cambio de
estado deja la suya, cada tarea dice lo que hizo y un rechazo deja una sola, con la regla de la ruta. Y ninguna lleva
el correo de una persona, lo que tecleó, un código de descuento ni el token de un enlace.

Con ``app.testing`` el núcleo no pone salidas: ``caplog`` recoge lo que llega a la raíz, de la tienda y del núcleo."""
import json
import logging
import re

import httpx
import pytest

from zlecitool_core import testing

from edgefolio import fx
from edgefolio.paypal import PayPalError
from edgefolio.shop import install
from tests.conftest import ROWS, cart_id, outbox, prove, signed, strategy_id, visitor
from tests.test_alerts import follow, republish
from tests.test_free import FREE_ID, claim, emailed_link, free_file  # noqa: F401  (la fixture)
from tests.test_mine import buy
from tests.test_tasks import TUESDAY_9, TUESDAY_17, Answer

AAPL, MSFT, TSLA = strategy_id(ROWS[0]), strategy_id(ROWS[1]), strategy_id(ROWS[3])
EMAIL = "logs-edgefolio@example.test"     # la cuenta de prueba de la ronda: se busca en los logs
NAME = "Zelda Logsprueba"                 # lo que teclea la persona


@pytest.fixture(autouse=True)
def _everything(caplog):
    caplog.set_level(logging.DEBUG)
    caplog.set_level(logging.DEBUG, logger="edgefolio")   # el núcleo pone el de la herramienta en INFO al arrancar


def said(caplog, level=None) -> list:
    """Lo que escribió la tienda (sus loggers: edgefolio.*), como sale: «Qué pasó | clave=valor»."""
    return [r.getMessage() for r in caplog.records
            if r.name.startswith("edgefolio") and (level is None or r.levelname == level)]


def one(caplog, start: str, level: str = "INFO") -> str:
    found = [m for m in said(caplog, level) if m.startswith(start)]
    assert len(found) == 1, (start, said(caplog))
    return found[0]


def everything(caplog) -> str:
    """Todas las líneas, de la tienda y del núcleo, con sus trazas."""
    return "\n".join(caplog.messages + [r.exc_text or "" for r in caplog.records])


# ── un cambio de estado deja su línea ────────────────────────────────────────

def test_an_order_says_it_was_created_paid_and_downloaded_without_the_code_or_the_links(client, caplog):
    order = client.post("/api/orders", json={"items": [AAPL], "code": "spring20"}).json
    created = one(caplog, "Pedido creado")
    assert re.fullmatch(rf"Pedido creado \| pedido={order['id']} user_id=- estrategias=1 lotes=0 pack=no "
                        r"total=\d+\.\d\d moneda=USD código=sí", created), created
    first = client.post(f"/api/orders/{order['id']}/capture").json
    client.post(f"/api/orders/{order['id']}/capture")              # otra vez: ni otro cobro ni otros enlaces
    assert one(caplog, "Pedido cobrado").startswith(f"Pedido cobrado | pedido={order['id']} user_id=- estrategias=1")
    assert one(caplog, "Enlaces de descarga") == f"Enlaces de descarga | pedido={order['id']} nuevos=1"
    assert client.get(first["downloads"][0]["url"]).status_code == 200
    assert client.get(first["downloads"][0]["zip"]).status_code == 200
    assert [m for m in said(caplog) if m.startswith("Descarga |")] == [
        f"Descarga | estrategia={AAPL} tipo=pago formato=pine", f"Descarga | estrategia={AAPL} tipo=pago formato=zip"]
    token = first["downloads"][0]["url"].rsplit("/", 1)[1]
    text = everything(caplog)
    assert "spring20" not in text and token not in text, "ni el código ni el enlace"


def test_an_account_s_changes_each_leave_a_line_with_its_id_and_never_its_email(app, caplog):
    ana = signed(app, EMAIL)
    prove(ana)
    assert one(caplog, "Prueba de correo pedida").startswith(f"Prueba de correo pedida | user_id={ana.user_id} prueba=")
    assert one(caplog, "Correo demostrado").startswith(f"Correo demostrado | user_id={ana.user_id} prueba=")
    ana.post("/api/mine/proofs", json={"email": EMAIL})            # ya demostrado: no sale nada, y el log dice por qué
    assert one(caplog, "Prueba de correo sin mandar").startswith(
        f"Prueba de correo sin mandar | user_id={ana.user_id} motivo=demostrado")
    follow(ana, AAPL, nv=True, pd=True)
    follow(ana, AAPL, nv=True)
    assert [m for m in said(caplog) if m.startswith("Favorita guardada")] == [
        f"Favorita guardada | user_id={ana.user_id} estrategia={AAPL} nueva=sí avisos=nv,pd",
        f"Favorita guardada | user_id={ana.user_id} estrategia={AAPL} nueva=no avisos=nv"]
    ana.delete(f"/api/favourites/{AAPL}")
    assert one(caplog, "Favorita quitada") == f"Favorita quitada | user_id={ana.user_id} estrategia={AAPL} borradas=1"
    assert EMAIL not in everything(caplog)


def test_a_free_download_and_the_news_leave_their_lines_without_the_address(app, client, free_file, caplog):  # noqa: F811
    assert claim(client, EMAIL, news=True).status_code == 200
    assert one(caplog, "Gratis mandada") == f"Gratis mandada | estrategia={FREE_ID} user_id=- novedades=pendientes"
    assert one(caplog, "Novedades pendientes de confirmar") == "Novedades pendientes de confirmar | origen=free"
    link = emailed_link(EMAIL)
    assert client.get(link).status_code == 200
    assert one(caplog, "Descarga |") == f"Descarga | estrategia={FREE_ID} tipo=gratis formato=pine"
    confirm = re.search(r"/api/news/confirm\?token=([\w-]+)", outbox(EMAIL)[-1]["body"]).group(1)
    client.get(f"/api/news/confirm?token={confirm}")
    client.get(f"/api/news/confirm?token={confirm}")               # otra vez: ya usado
    assert [m for m in said(caplog) if m.startswith("Novedades")][-2:] == [
        "Novedades confirmadas", "Novedades sin confirmar: enlace usado, viejo o inventado"]
    text = everything(caplog)
    assert EMAIL not in text and link.rsplit("/", 1)[1] not in text and confirm not in text


def test_deleting_an_account_says_how_many_rows_went(app, free_file, caplog):  # noqa: F811
    ana = signed(app, EMAIL)
    prove(ana)
    claim(ana, EMAIL)
    follow(ana, AAPL, nv=True)
    assert not testing.close_account(app, ana.user_id)
    line = one(caplog, "Tus datos: lo de la tienda, borrado")
    assert line.startswith(f"Tus datos: lo de la tienda, borrado | user_id={ana.user_id} pedidos_sin_dueño=0 gratis=1 "
                           "favoritas=1 "), line
    assert EMAIL not in everything(caplog)


# ── un rechazo, una línea: la regla de la ruta, nunca su token ───────────────

def test_a_refusal_leaves_one_line_with_the_route_rule_and_not_its_token(client, caplog):
    secret = "UnTokenQueNoEsDeNadie1234567890ab"
    assert client.get(f"/api/download/{secret}", headers={"Accept": "application/json"}).status_code == 404
    assert one(caplog, "Rechazo") == ("Rechazo | método=GET ruta=/api/download/<token> clave=errLinkNotFound estado=404 "
                                      "user_id=-")
    assert client.get("/api/strategies?size=abc").status_code == 400
    assert said(caplog)[-1] == "Rechazo | método=GET ruta=/api/strategies clave=errRequest estado=400 user_id=- campo=size"
    assert client.get(f"/api/strategies?q={NAME}").status_code == 200   # una búsqueda no es un rechazo
    text = everything(caplog)
    assert secret not in text and NAME not in text


def test_a_refusal_opened_in_the_tab_is_logged_before_going_back_to_the_shop(client, caplog):
    r = client.get("/api/download/no-es-de-nadie", headers={"Sec-Fetch-Dest": "document"})
    assert r.status_code == 303
    assert one(caplog, "Rechazo").startswith("Rechazo | método=GET ruta=/api/download/<token> clave=errLinkNotFound")


# ── un error deja su línea ───────────────────────────────────────────────────

def test_paypal_failing_to_create_the_order_is_a_warning(client, paypal, monkeypatch, caplog):
    def down(*a, **k):
        raise PayPalError("PayPal no contestó: ConnectError")

    monkeypatch.setattr(paypal, "create_order", down)
    assert client.post("/api/orders", json={"items": [AAPL]}).status_code == 502
    assert one(caplog, "PayPal no creó el pedido", "WARNING").startswith(
        "PayPal no creó el pedido | estrategias=1 total=")
    assert one(caplog, "Rechazo", "WARNING").startswith("Rechazo | método=POST ruta=/api/orders clave=errPayPal estado=502")
    assert not [m for m in said(caplog) if m.startswith("Pedido creado")]


def test_a_payment_that_does_not_match_is_a_warning(client, paypal, monkeypatch, caplog):
    order = client.post("/api/orders", json={"items": [AAPL]}).json["id"]
    real = paypal.capture

    def less(order_id):
        cap = real(order_id)
        return type(cap)(cap.status, cap.amount - 1, cap.currency, cap.payer)

    monkeypatch.setattr(paypal, "capture", less)
    assert client.post(f"/api/orders/{order}/capture").status_code == 402
    assert one(caplog, "Cobro que no cuadra", "WARNING") == (
        f"Cobro que no cuadra: el pedido queda FAILED | pedido={order} estado=COMPLETED importe=distinto")


def test_unreadable_levels_are_an_error(app, settings, paypal, caplog):
    settings.levels.write_text("{ esto no es json")
    install(app, settings, paypal)
    assert one(caplog, "Niveles sin leer", "ERROR").startswith("Niveles sin leer: el árbol enseña la puntuación | "
                                                                "fichero=levels.json | ")


def test_the_catalogue_says_what_it_loaded_and_what_it_misses(app, settings, paypal, caplog):
    rows = [dict(r) for r in ROWS]
    rows[0]["path_stra"] = "assets/charts/NO_ESTA.png"
    republish(app, settings, paypal, rows, [])
    line = one(caplog, "Catálogo cargado", "WARNING")
    assert line == "Catálogo cargado | estrategias=4 lotes=0 niveles=0 vistas_previas_ausentes=0 gráficos_ausentes=1"
    assert one(caplog, "Tienda en marcha") == "Tienda en marcha | paypal=fake estrategias=4 lotes=0"


# ── cada tarea dice lo que hizo ──────────────────────────────────────────────

def test_fx_update_says_which_day_and_how_many_and_a_repeat_says_it_did_nothing(app, monkeypatch, caplog):
    monkeypatch.setattr(fx.httpx, "get", lambda *a, **k: Answer())
    testing.run_task(app, "fx_update", at=TUESDAY_17)
    assert one(caplog, "Cambios del BCE guardados") == "Cambios del BCE guardados | día=2026-11-03 cambios=4"
    testing.run_task(app, "fx_update", at=TUESDAY_17)
    assert one(caplog, "Tarea ya hecha") == "Tarea ya hecha: nada que hacer | tarea=fx_update vez=edgefolio:fx_update:2026-11-03"


def test_the_ecb_failing_is_a_warning_and_the_task_fails(app, monkeypatch, caplog):
    def down(*a, **k):
        raise httpx.ConnectError("sin red")

    monkeypatch.setattr(fx.httpx, "get", down)
    assert testing.run_task(app, "fx_update", at=TUESDAY_17, raise_errors=False).status == "failed"
    assert one(caplog, "BCE sin cambios nuevos", "WARNING") == (
        "BCE sin cambios nuevos: fx-today.json sigue como estaba | error=ConnectError: sin red")


def test_send_alerts_says_what_it_sent(app, settings, paypal, monkeypatch, caplog):
    monkeypatch.setenv("ZLECITOOL_PUBLIC_URL", "https://shop.example")
    ana = signed(app, EMAIL)
    prove(ana)
    follow(ana, TSLA, pd=True)
    testing.run_task(app, "send_alerts", at=TUESDAY_9)
    assert one(caplog, "Avisos de las favoritas: primera vuelta") == (
        "Avisos de las favoritas: primera vuelta, sólo la foto | estrategias=4")
    rows = [dict(r) for r in ROWS]
    rows[3]["Price"] = "40"
    republish(app, settings, paypal, rows, [])
    testing.run_task(app, "send_alerts", at=TUESDAY_9.replace(day=4))
    assert one(caplog, "Avisos de las favoritas |") == (
        "Avisos de las favoritas | cambios=1 correos=1 sin_confirmar=0 cerradas=0")
    assert EMAIL not in everything(caplog)


def test_purge_says_what_it_deleted(app, caplog):
    testing.run_task(app, "purge", at=TUESDAY_9)
    assert one(caplog, "Limpieza de lo que ya no se guarda") == (
        "Limpieza de lo que ya no se guarda | altas_sin_confirmar=0 gratis=0 buzones=0")


# ── los comandos ─────────────────────────────────────────────────────────────

def test_the_subscribers_command_leaves_how_many_and_not_who(app, client, free_file, caplog):  # noqa: F811
    claim(client, EMAIL, news=True)
    confirm = re.search(r"/api/news/confirm\?token=([\w-]+)", outbox(EMAIL)[-1]["body"]).group(1)
    client.get(f"/api/news/confirm?token={confirm}")
    out = app.test_cli_runner().invoke(args=["edgefolio", "subscribers"])
    assert EMAIL in out.output, "la salida del comando, sí: es la lista"
    assert one(caplog, "Lista de las novedades sacada") == "Lista de las novedades sacada | direcciones=1"
    assert EMAIL not in everything(caplog)


def test_every_line_of_the_shop_follows_the_format(app, client, free_file, caplog):  # noqa: F811
    """«Qué pasó | clave=valor clave=valor», y después de un segundo «|», si acaso, el error tal cual."""
    claim(client, EMAIL, news=True)
    order = client.post("/api/orders", json={"items": [AAPL, MSFT], "code": "nope"}).json
    client.post(f"/api/orders/{order['id']}/capture")
    client.get("/api/download/nada", headers={"Accept": "application/json"})
    pair = r"[\wáéíóúñü]+=[^\s|]+"
    for line in said(caplog):
        assert re.fullmatch(rf"[^|]+(\| {pair}( {pair})*( \| .+)?)?", line), line
    assert json.dumps(said(caplog), ensure_ascii=False).count(EMAIL) == 0


# ── la segunda vuelta (+25 %, 16-11-2026) ────────────────────────────────────

def test_capturing_again_and_from_another_browser_says_so(app, client, caplog):
    order = client.post("/api/orders", json={"items": [AAPL]}).json["id"]
    client.post(f"/api/orders/{order}/capture")
    other = visitor(app)                                            # con el id del pedido, sin su cookie
    r = other.post(f"/api/orders/{order}/capture").json
    assert r["links_hidden"] is True
    assert one(caplog, "Cobro repetido") == f"Cobro repetido: el pedido ya estaba pagado | pedido={order}"
    assert one(caplog, "Recibo sin enlaces") == (
        f"Recibo sin enlaces: ni el navegador que compró ni su cuenta | pedido={order} user_id=-")


def test_a_strategy_leaving_the_catalogue_while_paying_is_not_charged_and_says_so(app, client, settings, paypal,
                                                                                    caplog):
    order = client.post("/api/orders", json={"items": [AAPL, TSLA]}).json["id"]
    republish(app, settings, paypal, [r for r in ROWS if r is not ROWS[0]], [])
    assert client.post(f"/api/orders/{order}/capture").status_code == 409
    assert one(caplog, "Pedido sin cobrar", "WARNING") == (
        f"Pedido sin cobrar: estrategias que salieron del catálogo mientras se pagaba | pedido={order} faltan=1 de=2")


def test_a_paid_script_missing_on_the_server_is_a_warning(app, client, settings, caplog):
    first = buy(client, [AAPL])["downloads"][0]
    for script in settings.strategies_dir.glob("*.pine"):
        script.unlink()
    assert client.get(first["url"], headers={"Accept": "application/json"}).status_code == 404
    assert one(caplog, "Script de pago que no está", "WARNING") == (
        f"Script de pago que no está en STRATEGIES_DIR | estrategia={AAPL}")


def test_a_head_only_looks_and_too_many_links_are_cut(client, caplog):
    first = buy(client, [AAPL])["downloads"][0]
    assert client.head(first["url"]).status_code == 200
    assert one(caplog, "Enlace mirado sin gastar") == (
        "Enlace mirado sin gastar (HEAD: un escáner de correo, una vista previa) | enlaces=1")
    many = "&".join(f"t=nada{i}" for i in range(101))
    assert client.get(f"/api/download/all?{many}", headers={"Accept": "application/json"}).status_code == 404
    assert one(caplog, "Más enlaces de los que se miran", "WARNING") == (
        "Más enlaces de los que se miran: los 100 primeros | enlaces=101")


def test_the_free_daily_limit_says_which_one(client, free_file, caplog):  # noqa: F811
    for _ in range(10):
        assert claim(client, EMAIL).status_code == 200
    assert claim(client, EMAIL).status_code == 429
    assert one(caplog, "Gratis: tope del día") == "Gratis: tope del día | por=quien_pide tope=10"


def test_an_old_or_unknown_strategy_address_leaves_its_line_without_what_was_typed(client, caplog):
    assert client.get(f"/s/{cart_id(ROWS[0])}").status_code == 301
    assert one(caplog, "Ficha por su dirección de antes") == (
        f"Ficha por su dirección de antes (el base64 de la tienda vieja): a la nueva | estrategia={AAPL}")
    assert client.get(f"/s/{NAME.replace(' ', '_')}/tree").status_code == 302
    assert one(caplog, "Ficha que no existe") == "Ficha que no existe: a la tienda | pestaña=tree"
    assert NAME.replace(" ", "_") not in everything(caplog)


def test_reaching_the_limit_of_wrong_codes_is_a_warning_once(client, caplog):
    for i in range(20):
        assert client.post("/api/quote", json={"items": [AAPL], "code": f"nope{i}"}).json["code_status"] == "invalid"
    assert one(caplog, "Códigos de descuento", "WARNING") == (
        "Códigos de descuento: una red llega al tope de los que no valen (¿probándolos?) | tope=20 ventana_s=3600")
    assert client.post("/api/quote", json={"items": [AAPL], "code": "nope20"}).status_code == 429
    assert len([m for m in said(caplog, "WARNING") if m.startswith("Códigos de descuento")]) == 1
    assert "nope1" not in everything(caplog)


def test_a_proof_link_of_nobody_and_the_owner_s_script_leave_their_lines(app, caplog):
    ana = signed(app, EMAIL)
    ana.post("/api/mine/proofs/peek", json={"token": "no-es-de-nadie"})
    assert one(caplog, "Prueba de correo: el enlace no vale") == (
        f"Prueba de correo: el enlace no vale para esta cuenta | user_id={ana.user_id}")
    ana.get("/api/mine")                                             # sin demostrar su correo
    assert one(caplog, "Mis estrategias sin lo hecho sin cuenta", "DEBUG").endswith(f"user_id={ana.user_id}")
    buy(ana, [AAPL])
    assert ana.get(f"/api/mine/{AAPL}/script").status_code == 200
    assert one(caplog, "Script completo") == f"Script completo, a su dueño | user_id={ana.user_id} estrategia={AAPL}"


def test_exporting_an_account_says_how_many_parts(app, free_file, caplog):  # noqa: F811
    ana = signed(app, EMAIL)
    prove(ana)
    claim(ana, EMAIL)
    testing.export_account(app, ana.user_id)
    assert one(caplog, "Tus datos: lo de la tienda, exportado") == (
        f"Tus datos: lo de la tienda, exportado | user_id={ana.user_id} partes=7 fuera=0")
    assert EMAIL not in everything(caplog)


def test_the_page_logs_its_views_and_its_failures_with_fixed_names(real_app, chromium):
    """Cliente (static/js/lib/log.js): sin zt.log (la 0.36), a la consola, «[edgefolio] nivel Qué | k=v»; los cambios
    de pantalla, de pestaña y de diálogo, sólo cuando cambian y con su nombre fijo; un servicio que falla, warn."""
    from zlecitool_core.testing import mobile

    from tests.test_strategy_page import TOUR_SEEN, UI, pick
    _, paid, _ = pick(real_app)
    with mobile.serve(real_app) as live:
        tab = mobile.open_page(chromium, live, "laptop")
        page = tab.page
        try:
            lines = []
            page.on("console", lambda m: lines.append(m.text) if m.text.startswith("[edgefolio]") else None)
            page.add_init_script(TOUR_SEEN + "try { localStorage.setItem('tuisku-sf-mode', 'lite'); } catch (e) {}")
            page.route("**/api/fx", lambda route: route.fulfill(status=500, content_type="application/json",
                                                               body='{"error": "errLater"}'))
            tab.goto(f"/s/{paid['id']}")
            page.get_by_role("tab", name=UI["howItDecides"]["es"]).click()
            page.wait_for_function("() => location.pathname.endsWith('/tree')")
            page.get_by_role("radio", name="Pro").click()
            page.wait_for_function("() => location.pathname === '/'")
            page.wait_for_timeout(300)
            assert "[edgefolio] warn Cambios de moneda sin cargar: los precios, en dólares | estado=500" in lines
            views = [x for x in lines if " Vista " in x]
            assert views == ["[edgefolio] info Vista | tipo=tab nombre=detail.tree",
                             "[edgefolio] info Vista | tipo=screen nombre=shop",
                             "[edgefolio] info Vista | tipo=tab nombre=pro"], lines
            assert not [x for x in lines if paid["id"] in x and " Vista " in x], "una vista no lleva la estrategia"
        finally:
            tab.close()

