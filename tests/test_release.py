# -*- coding: utf-8 -*-
"""flask --app app edgefolio import PAQUETE: el paquete del generador y sus scripts completos, comprobados
enteros antes de escribir nada; luego el catálogo, sus ficheros, los scripts y las miniaturas.

La tienda de estas pruebas tiene su catálogo, su static/ y su carpeta privada en tmp: nada del repo se toca."""
import errno
import json
import os
import shutil
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from edgefolio import levels, release
from tests.conftest import ROWS, strategy_id
from tests.test_levels import script_of
from tests.test_publish import (CONTRACT, CRYPTO_HOURLY, PLACEHOLDER, edit_manifest, factory, package_of, private_file,
                                sha, with_since_release)


@pytest.fixture
def settings(settings, tmp_path):
    """Las de conftest, con static/ también en tmp: el comando copia ahí los gráficos (nunca a los del repo). Y con
    las intradía de acciones: estas pruebas son de cómo se importa, con las cuatro de conftest (MSFT es de 1Hour);
    las que se dejan fuera sin LIST_INTRADAY_STOCKS, aparte (test_the_import_leaves_out_intraday_stocks)."""
    return replace(settings, static=tmp_path / "static", list_intraday_stocks=True)


@pytest.fixture
def made(tmp_path, settings):
    """El d_result/ del generador con su paquete; y una miniatura de antes en la tienda."""
    d_result, rows = factory(tmp_path)
    settings.thumbs_dir.mkdir(parents=True, exist_ok=True)
    (settings.thumbs_dir / "AAPL_1Day_1ADX_aaaa1111_profit.webp").write_bytes(b"webp de antes")
    return d_result, package_of(d_result, rows)


def run(app, *args):
    return app.test_cli_runner().invoke(args=["edgefolio", "import", *map(str, args)])


def snapshot(settings) -> dict:
    """Todo lo que el comando podría escribir: catálogo, static/, scripts y miniaturas."""
    folders = (settings.catalogue.parent, settings.static, settings.strategies_dir, settings.thumbs_dir)
    return {p: p.read_bytes() for f in folders if f.exists() for p in sorted(f.rglob("*")) if p.is_file()}


def test_import_with_scripts_copies_only_the_listed_ones(app, settings, made):
    d_result, package = made
    scripts = d_result / "pine_TW_b"
    (scripts / "otro.pine").write_text("//@version=5\n")   # de la carpeta, sólo los del manifiesto
    (settings.strategies_dir / "viejo.pine").write_text("de otra publicación")
    result = run(app, package, "--scripts", scripts)
    assert result.exit_code == 0, result.output
    assert "4 estrategias del contrato 1" in result.output and "commit 0123456789ab" in result.output
    assert "4 scripts copiados" in result.output and "1 miniaturas borradas" in result.output

    names = {private_file(r) for r in ROWS}
    assert {p.name for p in settings.strategies_dir.iterdir()} == names | {"viejo.pine"}
    for name in names:
        assert sha(settings.strategies_dir / name) == sha(scripts / name)
    catalogue = pd.read_csv(settings.catalogue, sep="\t", dtype=str)
    assert list(catalogue.columns) == CONTRACT["columns"] and len(catalogue) == 4
    assert all((settings.static / p).is_file() for col in CONTRACT["folders"] for p in catalogue[col])
    assert json.loads((settings.catalogue.parent / "release.json").read_text())["created"] == "2026-10-06T09:30:00Z"
    assert not list(settings.thumbs_dir.glob("*.webp"))

    again = run(app, package, "--scripts", scripts)
    assert again.exit_code == 0 and "0 ficheros copiados" in again.output and "0 scripts copiados" in again.output


def test_a_script_with_another_sha256_refuses_and_writes_nothing(app, settings, made):
    d_result, package = made
    changed = d_result / "pine_TW_b" / private_file(ROWS[2])
    changed.write_text("//@version=5\n// otra ejecución\n")
    before = snapshot(settings)
    result = run(app, package, "--scripts", d_result / "pine_TW_b")
    assert result.exit_code != 0 and changed.name in result.output and "sha256 del manifiesto" in result.output
    assert snapshot(settings) == before, "ni el catálogo, ni static/, ni un script, ni las miniaturas"


