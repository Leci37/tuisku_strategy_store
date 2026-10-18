# -*- coding: utf-8 -*-
"""Los comandos de la tienda: ``flask --app app edgefolio …``.

    import PAQUETE [--scripts DIR | --skip-scripts] [--prune]
                                publica un paquete del generador: catálogo, ficheros y scripts (release.py)
    restore-scripts [--force]   copia los scripts de pago a la carpeta privada desde la historia del repo
    fx-update                   los cambios de moneda del día (del BCE)
    send-alerts                 los avisos de las favoritas (una vez al día)
    subscribers                 quién ha confirmado las novedades (CSV)

Los scripts de pago no están en el repo, sólo en su historia (``git checkout c3fa796 --
d_result/pine_TW_b``). ``restore-scripts`` los saca de ahí sin tocar la copia de trabajo ni el índice
(``git archive``) y los deja con sus nombres en STRATEGIES_DIR (por defecto, <datos>/edgefolio/strategies):
es lo que hace el lanzador de la familia la primera vez.
"""
from __future__ import annotations

import csv
import io
import os
import subprocess
import sys
import tarfile
from pathlib import Path

import click
from flask import current_app

from .settings import ROOT

SCRIPTS_COMMIT = "c3fa796"
SCRIPTS_PATH = "d_result/pine_TW_b"


def restore(target: Path, commit: str = SCRIPTS_COMMIT, path: str = SCRIPTS_PATH, repo: Path = ROOT,
            force: bool = False) -> int:
    """Copia a ``target`` los .pine de ``path`` en ``commit``; devuelve cuántos. Si ya hay alguno, no
    hace nada (salvo con ``force``) y devuelve -1."""
    target = Path(target)
    if not force and target.is_dir() and any(target.glob("*.pine")):
        return -1
    tar = subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", commit, path],
                         capture_output=True, check=False)
    if tar.returncode != 0:
        raise click.ClickException(f"git archive {commit} {path}: {tar.stderr.decode(errors='replace').strip()}")
    target.mkdir(parents=True, exist_ok=True)
    count = 0
    prefix = path.rstrip("/") + "/"
    with tarfile.open(fileobj=io.BytesIO(tar.stdout)) as archive:
        for member in archive.getmembers():
            name = member.name
            # sólo los ficheros que hay justo dentro de la carpeta, y con su nombre (nada de rutas)
            if not member.isfile() or not name.startswith(prefix) or "/" in name[len(prefix):]:
                continue
            leaf = name[len(prefix):]
            if not leaf.endswith(".pine") or leaf.startswith("."):
                continue
            data = archive.extractfile(member).read()
            tmp = target / (leaf + ".tmp")
            tmp.write_bytes(data)
            os.replace(tmp, target / leaf)
            count += 1
    return count


