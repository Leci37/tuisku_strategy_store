# -*- coding: utf-8 -*-
"""Las tareas de la tienda en el reloj del núcleo (``"schedule"`` de tool.json, núcleo 0.25), una vez al día entre
todos los procesos y servidores: los cambios de moneda del BCE (``fx_update``) y los avisos de las favoritas
(``send_alerts``). Antes iban con cron, en un solo servidor; los comandos (``flask --app app edgefolio fx-update``
y ``send-alerts``) siguen, para correrlos a mano.

Corren en otro hilo, sin la petición de nadie ni ``current_user``: la tienda es la de la app (``shop.of``) y los
enlaces de los correos, con la dirección pública (``external_url(…, trusted_host_ok=False)``). Y una vez puede
repetirse (un proceso que muere al acabar, ``flask --app app zt task run``): lo hecho se apunta con ``run.key`` en
edgefolio_task_done, en la misma transacción que lo que cambia, y una repetición que lo encuentra no hace nada.
Lo que se fecha, con ``run.scheduled_for`` (cuándo tocaba), nunca con «ahora».
"""
from __future__ import annotations

from flask import current_app

from zlecitool_core.db import db, end_idle_transaction
from zlecitool_core.http import external_url
from zlecitool_core.mail import send as send_mail

from . import alerts, fx
from .models import TaskDone
from .shop import of


def done(run) -> bool:
    """Si esta vez (``run.key``) ya se hizo: una repetición no hace nada."""
    return db.session.get(TaskDone, run.key) is not None


def note(run, result: dict) -> None:
    """Apunta la vez, sin guardar: se guarda con lo que la tarea cambia, en la misma transacción. Si otra vuelta de
    la misma vez la apuntó antes, el ``commit`` falla (su clave es única) y no se guarda nada dos veces."""
    db.session.add(TaskDone(run_key=run.key, task=run.name, scheduled_for=run.scheduled_for, result=result))


def public_link(endpoint: str, **values) -> str:
    """La dirección de un enlace de un correo: con ZLECITOOL_PUBLIC_URL (en desarrollo, sin ella, la de localhost).
    Sin ella en producción no hay una que dar: la vez falla y lo dice («Sistema» y el aviso de errores del núcleo), y
    lo que tenía que salir sale al día siguiente, con ella puesta."""
    url = external_url(endpoint, trusted_host_ok=False, **values)
    if url is None:
        raise RuntimeError("falta ZLECITOOL_PUBLIC_URL: los avisos llevan enlaces a la tienda")
    return url


def fx_update(run) -> None:
    """Los cambios del día del BCE en <datos>/edgefolio/fx.json (los del «≈»)."""
    if done(run):
        return
    out = of(current_app).settings.fx_today
    # frankfurter.app tarda lo que tarde: sin una transacción abierta (una conexión parada detrás de PgBouncer)
    end_idle_transaction()
    try:
        data = fx.fetch()
    except fx.FAILURES as e:
        # la vez queda «falló» y avisa; fx.json sigue con los de antes, y la próxima vez lo intenta otra vez
        raise RuntimeError(f"sin cambios nuevos ({out.name} sigue como estaba): {e}") from e
    fx.write(data, out)
    note(run, {"date": data["date"], "rates": len(data["rates"])})
    db.session.commit()


def send_alerts(run) -> None:
    """Los avisos de las favoritas (``alerts.run``): la foto del catálogo y la vez, en una transacción; los correos,
    después."""
    if done(run):
        return
    alerts.run(of(current_app), public_link, send_mail, at=run.scheduled_for,
               before_commit=lambda result: note(run, result))
