"""Turn the strategy factory's output into the shop's catalogue.

The factory is the twin repository that generates the data, Leci37/tuisku_strategy_generator:
its step 7 (S_04_ladding_file_info_to_see_in_web.py) writes the export, d_result/ and a package of both,
d_result/package/.

    python catalogue/publish.py --package DIR [--prune]
    python catalogue/publish.py EXPORT.csv [--assets DIR] [--prune]

catalogue/contract.json is the contract between the two repositories: the catalogue's columns, which
factory folder holds each file a row names, which static/assets/ folder it goes to and how each full
script is named. Both forms check the columns against it: a missing column, or one the contract does
not know, stops the publish before anything is written (drift between the twins must be loud).

--package DIR  the factory's package: catalogue.csv, the charts, icons and previews its rows name, and
               manifest.json with the sha256 of every file and of every full script (which stay out of
               the package). The whole package is checked first (read_package): its contract is this
               one, every file is listed with the right sha256 and nothing else is there, every file a
               row names is in it or already in static/assets/, and the private list names the script
               of every row. Then exactly what was checked is published as below (each file's bytes are
               checked again as they are copied: the factory may be writing d_result/ meanwhile),
               replacing the charts and previews that changed and the factory's placeholder logos the
               shop still shows (any other logo the shop has is kept, and said), and
               catalogue/release.json records which factory run the shop shows.
EXPORT.csv     the tab-separated export (pine_TW_img_info_*_WEB.csv), the form before packages;
--assets DIR   then copies the files the catalogue uses from DIR (the factory's d_result/) into
               static/assets/, leaving the ones already there as they are. An export has no manifest:
               a release.json of an earlier package is deleted, since it no longer says what is shown.
--prune        deletes files in static/assets/{charts,previews} that no catalogue row uses.

Publishing:
  - keeps one row per strategy (ticker, interval, key_techs, id_model): the export repeats some;
  - rewrites every image and preview path to a relative assets/... path (under static/), whether the
    export gave a local path or an absolute raw.githubusercontent.com URL;
  - drops pine_path, the location of the full paid script, which must never be public;
  - names a ticker the export calls by its exchange code (BINANCE:XRPUSD) as "XRP / US Dollar",
    or by the name another row of the same ticker has;
  - keeps the shop's own optional columns (version) from the current catalogue.csv when the
    export does not bring them, so a re-publish does not reset every strategy to v1;
  - writes catalogue/catalogue.csv, the one file both the page and the server read
    (the server takes prices from it, never from the browser).
Every file is first written beside its destination and all are renamed into place only when every one
was written (Staged): a failure half way (a full disk, a package that changed) leaves the shop as it was.
The paid scripts are not handled here: they go to the private storage (STRATEGIES_DIR, by default
<ZLECITOOL_DATA_DIR>/edgefolio/strategies); `flask --app app edgefolio import DIR` does both.

Every preview is cut as the factory cuts the paid ones (the script up to 50 lines into its first
tree, then a note): the factory's previews of the free strategies were the whole script, which
made the free download's email step pointless.

ROOT, ASSETS and OUT are module attributes, and every function takes out=/assets= too, so tests (here
and in the factory) point them at temporary folders; release.json always goes beside OUT.
"""
import argparse
import base64
import hashlib
import io
import json
import os
import posixpath
import re
import sys
from pathlib import Path

import pandas as pd

from previews import cut_preview

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "static" / "assets"   # the catalogue's paths ("assets/...") are relative to static/
OUT = ROOT / "catalogue" / "catalogue.csv"
CONTRACT = Path(__file__).resolve().parent / "contract.json"
MANIFEST = "manifest.json"
PACKAGE_CATALOGUE = "catalogue.csv"
RELEASE = "release.json"              # beside OUT
KEY = ["ticker", "interval", "key_techs", "id_model"]
KEY_TYPES = {k: str for k in KEY}
SHOWN = 10                            # names listed in one problem; the rest are counted


def load_contract(path: Path = None) -> dict:
    return json.loads(Path(path or CONTRACT).read_text(encoding="utf-8"))


