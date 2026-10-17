# -*- coding: utf-8 -*-
"""Las convenciones del repo que nadie revisa a ojo hasta que fallan."""
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = "zlecitool-core"


def _lines(name):
    text = (ROOT / name).read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]


def test_production_pins_the_core_to_a_version():
    pinned = [line for line in _lines("requirements.txt") if line.startswith(CORE)]
    assert len(pinned) == 1 and "@ git+https://github.com/Leci37/zlecitool-core@v" in pinned[0], (
        "requirements.txt tiene que fijar el núcleo a una etiqueta vX.Y.Z")


def test_development_uses_the_core_beside_this_repo():
    assert any(line.startswith("-e ../zlecitool-core") for line in _lines("requirements-dev.txt"))


def test_dev_requirements_cover_production():
    own = [line.split("#")[0].strip() for line in _lines("requirements.txt") if not line.startswith(CORE)]
    missing = sorted(set(own) - {line.split("#")[0].strip() for line in _lines("requirements-dev.txt")})
    assert not missing, f"requirements-dev.txt no tiene {missing}: en desarrollo faltarían"


def test_no_fastapi_left():
    reqs = "\n".join(_lines("requirements.txt") + _lines("requirements-dev.txt")).lower()
    assert "fastapi" not in reqs and "uvicorn" not in reqs
    assert not (ROOT / "api").exists() and not (ROOT / "storefront").exists()


def test_production_runs_gunicorn_with_its_config(monkeypatch):
    assert "-c gunicorn.conf.py" in (ROOT / "Procfile").read_text(encoding="utf-8")
    for name in ("WEB_CONCURRENCY", "GUNICORN_THREADS", "GUNICORN_TIMEOUT", "GUNICORN_MAX_REQUESTS", "PORT"):
        monkeypatch.delenv(name, raising=False)
    conf = runpy.run_path(str(ROOT / "gunicorn.conf.py"))
    assert conf["worker_class"] == "gthread" and conf["bind"] == "0.0.0.0:5105"


def test_gunicorn_does_not_preload_the_app(monkeypatch):
    """Con ``preload_app``, la app arrancaría en el proceso padre, y su reloj de las tareas (núcleo 0.25) con
    ella: sus hilos no pasan de un fork, y ningún proceso que atiende serviría «Tus datos» (núcleo 0.30) ni
    latiría."""
    for name in ("WEB_CONCURRENCY", "GUNICORN_THREADS", "GUNICORN_TIMEOUT", "GUNICORN_MAX_REQUESTS", "PORT"):
        monkeypatch.delenv(name, raising=False)
    assert not runpy.run_path(str(ROOT / "gunicorn.conf.py")).get("preload_app")
    assert "--preload" not in (ROOT / "Procfile").read_text(encoding="utf-8")


def test_the_local_port_is_the_launchers():
    assert 'os.environ.get("PORT", "5105")' in (ROOT / "app.py").read_text(encoding="utf-8")
    assert "PORT=5105" in (ROOT / ".env.example").read_text(encoding="utf-8")
