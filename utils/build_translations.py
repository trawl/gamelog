#!/usr/bin/env python3
"""Update and compile translation catalogues, one per translatable unit.

Each unit owns its ``.ts`` sources and produces matching ``.qm`` catalogues:

* **core** — framework strings in ``core/**/*.py`` -> ``core/resources/i18n/core_<locale>.ts``
* **each game** — ``games/<name>/**/*.py`` -> ``games/<name>/i18n/<name>_<locale>.ts``

For every unit this runs ``lupdate`` (sync ``.ts`` with the source strings,
dropping obsolete entries) then ``lrelease`` (compile ``.ts`` -> ``.qm``).  After
running it, refresh the resource bundle with ``python utils/build_resources.py``.

Translate the resulting ``.ts`` files with ``pyside6-linguist`` between the
lupdate and the (re-)release if there are new, untranslated strings.

Usage (from the repository root)::

    python utils/build_translations.py
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCALES = ["en_GB", "es_ES", "ca_ES"]


def _tool(name: str) -> str:
    candidate = Path(sys.executable).parent / name
    return str(candidate) if candidate.exists() else name


def _units() -> list[tuple[str, Path, Path]]:
    """(name, sources_root, i18n_dir) for core and every game."""
    units = [
        ("core", PROJECT_ROOT / "core", PROJECT_ROOT / "core" / "resources" / "i18n")
    ]
    for game_dir in sorted((PROJECT_ROOT / "games").iterdir()):
        if game_dir.is_dir() and (game_dir / "__init__.py").exists():
            units.append((game_dir.name, game_dir, game_dir / "i18n"))
    return units


def _sources(root: Path, name: str) -> list[str]:
    files = [f for f in sorted(root.rglob("*.py")) if f.name != "resources_rc.py"]
    if name == "core":
        # core owns only framework code, never the games package.
        files = [f for f in files if "games" not in f.relative_to(PROJECT_ROOT).parts]
    return [str(f) for f in files]


def _unfinished_ts_files(ts_files: list[Path]) -> list[Path]:
    """Return .ts files that contain at least one unfinished translation."""
    needs_work = []
    for ts in ts_files:
        if not ts.exists():
            continue
        try:
            tree = ET.parse(ts)
        except ET.ParseError:
            continue
        for msg in tree.iter("message"):
            translation = msg.find("translation")
            if translation is not None and translation.get("type") == "unfinished":
                needs_work.append(ts)
                break
    return needs_work


def build_unit(name: str, root: Path, i18n_dir: Path) -> tuple[list[Path], bool, str]:
    """Build translations for one unit.

    Returns (unfinished_ts_files, qm_changed, captured_output) so the caller
    can print output atomically and avoid interleaving with other parallel units.
    """
    buf: list[str] = []

    def _run(cmd: list[str]) -> None:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
        if result.stdout:
            buf.append(result.stdout.rstrip())
        if result.stderr:
            buf.append(result.stderr.rstrip())

    i18n_dir.mkdir(parents=True, exist_ok=True)
    ts_files = [i18n_dir / f"{name}_{locale}.ts" for locale in LOCALES]
    sources = _sources(root, name)

    _run(
        [
            _tool("pyside6-lupdate"),
            *sources,
            "-ts",
            *[str(t) for t in ts_files],
            "-no-obsolete",
        ]
    )

    needs_work = _unfinished_ts_files(ts_files)

    def _digest(path: Path) -> bytes:
        return hashlib.md5(path.read_bytes()).digest() if path.exists() else b""

    qm_files = [ts.with_suffix(".qm") for ts in ts_files]
    pre = {qm: _digest(qm) for qm in qm_files}

    with ThreadPoolExecutor() as pool:
        futures = [
            pool.submit(_run, [_tool("pyside6-lrelease"), str(ts)]) for ts in ts_files
        ]
        for f in as_completed(futures):
            f.result()  # re-raise any subprocess error

    qm_changed = any(_digest(qm) != pre[qm] for qm in qm_files)
    return needs_work, qm_changed, "\n".join(buf)


def _brace_compress(paths: list[str]) -> str:
    """Compress a list of paths that share a common prefix and suffix into one
    shell brace-expansion token, e.g. ``core/i18n/core_{en_GB,es_ES}.ts``."""
    if len(paths) == 1:
        return paths[0]
    # Find longest common prefix and suffix across all path strings.
    prefix = paths[0]
    for p in paths[1:]:
        while not p.startswith(prefix):
            prefix = prefix[:-1]
    suffix = paths[0][len(prefix) :]
    for p in paths[1:]:
        tail = p[len(prefix) :]
        while not tail.endswith(suffix):
            suffix = suffix[1:]
    middles = [
        p[len(prefix) : len(p) - len(suffix) if suffix else len(p)] for p in paths
    ]
    if len(set(middles)) < len(middles):
        return " ".join(paths)  # duplicates — fall back to plain list
    return f"{prefix}{{{','.join(middles)}}}{suffix}"


def main() -> None:
    units = _units()
    all_unfinished: list[Path] = []

    def _run(args: tuple[str, Path, Path]) -> tuple[str, list[Path], bool, str]:
        name, root, i18n_dir = args
        unfinished, qm_changed, output = build_unit(name, root, i18n_dir)
        return name, unfinished, qm_changed, output

    any_qm_changed = False
    with ThreadPoolExecutor(max_workers=len(units)) as pool:
        futures = {pool.submit(_run, u): u[0] for u in units}
        for f in as_completed(futures):
            name, unfinished, qm_changed, output = f.result()
            print(f"== {name} ==")
            if output:
                print(output)
            all_unfinished.extend(unfinished)
            any_qm_changed = any_qm_changed or qm_changed

    if all_unfinished:
        print(
            "\n⚠️  Unfinished translations found. Translate them and re-run before committing:"
        )
        linguist = _tool("pyside6-linguist")
        # Group by i18n directory — linguist requires all files in one call to
        # belong to the same translation unit (same strings, different locales).
        groups: dict[Path, list[Path]] = {}
        for ts in all_unfinished:
            groups.setdefault(ts.parent, []).append(ts)
        for ts_group in groups.values():
            rel = [str(f.relative_to(PROJECT_ROOT)) for f in ts_group]
            print(f"\n    {linguist} {_brace_compress(rel)} &")
        print()
        sys.exit(1)

    if not any_qm_changed:
        print("\nNo translation changes — skipping resource rebuild.")
        return

    print("\nAll translations complete — building resources...")
    subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "build_resources.py")],
        check=True,
    )


if __name__ == "__main__":
    main()
