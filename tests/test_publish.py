# -*- coding: utf-8 -*-
"""catalogue/publish.py, el puente con la aplicación gemela que genera los datos
(Leci37/tuisku_strategy_generator): su paquete (o su export) pasa a ser
catalogue/catalogue.csv y sus gráficos, iconos y vistas previas van a static/assets/, de donde los sirve la
tienda. catalogue/contract.json dice qué columnas y qué carpetas valen: lo que se sale, no se publica.

Todo se escribe en carpetas temporales: ni el catalogue.csv ni el static/assets del repo se tocan."""
import errno
import hashlib
import importlib.util
import json
import os
import posixpath
import shutil
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from edgefolio.catalogue import Strategy
from tests.conftest import ROWS

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = json.loads((ROOT / "catalogue" / "contract.json").read_text(encoding="utf-8"))
KEY = ["ticker", "interval", "key_techs", "id_model"]
# Lo que el generador pone en las columnas que no son ni la clave ni una ruta.
FIGURES = {"Net Profit_usd": "1520.5", "Full Indicator Name": "Average Directional Index", "Index": "NASDAQ",
           "Net Profit_per": "15.2", "Trade Activity Per Candle": "0.05", "Total Closed Trades": "120",
           "Percent Profitable_per": "55.1", "Profit Factor": "1.8", "Max Drawdown_usd": "300",
           "Max Drawdown_per": "3.1", "Avg Trade_usd": "12.6", "Avg Trade_per": "0.12", "Avg # Bars in Trades": "4.5",
           "Release date": "2026-10-01", "months_trained": "24", "n_candles": "3000", "Precision f1_per": "61.2",
           "Tree Deep": "6"}
FACTORY_ROW = {**FIGURES, "Price": "79", "ticker": "AAPL", "interval": "1Day", "key_techs": "1ADX",
               "id_model": "aaaa1111", "Name": "Apple", "pine_path": "C:/fabrica/d_result/pine_TW_b/secreto.pine",
               "path_stra": "C:\\fabrica\\d_result\\pine_TW_img\\AAPL_1Day_1ADX_aaaa1111_profit.png",
               "path_candle": "https://raw.githubusercontent.com/x/y/main/d_result/pine_TW_img/AAPL_1Day_1ADX_aaaa1111_candel.png",
               "path_ico": "d_result/icons/AAPL.png", "path_ico_big": "d_result/icons/AAPL_big.png",
               "pine_path_shadow": "d_result/pine_TW_hide/AAPL_1Day_1ADX_aaaa1111.pine"}

# El logo de relleno que escribe el paso 7 cuando no tiene el de verdad (placeholder_svg de su S_04).
PLACEHOLDER = ('<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
               '<circle cx="{half}" cy="{half}" r="{half}" fill="#5b6b7c"/>'
               '<text x="50%" y="54%" dominant-baseline="middle" text-anchor="middle" font-family="Arial, sans-serif" '
               'font-size="{font}" font-weight="bold" fill="#ffffff">{label}</text></svg>')


def script(name: str) -> str:
    """Un script de estrategia como los del generador: 80 líneas en su primer árbol."""
    lines = ["//@version=5", f'strategy("{name}")', "decision_tree_0() =>"] + [f"    x{i} = {i}" for i in range(80)]
    return "\n".join(lines) + "\n"


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def private_file(row: dict) -> str:
    return Strategy(row["ticker"], row["interval"], row["key_techs"], row["id_model"], Decimal(row["Price"]),
                    row).private_file


