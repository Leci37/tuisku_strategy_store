# -*- coding: utf-8 -*-
"""Publicar un paquete del generador: ``flask --app app edgefolio import PAQUETE``.

El paso 7 del generador (Leci37/tuisku_strategy_generator) deja en su
d_result/package/ el catálogo, los gráficos, iconos y vistas previas que nombra y un manifest.json con el
sha256 de cada fichero y de cada script completo (los scripts no van en el paquete: están en su
d_result/pine_TW_b/). Importarlo es, por este orden:

1. comprobar el paquete entero (``read_package`` de catalogue/publish.py), una vez, y los scripts: con
   ``scripts``, que cada uno de la lista esté en esa carpeta con su sha256; sin ella, que ya estén en
   STRATEGIES_DIR. Si algo falla no se escribe nada: ni el catálogo, ni un gráfico, ni un script;
2. copiar los scripts de la lista (sólo esos, nunca otro fichero de la carpeta), publicar el catálogo y sus
   ficheros (``publish_package``, que apunta en catalogue/release.json de qué ejecución del generador es)
   y vaciar las miniaturas, que pueden ser de gráficos de antes.

Lo que se publica es lo que se comprobó en el paso 1, no una segunda lectura del paquete: el paso 7 puede
volver a escribirlo mientras tanto (y sus ficheros son enlaces a d_result/, que cambia en su sitio), así que
cada fichero se vuelve a comprobar con su sha256 al copiarlo. Y todo (scripts, static/assets, catálogo y
release.json) se escribe primero al lado de su sitio y sólo se renombra cuando todo se ha escrito
(``Staged`` de publish.py): un fallo a medias, el disco lleno o el paquete que cambió, deja la tienda como estaba.

Sin Flask: el comando (cli.py) sólo pasa la configuración y enseña el resumen.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Optional

from .settings import CATALOGUE

SHOWN = 10   # los nombres que se enseñan en un problema; los demás se cuentan


class Refused(Exception):
    """El paquete o sus scripts no valen; ``problems`` dice todo lo que falla. No se ha escrito nada."""

    def __init__(self, problems):
        self.problems = list(problems)
        super().__init__("\n".join(self.problems))


_publisher = None


def publisher():
    """catalogue/publish.py. Corre también solo (``python catalogue/publish.py``, con pandas y nada más),
    así que no es parte de este paquete: se carga por su ruta, con previews.py a su lado."""
    global _publisher
    if _publisher is None:
        folder = str(CATALOGUE)
        sys.path.insert(0, folder)
        try:
            spec = importlib.util.spec_from_file_location("edgefolio_publish", CATALOGUE / "publish.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            sys.path.remove(folder)
        _publisher = module
    return _publisher


def listed(names) -> str:
    names = list(names)
    more = f" y {len(names) - SHOWN} más" if len(names) > SHOWN else ""
    return ", ".join(names[:SHOWN]) + more


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def regular(path: Path) -> bool:
    """Un fichero de verdad: un enlace simbólico podría llevar a cualquier sitio del disco."""
    return path.is_file() and not path.is_symlink()


def already_there(folder: Path, wanted: dict) -> set:
    """Los scripts de ``wanted`` (nombre → sha256) que ``folder`` ya tiene, y con ese contenido."""
    return {name for name, digest in wanted.items()
            if regular(folder / name) and sha256_of((folder / name).read_bytes()) == digest.lower()}


def check_scripts(wanted: dict, scripts: Path, have: set) -> dict:
    """Los scripts que hay que copiar de ``scripts`` (nombre → ruta), comprobados todos antes de copiar
    ninguno. Sólo los nombres del manifiesto, que read_package ya ha comprobado que son los de las filas
    (sin separadores): nunca otro fichero de la carpeta."""
    if not Path(scripts).is_dir():
        raise Refused([f"{scripts}: no es una carpeta"])
    absent, different, copy = [], [], {}
    for name, digest in sorted(wanted.items()):
        src = Path(scripts) / name
        if not regular(src):
            absent.append(name)
        elif sha256_of(src.read_bytes()) != digest.lower():
            different.append(name)
        elif name not in have:
            copy[name] = src
    problems = []
    if absent:
        problems.append(f"{len(absent)} scripts del manifiesto no están en {scripts}: {listed(absent)}")
    if different:
        problems.append(f"{len(different)} scripts de {scripts} no tienen el sha256 del manifiesto (¿son de otra "
                        f"ejecución del generador?): {listed(different)}")
    if problems:
        raise Refused(problems)
    return copy


def stage_scripts(copy: dict, wanted: dict, target: Path, stage) -> int:
    """Cada uno se escribe al lado, en ``stage``, y se renombra con el resto de la publicación: la tienda nunca
    entrega medio script. Se vuelve a comprobar al leerlo, por si cambió después de la comprobación."""
    for name, src in copy.items():
        data = src.read_bytes()
        if sha256_of(data) != wanted[name].lower():
            raise Refused([f"{name}: cambió en {src.parent} mientras se importaba"])
        stage.write(target / name, data)
    return len(copy)


def clear_thumbs(folder: Path) -> int:
    """Las miniaturas WebP se hacen de los gráficos la primera vez que se piden: tras publicar pueden ser de
    gráficos que ya han cambiado."""
    if not Path(folder).is_dir():
        return 0
    gone = 0
    for f in Path(folder).glob("*.webp"):
        f.unlink()
        gone += 1
    return gone


def bundles_left_out(path, catalogue) -> list:
    """Los lotes de bundles.json que nombran estrategias que ``catalogue`` ya no trae, con cuáles: la tienda
    los deja fuera enteros al arrancar (``Catalogue._bundles``) y sólo lo apunta en el log."""
    if not path or not Path(path).is_file():
        return []
    ids = {"_".join(k) for k in catalogue[["ticker", "interval", "key_techs", "id_model"]].astype(str)
           .itertuples(index=False)}
    out = []
    for b in json.loads(Path(path).read_text(encoding="utf-8")):
        gone = [i for i in b.get("ids", []) if i not in ids]
        if gone:
            out.append(f"{b.get('key')} ({', '.join(gone)})")
    return out


def import_package(package: Path, settings, scripts: Optional[Path] = None, skip_scripts: bool = False,
                   prune: bool = False) -> dict:
    """Comprueba e importa ``package`` en la tienda de ``settings`` (catálogo, static/assets, STRATEGIES_DIR,
    miniaturas). Refused si algo no vale, sin haber escrito nada (o, si falla al renombrar, lo último, diciendo
    cuántos ficheros ya estaban en su sitio). Devuelve el resumen."""
    if scripts is not None and skip_scripts:
        raise ValueError("scripts y skip_scripts no van juntos")
    pub = publisher()
    assets = Path(settings.static) / "assets"
    try:
        checked = pub.read_package(package, assets=assets)
    except pub.ContractError as e:
        raise Refused(e.problems) from e
    manifest = checked[0]
    wanted = manifest["private"]["files"]
    target = Path(settings.strategies_dir)
    have = already_there(target, wanted)
    # los que no están, y los que están con otro contenido: la tienda entregaría ese, el de antes
    outdated = sorted(name for name in wanted if name not in have and regular(target / name))
    absent = sorted(set(wanted) - have - set(outdated))
    copy = {}
    if scripts is not None:
        copy = check_scripts(wanted, Path(scripts), have)
    elif not skip_scripts and (absent or outdated):
        raise Refused([f"{len(absent) + len(outdated)} de los {len(wanted)} scripts del paquete no están en {target} "
                       f"con el sha256 del manifiesto ({len(absent)} no están y {len(outdated)} tienen otro "
                       f"contenido): {listed(absent + outdated)}. Con --scripts <generador>/d_result/pine_TW_b se "
                       "copian (o --skip-scripts para publicar sin ellos)"])

    stage = pub.Staged()
    try:
        copied_scripts = stage_scripts(copy, wanted, target, stage)
        catalogue = pub.publish_package(package, prune=prune, out=Path(settings.catalogue), assets=assets,
                                        checked=checked, stage=stage)
    except Exception as e:
        problems = e.problems if isinstance(e, (Refused, pub.ContractError)) else [f"{type(e).__name__}: {e}"]
        if stage.done:
            problems.append(f"falló a medias: {stage.done} ficheros (los scripts primero, luego static/assets, el "
                            "catálogo y release.json, por ese orden) ya estaban en su sitio; los demás no se han "
                            "tocado. Vuelve a importar el paquete")
        else:
            problems.append("no se ha escrito nada: ni un script, ni static/assets, ni el catálogo")
        raise Refused(problems) from e
    finally:
        stage.discard()
        # lo que ya está en su sitio puede ser un gráfico nuevo con el nombre de uno de antes, aunque algo fallara
        thumbs = clear_thumbs(settings.thumbs_dir) if stage.done else 0
    done = catalogue.attrs["published"]
    return {
        "rows": done["rows"], "files": done["copied"], "cut": done["cut"], "pruned": done["pruned"],
        "kept": done["kept"], "scripts": copied_scripts, "scripts_missing": len(absent) if skip_scripts else 0,
        "scripts_outdated": len(outdated) if skip_scripts else 0, "thumbs": thumbs,
        "bundles_out": bundles_left_out(settings.bundles, catalogue),
        "contract": manifest["contract"], "created": manifest["created"],
        "commit": str(manifest["generator"].get("commit") or ""),
    }