def test_without_scripts_they_must_already_be_in_the_private_folder(app, settings, made):
    """Los de conftest tienen otro contenido y la gratis no está: así no se publica."""
    d_result, package = made
    before = snapshot(settings)
    result = run(app, package)
    assert result.exit_code != 0 and "4 de los 4 scripts del paquete no están" in result.output
    assert "--scripts" in result.output and snapshot(settings) == before
    for r in ROWS:
        name = private_file(r)
        (settings.strategies_dir / name).write_bytes((d_result / "pine_TW_b" / name).read_bytes())
    result = run(app, package)
    assert result.exit_code == 0, result.output
    assert "0 scripts copiados" in result.output and len(pd.read_csv(settings.catalogue, sep="\t")) == 4


def test_skip_scripts_publishes_and_says_how_many_are_missing(app, settings, made):
    """Los de conftest tienen otro contenido y la gratis no está: no es lo mismo. Uno que falta no se puede
    entregar; uno de antes, sí, y se entregaría ese: se dice aparte."""
    _, package = made
    private = {p.name: p.read_bytes() for p in settings.strategies_dir.iterdir()}
    result = run(app, package, "--skip-scripts")
    assert result.exit_code == 0, result.output
    assert "1 scripts del paquete no están en STRATEGIES_DIR" in result.output
    assert "3 scripts de STRATEGIES_DIR no son los del paquete (otro sha256)" in result.output
    assert "se entregan en su versión de antes" in result.output
    assert len(pd.read_csv(settings.catalogue, sep="\t")) == 4
    assert {p.name: p.read_bytes() for p in settings.strategies_dir.iterdir()} == private


def test_without_scripts_the_refusal_tells_absent_from_outdated(app, settings, made):
    result = run(app, made[1])
    assert result.exit_code != 0 and "(1 no están y 3 tienen otro contenido)" in result.output


def test_a_package_that_does_not_validate_is_refused(app, settings, made):
    d_result, package = made
    chart = next((package / "pine_TW_img").iterdir())
    chart.unlink()
    chart.write_bytes(b"otro grafico")
    before = snapshot(settings)
    result = run(app, package, "--scripts", d_result / "pine_TW_b")
    assert result.exit_code != 0 and f"pine_TW_img/{chart.name}: its sha256" in result.output
    assert snapshot(settings) == before


def test_scripts_and_skip_scripts_do_not_go_together(app, made):
    d_result, package = made
    result = run(app, package, "--scripts", d_result / "pine_TW_b", "--skip-scripts")
    assert result.exit_code == 2 and "no los dos" in result.output
    with pytest.raises(ValueError):
        release.import_package(package, None, scripts=Path("x"), skip_scripts=True)


def test_what_is_published_is_the_package_that_was_checked(app, settings, tmp_path, monkeypatch):
    """El paso 7 vuelve a escribir d_result/package/ con otra ejecución mientras se importa: la tienda publicaría
    una estrategia cuyo script no ha copiado. Se publica lo comprobado, y como ya no está, no se publica nada."""
    d_a, rows_a = factory(tmp_path / "a", ROWS[:1])
    package = package_of(d_a, rows_a)
    d_b, rows_b = factory(tmp_path / "b", ROWS[1:2])
    other = package_of(d_b, rows_b)
    real = release.stage_scripts

    def meanwhile(*args):
        n = real(*args)
        shutil.rmtree(package)
        shutil.copytree(other, package)   # un paquete que también vale, pero no el comprobado
        return n

    monkeypatch.setattr(release, "stage_scripts", meanwhile)
    before = snapshot(settings)
    result = run(app, package, "--scripts", d_a / "pine_TW_b")
    assert result.exit_code != 0, result.output
    assert "gone from the package since it was checked" in result.output and "no se ha escrito nada" in result.output
    assert snapshot(settings) == before, "ni el catálogo de la otra ejecución, ni un script, ni un gráfico"


