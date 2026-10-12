# -*- coding: utf-8 -*-
"""tools/design_update.py, con una exportación hecha de docs/design: la que llegó la última vez.

Si una exportación igual que la anterior cambiara algo, la mezcla a tres estaría tocando lo que la tienda
adaptó; y un cambio del diseño tiene que llegar a la vista ya adaptada. Las dos, sin escribir nada (sin
--apply): la prueba no toca el repo.

Desde la de octubre la exportación trae también prototype/vendor/ (React, ReactDOM, Babel y Font Awesome,
para abrir la maqueta sin internet), más notas (FLUJO_USUARIO.md, STATUS.md, docs/USER-FLOW-v7.md) y cosas
que la tienda no usa (versions/, offline/, prototype/brand/, docs/img/, texts.json, MANIFEST.md). Y
docs/design/serve.py, que la abre, tiene que encontrar el núcleo instalado.
"""
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESIGN = ROOT / "docs" / "design"
STOREFRONT = "Storefront v7.dc.html"
REACT = "vendor/react/react.production.min.js"
# Lo de docs/design/ que es de la tienda y no viene en el prototype/ de la exportación: el texto de las
# notas, las notas mezcladas con lo suyo y el servidor de la maqueta.
SHOP_OWN = {"handoff", "HANDOFF.md", "PR_DESCRIPTION.md", "STATUS.md", "FLUJO_USUARIO.md", "README.md", "serve.py",
            "__pycache__"}

sys.path.insert(0, str(ROOT / "tools"))
import design_update  # noqa: E402


def _export(tmp_path, change=None, files=None):
    """El zip como lo exporta Claude Design: prototype/ con la maqueta y, fuera, sus notas (docs/design/handoff/).
    ``files``: lo que se añade o se cambia (ruta en el zip -> texto o bytes)."""
    src = tmp_path / "export"
    shutil.copytree(DESIGN, src / "prototype",
                    ignore=lambda folder, names: SHOP_OWN & set(names) if Path(folder) == DESIGN else ())
    shutil.copytree(DESIGN / "handoff", src, dirs_exist_ok=True)
    if change:
        page = src / "prototype" / STOREFRONT
        old, new = change
        text = page.read_text(encoding="utf-8")
        assert text.count(old) == 1
        page.write_text(text.replace(old, new), encoding="utf-8")
    for rel, data in (files or {}).items():
        path = src / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
    out = tmp_path / "export.zip"
    with zipfile.ZipFile(out, "w") as z:
        for f in sorted(src.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(src).as_posix())
    return out


def _run(zip_path):
    return subprocess.run([sys.executable, "tools/design_update.py", str(zip_path)], cwd=ROOT,
                          capture_output=True, text=True, timeout=300)


def _lite_style():
    """Un estilo que sólo está una vez en la maqueta y una vez en la vista de Lite."""
    page = (DESIGN / STOREFRONT).read_text(encoding="utf-8")
    view = (ROOT / "static" / "js" / "views" / "lite.js").read_text(encoding="utf-8")
    style = next((s for s in re.findall(r'style="([^"]{30,80})"', view)
                  if page.count(s) == 1 and view.count(s) == 1), None)
    assert style, "no hay un estilo de Lite que esté una sola vez en la maqueta y en la vista"
    return style


def test_an_export_like_the_last_one_changes_nothing(tmp_path):
    done = _run(_export(tmp_path))
    assert done.returncode == 0, done.stdout + done.stderr
    assert "Cambiaría: 0 ficheros" in done.stdout, done.stdout


def test_a_design_change_reaches_the_adapted_view(tmp_path):
    # Cambiar en el diseño un estilo de Lite tiene que llegar a lite.js aunque la tienda haya cambiado lo de
    # alrededor.
    lite = ROOT / "static" / "js" / "views" / "lite.js"
    style = _lite_style()
    before = lite.read_bytes()

    done = _run(_export(tmp_path, change=(style, style + ";outline:0")))

    assert done.returncode == 0, done.stdout + done.stderr
    assert "static/js/views/lite.js" in done.stdout, done.stdout
    assert lite.read_bytes() == before, "sin --apply no se escribe nada"