def factory(tmp_path: Path, rows=ROWS):
    """El d_result/ del generador tras su paso 7, con las filas de ``rows`` completas (las del contrato y
    pine_path) y sus ficheros: gráficos, iconos, vistas previas y los scripts completos. Da (d_result, filas)."""
    d_result = tmp_path / "fabrica" / "d_result"
    full = []
    for r in rows:
        stem = "_".join(r[k] for k in KEY)
        row = {**FIGURES, **r, "pine_path": f"d_result/pine_TW_b/{private_file(r)}",
               "path_stra": f"d_result/pine_TW_img/{stem}_profit.png",
               "path_candle": f"d_result/pine_TW_img/{stem}_candel.png",
               "path_ico": f"d_result/icons/{r['ticker']}.svg", "path_ico_big": f"d_result/icons/{r['ticker']}_big.svg",
               "pine_path_shadow": f"d_result/pine_TW_hide/{stem}.pine"}
        for col in ("path_stra", "path_candle", "path_ico", "path_ico_big"):
            f = d_result.parent / row[col]
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(b"image " + f.name.encode())
        for col in ("pine_path_shadow", "pine_path"):
            f = d_result.parent / row[col]
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(script(stem), encoding="utf-8")
        full.append(row)
    return d_result, full


def package_of(d_result: Path, rows: list, leave_out=()) -> Path:
    """El paquete que deja el paso 7 en d_result/package/: catalogue.csv con las columnas del contrato, los
    ficheros que nombran sus filas (menos ``leave_out``, enlazados como hace el generador) y manifest.json
    con el sha256 de cada uno y de cada script completo, que no va dentro."""
    package = d_result / "package"
    package.mkdir()
    pd.DataFrame(rows)[CONTRACT["columns"]].to_csv(package / "catalogue.csv", sep="\t", index=False)
    for r in rows:
        for col, folder in CONTRACT["folders"].items():
            rel = f"{folder}/{posixpath.basename(r[col])}"
            if rel not in leave_out and not (package / rel).exists():
                (package / folder).mkdir(exist_ok=True)
                os.link(d_result / rel, package / rel)
    manifest = {
        "contract": CONTRACT["version"], "created": "2026-10-06T09:30:00Z",
        "generator": {"repo": "Leci37/tuisku_strategy_generator", "commit": "0123456789abcdef"},
        "rows": len(rows),
        "files": {p.relative_to(package).as_posix(): sha(p) for p in sorted(package.rglob("*")) if p.is_file()},
        "private": {"folder": CONTRACT["private"]["folder"],
                    "files": {private_file(r): sha(d_result / "pine_TW_b" / private_file(r)) for r in rows}},
    }
    (package / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return package


def edit_manifest(package: Path, change):
    path = package / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    change(manifest)
    path.write_text(json.dumps(manifest), encoding="utf-8")


def rewrite_catalogue(package: Path, change):
    """Cambia catalogue.csv del paquete y pone su sha256 nuevo en el manifiesto: sólo falla lo que se prueba."""
    df = change(pd.read_csv(package / "catalogue.csv", sep="\t", dtype=str))
    df.to_csv(package / "catalogue.csv", sep="\t", index=False)
    edit_manifest(package, lambda m: m["files"].update({"catalogue.csv": sha(package / "catalogue.csv")}))


@pytest.fixture
def publish():
    sys.path.insert(0, str(ROOT / "catalogue"))  # publish.py importa previews, a su lado
    try:
        spec = importlib.util.spec_from_file_location("publish", ROOT / "catalogue" / "publish.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.path.remove(str(ROOT / "catalogue"))


@pytest.fixture
def shop(tmp_path):
    """La tienda donde se publica en las pruebas: su catalogue/ y su static/assets/, vacíos."""
    return tmp_path / "shop"


def into(shop: Path) -> dict:
    return {"out": shop / "catalogue" / "catalogue.csv", "assets": shop / "static" / "assets"}


def refused(publish, package: Path, shop: Path) -> str:
    """Publicar ``package`` falla con todos sus problemas juntos y sin escribir nada; da el texto."""
    with pytest.raises(publish.PackageError) as e:
        publish.publish_package(package, **into(shop))
    assert not shop.exists(), "un paquete que no vale no escribe nada"
    return str(e.value)


def test_the_assets_go_where_the_shop_serves_them(publish):
    """Las rutas del catálogo ("assets/charts/…") son relativas a static/: ahí copia publish.py."""
    assert publish.ASSETS == ROOT / "static" / "assets"
    first = pd.read_csv(ROOT / "catalogue" / "catalogue.csv", sep="\t", nrows=1, dtype=str).iloc[0]
    for col in ("path_stra", "path_candle", "path_ico", "pine_path_shadow"):
        assert (publish.ASSETS.parent / first[col]).is_file(), col


def test_an_export_of_the_factory_is_published(publish, tmp_path, monkeypatch):
    """La forma de antes de los paquetes (EXPORT.csv --assets DIR) sigue valiendo."""
    d_result = tmp_path / "fabrica" / "d_result"
    for sub, name in [("pine_TW_img", "AAPL_1Day_1ADX_aaaa1111_profit.png"),
                      ("pine_TW_img", "AAPL_1Day_1ADX_aaaa1111_candel.png"), ("icons", "AAPL.png"),
                      ("icons", "AAPL_big.png")]:
        (d_result / sub).mkdir(parents=True, exist_ok=True)
        (d_result / sub / name).write_bytes(b"png")
    (d_result / "pine_TW_hide").mkdir()
    (d_result / "pine_TW_hide" / "AAPL_1Day_1ADX_aaaa1111.pine").write_text(script("AAPL"))
    export = tmp_path / "pine_TW_img_info_6_WEB.csv"
    pd.DataFrame([FACTORY_ROW, FACTORY_ROW]).to_csv(export, sep="\t", index=False)  # el export repite filas

    shop = tmp_path / "shop"
    monkeypatch.setattr(publish, "ROOT", shop)
    monkeypatch.setattr(publish, "ASSETS", shop / "static" / "assets")
    monkeypatch.setattr(publish, "OUT", shop / "catalogue.csv")
    df = publish.publish(export, d_result)

    assert len(df) == 1 and "pine_path" not in df.columns  # dónde está el script de pago nunca sale
    row = df.iloc[0]
    assert row["path_stra"] == "assets/charts/AAPL_1Day_1ADX_aaaa1111_profit.png"
    for col in ("path_stra", "path_candle", "path_ico", "path_ico_big", "pine_path_shadow"):
        assert (shop / "static" / row[col]).is_file(), col
    preview = (shop / "static" / row["pine_path_shadow"]).read_text()
    assert preview.endswith(sys.modules["previews"].PREVIEW_TAIL) and "x70 = 70" not in preview  # cortada

    (shop / "static" / "assets" / "charts" / "OLD_profit.png").write_bytes(b"png")
    assert [f.name for f in publish.unused_assets(df)] == ["OLD_profit.png"]


def test_the_contract_is_what_publish_reads(publish):
    """contract.json es la única fuente: de él salen las carpetas de publish.py, y su script privado se llama
    como lo busca la tienda (Strategy.private_file)."""
    assert publish.PATH_COLUMNS == {col: (CONTRACT["assets"][col], folder) for col, folder in CONTRACT["folders"].items()}
    assert publish.OPTIONAL == ["version"] and publish.DROPPED == ["pine_path"]
    assert "pine_path" not in CONTRACT["columns"] and set(CONTRACT["folders"]) == set(CONTRACT["assets"])
    assert set(CONTRACT["folders"]) <= set(CONTRACT["columns"]) and len(set(CONTRACT["columns"])) == 29
    assert "tuisku" in CONTRACT["private"]["name"] and CONTRACT["private"]["folder"] == "pine_TW_b"
    for row in ROWS + [{**ROWS[0], "ticker": "BTCUSDT", "interval": "15min", "key_techs": "2C0_"}]:
        assert publish.private_name(*(row[k] for k in KEY)) == private_file(row)


def test_the_real_catalogue_follows_the_contract(publish):
    publish.check_columns(pd.read_csv(ROOT / "catalogue" / "catalogue.csv", sep="\t", dtype=str, nrows=5))


@pytest.mark.parametrize("change, says", [
    (lambda r: {k: v for k, v in r.items() if k != "Profit Factor"}, "missing: Profit Factor"),
    (lambda r: {**r, "Sharpe": "1.2"}, "does not know: Sharpe"),
])
def test_the_export_form_also_checks_the_columns(publish, tmp_path, change, says):
    export = tmp_path / "export.csv"
    pd.DataFrame([change(FACTORY_ROW)]).to_csv(export, sep="\t", index=False)
    with pytest.raises(publish.ContractError, match=says):
        publish.publish(export, **into(tmp_path / "shop"))
    assert not (tmp_path / "shop").exists()


def test_a_package_is_published(publish, tmp_path, shop):
    d_result, rows = factory(tmp_path)
    package = package_of(d_result, rows)
    df = publish.publish_package(package, **into(shop))

    assert len(df) == 4 and "pine_path" not in df.columns
    written = pd.read_csv(shop / "catalogue" / "catalogue.csv", sep="\t", dtype=str)
    assert list(written.columns) == CONTRACT["columns"] and list(written["ticker"]) == [r["ticker"] for r in ROWS]
    for _, row in written.iterrows():
        for col in CONTRACT["folders"]:
            assert row[col].startswith("assets/") and (shop / "static" / row[col]).is_file(), col
    preview = shop / "static" / written.iloc[0]["pine_path_shadow"]
    assert preview.read_text().endswith(sys.modules["previews"].PREVIEW_TAIL)  # sólo su parte pública
    chart = shop / "static" / written.iloc[0]["path_stra"]
    assert chart.read_bytes() == (d_result / "pine_TW_img" / chart.name).read_bytes()
    release = json.loads((shop / "catalogue" / "release.json").read_text())
    assert release == {"contract": 1, "created": "2026-10-06T09:30:00Z", "rows": 4, "generator": {
        "repo": "Leci37/tuisku_strategy_generator", "commit": "0123456789abcdef"}}
    assert df.attrs["published"]["copied"] == 4 * 2 + 4 * 2 + 4  # gráficos, iconos y vistas previas

    again = publish.publish_package(package, **into(shop))
    assert again.attrs["published"]["copied"] == 0, "lo que no cambió no se vuelve a copiar"
    (shop / "static" / "assets" / "charts" / "OLD_profit.png").write_bytes(b"png")
    chart.write_bytes(b"un grafico de antes")
    pruned = publish.publish_package(package, prune=True, **into(shop))
    assert pruned.attrs["published"]["copied"] == 1, "un gráfico que cambió en el generador se reemplaza"
    assert chart.read_bytes() == (d_result / "pine_TW_img" / chart.name).read_bytes()
    assert pruned.attrs["published"]["pruned"] == 1 and not (shop / "static/assets/charts/OLD_profit.png").exists()


def test_a_file_with_another_sha256_is_refused(publish, tmp_path, shop):
    d_result, rows = factory(tmp_path)
    package = package_of(d_result, rows)
    chart = next((package / "pine_TW_img").iterdir())
    chart.unlink()
    chart.write_bytes(b"otro grafico")
    assert f"pine_TW_img/{chart.name}: its sha256 is not the manifest's" in refused(publish, package, shop)


def test_a_package_of_another_contract_is_refused(publish, tmp_path, shop):
    d_result, rows = factory(tmp_path)
    package = package_of(d_result, rows)
    edit_manifest(package, lambda m: m.update(contract=2))
    assert "package of contract 2, this shop reads contract 1" in refused(publish, package, shop)
    (package / "manifest.json").unlink()
    assert "no manifest.json" in refused(publish, package, shop)
    (package / "manifest.json").write_text("{no es json")
    assert "not valid JSON" in refused(publish, package, shop)


@pytest.mark.parametrize("change, says", [
    (lambda df: df.drop(columns=["Max Drawdown_usd"]), "missing: Max Drawdown_usd"),
    (lambda df: df.assign(Sharpe="1.2"), "does not know: Sharpe"),
    (lambda df: df.assign(pine_path="d_result/pine_TW_b/x.pine").drop(columns=["Tree Deep"]), "missing: Tree Deep"),
])
def test_columns_out_of_the_contract_are_refused(publish, tmp_path, shop, change, says):
    """Una columna que falta o una que el contrato no conoce: el generador y la tienda ya no hablan de lo mismo."""
    d_result, rows = factory(tmp_path)
    package = package_of(d_result, rows)
    rewrite_catalogue(package, change)
    assert says in refused(publish, package, shop)


@pytest.mark.parametrize("key", ["../x", "/abs", "a/b/c", "pine_TW_img/a/b", "back\\slash", "pine_TW_img/..",
                                 "manifest.json", "pine_TW_b/secreto.pine", "pine_TW_img/.oculto"])
def test_unsafe_paths_in_the_manifest_are_refused(publish, tmp_path, shop, key):
    """Una clave de files sólo puede ser catalogue.csv o <carpeta del contrato>/<nombre>: nada fuera del paquete."""
    d_result, rows = factory(tmp_path)
    package = package_of(d_result, rows)
    (tmp_path / "x").write_bytes(b"fuera del paquete")
    edit_manifest(package, lambda m: m["files"].update({key: sha(tmp_path / "x")}))
    assert f"{key!r}: not a package path" in refused(publish, package, shop)


def test_a_file_the_manifest_does_not_list_is_refused(publish, tmp_path, shop):
    d_result, rows = factory(tmp_path)
    package = package_of(d_result, rows)
    (package / "pine_TW_img" / "colado.png").write_bytes(b"png")
    (package / "notas.txt").write_text("hola")
    problems = refused(publish, package, shop)
    assert "2 files in the package are not in the manifest: notas.txt, pine_TW_img/colado.png" in problems


def test_a_file_a_row_names_must_be_in_the_package_or_in_the_shop(publish, tmp_path, shop):
    """Con SHOP_ICONS_DIR el generador nombra un logo que no escribe porque la tienda ya lo tiene."""
    d_result, rows = factory(tmp_path)
    package = package_of(d_result, rows, leave_out={"icons/AAPL.svg"})
    assert "path_ico: 1 files neither in the package (icons/) nor in the shop (static/assets/icons/): AAPL.svg" in (
        refused(publish, package, shop))
    (shop / "static" / "assets" / "icons").mkdir(parents=True)
    (shop / "static" / "assets" / "icons" / "AAPL.svg").write_bytes(b"el logo de la tienda")
    df = publish.publish_package(package, **into(shop))
    assert df.iloc[0]["path_ico"] == "assets/icons/AAPL.svg"
    assert (shop / "static" / "assets" / "icons" / "AAPL.svg").read_bytes() == b"el logo de la tienda"


def test_a_logo_the_shop_has_is_kept_even_if_the_package_brings_another(publish, tmp_path, shop):
    """Sin SHOP_ICONS_DIR, el paso 7 deja un logo de relleno en d_result/icons y entra en el paquete: el de la
    tienda es el bueno y no se cambia por él. Los gráficos y las vistas previas sí se reemplazan (otra prueba)."""
    d_result, rows = factory(tmp_path)
    package = package_of(d_result, rows)
    icons = shop / "static" / "assets" / "icons"
    icons.mkdir(parents=True)
    (icons / "AAPL.svg").write_bytes(b"el logo de la tienda")
    df = publish.publish_package(package, **into(shop))
    assert (icons / "AAPL.svg").read_bytes() == b"el logo de la tienda"
    assert (icons / "AAPL_big.svg").read_bytes() == (d_result / "icons" / "AAPL_big.svg").read_bytes()  # faltaba
    assert df.attrs["published"]["copied"] == 4 * 2 + 4 * 2 + 4 - 1
    assert df.attrs["published"]["kept"] == ["AAPL.svg"], "y se dice cuáles se han dejado"


def test_a_placeholder_logo_of_the_shop_gives_way_to_the_real_one(publish, tmp_path, shop):
    """Una ejecución sin logo deja en la tienda el de relleno del generador; cuando el logo de verdad llega en
    otro paquete, lo reemplaza. Un logo de verdad de la tienda, no."""
    d_result, rows = factory(tmp_path)
    package = package_of(d_result, rows)
    icons = shop / "static" / "assets" / "icons"
    icons.mkdir(parents=True)
    (icons / "AAPL.svg").write_text(PLACEHOLDER.format(size=18, half=9.0, font=7.6, label="AAPL"))
    (icons / "AAPL_big.svg").write_text(PLACEHOLDER.format(size=56, half=28.0, font=18.5, label="AAPL"))
    (icons / "MSFT.svg").write_bytes(b"<svg>el logo de verdad de la tienda</svg>")
    df = publish.publish_package(package, **into(shop))
    for name in ("AAPL.svg", "AAPL_big.svg"):
        assert (icons / name).read_bytes() == (d_result / "icons" / name).read_bytes(), name
    assert (icons / "MSFT.svg").read_bytes() == b"<svg>el logo de verdad de la tienda</svg>"
    assert df.attrs["published"]["kept"] == ["MSFT.svg"]
    assert publish.is_placeholder(PLACEHOLDER.format(size=18, half=9.0, font=7.6, label="BTC").encode())
    assert not publish.is_placeholder(b'<svg><circle fill="#5b6b7c"/><path d="M0 0"/></svg>')


def test_every_row_needs_its_script_in_the_private_list(publish, tmp_path, shop):
    d_result, rows = factory(tmp_path)
    package = package_of(d_result, rows)
    gone = private_file(ROWS[1])

    def change(m):
        del m["private"]["files"][gone]
        m["private"]["files"]["ajeno.pine"] = "0" * 64
    edit_manifest(package, change)
    problems = refused(publish, package, shop)
    assert f"private.files lacks the script of 1 rows: {gone}" in problems
    assert "private.files names 1 scripts of no row: ajeno.pine" in problems
    private = {private_file(r) for r in ROWS}
    assert not [p for p in package.rglob("*") if p.name in private], "los scripts completos nunca van en el paquete"


def test_a_full_script_disguised_as_a_chart_is_refused(publish, tmp_path, shop):
    """Un script completo sólo viaja como vista previa de una gratis (y se corta al publicar): como gráfico
    o como logo acabaría entero en static/assets, así que el paquete no vale."""
    d_result, rows = factory(tmp_path)
    package = package_of(d_result, rows)
    chart = next((package / "pine_TW_img").iterdir())
    chart.unlink()
    chart.write_bytes((d_result / "pine_TW_b" / private_file(ROWS[0])).read_bytes())
    edit_manifest(package, lambda m: m["files"].update({f"pine_TW_img/{chart.name}": sha(chart)}))
    problems = refused(publish, package, shop)
    assert f"1 files of the package are full scripts of private.files, which are never published: " \
           f"pine_TW_img/{chart.name}" in problems


def test_what_cannot_be_published_safely_is_refused(publish, tmp_path, shop):
    """Un enlace simbólico (podría llevar a cualquier sitio del disco), una vista previa que no es un script
    de estrategia (no se puede cortar) y una fila sin su clave."""
    d_result, rows = factory(tmp_path)
    package = package_of(d_result, rows)
    os.symlink("/etc/passwd", package / "icons" / "enlace.svg")
    preview = package / "pine_TW_hide" / posixpath.basename(rows[0]["pine_path_shadow"])
    preview.unlink()
    preview.write_text("sin arbol\n")
    rewrite_catalogue(package, lambda df: df.assign(id_model=["aaaa1111", "", "cccc3333", "dddd4444"]))
    edit_manifest(package, lambda m: m["files"].update({"icons/enlace.svg": "0" * 64,
                                                        f"pine_TW_hide/{preview.name}": sha(preview)}))
    problems = refused(publish, package, shop)
    assert "icons/enlace.svg: in the manifest but not a file of the package" in problems
    assert f"pine_TW_hide/{preview.name}: not a preview of a strategy script" in problems
    assert "1 rows without ticker, interval, key_techs, id_model: lines 3 of catalogue.csv" in problems


def test_publish_needs_nothing_but_pandas():
    """publish.py corre en la máquina del generador sin la tienda instalada: la biblioteca estándar, pandas y
    previews.py, a su lado."""
    import ast
    tree = ast.parse((ROOT / "catalogue" / "publish.py").read_text(encoding="utf-8"))
    imported = {(n.module if isinstance(n, ast.ImportFrom) else a.name).split(".")[0]
                for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
    assert imported - set(sys.stdlib_module_names) == {"pandas", "previews"}


def test_every_problem_is_said_at_once(publish, tmp_path, shop):
    d_result, rows = factory(tmp_path)
    package = package_of(d_result, rows)
    (package / "notas.txt").write_text("hola")
    edit_manifest(package, lambda m: (m.update(rows=3), m["private"]["files"].popitem()))
    problems = refused(publish, package, shop)
    assert "notas.txt" in problems and "rows is 3" in problems and "private.files lacks" in problems


def test_publish_runs_alone_with_a_package(tmp_path):
    """python catalogue/publish.py --package DIR, sin la tienda instalada: sólo pandas. Corre una copia en
    una tienda temporal (su ROOT es la carpeta de encima de la suya)."""
    shop = tmp_path / "shop"
    (shop / "catalogue").mkdir(parents=True)
    for name in ("publish.py", "previews.py", "contract.json"):
        shutil.copy(ROOT / "catalogue" / name, shop / "catalogue" / name)
    d_result, rows = factory(tmp_path)
    package = package_of(d_result, rows)

    def run(*args):
        return subprocess.run([sys.executable, str(shop / "catalogue" / "publish.py"), *map(str, args)],
                              capture_output=True, text=True, cwd=tmp_path)
    assert run().returncode == 2 and run("x.csv", "--package", package).returncode == 2
    edit_manifest(package, lambda m: m.update(rows=9))
    bad = run("--package", package)
    assert bad.returncode == 1 and "nothing published" in bad.stderr and "rows is 9" in bad.stderr
    assert not (shop / "catalogue" / "catalogue.csv").exists() and not (shop / "static").exists()
    edit_manifest(package, lambda m: m.update(rows=4))
    ok = run("--package", package, "--prune")
    assert ok.returncode == 0, ok.stderr
    assert "4 strategies" in ok.stdout and (shop / "catalogue" / "release.json").is_file()
    assert len(list((shop / "static" / "assets" / "charts").iterdir())) == 8


@pytest.mark.parametrize("how, says", [
    (lambda f: (f.unlink(), f.write_bytes(b"otro grafico")), "changed since it was checked"),
    (lambda f: f.unlink(), "gone from the package since it was checked"),
])
def test_a_file_that_changes_after_the_check_is_not_published(publish, tmp_path, shop, monkeypatch, how, says):
    """Los ficheros del paquete son enlaces a d_result/, que el generador reescribe en su sitio: lo que se copia
    se vuelve a comprobar con su sha256, y si ya no es lo comprobado no se publica nada."""
    d_result, rows = factory(tmp_path)
    package = package_of(d_result, rows)
    chart = package / "pine_TW_img" / posixpath.basename(rows[0]["path_stra"])
    real = publish.read_package

    def then_changed(*args, **kwargs):
        checked = real(*args, **kwargs)
        how(chart)
        return checked

    monkeypatch.setattr(publish, "read_package", then_changed)
    with pytest.raises(publish.PackageError, match=says):
        publish.publish_package(package, **into(shop))
    assert not [p for p in shop.rglob("*") if p.is_file()], "ni un gráfico, ni un .tmp, ni el catálogo"


def test_what_is_published_is_what_was_checked(publish, tmp_path, shop):
    """Con checked (lo que ya devolvió read_package), el paquete no se vuelve a leer: se publica ese catálogo, y
    sus ficheros sólo si siguen siendo los comprobados."""
    d_result, rows = factory(tmp_path)
    package = package_of(d_result, rows)
    checked = publish.read_package(package, into(shop)["assets"])
    rewrite_catalogue(package, lambda df: df.iloc[:1])   # otra ejecución del paso 7, entretanto
    df = publish.publish_package(package, checked=checked, **into(shop))
    assert len(df) == 4 and len(pd.read_csv(shop / "catalogue" / "catalogue.csv", sep="\t")) == 4

    d_other, others = factory(tmp_path / "otra", [{**ROWS[0], "id_model": "eeee5555"}])
    checked = publish.read_package(package_of(d_other, others), into(shop)["assets"])
    shutil.rmtree(d_other / "package")
    before = {p: p.read_bytes() for p in shop.rglob("*") if p.is_file()}
    with pytest.raises(publish.PackageError, match="gone from the package"):
        publish.publish_package(d_other / "package", checked=checked, **into(shop))
    assert {p: p.read_bytes() for p in shop.rglob("*") if p.is_file()} == before


def test_a_failure_half_way_leaves_the_shop_as_it_was(publish, tmp_path, shop, monkeypatch):
    """Todo se escribe al lado y se renombra al final: si el disco se llena a mitad de los gráficos, la tienda
    sigue con su catálogo y sus gráficos de antes, y sin ningún .tmp."""
    d_result, rows = factory(tmp_path)
    publish.publish_package(package_of(d_result, rows), **into(shop))
    shutil.rmtree(d_result / "package")
    for f in sorted((d_result / "pine_TW_img").iterdir())[:3]:
        f.write_bytes(b"un grafico nuevo")
    package = package_of(d_result, rows[:3])
    before = {p: p.read_bytes() for p in shop.rglob("*") if p.is_file()}
    real, calls = publish.Staged.write, []

    def full(self, dest, data):
        calls.append(dest)
        if len(calls) == 2:
            raise OSError(errno.ENOSPC, "No space left on device")
        return real(self, dest, data)

    monkeypatch.setattr(publish.Staged, "write", full)
    with pytest.raises(OSError):
        publish.publish_package(package, **into(shop))
    assert {p: p.read_bytes() for p in shop.rglob("*") if p.is_file()} == before


def test_the_export_form_forgets_the_release_of_a_package(publish, tmp_path, shop):
    """release.json dice qué ejecución del generador enseña la tienda; un export no la dice, y tras publicarlo
    el release.json de un paquete de antes mentiría: se borra."""
    d_result, rows = factory(tmp_path)
    publish.publish_package(package_of(d_result, rows), **into(shop))
    assert (shop / "catalogue" / "release.json").is_file()
    export = tmp_path / "export.csv"
    pd.DataFrame(rows[:1]).to_csv(export, sep="\t", index=False)
    df = publish.publish(export, d_result, **into(shop))
    assert len(df) == 1 and len(pd.read_csv(shop / "catalogue" / "catalogue.csv", sep="\t")) == 1
    assert not (shop / "catalogue" / "release.json").exists()


def test_the_preview_is_cut_wherever_the_contract_sends_it(tmp_path, shop):
    """La columna de la vista previa se corta vaya a la carpeta que vaya según contract.json: entera, sería el
    script. Una copia de publish.py con un contrato que la manda a static/assets/teasers."""
    folder = tmp_path / "catalogue"
    folder.mkdir()
    for name in ("publish.py", "previews.py"):
        shutil.copy(ROOT / "catalogue" / name, folder / name)
    contract = json.loads(json.dumps(CONTRACT))
    contract["assets"]["pine_path_shadow"] = "teasers"
    (folder / "contract.json").write_text(json.dumps(contract), encoding="utf-8")
    sys.path.insert(0, str(folder))
    try:
        spec = importlib.util.spec_from_file_location("publish_teasers", folder / "publish.py")
        teasers = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(teasers)
    finally:
        sys.path.remove(str(folder))
    assert teasers.PREVIEWS == "teasers" and teasers.REPLACED == ["charts", "teasers"]

    d_result, rows = factory(tmp_path)
    shadow = posixpath.basename(rows[1]["pine_path_shadow"])
    package = package_of(d_result, rows, leave_out={f"pine_TW_hide/{shadow}"})
    (shop / "static" / "assets" / "teasers").mkdir(parents=True)
    (shop / "static" / "assets" / "teasers" / shadow).write_text(script("ya en la tienda, entera"))
    df = teasers.publish_package(package, **into(shop))
    assert all(p.startswith("assets/teasers/") for p in df["pine_path_shadow"])
    published = list((shop / "static" / "assets" / "teasers").iterdir())
    assert len(published) == 4 and not (shop / "static" / "assets" / "previews").exists()
    for f in published:
        text = f.read_text()
        assert text.endswith(sys.modules["previews"].PREVIEW_TAIL) and "x70 = 70" not in text, f.name
