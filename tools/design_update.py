# -*- coding: utf-8 -*-
"""Aplicar una exportación nueva del diseño (el zip de Claude Design) a la tienda.

    python tools/design_update.py RUTA/AL/ZIP            # dice qué cambiaría; no escribe nada
    python tools/design_update.py RUTA/AL/ZIP --apply    # lo aplica (con la copia de trabajo limpia)

docs/design/ es la exportación anterior tal como llegó (y docs/design/handoff/, el texto de sus notas): es la
base de una mezcla a tres. Lo que hace:

1. abre el zip en una carpeta temporal (rechaza rutas que salen de él y enlaces; nunca ejecuta nada de
   dentro) y busca su prototype/ con las plantillas .dc.html; las de versions/ (versiones anteriores y
   bocetos) no se convierten ni se guardan;
2. compara sus ficheros con docs/design/ y enseña la sección «What changed since the previous export» de
   su README; de lo que trae y no se usa (versions/, offline/, prototype/brand/, docs/img/, texts.json,
   MANIFEST.md...) da una nota por carpeta, no una por fichero;
3. convierte con tools/dc2htm.py la plantilla anterior y la nueva, y las mezcla a tres en static/js/views/
   (git merge-file): lo que cambió el diseño entra, lo que cambió la tienda se queda, y donde los dos
   tocaron lo mismo queda el conflicto marcado (<<<<<<<) y contado;
4. rehace en static/css/edgefolio.css las clases de style-hover y style-focus (también a tres);
5. mezcla a tres, idioma por idioma, los textos de i18n/storefront.ui.json en i18n/ui.json: una clave nueva
   tiene que venir en todos los idiomas de la tienda, con las mismas variables, y no puede ser una del
   núcleo;
6. dice qué valores nuevos usan las vistas (v.algo, v.tx.algo) que static/js/ todavía no da: es la
   funcionalidad que hay que construir;
7. con --apply, además, deja la exportación nueva en docs/design/: las plantillas, support.js, sus textos
   y vendor/ (React, ReactDOM y Babel, que carga support.js, y el Font Awesome de las plantillas: la
   maqueta abre sin internet); el texto de sus notas, en docs/design/handoff/; y mezcla a tres esas notas
   en docs/design/HANDOFF.md, docs/design/PR_DESCRIPTION.md, docs/design/STATUS.md,
   docs/design/FLUJO_USUARIO.md, docs/IMPLEMENTATION-v7.md, docs/USER-FLOW-v7.md y docs/catalogue-updates.md.
   Una nota que la tienda aún no tiene entra entera.

Sale con 0 si todo entra limpio, con 1 si queda un conflicto o algo por decidir (lo dice), con 2 si el zip
no vale. Después: pytest, python tools/screenshots.py y comparar con python docs/design/serve.py.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dc2htm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Lo del prototype/ del zip que se guarda en docs/design/ (las plantillas y lo que cargan: vendor/ son las
# copias de React, ReactDOM, Babel y Font Awesome, que support.js y las plantillas ya no piden a internet)...
COPIED = ("Storefront v7.dc.html", "Strategy Tree.dc.html", "support.js", "i18n/", "trees/", "zlecitool_core/i18n/",
          "vendor/")
# ...y lo que es de la maqueta: sus gráficos, iconos y vistas previas de muestra y las letras del núcleo. La
# tienda tiene los suyos (static/assets/, el núcleo): de aquí sólo se avisa de lo que la tienda no tiene.
MOCKUP = ("storefront/", "zlecitool_core/ui/")
# Las notas del diseño (ruta en el zip -> la copia de la tienda, que lleva cambios propios).
NOTES = {"README.md": "docs/design/HANDOFF.md", "PR_DESCRIPTION.md": "docs/design/PR_DESCRIPTION.md",
         "STATUS.md": "docs/design/STATUS.md", "FLUJO_USUARIO.md": "docs/design/FLUJO_USUARIO.md",
         "docs/IMPLEMENTATION-v7.md": "docs/IMPLEMENTATION-v7.md", "docs/USER-FLOW-v7.md": "docs/USER-FLOW-v7.md",
         "docs/catalogue-updates.md": "docs/catalogue-updates.md"}
HANDOFF = "docs/design/handoff"         # esas notas tal como llegaron la última vez: la base de su mezcla
TEXTS_IN_EXPORT = "i18n/storefront.ui.json"
SHELL_MODULES = {"footer"}              # lo dibuja la carcasa del núcleo: la tienda no lo usa
HOVER = re.compile(r"^\.(sf|tr)-[\w-]+?\d+:")
CHANGES = re.compile(r"^(#+)\s*what changed since the previous export", re.I)
PLACEHOLDER = re.compile(r"\{(\w+)\}")


class BadExport(Exception):
    """El zip no es una exportación del diseño que se pueda leer."""


class Plan:
    """Lo que cambiaría: ficheros (ruta relativa -> contenido nuevo), lo que hay que saber y lo que hay que
    decidir (problems: con alguno, el comando sale con 1)."""

    def __init__(self):
        self.writes = {}
        self.notes, self.problems = [], []
        self.conflicts = {}                 # ruta -> conflictos marcados en ella
        self.changelog = ""

    def write(self, rel: str, text, root: Path):
        data = text.encode("utf-8") if isinstance(text, str) else text
        path = root / rel
        if not path.is_file() or path.read_bytes() != data:
            self.writes[rel] = data


# ---------------------------------------------------------------- el zip

def open_export(zip_path: Path, into: Path) -> Path:
    """Extrae el zip en ``into`` y da la carpeta de la exportación (la que tiene prototype/)."""
    try:
        archive = zipfile.ZipFile(zip_path)
    except (OSError, zipfile.BadZipFile) as e:
        raise BadExport(f"{zip_path}: no es un zip ({e})")
    with archive:
        for info in archive.infolist():
            name = info.filename
            parts = PurePosixPath(name).parts
            if name.startswith("/") or "\\" in name or ".." in parts or re.match(r"^[A-Za-z]:", name):
                raise BadExport(f"{name}: una ruta que sale del zip")
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise BadExport(f"{name}: un enlace simbólico")
        archive.extractall(into)
    roots = {p.parent.parent for p in into.rglob("prototype/*.dc.html") if not skipped(p.relative_to(into))}
    if len(roots) != 1:
        raise BadExport("el zip tiene que traer una exportación, con su prototype/ y las plantillas .dc.html "
                        f"dentro ({len(roots)} encontradas)")
    return roots.pop()


def skipped(rel: Path) -> bool:
    """Lo que añade un Mac al comprimir (__MACOSX/, ._algo, .DS_Store)."""
    return any(p == "__MACOSX" or p.startswith("._") or p == ".DS_Store" for p in rel.parts)


def files_of(folder: Path) -> list:
    if not folder.is_dir():
        return []
    return sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*")
                  if p.is_file() and not skipped(p.relative_to(folder)))


def changelog_of(readme: Path) -> str:
    """La sección «What changed since the previous export» del README de la exportación."""
    if not readme.is_file():
        return ""
    out, level = [], None
    for line in readme.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^(#+)\s", line)
        if level is None:
            m = CHANGES.match(line)
            if m:
                level = len(m.group(1))
                out.append(line)
        elif heading and len(heading.group(1)) <= level:
            break
        else:
            out.append(line)
    return "\n".join(out).strip()


# ---------------------------------------------------------------- mezclar

def merge3(ours: str, base: str, theirs: str) -> tuple:
    """(texto, conflictos) de git merge-file: lo de la tienda, la exportación anterior y la nueva."""
    with tempfile.TemporaryDirectory() as d:
        paths = []
        for name, text in (("tienda", ours), ("anterior", base), ("nuevo", theirs)):
            p = Path(d) / name
            p.write_text(text, encoding="utf-8")
            paths.append(str(p))
        r = subprocess.run(["git", "merge-file", "-p", "-L", "tienda", "-L", "diseño anterior", "-L", "diseño nuevo",
                            *paths], capture_output=True)
    if r.returncode < 0 or r.returncode > 127:
        raise RuntimeError(f"git merge-file: {r.stderr.decode(errors='replace')}")
    return r.stdout.decode("utf-8"), r.returncode


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def plan_views(plan: Plan, root: Path, export: Path, work: Path) -> dict:
    """Mezcla cada módulo de cada plantilla en static/js/views; da {plantilla: (anteriores, nuevos)}."""
    converted = {}
    for name, spec in dc2htm.SPLITS.items():
        new_src = export / "prototype" / name
        old_src = root / "docs" / "design" / name
        if not new_src.is_file():
            plan.problems.append(f"la plantilla {name} no viene en la exportación: si ha cambiado de nombre, "
                                 "que vuelva al de antes (o cambia SPLITS en tools/dc2htm.py)")
            continue
        base_dir, new_dir = work / "base" / spec["prefix"], work / "new" / spec["prefix"]
        try:
            dc2htm.convert(old_src, base_dir, spec=spec, name=name)
            dc2htm.convert(new_src, new_dir, spec=spec, name=name)
        except dc2htm.UnknownElement as e:
            plan.problems.append(str(e))
            continue
        converted[name] = (base_dir, new_dir)
        views = root / spec["views"]
        for mod in sorted({p.stem for p in base_dir.glob("*.js")} | {p.stem for p in new_dir.glob("*.js")}):
            rel = f"{spec['views']}/{mod}.js"
            base, theirs = read(base_dir / f"{mod}.js"), read(new_dir / f"{mod}.js")
            if not (views / f"{mod}.js").is_file():
                if mod in SHELL_MODULES or base:
                    if base != theirs:
                        plan.problems.append(f"el diseño cambió {mod}, que la tienda no usa"
                                             + (" (lo dibuja la carcasa del núcleo)" if mod in SHELL_MODULES else "")
                                             + ": míralo a mano")
                    continue
                plan.notes.append(f"{rel}: módulo nuevo del diseño")
                plan.write(rel, theirs, root)
                continue
            if not theirs:
                plan.problems.append(f"el diseño ya no tiene el módulo {mod}; la tienda lo sigue teniendo ({rel})")
                continue
            merged, conflicts = merge3(read(views / f"{mod}.js"), base, theirs)
            plan.write(rel, merged, root)
            if conflicts:
                plan.conflicts[rel] = conflicts
    return converted


def plan_hover(plan: Plan, root: Path, converted: dict):
    """Las clases de style-hover y style-focus del diseño, en su bloque de static/css/edgefolio.css."""
    if len(converted) != len(dc2htm.SPLITS):
        return
    rel = "static/css/edgefolio.css"
    css = read(root / rel).splitlines(keepends=True)

    def block(which):
        return "".join(read(dirs[which] / f"{spec['prefix']}.hover.css")
                       for name, spec in dc2htm.SPLITS.items() for dirs in [dict(zip(("base", "new"), converted[name]))])
    base, theirs = block("base"), block("new")
    if base == theirs:
        return
    rows = [i for i, line in enumerate(css) if HOVER.match(line)]
    if rows and rows != list(range(rows[0], rows[-1] + 1)):
        plan.problems.append(f"{rel}: las clases sf-/tr- no están juntas; no se tocan")
        return
    start, end = (rows[0], rows[-1] + 1) if rows else (len(css), len(css))
    merged, conflicts = merge3("".join(css[start:end]), base, theirs)
    plan.write(rel, "".join(css[:start]) + merged + "".join(css[end:]), root)
    if conflicts:
        plan.conflicts[rel] = conflicts


def core_keys() -> set:
    """Las claves del diccionario del núcleo instalado: una de la tienda no puede repetirlas."""
    try:
        import zlecitool_core
    except ImportError:
        return set()
    path = Path(zlecitool_core.__file__).resolve().parent / "i18n" / "common.json"
    if not path.is_file():
        return set()
    return {k for k in json.loads(path.read_text(encoding="utf-8")) if not k.startswith("_")}


def plan_texts(plan: Plan, root: Path, export: Path):
    """Los textos de la exportación, mezclados a tres en i18n/ui.json, idioma por idioma."""
    rel = "i18n/ui.json"
    new_path = export / "prototype" / TEXTS_IN_EXPORT
    if not new_path.is_file():
        plan.problems.append(f"la exportación no trae prototype/{TEXTS_IN_EXPORT}")
        return
    ours = json.loads(read(root / rel))
    base = json.loads(read(root / "docs" / "design" / TEXTS_IN_EXPORT) or "{}")
    theirs = json.loads(new_path.read_text(encoding="utf-8"))
    langs = ours.get("_languages") or ["en"]
    core = core_keys()
    if not core:
        plan.notes.append("sin el núcleo instalado no se comprueba que las claves nuevas no sean suyas")
    for key, text in theirs.items():
        if key.startswith("_") or not isinstance(text, dict):
            continue
        before = base.get(key)
        if key in core and key not in ours:
            if before != text:
                plan.problems.append(f"texto {key}: es del núcleo (la tienda usa el suyo); un cambio es para el núcleo")
            continue
        if key not in ours:
            if before is not None:
                if before != text:
                    plan.problems.append(f"texto {key}: el diseño lo cambió, y la tienda ya no lo tiene")
                continue
            missing = [lang for lang in langs if lang not in text]
            if missing:
                plan.problems.append(f"texto nuevo {key}: le faltan {', '.join(missing)}")
            vars_ = {lang: set(PLACEHOLDER.findall(json.dumps(t))) for lang, t in text.items()}
            if len({frozenset(v) for v in vars_.values()}) > 1:
                plan.problems.append(f"texto nuevo {key}: no tiene las mismas variables en todos los idiomas")
            ours[key] = text
            plan.notes.append(f"texto nuevo: {key}")
            continue
        mine = ours[key]
        for lang in sorted(set(text) | set(before or {}) | set(mine)):
            t, b, o = text.get(lang), (before or {}).get(lang), mine.get(lang)
            if t == b or t is None or o == t:
                continue
            if o == b:
                mine[lang] = t
            else:
                plan.problems.append(f"texto {key} ({lang}): la tienda y el diseño lo cambiaron distinto; se "
                                     "queda el de la tienda")
    for key in base:
        if not key.startswith("_") and key not in theirs and key in ours:
            plan.notes.append(f"texto {key}: el diseño ya no lo usa; la tienda lo conserva (quítalo si nada lo usa)")
    plan.write(rel, json.dumps(ours, ensure_ascii=False, indent=2) + "\n", root)


NAME = r"[A-Za-z_$][\w$]*"


def used_values(folder: Path) -> tuple:
    """(valores, textos) que leen las vistas de ``folder``: v.algo y v.tx.algo."""
    code = "".join(read(p) for p in folder.glob("*.js"))
    return (set(re.findall(rf"\bv\.({NAME})", code)) - {"tx"}, set(re.findall(rf"\bv\.tx\?\.({NAME})", code)))


def given_values(root: Path) -> tuple:
    """(valores, textos) que da static/js/: las claves de sus objetos (también las cortas) y TX_KEYS."""
    code = "".join(read(p) for p in sorted((root / "static" / "js").rglob("*.js"))
                   if "views" not in p.relative_to(root / "static" / "js").parts)
    keys = set(re.findall(rf"(?<![\w$.?])({NAME})\s*:(?!:)", code))
    keys |= set(re.findall(rf"[{{,]\s*({NAME})\s*(?=[,}}])", code))
    texts = set(re.findall(rf"\btx\.({NAME})\s*=", code))
    m = re.search(r"TX_KEYS\s*=\s*\[(.*?)\]", code, re.S)
    if m:
        texts |= set(re.findall(r"'([^']+)'", m.group(1)))
    return keys, texts


def plan_values(plan: Plan, root: Path, converted: dict):
    """Los valores que el diseño nuevo usa y antes no, y que static/js/ aún no da."""
    keys, texts = given_values(root)
    for name, (base_dir, new_dir) in converted.items():
        old_v, old_t = used_values(base_dir)
        new_v, new_t = used_values(new_dir)
        for v in sorted(new_v - old_v - keys):
            plan.problems.append(f"{name}: valor nuevo v.{v}, que static/js/ no da todavía (funcionalidad por hacer)")
        for t in sorted(new_t - old_t - texts):
            plan.problems.append(f"{name}: texto nuevo v.tx.{t}, que la página no lee todavía (añádelo a TX_KEYS en "
                                 "static/js/lib/vals.js)")


def plan_files(plan: Plan, root: Path, export: Path):
    """Las plantillas y lo que cargan, a docs/design/; las notas, a tres; y qué trae el zip que no se usa."""
    design = root / "docs" / "design"
    proto = export / "prototype"
    unused = {}                         # ruta en el zip -> por qué no se usa
    for rel in files_of(proto):
        if rel.startswith(COPIED) or rel in COPIED:
            plan.write(f"docs/design/{rel}", (proto / rel).read_bytes(), root)
        elif rel.startswith(MOCKUP):
            shop = root / "static" / rel[len("storefront/"):] if rel.startswith("storefront/") else None
            if shop is not None and not shop.is_file():
                plan.notes.append(f"la maqueta usa prototype/{rel}, que la tienda no tiene en static/: si es un "
                                  "icono o una imagen nueva del diseño, cópialo")
        else:
            unused[f"prototype/{rel}"] = "de prototype/ sólo se guardan las plantillas y lo que cargan"
    for rel in files_of(design):
        if (rel.startswith(COPIED) or rel in COPIED) and not (proto / rel).is_file():
            plan.notes.append(f"docs/design/{rel}: ya no viene en la exportación; se deja")
    everything = files_of(export)
    for rel in everything:
        if not rel.startswith("prototype/") and rel not in NOTES:
            unused[rel] = "de fuera de prototype/ sólo se guardan las notas"
    note_unused(plan, unused, everything)
    for rel, dest in NOTES.items():
        new = export / rel
        if not new.is_file():
            plan.notes.append(f"{rel}: no viene en la exportación")
            continue
        theirs = new.read_text(encoding="utf-8")
        plan.write(f"{HANDOFF}/{rel}", theirs, root)
        if not (root / dest).is_file():
            # A tres contra un texto vacío saldría vacío (como si la tienda la hubiera borrado entera).
            plan.write(dest, theirs, root)
            plan.notes.append(f"{dest}: nuevo, {rel} de la exportación entero")
            continue
        base = read(root / HANDOFF / rel)
        merged, conflicts = merge3(read(root / dest), base or theirs, theirs)
        plan.write(dest, merged, root)
        if conflicts:
            plan.conflicts[dest] = conflicts


def note_unused(plan: Plan, unused: dict, everything: list):
    """Una nota por carpeta de lo que no se usa: la más alta en la que nada se usa (versions/, offline/,
    prototype/brand/, docs/img/), con cuántos ficheros trae; los sueltos de una carpeta que sí se usa
    (texts.json y MANIFEST.md, en la raíz), juntos en otra."""
    used = [rel for rel in everything if rel not in unused]
    groups = {}                         # (carpeta, entera) -> rutas
    for rel in sorted(unused):
        parts = rel.split("/")
        folders = ("/".join(parts[:i]) + "/" for i in range(1, len(parts)))
        folder = next((f for f in folders if not any(u.startswith(f) for u in used)), None)
        key = (folder, True) if folder else (rel.rpartition("/")[0], False)
        groups.setdefault(key, []).append(rel)
    for (folder, whole), rels in sorted(groups.items()):
        why = unused[rels[0]]
        if whole:
            count = f"{len(rels)} fichero" + ("s" if len(rels) != 1 else "")
            plan.notes.append(f"{folder} ({count}): no se usa; {why}")
        else:
            plan.notes.append(f"{', '.join(rels)}: no se usa{'n' if len(rels) != 1 else ''}; {why}")


def make_plan(zip_path: Path, root: Path = ROOT) -> Plan:
    plan = Plan()
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        export = open_export(Path(zip_path), work / "zip")
        plan.changelog = changelog_of(export / "README.md")
        if not plan.changelog:
            plan.problems.append("el README de la exportación no tiene «What changed since the previous export»")
        converted = plan_views(plan, root, export, work / "conv")
        plan_hover(plan, root, converted)
        plan_texts(plan, root, export)
        plan_values(plan, root, converted)
        plan_files(plan, root, export)
    return plan


# ---------------------------------------------------------------- aplicar

def dirty(root: Path, paths) -> list:
    """Los de ``paths`` con cambios sin guardar en git (nada, si ``root`` no es un repo)."""
    r = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", *paths], capture_output=True, text=True)
    return [line[3:] for line in r.stdout.splitlines()] if r.returncode == 0 else []


def apply(plan: Plan, root: Path = ROOT):
    for rel, data in plan.writes.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)


def report(plan: Plan, root: Path, applied: bool, out=sys.stdout):
    say = lambda line="": print(line, file=out)  # noqa: E731
    if plan.changelog:
        say(plan.changelog)
        say()
    say(("Escrito" if applied else "Cambiaría") + f": {len(plan.writes)} ficheros")
    for rel, data in sorted(plan.writes.items()):
        old = read(root / rel).splitlines() if not applied else None
        if old is not None and not rel.startswith("docs/design/") or rel.startswith("static/") and old is not None:
            new = data.decode("utf-8", errors="replace").splitlines()
            changed = sum(1 for line in difflib.unified_diff(old, new, lineterm="", n=0)
                          if line[:1] in "+-" and not line.startswith(("+++", "---")))
            extra = f" ({changed} líneas)"
        else:
            extra = ""
        mark = f"  — {plan.conflicts[rel]} conflictos" if rel in plan.conflicts else ""
        say(f"  {rel}{extra}{mark}")
    for title, lines in (("Para saber", plan.notes), ("Por decidir o construir", plan.problems)):
        if lines:
            say()
            say(f"{title}:")
            for line in lines:
                say(f"  - {line}")
    if plan.conflicts:
        say()
        say("Conflictos marcados con <<<<<<< tienda / ======= / >>>>>>> diseño nuevo: "
            + ", ".join(f"{k} ({v})" for k, v in sorted(plan.conflicts.items())))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("zip", type=Path, help="la exportación de Claude Design (.zip)")
    ap.add_argument("--apply", action="store_true", help="escribirlo (si no, sólo dice qué cambiaría)")
    ap.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    try:
        plan = make_plan(args.zip, args.root)
    except BadExport as e:
        print(f"no se aplica {args.zip}: {e}", file=sys.stderr)
        return 2
    if args.apply:
        busy = dirty(args.root, sorted(plan.writes))
        if busy:
            print("hay cambios sin guardar en lo que se escribiría; guárdalos (git commit o stash) antes: "
                  + ", ".join(busy), file=sys.stderr)
            return 2
        apply(plan, args.root)
    report(plan, args.root, args.apply)
    return 1 if plan.problems or plan.conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
