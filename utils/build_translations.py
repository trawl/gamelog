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

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCALES = ["en_GB", "es_ES", "ca_ES"]


def _tool(name: str) -> str:
    candidate = Path(sys.executable).parent / name
    return str(candidate) if candidate.exists() else name


def _units() -> list[tuple[str, Path, Path]]:
    """(name, sources_root, i18n_dir) for core and every game."""
    units = [("core", PROJECT_ROOT / "core", PROJECT_ROOT / "core" / "resources" / "i18n")]
    for game_dir in sorted((PROJECT_ROOT / "games").iterdir()):
        if game_dir.is_dir() and (game_dir / "__init__.py").exists():
            units.append((game_dir.name, game_dir, game_dir / "i18n"))
    return units


def _sources(root: Path, name: str) -> list[str]:
    files = sorted(root.rglob("*.py"))
    if name == "core":
        # core owns only framework code, never the games package.
        files = [f for f in files if "games" not in f.relative_to(PROJECT_ROOT).parts]
    return [str(f) for f in files]


def build_unit(name: str, root: Path, i18n_dir: Path) -> None:
    i18n_dir.mkdir(parents=True, exist_ok=True)
    ts_files = [i18n_dir / f"{name}_{locale}.ts" for locale in LOCALES]
    sources = _sources(root, name)

    lupdate = [_tool("pyside6-lupdate"), *sources, "-ts",
               *[str(t) for t in ts_files], "-no-obsolete"]
    subprocess.run(lupdate, check=True)

    for ts in ts_files:
        subprocess.run([_tool("pyside6-lrelease"), str(ts)], check=True)


def main() -> None:
    for name, root, i18n_dir in _units():
        print(f"== {name} ==")
        build_unit(name, root, i18n_dir)
    print("\nTranslations updated. Now run: python utils/build_resources.py")


if __name__ == "__main__":
    main()
