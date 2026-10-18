# -*- coding: utf-8 -*-
"""Demostrar un correo: el enlace de un solo uso, en dos pasos (un lector de correo que lo abre no
confirma nada), sólo para la cuenta que lo pidió, guardado como hash, sin llenar buzones ajenos y en el
idioma de quien lo pide. Las cuentas y la sesión son las del núcleo: aquí no hay otro modo de entrar."""
import json
import re
from datetime import timedelta

from zlecitool_core.db import db

from edgefolio.models import EmailProof
from edgefolio.proofs import MAX_PENDING
from edgefolio.settings import ROOT
from tests.conftest import outbox, proof_token, prove, signed


def ask(client, email):
    return client.post("/api/mine/proofs", json={"email": email})


def test_the_proof_link_is_emailed_and_works_once(app):
    ana = signed(app, "ana@example.com")
    assert ana.get("/api/mine").json["proof_needed"] is True
    assert ask(ana, " Ana@Example.com ").json == {"sent": True}
    [mail] = outbox("ana@example.com")
    assert re.search(r"\nhttp://localhost/mine\?proof=[\w-]+\n", mail["body"]), "el enlace, en su renglón"
    assert "ana@example.com" in mail["body"] and "{" not in mail["body"], "cada hueco relleno"
    token = proof_token("ana@example.com")
    assert ana.post("/api/mine/proofs/confirm", json={"token": token}).json == {"email": "ana@example.com"}
    again = ana.post("/api/mine/proofs/confirm", json={"token": token})
    assert again.status_code == 400 and again.json == {"error": "errProofExpired"}
    assert ana.post("/api/mine/proofs/peek", json={"token": token}).json == {"email": None}, "usado: de nadie"
    body = ana.get("/api/mine").json
    assert body["emails"] == ["ana@example.com"] and body["proof_needed"] is False


def test_opening_the_link_confirms_nothing(app):
    """Un lector de correo que abre (o pinta) el enlace no gasta nada: sólo el clic de la persona."""
    ana = signed(app, "ana@example.com")
    ask(ana, "ana@example.com")
    token = proof_token("ana@example.com")
    assert ana.get(f"/mine?proof={token}").status_code == 200        # la página
    for _ in range(3):
        assert ana.post("/api/mine/proofs/peek", json={"token": token}).json == {"email": "ana@example.com"}
    assert ana.get("/api/mine").json["emails"] == []
    assert ana.post("/api/mine/proofs/confirm", json={"token": token}).status_code == 200
    assert ana.get("/api/mine").json["emails"] == ["ana@example.com"]


def test_a_link_is_only_for_the_account_that_asked(app):
    ana, luis = signed(app, "ana@example.com"), signed(app, "luis@example.com")
    ask(ana, "shared@example.com")
    token = proof_token("shared@example.com")
    assert luis.post("/api/mine/proofs/peek", json={"token": token}).json == {"email": None}
    assert luis.post("/api/mine/proofs/confirm", json={"token": token}).json == {"error": "errProofExpired"}
    assert luis.get("/api/mine").json["emails"] == []
    assert ana.post("/api/mine/proofs/confirm", json={"token": token}).status_code == 200, "sigue valiendo para ana"


def test_an_expired_or_made_up_link(app):
    ana = signed(app, "ana@example.com")
    ask(ana, "ana@example.com")
    token = proof_token("ana@example.com")
    with app.app_context():
        EmailProof.query.one().expires_at -= timedelta(days=2)
        db.session.commit()
    for t in (token, "made-up", ""):
        assert ana.post("/api/mine/proofs/peek", json={"token": t}).json == {"email": None}, t
        r = ana.post("/api/mine/proofs/confirm", json={"token": t})
        assert r.status_code == 400 and r.json == {"error": "errProofExpired"}, t


def test_only_hashes_are_stored(app):
    ana = signed(app, "ana@example.com")
    ask(ana, "ana@example.com")
    token = proof_token("ana@example.com")
    with app.app_context():
        dump = json.dumps([list(map(str, r)) for r in db.session.execute(db.text("SELECT * FROM edgefolio_email_proof"))])
    assert token not in dump


