# -*- coding: utf-8 -*-
"""Las tareas de la tienda en el reloj del núcleo (``"schedule"`` de tool.json, núcleo 0.25; antes, cron): los cambios
del BCE (``fx_update``) y los avisos de las favoritas (``send_alerts``), una vez al día entre todos los procesos.

Una vez puede repetirse: ``testing.run_task`` dos veces con la misma hora es la misma vez (``run.key``), y la segunda
no hace nada (no pide otra vez los cambios, no manda otra vez un correo): lo hecho está apuntado en
edgefolio_task_done. ``testing.tick`` da una vuelta del reloj a una hora: a la suya corre cada una, un minuto antes,
nada. Los cambios se piden sin una transacción abierta (``db.end_idle_transaction``); los enlaces de los avisos, con la
dirección pública, y sin ella en producción la vez falla y no manda nada; a una cuenta borrada, nada."""
import json
from datetime import datetime, timedelta

import httpx

from zlecitool_core import load_ficha, testing
from zlecitool_core.db import db, utcnow

from edgefolio import fx, tasks
from edgefolio.models import AlertState, EmailProof, Favourite, TaskDone
from edgefolio.settings import ROOT
from tests.conftest import BUNDLES, ROWS, strategy_id
from tests.test_alerts import account, follow, mails, republish

TSLA = strategy_id(ROWS[3])
# 2026-11-03 es martes; en Madrid, CET (UTC+1): las 09:00 son las 08:00 UTC y las 17:00, las 16:00
MONDAY_9, TUESDAY_9 = datetime(2026, 11, 2, 8, 0), datetime(2026, 11, 3, 8, 0)
TUESDAY_17 = datetime(2026, 11, 3, 16, 0)


class Answer:
    """Lo que contesta frankfurter.app."""

    def raise_for_status(self):
        pass

    def json(self):
        return {"amount": 1.0, "base": "USD", "date": "2026-11-03", "rates": {"EUR": 0.85, "INR": 88.7}}


def done(app) -> dict:
    with app.app_context():
        out = {r.run_key: (r.task, r.scheduled_for, r.result) for r in TaskDone.query.all()}
        db.session.remove()
        return out


def cheaper_tesla(app, settings, paypal, price="40"):
    rows = [dict(r) for r in ROWS]
    rows[3]["Price"] = price
    republish(app, settings, paypal, rows, BUNDLES)


def test_the_schedule_is_in_the_ficha():
    """Los cambios del BCE, los días laborables a las 17:00 de Madrid (los publica hacia las 16:00 de Fráncfort); los
    avisos, cada día a las 09:00."""
    schedule = {t.name: (t.at, t.tz, t.days) for t in load_ficha(ROOT).schedule}
    assert schedule == {"fx_update": ("17:00", "Europe/Madrid", ("mon", "tue", "wed", "thu", "fri")),
                        "send_alerts": ("09:00", "Europe/Madrid", ())}


def test_fx_update_runs_once_per_time_without_holding_a_connection(app, settings, monkeypatch):
    calls = []
    monkeypatch.setattr(tasks, "end_idle_transaction", lambda: calls.append("idle") or True)
    monkeypatch.setattr(fx.httpx, "get", lambda *a, **k: calls.append("ecb") or Answer())
    first = testing.run_task(app, "fx_update", at=TUESDAY_17)
    assert (first.status, first.key) == ("ok", "edgefolio:fx_update:2026-11-03")
    assert calls == ["idle", "ecb"], "la transacción, cerrada antes de esperar al BCE"
    data = json.loads(settings.fx_today.read_text())
    assert data["date"] == "2026-11-03" and data["rates"] == {"USD": 1, "EUR": 0.85, "INR": 88.7, "SAR": 3.75}
    again = testing.run_task(app, "fx_update", at=TUESDAY_17)
    assert (again.key, again.attempt, again.status) == (first.key, 2, "ok") and calls == ["idle", "ecb"], \
        "la misma vez, otra vez: no se piden"
    assert done(app) == {first.key: ("fx_update", TUESDAY_17, {"date": "2026-11-03", "rates": 4})}


def test_a_failed_fx_update_keeps_the_rates_and_is_done_when_run_again(app, settings, monkeypatch):
    def down(*a, **k):
        raise httpx.ConnectError("sin red")

    monkeypatch.setattr(fx.httpx, "get", down)
    failed = testing.run_task(app, "fx_update", at=TUESDAY_17, raise_errors=False)
    assert failed.status == "failed" and "sin cambios nuevos" in failed.error and "sin red" in failed.error
    assert not settings.fx_today.exists() and done(app) == {}
    monkeypatch.setattr(fx.httpx, "get", lambda *a, **k: Answer())
    assert testing.run_task(app, "fx_update", at=TUESDAY_17).status == "ok" and settings.fx_today.exists()