def test_a_failure_half_way_leaves_the_shop_as_it_was(app, settings, made, monkeypatch):
    """El disco se llena a mitad de los gráficos: nada está en su sitio todavía, y no queda ningún .tmp."""
    d_result, package = made
    pub = release.publisher()
    real, calls = pub.Staged.write, []

    def full(self, dest, data):
        calls.append(dest)
        if len(calls) == 8:   # tras los 4 scripts, los niveles y dos gráficos
            raise OSError(errno.ENOSPC, "No space left on device")
        return real(self, dest, data)

    monkeypatch.setattr(pub.Staged, "write", full)
    before = snapshot(settings)
    result = run(app, package, "--scripts", d_result / "pine_TW_b")
    assert result.exit_code != 0 and "No space left on device" in result.output
    assert "no se ha escrito nada" in result.output
    assert snapshot(settings) == before, "ni scripts, ni gráficos, ni catálogo, ni un .tmp"


def test_a_failure_while_renaming_says_what_is_already_in_place(app, settings, made, monkeypatch):
    """Si falla al renombrar (lo último), lo renombrado se queda: el comando lo dice, borra los .tmp y vacía las
    miniaturas, que pueden ser de un gráfico ya reemplazado."""
    d_result, package = made
    real, renamed = os.replace, []

    def replace_some(src, dest):
        if len(renamed) == 5:   # los 4 scripts y los niveles
            raise OSError(errno.EIO, "Input/output error")
        real(src, dest)
        renamed.append(dest)

    monkeypatch.setattr(release.publisher().os, "replace", replace_some)
    catalogue = settings.catalogue.read_bytes()
    result = run(app, package, "--scripts", d_result / "pine_TW_b")
    assert result.exit_code != 0 and "falló a medias: 5 ficheros" in result.output
    assert len([p for p in renamed if p.parent == settings.strategies_dir]) == 4, "los scripts, lo primero"
    assert settings.catalogue.read_bytes() == catalogue, "el catálogo, lo último: sigue el de antes"
    assert not (settings.catalogue.parent / "release.json").exists()
    assert not [p for f in (settings.static, settings.strategies_dir) for p in f.rglob("*.tmp")]
    assert not list(settings.thumbs_dir.glob("*.webp"))


def test_the_import_writes_the_levels_of_the_scripts_it_checked(app, settings, tmp_path):
    """catalogue/levels.json, con los de cada script del paquete que lleva el nombre de su estrategia (los de la
    fábrica de estas pruebas no lo llevan); con --skip-scripts, sólo los que ya están con su sha256: los de antes
    tendrían los niveles de otra versión."""
    d_result, rows = factory(tmp_path)
    aapl, msft = strategy_id(ROWS[0]), strategy_id(ROWS[1])
    (d_result / "pine_TW_b" / private_file(ROWS[0])).write_text(script_of(aapl, "0.8", "-0.55"), encoding="utf-8")
    (d_result / "pine_TW_b" / private_file(ROWS[1])).write_text(script_of(msft, "0.45"), encoding="utf-8")
    settings.levels.write_text('{\n  "OLD_1Day_X_0": {"buy_at": 0.6, "close_at": -0.9}\n}\n')
    package = package_of(d_result, rows)
    result = run(app, package, "--scripts", d_result / "pine_TW_b")
    assert result.exit_code == 0, result.output
    assert "catalogue/levels.json: 2 de 4 estrategias con los niveles de su script" in result.output
    assert "2 cuyo script es el de otra estrategia" in result.output
    assert levels.load(settings.levels) == {aapl: {"buy_at": 0.8, "close_at": -0.55},
                                            msft: {"buy_at": 0.45, "close_at": -0.9}}, "los de antes, fuera"

    (settings.strategies_dir / private_file(ROWS[1])).write_text("de otra versión")
    result = run(app, package, "--skip-scripts")
    assert result.exit_code == 0, result.output
    assert levels.load(settings.levels) == {aapl: {"buy_at": 0.8, "close_at": -0.55}}
    assert "1 sin su script" in result.output