def test_an_october_export_like_the_last_one_changes_nothing(tmp_path, monkeypatch):
    # La de octubre, igual que docs/design: vendor/ en prototype/, las notas nuevas fuera y lo que no se usa.
    # Una versión anterior de la plantilla en versions/ (con un estilo de Lite distinto) no se convierte: si
    # se mezclara, cambiaría lite.js.
    assert (DESIGN / REACT).is_file()
    for rel in ("FLUJO_USUARIO.md", "STATUS.md", "docs/USER-FLOW-v7.md"):
        assert (DESIGN / "handoff" / rel).is_file(), rel
    style = _lite_style()
    old = (DESIGN / STOREFRONT).read_text(encoding="utf-8").replace(style, style + ";outline:0")
    zip_path = _export(tmp_path, files={
        "versions/Storefront v6.dc.html": old,
        "offline/storefront-offline.html": "<!doctype html><title>Storefront v7</title>\n",
        "prototype/brand/tuisku-logo-96.png": b"\x89PNG\r\n",
        "prototype/brand/tuisku-logo-192.png": b"\x89PNG\r\n",
        "docs/img/shop_cart.png": b"\x89PNG\r\n",
        "texts.json": "{}\n",
        "MANIFEST.md": "# MANIFEST\n",
    })
    converted = []
    convert = design_update.dc2htm.convert
    monkeypatch.setattr(design_update.dc2htm, "convert",
                        lambda src, *a, **k: converted.append(Path(src)) or convert(src, *a, **k))

    plan = design_update.make_plan(zip_path, ROOT)

    assert sorted(plan.writes) == [], plan.notes
    assert not plan.problems and not plan.conflicts, plan.problems
    assert sorted(p.name for p in converted) == sorted(["Strategy Tree.dc.html", STOREFRONT] * 2)
    assert not [p for p in converted if "versions" in p.parts], converted
    # Lo que no se usa, una nota por carpeta (los sueltos de la raíz, juntos); vendor/ sí se usa.
    unused = sorted(n.split(": ")[0] for n in plan.notes if "no se usa" in n)
    assert unused == ["MANIFEST.md, texts.json", "docs/img/ (1 fichero)", "offline/ (1 fichero)",
                      "prototype/brand/ (2 ficheros)", "versions/ (1 fichero)"], plan.notes
    assert not [n for n in plan.notes if "vendor" in n], plan.notes


def test_a_new_vendor_copy_reaches_docs_design(tmp_path):
    before = (DESIGN / REACT).read_bytes()
    newer = before + b"\n/* React 18.3.2 */\n"

    plan = design_update.make_plan(_export(tmp_path, files={f"prototype/{REACT}": newer}), ROOT)

    assert sorted(plan.writes) == [f"docs/design/{REACT}"]
    assert plan.writes[f"docs/design/{REACT}"] == newer
    assert not plan.problems and not plan.conflicts, plan.problems
    assert (DESIGN / REACT).read_bytes() == before, "sin --apply no se escribe nada"


def test_a_note_the_shop_does_not_have_yet_comes_whole(tmp_path):
    # Una tienda sin sus copias de las notas que van a docs/ (ni su flujo, docs/design/FLUJO_USUARIO.md) y sin
    # STATUS.md (ni su texto en handoff/): a tres contra un texto vacío saldrían vacías; entran enteras, y su
    # texto, a docs/design/handoff/.
    root = tmp_path / "shop"
    shutil.copytree(DESIGN, root / "docs" / "design")
    (root / "docs" / "design" / "FLUJO_USUARIO.md").unlink()
    (root / "docs" / "design" / "STATUS.md").unlink()
    (root / "docs" / "design" / "handoff" / "STATUS.md").unlink()
    export = design_update.open_export(_export(tmp_path), tmp_path / "zip")
    plan = design_update.Plan()

    design_update.plan_files(plan, root, export)

    new = {rel: dest for rel, dest in design_update.NOTES.items() if not (root / dest).is_file()}
    assert sorted(new.values()) == ["docs/IMPLEMENTATION-v7.md", "docs/USER-FLOW-v7.md", "docs/catalogue-updates.md",
                                    "docs/design/FLUJO_USUARIO.md", "docs/design/STATUS.md"]
    for rel, dest in new.items():
        text = (export / rel).read_bytes()
        assert text.strip() and plan.writes[dest] == text, dest
        assert f"{dest}: nuevo" in "\n".join(plan.notes), plan.notes
    assert plan.writes["docs/design/handoff/STATUS.md"] == (export / "STATUS.md").read_bytes()
    assert sorted(plan.writes) == sorted([*new.values(), "docs/design/handoff/STATUS.md"])
    assert not plan.conflicts


def test_serve_finds_the_installed_core_with_its_folder_first_on_the_path():
    # python docs/design/serve.py pone docs/design (absoluta) la primera en sys.path, y su zlecitool_core/ (la
    # copia de los textos del núcleo, sin __init__.py) taparía el núcleo instalado: la maqueta, sin letras.
    code = (
        "import json, runpy, sys\n"
        f"sys.path.insert(0, {str(DESIGN)!r})\n"
        f"g = runpy.run_path({str(DESIGN / 'serve.py')!r}, run_name='serve')\n"
        "h = g['Handler'].__new__(g['Handler'])\n"
        "h.directory = str(g['HERE'])\n"
        "print(json.dumps([str(g['FONTS']), h.translate_path('/vendor/react/react.production.min.js'),\n"
        "                  h.translate_path('/storefront/assets/icons/TW_ICO.svg')]))\n"
    )
    done = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    fonts, vendor, icon = map(Path, json.loads(done.stdout))
    assert (fonts / "Ubuntu-400-latin.woff2").is_file(), fonts
    assert vendor == DESIGN / REACT and vendor.is_file()
    assert icon == ROOT / "static" / "assets" / "icons" / "TW_ICO.svg" and icon.is_file()
