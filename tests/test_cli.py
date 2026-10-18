# -*- coding: utf-8 -*-
"""Los comandos: los scripts de pago, de la historia del repo a la carpeta privada, sin tocar la copia de
trabajo; y la lista de quien confirmó las novedades."""
import subprocess

import pytest

from edgefolio.cli import SCRIPTS_COMMIT, SCRIPTS_PATH
from edgefolio.settings import ROOT


def has_history() -> bool:
    return subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{SCRIPTS_COMMIT}:{SCRIPTS_PATH}"],
                          capture_output=True).returncode == 0


@pytest.mark.skipif(not has_history(), reason="esta copia del repo no tiene la historia con los scripts")
def test_restore_scripts_copies_them_once_without_touching_the_working_tree(app, settings):
    target = settings.strategies_dir
    for f in target.iterdir():
        f.unlink()
    status = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True, text=True).stdout
    runner = app.test_cli_runner()
    result = runner.invoke(args=["edgefolio", "restore-scripts"])
    assert result.exit_code == 0, result.output
    assert "4578 scripts" in result.output and len(list(target.glob("*.pine"))) == 4578
    assert subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True,
                          text=True).stdout == status, "ni la copia de trabajo ni el índice cambian"
    assert not (ROOT / "d_result").exists()
    again = runner.invoke(args=["edgefolio", "restore-scripts"])
    assert again.exit_code == 0 and "ya tiene scripts" in again.output
    first = sorted(target.glob("*.pine"))[0]
    first.write_text("cambiado")
    assert runner.invoke(args=["edgefolio", "restore-scripts", "--force"]).exit_code == 0
    assert first.read_text() != "cambiado"


def test_restore_scripts_says_why_it_failed(app):
    result = app.test_cli_runner().invoke(args=["edgefolio", "restore-scripts", "--force", "--commit", "0" * 40])
    assert result.exit_code != 0 and "git archive" in result.output


def test_subscribers_lists_only_confirmed_ones(app, client):
    from edgefolio import free
    with app.app_context():
        token = free.request_news("keen@example.com", "free", "es")
        free.request_news("pending@example.com", "free", "es")
        assert free.confirm_news(token) == "keen@example.com"
    out = app.test_cli_runner().invoke(args=["edgefolio", "subscribers"]).output
    assert out.splitlines()[0] == "email,lang,source,consent_at,confirmed_at"
    assert "keen@example.com,es,free," in out and "pending@example.com" not in out