_contract = load_contract()
# Columns the shop adds that the factory does not write (the API defaults them when missing).
OPTIONAL = list(_contract["optional_columns"])
DROPPED = list(_contract["dropped_columns"])
# column -> (assets subfolder, the factory's folder name)
PATH_COLUMNS = {col: (_contract["assets"][col], folder) for col, folder in _contract["folders"].items()}
# The script's preview, found by its column (the one edgefolio/catalogue.py serves as the preview); its folders
# come from the contract like every other. It is cut wherever the contract sends it: whole, it is the script.
PREVIEW_COLUMN = "pine_path_shadow"
PREVIEWS = PATH_COLUMNS[PREVIEW_COLUMN][0]
# One logo per ticker, shared by all its strategies.
LOGOS = {PATH_COLUMNS[col][0] for col in ("path_ico", "path_ico_big")}
# What a package replaces when the shop's copy differs: every file of one strategy, since a new factory run may
# redraw a chart, or turn a free strategy's preview into a paid one, under the same name. Not the logos: the
# factory writes a placeholder into its d_result/icons when it has none (S_04 without SHOP_ICONS_DIR) and the
# shop's are the real ones, so a package replaces a logo only when the shop's is that placeholder (is_placeholder).
# These are also the folders --prune looks at.
REPLACED = sorted({sub for sub, _ in PATH_COLUMNS.values()} - LOGOS)
# The factory's placeholder logo (S_04's placeholder_svg): a grey circle with the ticker on it.
PLACEHOLDER = re.compile(rb'\s*<svg xmlns="http://www\.w3\.org/2000/svg" width="[\d.]+" height="[\d.]+" '
                         rb'viewBox="[\d. ]+"><circle cx="[\d.]+" cy="[\d.]+" r="[\d.]+" fill="#5b6b7c"/>'
                         rb'<text [^<>]*>[^<>]*</text></svg>\s*')


class ContractError(ValueError):
    """What does not follow the contract; problems lists every one."""

    def __init__(self, problems):
        self.problems = list(problems)
        super().__init__("\n".join(self.problems))


class PackageError(ContractError):
    """A package that cannot be published; nothing was written."""


class Staged:
    """The writes of one publish, each beside its destination (.<name>.<pid>.tmp) until commit() renames them
    all, in the order they were written; discard() deletes the ones not renamed. done counts the renamed."""

    def __init__(self):
        self.pending = {}   # destination -> its tmp, in write order
        self.done = 0

    def __contains__(self, dest) -> bool:
        return Path(dest) in self.pending

    def write(self, dest: Path, data: bytes):
        dest = Path(dest)
        if dest in self.pending:
            raise ValueError(f"{dest}: written twice in one publish")
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(f".{dest.name}.{os.getpid()}.tmp")
        self.pending[dest] = tmp
        tmp.write_bytes(data)

    def commit(self):
        for dest, tmp in list(self.pending.items()):
            os.replace(tmp, dest)
            # The rename keeps the time the tmp was written, maybe long before; a thumbnail made from the old
            # file meanwhile (edgefolio/media.py rebuilds one older than its chart) would look newer than it.
            os.utime(dest)
            del self.pending[dest]
            self.done += 1

    def discard(self):
        for tmp in self.pending.values():
            tmp.unlink(missing_ok=True)
        self.pending.clear()


def listed(names) -> str:
    names = list(names)
    more = f" and {len(names) - SHOWN} more" if len(names) > SHOWN else ""
    return ", ".join(map(str, names[:SHOWN])) + more


def column_problems(columns) -> list:
    known = set(_contract["columns"]) | set(OPTIONAL) | set(DROPPED)
    missing = [c for c in _contract["columns"] if c not in columns]
    unknown = [c for c in columns if c not in known]
    problems = []
    if missing:
        problems.append(f"columns of contract {_contract['version']} missing: {listed(missing)}")
    if unknown:
        problems.append(f"columns contract {_contract['version']} does not know: {listed(unknown)} (a new column "
                        "goes into catalogue/contract.json and the factory's SHOP_COLUMNS at once)")
    return problems


def check_columns(df: pd.DataFrame):
    """Raises ContractError when a contract column is missing or a column is neither contract, optional
    nor dropped."""
    problems = column_problems(list(df.columns))
    if problems:
        raise ContractError(problems)


