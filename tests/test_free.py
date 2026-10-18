# -*- coding: utf-8 -*-
"""Las estrategias gratis para un correo: sólo las de precio 0, el enlace va por correo, las novedades sólo
si se marcan y se confirman, un límite al día, y el correo en el idioma de quien la pide."""
import io
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from urllib.parse import urlsplit

import pytest

from zlecitool_core.db import db

from edgefolio import downloads, free
from edgefolio.catalogue import Strategy
from edgefolio.models import FreeClaim, Subscriber
from edgefolio.web import digest
from tests.conftest import ROWS, outbox, signed, visitor
from tests.test_formats import ONE_TREE

FREE = ROWS[2]
FREE_ID = "NVDA_1Day_1ULT_cccc3333"


@pytest.fixture
def free_file(settings):
    """El script entero de la gratis en la carpeta privada (la de conftest sólo tiene las de pago)."""
    s = Strategy(FREE["ticker"], FREE["interval"], FREE["key_techs"], FREE["id_model"], Decimal("0"), FREE)
    path = settings.strategies_dir / s.private_file
    path.write_text(ONE_TREE)
    return path


def claim(client, email="ana@example.com", news=False, item=FREE_ID, lang="es"):
    return client.post("/api/free", json={"id": item, "email": email, "news": news},
                       headers={"Accept-Language": lang})


def emailed_link(email="ana@example.com") -> str:
    body = outbox(email)[-1]["body"]
    found = urlsplit(next(w for w in body.split() if "/api/download/" in w and "format=zip" not in w))
    return found.path


def rows(app, model):
    with app.app_context():
        return [{c.name: getattr(r, c.name) for c in model.__table__.columns} for r in model.query.all()]


def test_claim_emails_a_link_to_the_script_and_its_zip(client, free_file):
    r = claim(client)
    assert r.status_code == 200 and r.json == {"sent": True}
    [mail] = outbox("ana@example.com")
    assert "Nvidia" in mail["subject"]
    assert "http://localhost/api/download/" in mail["body"] and "?format=zip" in mail["body"]
    link = emailed_link()
    f = client.get(link)
    assert f.status_code == 200 and f.get_data(as_text=True) == ONE_TREE and f.headers["cache-control"] == "private, no-store"
    assert 'filename="Tuisku_NVDA_1Day_1ULT_cccc3333.pine"' in f.headers["content-disposition"]
    z = zipfile.ZipFile(io.BytesIO(client.get(link + "?format=zip").data))
    assert "Tuisku_NVDA_1Day_1ULT_cccc3333.md" in z.namelist()
    assert "→ Buy (score 1.00)" in z.read("Tuisku_NVDA_1Day_1ULT_cccc3333.md").decode()


def test_news_is_recorded_only_when_ticked(app, client, free_file):
    claim(client, "quiet@example.com", news=False)
    claim(client, "Keen@Example.com", news=True)
    assert [(r["email"], r["news"], r["source"], r["lang"]) for r in rows(app, Subscriber)] == [
        ("keen@example.com", True, "free", "es")]
    claims = {r["email"]: r["news"] for r in rows(app, FreeClaim)}
    assert claims == {"quiet@example.com": False, "keen@example.com": True}
    assert all(r["consent_at"] for r in rows(app, FreeClaim))


def test_only_free_strategies(client, free_file, ids):
    r = claim(client, item=ids[0])
    assert r.status_code == 400 and r.json == {"error": "errNotFree"}, "una de pago nunca sale por un correo"
    assert claim(client, item="NOPE_1Day_X_00000000").json == {"error": "errUnknownStrategy"}
    assert claim(client, email="not-an-email").json == {"error": "errEmailInvalid", "field": "email"}
    assert claim(client, item=ids[2]).status_code == 200, "el id del carrito de antes también vale"
    assert len(outbox()) == 1


def test_ten_claims_per_email_per_day(client, free_file):
    assert [claim(client).status_code for _ in range(11)] == [200] * 10 + [429]
    assert claim(client).json == {"error": "errFreeDaily"}
    assert claim(client, "other@example.com").status_code == 200


def test_missing_file_sends_nothing(client):
    r = claim(client)
    assert r.status_code == 404 and r.json["error"] == "errFileMissing" and outbox() == []


def test_free_links_expire_and_run_out(client, free_file, settings):
    settings.max_downloads = 2
    claim(client)
    link = emailed_link()
    assert [client.get(link).status_code for _ in range(3)] == [200, 200, 429]
    settings.download_days = -1
    claim(client, "late@example.com")
    assert client.get(emailed_link("late@example.com")).status_code == 410


def confirm_link(email):
    """El enlace que confirma las novedades del último correo a ``email``, como ruta, o None."""
    body = outbox(email)[-1]["body"]
    found = next((w for w in body.split() if "/api/news/confirm?token=" in w), None)
    return found and f"{urlsplit(found).path}?{urlsplit(found).query}"


def opened(client, path) -> str:
    r = client.get(path)
    assert r.status_code == 303
    return r.headers["location"]


