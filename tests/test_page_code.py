# -*- coding: utf-8 -*-
"""El código de la página después de mezclar una exportación del diseño (tools/design_update.py): sin
marcas de conflicto, cada valor y cada texto que leen las vistas lo da static/js, y cada texto de la tienda
está en los 8 idiomas, con las mismas variables, sin repetir una clave del núcleo. Lo que una mezcla deja
a medias se ve aquí, no en el navegador."""
import json
import re
import sys
from pathlib import Path

import zlecitool_core

from edgefolio.settings import ROOT

sys.path.insert(0, str(ROOT / "tools"))
import design_update  # noqa: E402

TEXTS = json.loads((ROOT / "i18n" / "ui.json").read_text(encoding="utf-8"))
CORE = json.loads((Path(zlecitool_core.__file__).resolve().parent / "i18n" / "common.json").read_text(encoding="utf-8"))
MARK = re.compile(r"^(<{7} |={7}$|>{7} |\|{7} )", re.M)


def text_files():
    for pattern in ("static/js/**/*.js", "static/css/*.css", "templates/**/*.html", "i18n/*.json", "edgefolio/*.py",
                    "tools/*.py", "docs/**/*.md"):
        for path in ROOT.glob(pattern):
            if "vendor" not in path.relative_to(ROOT).parts:
                yield path


def test_no_merge_markers_left():
    marked = [str(p.relative_to(ROOT)) for p in text_files() if MARK.search(p.read_text(encoding="utf-8"))]
    assert not marked, f"conflictos de una mezcla sin resolver: {marked}"


def test_every_value_and_text_the_views_read_is_given():
    given, given_texts = design_update.given_values(ROOT)
    values, texts = design_update.used_values(ROOT / "static" / "js" / "views")
    assert not values - given, f"valores que leen las vistas y static/js no da: {sorted(values - given)}"
    assert not texts - given_texts, f"textos que leen las vistas y no están en TX_KEYS: {sorted(texts - given_texts)}"
    # también lo de cada fila (r?.algo, m?.algo…): un nombre que ningún objeto de static/js tiene
    code = "".join(p.read_text(encoding="utf-8") for p in (ROOT / "static" / "js" / "views").glob("*.js"))
    fields = set(re.findall(r"\b(?!tx\b)[a-z]{1,2}\?\.([A-Za-z_$][\w$]*)", code))
    assert not fields - given, f"campos de fila que static/js no da: {sorted(fields - given)}"


def test_every_text_the_page_reads_exists_in_every_language():
    vals = (ROOT / "static" / "js" / "lib" / "vals.js").read_text(encoding="utf-8")
    keys = re.findall(r"'([^']+)'", re.search(r"TX_KEYS\s*=\s*\[(.*?)\]", vals, re.S).group(1))
    for key in keys:
        entry = TEXTS.get(key) or CORE.get(key)
        assert entry, f"{key}: ni de la tienda ni del núcleo"
        missing = [lang for lang in TEXTS["_languages"] if not entry.get(lang)]
        assert not missing, f"{key}: le faltan {missing}"


def placeholders(text) -> set:
    forms = text.values() if isinstance(text, dict) else [text]  # un plural: {one, other…}
    return set().union(*(set(re.findall(r"\{(\w+)\}", f)) for f in forms))


def test_every_shop_text_is_in_the_8_languages_with_the_same_variables():
    langs = TEXTS["_languages"]
    assert len(langs) == 8
    for key, text in TEXTS.items():
        if key.startswith("_"):
            continue
        assert set(text) >= set(langs), f"{key}: le faltan {sorted(set(langs) - set(text))}"
        found = {lang: placeholders(text[lang]) for lang in langs}
        assert len({frozenset(v) for v in found.values()}) == 1, f"{key}: variables distintas {found}"


def test_no_shop_text_repeats_a_core_key():
    repeated = {k for k in TEXTS if not k.startswith("_")} & {k for k in CORE if not k.startswith("_")}
    assert not repeated, f"claves del núcleo repetidas: {sorted(repeated)}"


def test_the_table_view_uses_its_own_key():
    """viewTable era una clave del núcleo: la vista Tabla de Pro lee viewTableTab (exportación del 6 oct)."""
    assert "viewTableTab" in TEXTS and "pviewTable" not in TEXTS and "viewTable" not in TEXTS
    assert "tx.viewTableTab" in (ROOT / "static" / "js" / "lib" / "vals_shop.js").read_text(encoding="utf-8")