def private_name(ticker: str, interval: str, key_techs: str, id_model: str) -> str:
    """The full script's file name (the contract's private.name; edgefolio's Strategy.private_file)."""
    key = f"{ticker}_{interval}_{key_techs}tuisku{id_model}"
    return base64.urlsafe_b64encode(key.encode("utf-8")).decode("ascii").rstrip("=") + ".pine"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def is_sha256(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdefABCDEF" for c in value)


def is_placeholder(data: bytes) -> bool:
    return PLACEHOLDER.fullmatch(data) is not None


def file_name(value: str) -> str:
    """Last path component of a local path, a Windows path or a URL."""
    return posixpath.basename(str(value).replace("\\", "/"))


def path_problem(key, folders) -> str:
    """Why a manifest key is not a safe package path (None if it is): catalogue.csv or <folder>/<name>,
    one level, folder one of the contract's, so nothing outside the package is ever read or written."""
    if not isinstance(key, str) or "\\" in key or "\x00" in key:
        return f"{key!r}: not a package path (no backslashes)"
    parts = key.split("/")
    if parts == [PACKAGE_CATALOGUE]:
        return None
    if len(parts) != 2 or parts[0] not in folders or not parts[1] or parts[1].startswith("."):
        return (f"{key!r}: not a package path ({PACKAGE_CATALOGUE} or <folder>/<name>, folder one of "
                f"{', '.join(sorted(folders))})")
    return None


def read_package(package: Path, assets: Path = None):
    """Checks a factory package before anything is written and returns (manifest, catalogue). Every
    problem found goes into one PackageError. The catalogue is parsed from the very bytes that were hashed."""
    package, assets = Path(package), Path(assets or ASSETS)
    try:
        manifest = json.loads((package / MANIFEST).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise PackageError([f"{package}: no {MANIFEST} (the factory's step 7 writes it in d_result/package/)"])
    except (OSError, ValueError) as e:
        raise PackageError([f"{MANIFEST}: not valid JSON ({e})"])
    if not isinstance(manifest, dict):
        raise PackageError([f"{MANIFEST}: not a JSON object"])
    if type(manifest.get("contract")) is not int or manifest["contract"] != _contract["version"]:
        raise PackageError([f"package of contract {manifest.get('contract')!r}, this shop reads contract "
                            f"{_contract['version']}: publish it with a shop of its contract, or write it again with "
                            "a factory of this one"])
    problems = []
    absent = [k for k in ("created", "generator", "rows", "files", "private") if k not in manifest]
    if absent:
        problems.append(f"{MANIFEST}: no {', '.join(absent)}")
    if "created" in manifest and not isinstance(manifest["created"], str):
        problems.append(f"{MANIFEST}: created is not a string")
    if "generator" in manifest and not isinstance(manifest["generator"], dict):
        problems.append(f"{MANIFEST}: generator is not an object")
    files = manifest.get("files", {})
    if not isinstance(files, dict):
        problems.append(f"{MANIFEST}: files is not an object")
        files = {}

    folders = set(_contract["folders"].values())
    good = set()                   # keys that are safe files of the package with the right sha256
    table = None                   # catalogue.csv's bytes: the ones hashed are the ones parsed
    root = os.path.realpath(package)
    for key, digest in files.items():
        problem = path_problem(key, folders)
        if problem:
            problems.append(problem)
            continue
        path = package / key
        if path.is_symlink() or not path.is_file() or not os.path.realpath(path).startswith(root + os.sep):
            problems.append(f"{key}: in the manifest but not a file of the package")
            continue
        try:
            if key == PACKAGE_CATALOGUE:
                table = path.read_bytes()
                actual = hashlib.sha256(table).hexdigest()
            else:
                actual = sha256(path)
        except OSError as e:
            problems.append(f"{key}: cannot be read ({e})")
            continue
        if not is_sha256(digest) or actual != digest.lower():
            problems.append(f"{key}: its sha256 is not the manifest's")
        else:
            good.add(key)
    unlisted = []
    for here, dirs, names in os.walk(package):
        here = Path(here)
        for name in names + [d for d in dirs if (here / d).is_symlink()]:
            rel = (here / name).relative_to(package).as_posix()
            if rel != MANIFEST and rel not in files:
                unlisted.append(rel)
    if unlisted:
        problems.append(f"{len(unlisted)} files in the package are not in the manifest: {listed(sorted(unlisted))}")

    df = None
    if PACKAGE_CATALOGUE not in files:
        problems.append(f"{PACKAGE_CATALOGUE}: not in the manifest")
    elif table is not None:  # read even with a wrong sha256, to say everything else that fails
        try:
            df = pd.read_csv(io.BytesIO(table), sep="\t", dtype=KEY_TYPES)
        except ValueError as e:
            problems.append(f"{PACKAGE_CATALOGUE}: not a tab-separated table ({e})")
    if df is not None:
        problems += column_problems(list(df.columns))
        rows = manifest.get("rows")
        if type(rows) is not int or rows != len(df):
            problems.append(f"{MANIFEST}: rows is {rows!r}, {PACKAGE_CATALOGUE} has {len(df)}")
        problems += row_problems(df, package, assets, files, good, manifest.get("private"))
    if problems:
        raise PackageError(problems)
    return manifest, df


def row_problems(df, package, assets, files, good, private) -> list:
    """What the rows name that the package does not bring: files, the full scripts' list, previews."""
    problems = []
    for col, (sub, folder) in PATH_COLUMNS.items():
        if col not in df.columns:
            continue  # already a missing column
        names = df[col].map(file_name).unique()
        absent = sorted(n for n in names if f"{folder}/{n}" not in files and not (assets / sub / n).is_file())
        if absent:
            problems.append(f"{col}: {len(absent)} files neither in the package ({folder}/) nor in the shop "
                            f"(static/assets/{sub}/): {listed(absent)}")
        if col == PREVIEW_COLUMN:
            for n in names:
                if f"{folder}/{n}" in good:
                    try:
                        cut_preview((package / folder / n).read_text(encoding="utf-8"))
                    except ValueError as e:  # a UnicodeDecodeError is one too
                        problems.append(f"{folder}/{n}: not a preview of a strategy script ({e})")
    if not set(KEY) <= set(df.columns):
        return problems
    keys = df[KEY].fillna("")
    blank = keys.apply(lambda s: s.str.strip().eq("")).any(axis=1)
    if blank.any():
        problems.append(f"{int(blank.sum())} rows without {', '.join(KEY)}: lines "
                        f"{listed(i + 2 for i in df.index[blank])} of {PACKAGE_CATALOGUE}")
    if not isinstance(private, dict) or not isinstance(private.get("files"), dict):
        problems.append(f"{MANIFEST}: private.files is not an object")
        return problems
    if private.get("folder") != _contract["private"]["folder"]:
        problems.append(f"{MANIFEST}: private.folder is {private.get('folder')!r}, the contract's is "
                        f"{_contract['private']['folder']!r}")
    expected = {private_name(*k) for k in keys[~blank].itertuples(index=False)}
    named = set(private["files"])
    if expected - named:
        problems.append(f"private.files lacks the script of {len(expected - named)} rows: "
                        f"{listed(sorted(expected - named))}")
    if named - expected:
        problems.append(f"private.files names {len(named - expected)} scripts of no row: "
                        f"{listed(sorted(named - expected))}")
    wrong = sorted(n for n, d in private["files"].items() if not is_sha256(d))
    if wrong:
        problems.append(f"private.files: {len(wrong)} are not sha256 hex digests: {listed(wrong)}")
    # A full script may travel only as a free strategy's preview, which is cut before it is published.
    # As a chart or a logo it would land whole in static/assets: refuse a package file that is one.
    scripts = {d.lower() for d in private["files"].values() if is_sha256(d)}
    previews = PATH_COLUMNS[PREVIEW_COLUMN][1] + "/"
    whole = sorted(k for k, d in files.items()
                   if k in good and k != PACKAGE_CATALOGUE and not k.startswith(previews) and d.lower() in scripts)
    if whole:
        problems.append(f"{len(whole)} files of the package are full scripts of private.files, which are never "
                        f"published: {listed(whole)}")
    return problems


def checked_bytes(path: Path, key: str, digest: str) -> bytes:
    """A package file's bytes, which must still be the ones read_package checked: the package's files are hard
    links into d_result/, which the factory rewrites in place, so it may have changed since."""
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        raise PackageError([f"{key}: gone from the package since it was checked: nothing was published"])
    if hashlib.sha256(data).hexdigest() != digest.lower():
        raise PackageError([f"{key}: changed since it was checked (its sha256 is no longer the manifest's): "
                            "nothing was published"])
    return data


def cut_previews(names, assets: Path, stage: Staged) -> int:
    """Stages the cut of every preview of the catalogue already in the shop that is not cut yet; returns how
    many needed it."""
    done = 0
    for n in names:
        f = assets / PREVIEWS / n
        if f in stage or not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        cut = cut_preview(text)
        if cut != text:
            stage.write(f, cut.encode("utf-8"))
            done += 1
    return done


def keep_optional(df: pd.DataFrame, previous: Path) -> pd.DataFrame:
    if not previous.is_file():
        return df
    old = pd.read_csv(previous, sep="\t", dtype=str)
    carry = [c for c in OPTIONAL if c in old.columns and c not in df.columns]
    if not carry:
        return df
    old = old[KEY + carry].drop_duplicates(subset=KEY)
    return df.astype({k: str for k in KEY}).merge(old, on=KEY, how="left")


def readable_names(df: pd.DataFrame) -> pd.DataFrame:
    """The export names a few crypto rows by their exchange symbol; the page shows Name as is."""
    coded = df["Name"].astype(str).str.contains(":")
    good = df[~coded].drop_duplicates("ticker").set_index("ticker")["Name"]
    def name(row):
        if row["ticker"] in good:
            return good[row["ticker"]]
        base = row["ticker"][:-4] if row["ticker"].endswith("USDT") else row["ticker"]
        return f"{base} / US Dollar"
    df.loc[coded, "Name"] = df[coded].apply(name, axis=1)
    return df


def build(df: pd.DataFrame, assets_src: Path, out: Path, assets: Path, stage: Staged,
          files: dict = None) -> pd.DataFrame:
    """The publish itself, for both forms, written into stage (nothing is in place until it is committed).
    files is the manifest's (a package): a file is copied only with the bytes it was checked with, a chart or
    preview already in the shop is replaced when the factory's differs (REPLACED) and a logo only when the
    shop's is the factory's placeholder; the logos kept although the package's differ are listed in
    df.attrs["published"]["kept"]. Without files (an export), an asset already in the shop is left as it is."""
    before = len(df)
    df = df.drop_duplicates(subset=KEY, keep="first").drop(columns=DROPPED, errors="ignore")
    df = keep_optional(df, out)
    df = readable_names(df)
    copied = cut = 0
    kept = []
    for col, (sub, src_folder) in PATH_COLUMNS.items():
        names = df[col].map(file_name)
        df[col] = "assets/" + sub + "/" + names
        if not assets_src:
            continue
        for n in names.unique():
            src, dest = assets_src / src_folder / n, assets / sub / n
            if dest in stage:
                continue  # another column names the same file
            if files is None:
                if not src.is_file() or dest.exists():
                    continue
                data = src.read_bytes()
            else:
                key = f"{src_folder}/{n}"
                if key not in files:
                    continue  # read_package found it in the shop
                digest = files[key].lower()
                if dest.is_file() and col != PREVIEW_COLUMN and sha256(dest) == digest:
                    continue  # the same file: not even read
                if dest.is_file() and sub in LOGOS and not is_placeholder(dest.read_bytes()):
                    kept.append(n)
                    continue
                data = checked_bytes(src, key, digest)
            public = data
            if col == PREVIEW_COLUMN:  # only its public part ever reaches static/
                public = cut_preview(data.decode("utf-8")).encode("utf-8")
            if dest.is_file() and dest.read_bytes() == public:
                continue
            stage.write(dest, public)
            copied += 1
            cut += public != data
    cut += cut_previews(df[PREVIEW_COLUMN].map(file_name).unique(), assets, stage)
    stage.write(out, df.to_csv(sep="\t", index=False).encode("utf-8"))  # last: it names the files before it
    df.attrs["published"] = {"rows": len(df), "dropped": before - len(df), "copied": copied, "cut": cut,
                             "kept": sorted(kept)}
    return df


def say(df: pd.DataFrame, out: Path):
    done = df.attrs["published"]
    shown = out.relative_to(ROOT) if out.is_relative_to(ROOT) else out
    print(f"{shown}: {done['rows']} strategies ({done['dropped']} repeated rows dropped, {done['copied']} files "
          f"copied into static/assets, {done['cut']} previews cut to their public part)")
    if done["kept"]:
        print(f"{len(done['kept'])} logos of the package differ from the shop's and were kept (the shop's are taken "
              f"to be the real ones; delete one from static/assets/icons to take the factory's): "
              f"{listed(done['kept'])}")


def publish(export: Path, assets_src: Path = None, out: Path = None, assets: Path = None) -> pd.DataFrame:
    """The export form: EXPORT.csv [--assets DIR]. An export has no manifest, so the release.json of an
    earlier package, which would say the shop shows that run, is deleted."""
    out, assets = Path(out or OUT), Path(assets or ASSETS)
    df = pd.read_csv(export, sep="\t", dtype=KEY_TYPES)
    check_columns(df)
    stage = Staged()
    try:
        df = build(df, Path(assets_src) if assets_src else None, out, assets, stage)
        stage.commit()
    finally:
        stage.discard()
    (out.parent / RELEASE).unlink(missing_ok=True)
    say(df, out)
    return df


def publish_package(package: Path, prune: bool = False, out: Path = None, assets: Path = None,
                    checked: tuple = None, stage: Staged = None) -> pd.DataFrame:
    """The package form: read_package (nothing is written if it fails), the publish, release.json and,
    with prune, the unused charts and previews deleted. Returns the catalogue, with what it did in
    df.attrs["published"].

    checked is what read_package already returned for this package (the import checks the scripts against
    its manifest): then that is what is published, not a second read of a package that may have changed.
    stage brings the caller's own writes (the import's scripts): they are renamed with these, before them."""
    package, out, assets = Path(package), Path(out or OUT), Path(assets or ASSETS)
    manifest, df = checked if checked is not None else read_package(package, assets)
    stage = stage if stage is not None else Staged()
    release = {k: manifest[k] for k in ("contract", "created", "generator", "rows")}
    try:
        df = build(df, package, out, assets, stage, files=manifest["files"])
        stage.write(out.parent / RELEASE, (json.dumps(release, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
        stage.commit()
    finally:
        stage.discard()
    say(df, out)
    commit = str(manifest["generator"].get("commit") or "")[:12] or "unknown commit"
    print(f"{RELEASE}: contract {manifest['contract']}, factory run of {manifest['created']} ({commit})")
    df.attrs["published"].update(pruned=report_unused(df, assets, prune), release=release)
    return df


def unused_assets(df: pd.DataFrame, assets: Path = None) -> list:
    assets = Path(assets or ASSETS)
    used = {Path(p) for col in PATH_COLUMNS for p in df[col]}
    out = []
    for sub in REPLACED:
        for f in sorted((assets / sub).glob("*")):
            if f.relative_to(assets.parent) not in used:
                out.append(f)
    return out


def report_unused(df: pd.DataFrame, assets: Path = None, prune: bool = False) -> int:
    """Says how many charts and previews no row uses and, with prune, deletes them; returns how many it deleted."""
    unused = unused_assets(df, assets)
    print(f"{len(unused)} files in static/assets/{{{','.join(REPLACED)}}} are not used by any row")
    if not prune:
        return 0
    for f in unused:
        f.unlink()
    print("deleted them")
    return len(unused)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("export", type=Path, nargs="?", help="the factory's export (the form before packages)")
    ap.add_argument("--package", type=Path, help="the factory's package (its d_result/package/)")
    ap.add_argument("--assets", type=Path, help="with EXPORT.csv: factory d_result/ folder to copy assets from")
    ap.add_argument("--prune", action="store_true", help="delete charts/previews no row uses")
    args = ap.parse_args()
    if (args.export is None) == (args.package is None):
        ap.error("give either EXPORT.csv or --package DIR")
    if args.package and args.assets:
        ap.error("--assets goes with EXPORT.csv: a package brings its own files")
    try:
        if args.package:
            publish_package(args.package, args.prune)
        else:
            report_unused(publish(args.export, args.assets), prune=args.prune)
    except ContractError as e:
        sys.exit("nothing published:\n" + "\n".join(f"  - {p}" for p in e.problems))
