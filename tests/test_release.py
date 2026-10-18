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

from edgefolio import release
from tests.conftest import ROWS
from tests.test_publish import CONTRACT, PLACEHOLDER, factory, package_of, private_file, sha


@pytest.fixture
def settings(settings, tmp_path):
    """Las de conftest, con static/ también en tmp: el comando copia ahí los gráficos (nunca a los del repo)."""
    return replace(settings, static=tmp_path / "static")


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
        if len(calls) == 7:   # tras los 4 scripts y dos gráficos
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
        if len(renamed) == 5:   # los 4 scripts y un gráfico
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