def test_the_import_says_which_logos_it_kept(app, settings, made):
    """Un logo de verdad de la tienda no se cambia por el del paquete; uno de relleno, sí."""
    d_result, package = made
    icons = settings.static / "assets" / "icons"
    icons.mkdir(parents=True)
    (icons / "MSFT.svg").write_bytes(b"<svg>el logo de verdad de la tienda</svg>")
    (icons / "AAPL.svg").write_text(PLACEHOLDER.format(size=18, half=9.0, font=7.6, label="AAPL"))
    result = run(app, package, "--scripts", d_result / "pine_TW_b")
    assert result.exit_code == 0, result.output
    assert "1 logos del paquete son distintos de los de la tienda y se han dejado los de la tienda" in result.output
    assert "MSFT.svg" in result.output and "AAPL.svg" not in result.output
    assert (icons / "AAPL.svg").read_bytes() == (d_result / "icons" / "AAPL.svg").read_bytes()


def test_the_import_says_which_bundles_lose_a_strategy(app, settings, tmp_path):
    """Un catálogo nuevo sin una estrategia de un lote deja ese lote fuera entero: el resumen lo dice."""
    d_result, rows = factory(tmp_path, rows=ROWS[1:])   # sin AAPL, que va en el lote «duo»
    result = run(app, package_of(d_result, rows), "--scripts", d_result / "pine_TW_b")
    assert result.exit_code == 0, result.output
    assert "1 lotes de catalogue/bundles.json nombran estrategias que el catálogo ya no trae" in result.output
    assert "duo (AAPL_1Day_1ADX_aaaa1111)" in result.output


def test_the_real_bundles_name_strategies_of_the_real_catalogue():
    """Los lotes del repo se nombran como los compara el resumen del import (el id de /s/<id>)."""
    root = Path(__file__).resolve().parent.parent / "catalogue"
    catalogue = pd.read_csv(root / "catalogue.csv", sep="\t", dtype=str)
    assert release.bundles_left_out(root / "bundles.json", catalogue) == []


def test_without_pandas_the_import_says_where_to_run_it(app, made, monkeypatch):
    """Una instalación de producción (requirements.txt) no trae pandas: el comando lo dice, sin traza."""
    def no_pandas():
        raise ModuleNotFoundError("No module named 'pandas'", name="pandas")
    monkeypatch.setattr(release, "publisher", no_pandas)
    result = run(app, made[1], "--skip-scripts")
    assert result.exit_code != 0 and "requirements-dev.txt" in result.output
    assert "Traceback" not in result.output



