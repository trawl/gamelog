# Developer notes

# Installing the necessary environment
The easiest strategy is with [uv](https://docs.astral.sh/uv/getting-started/installation/). Once you have installed it, from the main project directory:

```
uv run gamelog.pyw
```
This will automatically create a local python venv under .venv with the necessary dependencies.

## Project layout
The code is split into a game-agnostic framework and one self-contained package
per game:

```
core/                     the framework — rarely touched when adding a game
  registry.py             GameDefinition + registry + object creation
  model/base.py           base match / round models
  engine/                 base engine, stats, resume, db, settings
  ui/                     base widgets (GameWidget, stats, plots, dialogs, ...)
  logging_config.py       log-level resolution
  resources/              shared icons / styles / i18n
games/
  __init__.py             discovery: imports every game sub-package
  <name>/                 ONE package per game
    __init__.py           registers a GameDefinition (import side-effect)
    model.py              Match / Round subclasses (rules, scoring, persistence)
    engine.py             engine (+ optional stats engines)
    widget.py             Qt board widget (+ optional quick-stats widget)
    icons/ styles/ i18n/  optional, per-game assets
```

Discovery is automatic: `load_builtin_games()` imports every sub-package under
`games/`, and each one registers itself. `GameDefinition` refers to its classes
by `"module:Class"` strings, so widgets (and Qt) aren't imported until a match
is actually created — registration itself stays Qt-free.

## Adding a new game
Adding a game is dropping in a directory; no other files need editing.

1. Create `games/<name>/` with `model.py`, `engine.py`, `widget.py`.
2. **model.py** — subclass `GenericRoundMatch` (or `GenericMatch`) and implement
   the rules: `computeWinner()`, per-round scoring, and any extra persistence.
3. **engine.py** — subclass `RoundGameEngine` (or `GameEngine`).
4. **widget.py** — subclass `GameWidget` and provide its input / detail widgets.
5. **__init__.py** — register the game:

   ```python
   from core.registry import GameDefinition, registry

   registry.register(
       GameDefinition(
           "My Game",  # name (shown in the UI, stored in the DB)
           6,  # max players
           "Short description",
           "Home rules",
           "games.mygame.model:MyGameMatch",
           "games.mygame.engine:MyGameEngine",
           "games.mygame.widget:MyGameWidget",
           # Optional, omit if not needed:
           # "games.mygame.widget:MyGameQSTW",              quick-stats widget
           # "games.mygame.engine:MyGameStatsEngine",       stats engine
           # "games.mygame.engine:MyGameParticularStatsEngine",
       )
   )
   ```

6. (Optional) drop assets into `games/<name>/{icons,styles,i18n}` and run
   `python utils/build_resources.py`; add translations with
   `python utils/build_translations.py`.
7. Add a test (a save/resume round-trip and a winner-rule check) under `tests/`.

Existing games make good templates — e.g. `games/ratuki/` for a simple
score-to-a-target game, `games/skullking/` for one with bidding and custom
statistics.

## Running the tests
The test suite lives in `tests/` and runs headlessly (no display, no real
database — each test gets its own throwaway SQLite file). Run it with:

```
uv run pytest
```

The suite covers the game registry, the parameterised SQL / persistence layer
(save & resume for every game), the statistics engines, log-level resolution,
and a widget-construction smoke test for every game. It needs the `dev`
dependency group (installed automatically by `uv run`/`uv sync`).

To see which code is exercised:

```
uv run pytest --cov --cov-report=term-missing
```

## Pre-commit hooks
Optional but recommended: run ruff (lint + format) automatically before each
commit. Install the git hook once:

```
uv run pre-commit install
```

The hooks call the project's own ruff (via `uv run`), so they always match the
version used in CI. Run them manually against everything with:

```
uv run pre-commit run --all-files
```

## I18N support
Translations are **split by unit**: framework strings live in
`core/resources/i18n/core_<locale>.ts`, and each game owns
`games/<name>/i18n/<name>_<locale>.ts`. A string is assigned to a unit by the
source file it appears in, so a game's translations travel with the game.

Whenever code with translatable text changes:

1. Sync and compile every catalogue (`lupdate` + `lrelease` per unit):
```
python utils/build_translations.py
```

2. Translate any new (unfinished) strings with Linguist, then re-run the
   command above to recompile:
```
pyside6-linguist core/resources/i18n/core_*.ts games/*/i18n/*.ts &
```

3. Refresh the resource bundle as explained below.

## Resources (styles, icons, translations)
Resources are **auto-discovered** and compiled into `resources_rc.py`. You never
edit `resources.qrc` by hand — it is generated. After adding, changing, or
removing any icon, stylesheet, or compiled translation (`.qm`), run:

```
python utils/build_resources.py
```

This scans the resource folders, regenerates `resources.qrc`, and compiles it
with `pyside6-rcc`.

### Where resources live
* **Shared / framework-wide:** `core/resources/{icons,styles,i18n}`
* **Per-game:** `games/<name>/{icons,styles,i18n}` — a game folder can carry its
  own assets, so adding a game needs no changes elsewhere.

Every file is exposed under a flat alias regardless of where it lives:
`:/icons/<name>`, `:/styles/<name>`, `:/i18n/<name>`. Because the namespace is
flat, **file names must be unique across all games** (the build script errors on
a collision).

### Per-game stylesheets
A game may ship an optional stylesheet that is layered on top of the global
theme, scoped to that game's widget:

* `games/<name>/styles/<name>.qss` — applied for any theme, or
* `games/<name>/styles/<name>.light.qss` / `<name>.dark.qss` — theme-specific
  (preferred over the plain file when present).

`<name>` is the game's package directory name. The stylesheet is applied
automatically when the game's board is opened and re-applied on theme changes.
