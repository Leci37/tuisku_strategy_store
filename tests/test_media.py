# -*- coding: utf-8 -*-
"""Las miniaturas de los gráficos y los cambios de moneda."""
import io
import json

from PIL import Image

from edgefolio import fx, media
from edgefolio.settings import STATIC

# un gráfico del catálogo publicado (el primero que tenga), no uno con nombre fijo: el catálogo cambia
STEM = sorted((STATIC / "assets" / "charts").glob("*_profit.png"))[0].stem


def test_thumbnail_is_a_small_webp_made_once(client, settings):
    r = client.get(f"/thumbs/{STEM}.webp")
    assert r.status_code == 200 and r.headers["content-type"] == "image/webp"
    assert "immutable" in r.headers["cache-control"]
    img = Image.open(io.BytesIO(r.data))
    assert img.format == "WEBP" and img.width == 640
    png = STATIC / "assets" / "charts" / f"{STEM}.png"
    assert len(r.data) < png.stat().st_size / 3
    cached = settings.thumbs_dir / f"{STEM}.webp"
    made = cached.stat().st_mtime_ns
    assert client.get(f"/thumbs/{STEM}.webp").data == r.data and cached.stat().st_mtime_ns == made


def test_only_existing_charts(client, settings):
    for path in ("/thumbs/NOPE_profit.webp", "/thumbs/..%2F..%2Fedgefolio%2Fsettings.webp", "/thumbs/.hidden.webp",
                 f"/thumbs/{STEM}.png.webp", "/thumbs/%2Fetc%2Fpasswd.webp"):
        assert client.get(path).status_code == 404, path
    assert not settings.thumbs_dir.exists() or not any(settings.thumbs_dir.iterdir())


def test_without_pillow_the_png_is_served(client, monkeypatch):
    monkeypatch.setattr(media, "Image", None)
    r = client.get(f"/thumbs/{STEM}.webp")
    assert r.status_code == 307 and r.headers["location"] == f"/static/assets/charts/{STEM}.png"


def test_fx(client, settings):
    body = client.get("/api/fx").json
    assert body["base"] == "USD" and body["source"] == "example"
    assert body["rates"] == {"USD": 1, "EUR": 0.92, "INR": 83.5, "CNY": 7.2, "SAR": 3.75}
    settings.fx_today.write_text(json.dumps({"base": "USD", "date": "2026-10-02", "rates": {"USD": 1, "EUR": 0.85},
                                             "source": "ECB via frankfurter.app"}))
    assert client.get("/api/fx").json["rates"] == {"USD": 1, "EUR": 0.85}, "los del día, si los hay"
    settings.fx_today.unlink()
    settings.fx.unlink()
    assert client.get("/api/fx").json["rates"] == {"USD": 1}


def test_fx_update_adds_the_pegged_riyal(app, settings, monkeypatch):
    class Answer:
        def raise_for_status(self):
            pass

        def json(self):
            return {"amount": 1.0, "base": "USD", "date": "2026-10-02", "rates": {"EUR": 0.85, "INR": 88.7}}

    monkeypatch.setattr(fx.httpx, "get", lambda *a, **k: Answer())
    result = app.test_cli_runner().invoke(args=["edgefolio", "fx-update"])
    assert result.exit_code == 0, result.output
    data = json.loads(settings.fx_today.read_text())
    assert data["date"] == "2026-10-02" and data["rates"] == {"USD": 1, "EUR": 0.85, "INR": 88.7, "SAR": 3.75}
    assert "ECB" in data["source"]
    assert settings.fx.read_text() != settings.fx_today.read_text(), "los de ejemplo del repo no se tocan"


def test_a_chart_published_again_gets_a_new_thumbnail(settings, tmp_path):
    """publish.py reemplaza un gráfico con el mismo nombre; ``python catalogue/publish.py --package`` no sabe dónde
    están las miniaturas para vaciarlas, así que una más vieja que su gráfico se rehace. Y aunque se pidiera
    mientras se publicaba (del gráfico de antes, con el nuevo ya escrito al lado), porque al renombrarlo se le
    pone la hora de ese momento."""
    from dataclasses import replace

    from edgefolio.release import publisher
    settings = replace(settings, static=tmp_path / "static")
    chart = settings.static / "assets" / "charts" / "NEW_1Day_1C00_00000000_profit.png"
    chart.parent.mkdir(parents=True)

    def png(colour) -> bytes:
        out = io.BytesIO()
        Image.new("RGB", (800, 400), colour).save(out, "PNG")
        return out.getvalue()

    def colour_of(path):
        with Image.open(path) as im:
            return im.convert("RGB").getpixel((5, 5))

    chart.write_bytes(png((255, 0, 0)))
    first = media.thumb(settings, chart.stem)
    assert colour_of(first)[0] > 200
    stage = publisher().Staged()
    stage.write(chart, png((0, 0, 255)))                  # escrito al lado, todavía sin renombrar
    first.unlink()
    assert colour_of(media.thumb(settings, chart.stem))[0] > 200, "aún es el de antes"
    stage.commit()
    assert colour_of(media.thumb(settings, chart.stem))[2] > 200, "el nuevo"


def test_a_pruned_chart_keeps_its_thumbnail_until_the_restart(settings, tmp_path):
    """--prune borra un gráfico con la tienda en marcha, que aún lo nombra hasta que se reinicia: su miniatura
    sigue valiendo, no es un error."""
    from dataclasses import replace
    settings = replace(settings, static=tmp_path / "static")
    chart = settings.static / "assets" / "charts" / "OLD_1Day_1C00_00000000_profit.png"
    chart.parent.mkdir(parents=True)
    Image.new("RGB", (800, 400), (0, 128, 0)).save(chart, "PNG")
    made = media.thumb(settings, chart.stem)
    chart.unlink()
    assert media.thumb(settings, chart.stem) == made and made.is_file()