def test_news_counts_only_once_confirmed_from_the_email(app, client, free_file):
    claim(client, "keen@example.com", news=True)
    [row] = rows(app, Subscriber)
    assert row["news"] and row["confirmed_at"] is None and row["consent_at"]
    with app.app_context():
        assert free.subscribers() == [], "teclear la dirección de otro no apunta a nadie"
    body = outbox("keen@example.com")[-1]["body"]
    assert "http://localhost/api/news/confirm?token=" in body and "Confírmalo con este enlace" in body
    link = confirm_link("keen@example.com")
    assert row["token_hash"] == digest(link.split("token=")[1]), "sólo se guarda el hash"
    assert opened(client, link) == "/?news=confirmed"
    with app.app_context():
        [sub] = free.subscribers()
    assert sub["email"] == "keen@example.com" and sub["lang"] == "es" and sub["confirmed_at"] >= sub["consent_at"]
    assert opened(client, link) == "/?news=expired", "usado"
    for bad in ("made-up", ""):
        assert opened(client, f"/api/news/confirm?token={bad}") == "/?news=expired"
    claim(client, "keen@example.com", news=True)
    assert confirm_link("keen@example.com") is None, "ya confirmado: nada más que pedir"
    with app.app_context():
        assert [s["email"] for s in free.subscribers()] == ["keen@example.com"]


def test_no_news_writes_nothing(app, client, free_file):
    claim(client, "quiet@example.com", news=False)
    assert rows(app, Subscriber) == []
    assert "/api/news/" not in outbox("quiet@example.com")[-1]["body"]


def test_only_the_latest_recent_confirmation_link_works(app, client, free_file):
    claim(client, "keen@example.com", news=True)
    first = confirm_link("keen@example.com")
    claim(client, "keen@example.com", news=True)
    latest = confirm_link("keen@example.com")
    assert opened(client, first) == "/?news=expired"
    with app.app_context():
        assert free.subscribers() == []
        db.session.get(Subscriber, "keen@example.com").consent_at -= timedelta(days=31)
        db.session.commit()
    assert opened(client, latest) == "/?news=expired", "una petición de hace un mes ya no se confirma"
    claim(client, "keen@example.com", news=True)
    assert opened(client, confirm_link("keen@example.com")) == "/?news=confirmed"


def test_free_email_in_the_visitors_language(app, client, free_file):
    """El idioma es el de la página (el que eligió en la carcasa o el de su navegador): el del núcleo."""
    claim(client, "de@example.com", news=True, lang="de")
    [mail] = outbox("de@example.com")
    assert mail["subject"] == "Deine kostenlose Strategie: Nvidia (NVDA, 1Day)"
    assert "Die Links gelten 7 Tage und für bis zu 10 Downloads" in mail["body"]
    assert "unter http://localhost/mine an" in mail["body"] and "Bestätige das mit diesem Link" in mail["body"]
    claim(client, "fr@example.com", lang="fr-CA")
    [mail] = outbox("fr@example.com")
    assert mail["subject"] == "Votre stratégie gratuite : Nvidia (NVDA, 1Day)" and "/api/news/" not in mail["body"]
    english = visitor(app)
    english.post("/zt/lang", json={"lang": "en"})        # el menú de idioma de la carcasa
    claim(english, "x@example.com", lang="xx")
    [mail] = outbox("x@example.com")
    assert mail["subject"] == "Your free strategy: Nvidia (NVDA, 1Day)" and "{" not in mail["body"]
    langs = {r["email"]: r["lang"] for r in rows(app, FreeClaim)}
    assert langs == {"de@example.com": "de", "fr@example.com": "fr", "x@example.com": "en"}


def test_parallel_free_downloads_never_pass_the_limit(app, client, free_file, settings, monkeypatch):
    settings.max_downloads = 2
    claim(client)
    link = emailed_link()
    read = downloads.find_link

    def slow(token):  # cada petición lee la cuenta antes de que ninguna la sume
        row = read(token)
        time.sleep(0.2)
        return row
    monkeypatch.setattr(downloads, "find_link", slow)
    with ThreadPoolExecutor(10) as pool:
        codes = sorted(pool.map(lambda _: client.get(link).status_code, range(10)))
    assert codes == [200] * 2 + [429] * 8
    with app.app_context():
        assert read(link.rsplit("/", 1)[1]).count == 2


def test_parallel_claims_never_pass_the_daily_limit(app, client, free_file, monkeypatch):
    """El recuento y el alta van con la fila de la dirección bloqueada: si no, todas leerían la misma cuenta
    aquí, en la pausa que se mete justo después de contar."""
    count = free.claims_since

    def slow(email, since):
        n = count(email, since)
        time.sleep(0.05)
        return n
    monkeypatch.setattr(free, "claims_since", slow)
    with ThreadPoolExecutor(15) as pool:
        codes = sorted(pool.map(lambda _: claim(client).status_code, range(15)))
    assert codes == [200] * 10 + [429] * 5
    assert len([r for r in rows(app, FreeClaim) if r["email"] == "ana@example.com"]) == 10
    assert len(outbox("ana@example.com")) == 10


def test_a_claim_made_signed_in_belongs_to_the_account(app, free_file):
    ana = signed(app, "ana@example.com")
    assert claim(ana, "ana.work@example.com").status_code == 200
    assert [r["user_id"] for r in rows(app, FreeClaim)] == [ana.user_id]
    assert [i["id"] for i in ana.get("/api/mine").json["items"]] == [FREE_ID]
    other = signed(app, "ana.work@example.com")        # el correo, sin demostrar: no es suya
    assert other.get("/api/mine").json["items"] == []
