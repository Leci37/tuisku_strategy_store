# -*- coding: utf-8 -*-
"""El catálogo de verdad, la página que se sirve y lo que no puede volver a ser público."""
import csv
import re

from edgefolio.catalogue import Catalogue
from edgefolio.settings import ROOT, STATIC

TEMPLATES = ROOT / "templates"


def test_real_catalogue_loads_one_row_per_strategy():
    cat = Catalogue(ROOT / "catalogue" / "catalogue.csv")
    assert len(cat) > 0
    with open(ROOT / "catalogue" / "catalogue.csv", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    assert len(rows) == len(cat), "catalogue/publish.py deja una fila por estrategia"
    assert "pine_path" not in rows[0], "dónde está el script de pago no se publica"
    for col in ("path_stra", "path_candle", "path_ico", "pine_path_shadow"):
        assert all(r[col].startswith("assets/") and (STATIC / r[col]).is_file() for r in rows[:200]), col


def test_every_page_is_the_shop_on_the_core_shell(client):
    """Una sola plantilla para todas las páginas, dentro de la carcasa del núcleo: la barra con la palabra
    Edgefolio y los huecos de la tienda, el pie, la página a todo lo ancho y el módulo de la página."""
    pages = {}
    for path in ("/", "/thanks?token=X", "/s/AAPL_1Day_1ADX_aaaa1111", "/s/AAPL_1Day_1ADX_aaaa1111/tree"):
        r = client.get(path)
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/html"), path
        html = r.get_data(as_text=True)
        pages[path] = html[html.index("<main"):html.index("</main>")]
        assert 'Edge<span class="app-brand-word-accent">folio</span>' in html, path
        assert 'data-ef-bar="start"' in html and 'data-ef-bar="end"' in html and 'id="app"' in html, path
        assert '<main class="zt-main zt-main-full">' in html and 'src="/static/js/main.js"' in html, path
        assert "/legal/privacidad" in html and "zt-balance" not in html, "sin precios en créditos, sin saldo"
    assert len(set(pages.values())) == 1, "la página lee la ruta en el navegador"


def test_security_headers_on_every_response(client):
    for path in ("/", "/api/config", "/api/strategies?size=1", "/static/favicon.svg", "/no-such-page"):
        h = client.get(path).headers
        assert "script-src 'self'" in h["content-security-policy"], path
        assert h["x-content-type-options"] == "nosniff"
        assert h["referrer-policy"] == "strict-origin-when-cross-origin"


def test_the_browser_no_longer_downloads_the_catalogue(client):
    for path in ("/catalogue/catalogue.csv", "/catalogue/indicators.csv", "/catalogue/bundles.json",
                 "/static/../catalogue/catalogue.csv", "/i18n/ui.json"):
        assert client.get(path).status_code == 404, path


def test_an_unknown_strategy_goes_to_the_shop_and_an_alias_to_its_id(client):
    """Una dirección que no es de ninguna estrategia lleva a la tienda, sin que el navegador pida nada que
    conteste 404; la de un alias (el id de la tienda de antes), a la de su id."""
    from tests.conftest import ROWS, cart_id, strategy_id
    for path in ("/s/NOPE_1Day_XXXX_00000000", "/s/NOPE_1Day_XXXX_00000000/tree"):
        r = client.get(path)
        assert r.status_code == 302 and r.headers["Location"] == "/", path
    alias, sid = cart_id(ROWS[0]), strategy_id(ROWS[0])
    for tail in ("", "/tree"):
        r = client.get(f"/s/{alias}{tail}")
        assert r.status_code == 301 and r.headers["Location"] == f"/s/{sid}{tail}"


def test_no_codes_prices_or_paid_files_in_the_browser_code():
    js = "\n".join(p.read_text(errors="ignore") for p in STATIC.rglob("*.js") if "vendor" not in p.parts)
    html = "\n".join(p.read_text(errors="ignore") for p in TEMPLATES.rglob("*.html"))
    for text in (js, html):
        assert "pine_TW_b" not in text and "raw.githubusercontent.com" not in text
        assert not re.search(r"ZnJlZT|Ym9sc2FfZnJlZQ", text), "códigos de descuento viejos, en base64"
        assert "actions.order.create" not in text, "el importe lo pone el servidor"
        assert "<script>" not in text and not re.search(r"\son[a-z]+=\"", text), "nada de JS en línea (CSP)"
    assert not (STATIC / "assets" / "strategies").exists()


def test_only_cut_previews_are_public():
    paid = {s.private_file for s in Catalogue(ROOT / "catalogue" / "catalogue.csv")}
    pine = list(STATIC.rglob("*.pine"))
    assert pine and all(p.parent == STATIC / "assets" / "previews" for p in pine)
    assert not paid & {p.name for p in STATIC.rglob("*")}, "un script de pago en static/"
    assert not paid & {p.name for p in ROOT.rglob("*.pine") if "data" not in p.parts}, "un script de pago en el repo"


def test_every_public_preview_is_cut():
    # Las vistas previas que hizo la fábrica de las 79 gratis eran el script entero: cualquiera se saltaba
    # el correo de la descarga gratis. Cada vista previa para a 50 líneas de su primer árbol.
    import sys
    sys.path.insert(0, str(ROOT / "catalogue"))
    from previews import PREVIEW_TAIL, PREVIEW_TREE_LINES, cut_preview

    previews = sorted((STATIC / "assets" / "previews").glob("*.pine"))
    assert len(previews) == len(Catalogue(ROOT / "catalogue" / "catalogue.csv"))
    for f in previews:
        text = f.read_text(encoding="utf-8")
        assert text.endswith(PREVIEW_TAIL), f.name
        lines = text.split("\n")
        start = next(i for i, line in enumerate(lines) if line.startswith("decision_tree_"))
        assert len(lines) <= start + PREVIEW_TREE_LINES + PREVIEW_TAIL.count("\n") + 1, f.name
    full = "//@version=5\ndecision_tree_0_X(a)=>\n" + "".join(f"\tif( a <= {i} )\n\t\tret := 1\n" for i in range(80))
    cut = cut_preview(full)
    assert cut.endswith(PREVIEW_TAIL) and cut.count("if( a <=") < 30 and cut_preview(cut) == cut


def test_no_paid_script_is_whole_in_an_archived_design_export():
    """docs/handoff/<fecha>/ guarda cada exportación del diseño tal como llegó. Sus vistas previas son las
    del repositorio cuando se hizo: una de pago entera ahí sería el script que se vende."""
    import sys
    import zipfile
    sys.path.insert(0, str(ROOT / "catalogue"))
    from previews import PREVIEW_TAIL

    cat = Catalogue(ROOT / "catalogue" / "catalogue.csv")
    exports = sorted((ROOT / "docs" / "handoff").glob("*/*.zip"))
    assert exports, "la exportación del 6 de octubre está archivada"
    seen = 0
    for path in exports:
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if not name.endswith(".pine"):
                    continue
                seen += 1
                s = cat.resolve(name.rsplit("/", 1)[-1][:-len(".pine")])
                # una estrategia que ya no está en el catálogo no se vende: nada suyo que proteger
                if s is not None and s.price > 0:
                    assert z.read(name).decode("utf-8").endswith(PREVIEW_TAIL), f"{path.name}: {name} entero"
    assert seen
