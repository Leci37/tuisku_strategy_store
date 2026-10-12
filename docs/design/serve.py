"""Open the reference design in a browser.

    python docs/design/serve.py          # then open http://localhost:8765/Storefront%20v7.dc.html

The mock-up loads its charts, icons and previews from storefront/assets/... and its fonts from the
core's path; this serves the first from the tool's static/ (where storefront/ went when the shop became a
zlecitool tool) and the fonts from the installed zlecitool-core, so nothing is copied here.
"""
import http.server
import sys
from urllib.parse import unquote
from functools import partial
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATIC = HERE.parent.parent / "static"
# Python puts this folder first on sys.path, and its zlecitool_core/ (the mock-up's copy of the core's
# texts) would hide the installed core: the fonts are looked up without it.
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != HERE]
try:
    import zlecitool_core
    FONTS = Path(zlecitool_core.__file__).resolve().parent / "ui" / "static" / "fonts"
except (ImportError, TypeError):  # without the core the mock-up falls back to the system font
    FONTS = HERE / "-"
ROUTES = {"/storefront/": STATIC, "/zlecitool_core/ui/static/fonts/": FONTS}


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        for prefix, folder in ROUTES.items():
            if path.startswith(prefix):
                target = (folder / unquote(path[len(prefix):].split("?")[0])).resolve()
                return str(target) if target.is_relative_to(folder.resolve()) else str(HERE / "-")
        return super().translate_path(path)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print(f"http://localhost:{port}/Storefront%20v7.dc.html")
    http.server.ThreadingHTTPServer(("", port), partial(Handler, directory=str(HERE))).serve_forever()