def test_the_clock_runs_each_task_at_its_time(app, monkeypatch):
    monkeypatch.setattr(fx.httpx, "get", lambda *a, **k: Answer())
    assert testing.tick(app, TUESDAY_9 - timedelta(minutes=1)) == []
    assert [r.name for r in testing.tick(app, TUESDAY_9)] == ["send_alerts"]
    assert testing.tick(app, TUESDAY_17 - timedelta(minutes=1)) == []
    assert [(r.name, r.status) for r in testing.tick(app, TUESDAY_17)] == [("fx_update", "ok")]
    friday, saturday = datetime(2026, 11, 6, 16, 0), datetime(2026, 11, 7, 16, 0)
    assert "fx_update" in [r.name for r in testing.tick(app, friday)]
    assert "fx_update" not in [r.name for r in testing.tick(app, saturday)], "el sábado el BCE no publica"


def test_the_alerts_task_mails_once_per_time_with_the_public_address(app, settings, paypal, monkeypatch):
    monkeypatch.setenv("ZLECITOOL_PUBLIC_URL", "https://shop.example")
    ana = account(app)
    follow(ana, TSLA, pd=True)
    first = testing.run_task(app, "send_alerts", at=MONDAY_9)          # la primera vez sólo toma la foto
    cheaper_tesla(app, settings, paypal)
    run = testing.run_task(app, "send_alerts", at=TUESDAY_9)
    assert run.status == "ok" and run.key == "edgefolio:send_alerts:2026-11-03"
    (mail,) = mails()
    assert f"https://shop.example/s/{TSLA}" in mail["body"] and "https://shop.example/mine" in mail["body"]
    again = testing.run_task(app, "send_alerts", at=TUESDAY_9)
    assert again.attempt == 2 and len(mails()) == 1, "la misma vez, otra vez: ningún correo más"
    assert done(app) == {
        first.key: ("send_alerts", MONDAY_9, {"first_run": True, "emails": 0, "unconfirmed": 0, "changes": 0}),
        run.key: ("send_alerts", TUESDAY_9, {"first_run": False, "emails": 1, "unconfirmed": 0, "changes": 1})}
    with app.app_context():
        assert {r.updated_at for r in AlertState.query.all()} == {TUESDAY_9}, "la foto, de cuándo tocaba"


def test_without_the_public_address_the_alerts_task_fails_and_mails_nothing(app, settings, paypal, monkeypatch):
    """En producción, sin ZLECITOOL_PUBLIC_URL, los enlaces no irían a ninguna parte: la vez falla («Sistema» y el
    aviso de errores del núcleo), sin mandar nada ni guardar la foto; con ella puesta, sale el cambio."""
    ana = account(app)
    follow(ana, TSLA, pd=True)
    testing.run_task(app, "send_alerts", at=MONDAY_9)
    cheaper_tesla(app, settings, paypal)
    monkeypatch.delenv("ZLECITOOL_INSECURE_COOKIES")
    failed = testing.run_task(app, "send_alerts", at=TUESDAY_9, raise_errors=False)
    assert failed.status == "failed" and "ZLECITOOL_PUBLIC_URL" in failed.error and mails() == []
    assert "edgefolio:send_alerts:2026-11-03" not in done(app)
    monkeypatch.setenv("ZLECITOOL_PUBLIC_URL", "https://shop.example")
    assert testing.run_task(app, "send_alerts", at=TUESDAY_9).status == "ok" and len(mails()) == 1


def test_the_alerts_task_never_writes_to_a_closed_account(app, settings, paypal):
    """Como el comando (tests/test_privacy.py): entre «Borrar mi cuenta» y la parte de la tienda pasan minutos, y sus
    favoritas y la prueba de su correo siguen ahí; la tarea no le escribe (``privacy.closed``)."""
    ana = account(app)
    follow(ana, TSLA, pd=True)
    testing.run_task(app, "send_alerts", at=MONDAY_9)
    assert not testing.close_account(app, ana.user_id)
    with app.app_context():                      # lo que había antes de que se sirviera su parte
        now = utcnow()
        key = app.extensions["edgefolio"].catalogue.resolve(TSLA).key
        db.session.add(Favourite(user_id=ana.user_id, item_key=key, alerts={"nv": False, "pd": True, "bd": False},
                                 email="ana@example.com", lang="es", created_at=now))
        db.session.add(EmailProof(user_id=ana.user_id, email="ana@example.com", token_hash="", requested_at=now,
                                  expires_at=now + timedelta(hours=24), verified_at=now))
        db.session.commit()
    cheaper_tesla(app, settings, paypal)
    run = testing.run_task(app, "send_alerts", at=TUESDAY_9)
    assert run.status == "ok" and mails("ana@example.com") == []
    assert done(app)[run.key][2] == {"first_run": False, "emails": 0, "unconfirmed": 0, "changes": 1}