def register(bp):
    """Los comandos, en el grupo del blueprint: ``flask edgefolio …``."""

    def shop():
        from .shop import of
        return of(current_app)

    @bp.cli.command("import")
    @click.argument("package", type=click.Path(exists=True, file_okay=False, path_type=Path))
    @click.option("--scripts", type=click.Path(exists=True, file_okay=False, path_type=Path),
                  help="La carpeta de los scripts completos (el d_result/pine_TW_b del generador): se copian los "
                       "del manifiesto, comprobado su sha256.")
    @click.option("--skip-scripts", is_flag=True, help="Publicar aunque falten scripts en STRATEGIES_DIR (dice cuántos).")
    @click.option("--prune", is_flag=True, help="Borrar los gráficos y vistas previas que ya no usa ninguna fila.")
    def import_package(package, scripts, skip_scripts, prune):
        """Publica un paquete del generador (su d_result/package/), comprobado entero antes de escribir nada."""
        from . import release
        if scripts and skip_scripts:
            raise click.UsageError("--scripts o --skip-scripts, no los dos")
        try:
            done = release.import_package(package, shop().settings, scripts=scripts, skip_scripts=skip_scripts,
                                          prune=prune)
        except release.Refused as e:
            raise click.ClickException(f"no se importa {package}:\n" + "\n".join(f"  - {p}" for p in e.problems))
        except ModuleNotFoundError as e:
            # publish.py usa pandas, que sólo está en requirements-dev.txt: se importa donde se desarrolla y se
            # despliega lo que deja (el catálogo y static/assets van en el repo; los scripts, a STRATEGIES_DIR)
            if e.name != "pandas":
                raise
            raise click.ClickException("el import necesita pandas, que sólo trae requirements-dev.txt: impórtalo "
                                       "en la máquina de desarrollo (pip install -r requirements-dev.txt) y "
                                       "despliega lo que deja") from e
        click.echo(f"{done['rows']} estrategias del contrato {done['contract']}, de la ejecución del generador del "
                   f"{done['created']} (commit {done['commit'][:12] or 'desconocido'})")
        click.echo(f"{done['files']} ficheros copiados a static/assets ({done['cut']} vistas previas cortadas, "
                   f"{done['pruned']} sin usar borrados); {done['scripts']} scripts copiados; "
                   f"{done['thumbs']} miniaturas borradas")
        if done["kept"]:
            click.echo(f"{len(done['kept'])} logos del paquete son distintos de los de la tienda y se han dejado los de "
                       "la tienda (para tomar el del generador, bórralo de static/assets/icons y vuelve a importar): "
                       f"{release.listed(done['kept'])}")
        if done["bundles_out"]:
            click.echo(f"{len(done['bundles_out'])} lotes de catalogue/bundles.json nombran estrategias que el "
                       "catálogo ya no trae y la tienda los dejará fuera enteros: cámbialos o quítalos: "
                       f"{release.listed(done['bundles_out'])}")
        if skip_scripts:
            click.echo(f"{done['scripts_missing']} scripts del paquete no están en STRATEGIES_DIR: esas estrategias "
                       "no se pueden entregar hasta que estén")
            if done["scripts_outdated"]:
                click.echo(f"{done['scripts_outdated']} scripts de STRATEGIES_DIR no son los del paquete (otro "
                           "sha256): esas estrategias se entregan en su versión de antes hasta que se copien "
                           "(--scripts)")
        # la tienda lee el catálogo al arrancar (shop.load_catalogue): la que está en marcha sigue con el de antes
        click.echo("reinicia la tienda para que sirva este catálogo")

    @bp.cli.command("restore-scripts")
    @click.option("--force", is_flag=True, help="Copiarlos aunque la carpeta ya tenga scripts.")
    @click.option("--commit", default=SCRIPTS_COMMIT, show_default=True, help="El commit que los tiene.")
    def restore_scripts(force, commit):
        """Los scripts de pago, de la historia del repo a la carpeta privada."""
        target = shop().settings.strategies_dir
        n = restore(target, commit=commit, force=force)
        if n < 0:
            click.echo(f"{target} ya tiene scripts: no se toca (--force para copiarlos otra vez)")
            return
        if n == 0:
            raise click.ClickException(f"{commit}:{SCRIPTS_PATH} no tiene ningún .pine")
        click.echo(f"{n} scripts en {target}")

    @bp.cli.command("fx-update")
    def fx_update():
        """Los cambios del día del BCE, para los precios «≈» en la moneda de quien mira."""
        import httpx

        from . import fx
        out = shop().settings.fx_today
        try:
            data = fx.fetch()
        except (httpx.HTTPError, KeyError, ValueError) as e:
            raise click.ClickException(f"sin cambios nuevos ({out.name} sigue como estaba): {e}") from e
        out.parent.mkdir(parents=True, exist_ok=True)
        fx.write(data, out)
        click.echo(f"{out}: {len(data['rates'])} cambios del {data['date']}")

    @bp.cli.command("send-alerts")
    def send_alerts():
        """Los avisos de las favoritas: una vez al día (la primera vez sólo apunta cómo está el catálogo)."""
        from zlecitool_core.http import public_base
        from zlecitool_core.mail import send

        from . import alerts
        base = public_base() or f"http://localhost:{os.environ.get('PORT', '5105')}"
        result = alerts.run(shop(), base, send)
        if result["first_run"]:
            click.echo("primera vez: apuntado cómo está el catálogo; los avisos salen desde la próxima")
        else:
            click.echo(f"{result['changes']} estrategias cambiaron; {result['emails']} correos; "
                       f"{result['unconfirmed']} cuentas sin el correo confirmado")

    @bp.cli.command("subscribers")
    def list_subscribers():
        """Las direcciones que confirmaron las novedades, en CSV (la única lista a la que se puede escribir)."""
        from .free import subscribers
        out = csv.writer(sys.stdout)
        out.writerow(["email", "lang", "source", "consent_at", "confirmed_at"])
        for row in subscribers():
            out.writerow([row["email"], row["lang"], row["source"], row["consent_at"].isoformat(),
                          row["confirmed_at"].isoformat()])