def test_the_page_keeps_its_hooks():
    """Lo que static/js busca en las vistas: el buscador (data-search, la barra del móvil lo enfoca) y el
    carrito (data-sf-cart: la barra del móvil, los avisos encima)."""
    views = ROOT / "static" / "js" / "views"
    app = (ROOT / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert 'data-search="lite"' in (views / "lite.js").read_text(encoding="utf-8")
    assert 'data-search="pro"' in (views / "pro.js").read_text(encoding="utf-8")
    assert "input[data-search]" in app
    for view in ("lite.js", "pro.js"):
        assert "data-sf-cart" in (views / view).read_text(encoding="utf-8")
    assert app.count("[data-sf-cart]") >= 2


def test_the_bottom_bar_takes_its_room_with_the_core_hook():
    """La barra de abajo del móvil (la del diseño) lleva data-zt-bottom (núcleo 0.28): la carcasa mide lo que
    tapa y deja ese sitio. Nada de dejarlo a mano en el CSS (CONTRATO.md del núcleo, §26): con un alto
    escrito, el aviso de cookies y los avisos del núcleo quedaban debajo de la barra (tests/test_phone_bar.py
    lo mira en un navegador)."""
    bar = (ROOT / "static" / "js" / "views" / "phonebar.js").read_text(encoding="utf-8")
    assert re.search(r"<nav data-zt-bottom style=\"position:fixed;[^\"]*bottom:0;", bar)
    css = (ROOT / "static" / "css" / "edgefolio.css").read_text(encoding="utf-8")
    assert not re.search(r"body\.app-shell\s*\{[^}]*padding-bottom", css)


def test_the_dialogs_name_their_crosses_and_mark_where_the_focus_goes():
    """Ninguna × se llama «×» (un lector de pantalla leía «por»): dice qué cierra (``dialogClose``, del núcleo)
    o qué quita (``removeName``). Cada diálogo marca lo suyo principal con ``data-ef-focus``, adonde
    static/js/lib/modal.js lleva el foco al abrirse (tests/test_keyboard.py lo mira en un navegador), y las
    imágenes de lo que se desliza en el recorrido y en el tutorial no se arrastran: con el ratón, arrastrar
    la imagen se comía el deslizamiento (``draggable=${false}``; con "false", Preact lo daba por cierto). El
    botón del ticker en la Tabla de Pro sólo lleva texto en línea: un <div> dentro de un <button> no vale."""
    views = ROOT / "static" / "js" / "views"
    code = {p.name: p.read_text(encoding="utf-8") for p in views.glob("*.js")}
    assert not [name for name, text in code.items() if 'aria-label="×"' in text]
    dialogs = code["dialogs.js"]
    blocks = re.split(r'(?=<div role="dialog")', dialogs)[1:]
    assert len(blocks) == 5 and all("data-ef-focus" in b for b in blocks)
    swipes = re.findall(r"onPointerDown=\$\{v\.(?:tour|inst)PD\}.*?(?=<div style=\"padding:20px 22px 18px)", dialogs, re.S)
    assert len(swipes) == 2
    for swipe in swipes:
        images = re.findall(r"<img [^>]*>", swipe)
        assert images and all("draggable=${false}" in img for img in images), images
    # el ticker de una fila de la Tabla es un botón (el teclado la abre): dentro, sólo texto en línea, sin <div>
    ticker = re.search(r'<button type="button" aria-expanded=\$\{String\(!!r\?\.isOpen\)\}.*?</button>', code["pro.js"], re.S)
    assert ticker and "<div" not in ticker.group(0)


def test_a_toast_keeps_clear_of_an_open_dialog():
    """C13: con un diálogo abierto, el aviso va arriba (``errTop``, ``noticeTop``) y cada velo le deja su sitio
    (``toastRoom``: el alto del aviso, que app.measureDock mide por ``data-ef-toast``), también los diálogos que
    miden 90vh o la ventana entera (Comparar, el pack, el tutorial y la gratis, que en un móvil tumbado se desliza
    por dentro: dos ``max-height``, en vh y, donde se entiende, en dvh, lo que se ve con la barra del navegador). Es
    de la tienda, no del diseño: que no se pierda al mezclar una exportación (tests/test_phone_bar.py y
    tests/test_buying_page.py lo miran en un navegador)."""
    dialogs = (ROOT / "static" / "js" / "views" / "dialogs.js").read_text(encoding="utf-8")
    veils = re.findall(r'<div style="(position:fixed;inset:0;z-index:\d+;[^"]*)">\s*<div role="dialog"', dialogs)
    assert len(veils) == 5 and all(v.endswith("padding:16px;padding-top:calc(16px + ${s(v.toastRoom)})") for v in veils), veils
    heights = re.findall(r"max-height:([^;\"]*vh[^;\"]*)", dialogs)       # lo que mide la ventana, no una imagen
    assert len(heights) == 5 and all(h.endswith(" - ${s(v.toastRoom)})") for h in heights), heights
    free = re.search(r'<div role="dialog" aria-modal="true" aria-label=\$\{v\.tx\?\.freeTitle\} style="([^"]*)"', dialogs)
    assert "max-height:calc(100dvh - 32px - ${s(v.toastRoom)});overflow:auto" in free.group(1), free.group(1)
    toasts = re.findall(r'<div role="(alert|status)" data-ef-toast style="([^"]*)"', dialogs)
    assert [(role, "top:${s(v.%sTop)};bottom:${s(v.%sBottom)}" % ((p,) * 2) in style)
            for (role, style), p in zip(toasts, ("err", "notice"))] == [("alert", True), ("status", True)], toasts