def test_same_answer_for_anyone_and_no_flooding(app):
    ana = signed(app, "ana@example.com")
    for _ in range(3):
        assert ask(ana, "victim@example.com").json == {"sent": True}
    assert len(outbox("victim@example.com")) == 1, "otra vez enseguida: el mismo enlace, sin otro correo"
    for i in range(MAX_PENDING + 2):
        assert ask(ana, f"p{i}@example.com").json == {"sent": True}
    assert len({m["to"] for m in outbox()}) == MAX_PENDING, "como mucho tantas direcciones pendientes"
    r = ask(ana, "one-more@example.com")
    assert r.status_code == 429 and r.json == {"error": "errTooMany"}, "y como mucho 10 por IP en 10 minutos"
    bo = signed(app, "bo@example.com")
    bo.environ_base["REMOTE_ADDR"] = "203.0.113.9"      # desde otra dirección
    prove(bo)
    assert ask(bo, "bo@example.com").json == {"sent": True}
    assert len(outbox("bo@example.com")) == 1, "ya demostrado: nada más que mandar"


def test_another_site_cannot_post(app):
    """Un formulario de otra web no lleva el token CSRF (el núcleo lo rechaza) ni puede mandar JSON."""
    ana = signed(app, "ana@example.com")
    ask(ana, "ana@example.com")
    token = proof_token("ana@example.com")
    bare = app.test_client()
    bare.set_cookie("zlecitool_session", ana.get_cookie("zlecitool_session").value)
    r = bare.post("/api/mine/proofs/confirm", json={"token": token}, headers={"Sec-Fetch-Dest": "empty"})
    assert r.status_code == 400 and r.json == {"error": "errStaleForm"}
    r = ana.post("/api/mine/proofs/confirm", data=f"token={token}",
                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert r.status_code == 400 and r.json == {"error": "errRequest", "field": "body"}
    assert ana.get("/api/mine").json["emails"] == []


def test_the_proof_email_in_the_readers_language(app):
    for lang, subject, words in (("es", "Confirma tu correo en Edgefolio", "Funciona una sola vez y durante 24 horas"),
                                 ("de", "Bestätige deine E-Mail bei Edgefolio", "Er funktioniert einmal und 24 Stunden lang"),
                                 ("ar", "أكّد بريدك الإلكتروني في Edgefolio", "ولمدة 24 ساعة"),
                                 ("pt", "Confirma o teu e-mail no Edgefolio", "durante 24 horas")):
        client = signed(app)
        client.post("/zt/lang", json={"lang": lang})     # el menú de idioma de la carcasa (y de la cuenta)
        address = f"{lang}@example.com"
        client.post("/api/mine/proofs", json={"email": address})
        [mail] = outbox(address)
        assert mail["subject"] == subject and words in mail["body"], lang


def test_every_email_text_is_in_every_language():
    data = json.loads((ROOT / "i18n" / "ui.json").read_text(encoding="utf-8"))
    keys = [k for k in data if k.startswith("mail")]
    assert {"mailProofSubject", "mailProofBody", "mailFreeSubject", "mailFreeBody", "mailNewsConfirm",
            "mailAlertSubject", "mailAlertBody"} <= set(keys)
    for key in keys:
        names = sorted(re.findall(r"\{(\w+)\}", data[key]["en"]))
        for lang in data["_languages"]:
            text = data[key][lang]
            assert text.strip() and sorted(re.findall(r"\{(\w+)\}", text)) == names, (key, lang)
            assert text != data[key]["en"] or lang == "en" or "{" == text[0], (key, lang)


def test_signing_out_is_the_cores(app):
    ana = signed(app, "ana@example.com")
    assert ana.get("/api/me").json == {"email": "ana@example.com"}
    assert ana.post("/logout").status_code in (200, 302)
    assert ana.get("/api/me").json == {"email": None}
    assert ana.get("/api/mine", headers={"Sec-Fetch-Dest": "empty"}).status_code == 401