def test_the_import_leaves_out_intraday_stocks(app, settings, tmp_path):
    """E2: sin LIST_INTRADAY_STOCKS (lo de por defecto), las estrategias intradía de acciones no se publican, ni sus
    ficheros, y su script ni se pide ni se copia: el plan gratis de TradingView enseña otros datos intradía de las
    acciones (sólo Cboe BZX), así que allí operan distinto que en su backtest. Las de cripto, también horarias, sí.
    El resumen dice cuántas y por qué; release.json, cuáles. Con LIST_INTRADAY_STOCKS=1, todas."""
    settings.list_intraday_stocks = False
    d_result, rows = factory(tmp_path, ROWS + [CRYPTO_HOURLY])
    package = package_of(d_result, rows)
    msft = private_file(ROWS[1])
    stale_msft = (settings.strategies_dir / msft).read_bytes()   # el de conftest: otro contenido
    for r in rows:
        if private_file(r) != msft:
            (settings.strategies_dir / private_file(r)).write_bytes((d_result / "pine_TW_b" / private_file(r)).read_bytes())
    result = run(app, package)   # sin --scripts: el de MSFT, de otro contenido, no se pide
    assert result.exit_code == 0, result.output
    assert "4 estrategias del contrato 1" in result.output and "0 scripts copiados" in result.output
    assert ("1 estrategias intradía de acciones fuera (LIST_INTRADAY_STOCKS=1 las publica): el plan gratis de "
            "TradingView enseña otros datos intradía de las acciones (sólo Cboe BZX)") in result.output
    assert "duo (MSFT_1Hour_2BB0_bbbb2222)" in result.output, "el lote que la tenía se queda fuera, y se dice"
    catalogue = pd.read_csv(settings.catalogue, sep="\t", dtype=str)
    assert list(catalogue["ticker"]) == ["AAPL", "NVDA", "TSLA", "BTCUSDT"]
    assert not [p for p in settings.static.rglob("*") if "MSFT" in p.name]
    assert (settings.strategies_dir / msft).read_bytes() == stale_msft
    left = json.loads((settings.catalogue.parent / "release.json").read_text())["left_out"]["intraday_stocks"]
    assert (left["rows"], left["ids"]) == (1, ["MSFT_1Hour_2BB0_bbbb2222"])

    settings.list_intraday_stocks = True
    result = run(app, package, "--scripts", d_result / "pine_TW_b")
    assert result.exit_code == 0, result.output
    assert "5 estrategias del contrato 1" in result.output and "intradía" not in result.output
    assert "left_out" not in json.loads((settings.catalogue.parent / "release.json").read_text())


def test_list_intraday_stocks_from_the_environment(tmp_path):
    from edgefolio.settings import Settings
    assert Settings.from_env(tmp_path, {}).list_intraday_stocks is False
    assert Settings.from_env(tmp_path, {"LIST_INTRADAY_STOCKS": "1"}).list_intraday_stocks is True
    assert Settings.from_env(tmp_path, {"LIST_INTRADAY_STOCKS": "off"}).list_intraday_stocks is False
    with pytest.raises(ValueError, match="LIST_INTRADAY_STOCKS"):
        Settings.from_env(tmp_path, {"LIST_INTRADAY_STOCKS": "maybe"})


def test_the_import_says_among_how_many_tried_and_brings_the_results_since_release(app, settings, made):
    """E1 y E11: lo dice el resumen. tried, del manifiesto (o del release.json de la misma ejecución); el
    since_release.csv del paquete, al lado del catálogo; uno de antes, sin otro en el paquete, se queda hasta --prune."""
    d_result, package = made
    scripts = d_result / "pine_TW_b"
    result = run(app, package, "--scripts", scripts)
    assert "el paquete no dice entre cuántas estrategias probadas se eligieron: la tienda no lo dice" in result.output
    edit_manifest(package, lambda m: m.update(tried=1531))
    with_since_release(package, "id,pct,as_of\nAAPL_1Day_1ADX_aaaa1111,-1.25,2026-10-25\n")
    result = run(app, package, "--scripts", scripts)
    assert result.exit_code == 0, result.output
    assert "elegidas entre 1531 estrategias probadas (la tienda lo dice en el aviso de sobreajuste)" in result.output
    assert "catalogue/since_release.csv: el resultado de cada estrategia desde su publicación, del paquete" in result.output
    since = settings.catalogue.parent / "since_release.csv"
    assert since.read_text() == "id,pct,as_of\nAAPL_1Day_1ADX_aaaa1111,-1.25,2026-10-25\n" == settings.since_release.read_text()

    (package / "since_release.csv").unlink()
    edit_manifest(package, lambda m: m["files"].pop("since_release.csv"))
    result = run(app, package, "--scripts", scripts)
    assert "es de un catálogo de antes y el paquete no trae uno: se queda (--prune lo borra)" in result.output
    assert "elegidas entre 1531" in result.output and since.is_file()
    result = run(app, package, "--scripts", scripts, "--prune")
    assert "catalogue/since_release.csv borrado" in result.output and not since.exists()
