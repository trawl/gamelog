# Developer notes

# Installing the necessary environment
The easiest strategy is with [uv](https://docs.astral.sh/uv/getting-started/installation/). Once you have installed it, from the main project directory:

```
uv run gamelog.pyw
```

This will automatically create a local python venv under `.venv` with the necessary dependencies.

## Project layout
The code is split into a game-agnostic framework and one self-contained package
per game:

```
core/                     the framework — rarely touched when adding a game
  registry.py             GameDefinition + registry + object creation
  model/match.py          base match / round / player models
  engine/                 engine hierarchy, stats, resume, db, settings
  ui/                     app shell, game sub-package (widgets, plots, stats), player sub-package
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
   In `computeWinner()`, set `self.winner` to a single player, or call
   `self.setWinners(players)` when players are still tied after every
   tie-breaker, so they share the victory.
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
           # short_name="MyG",  up to 4 letters where the name does not fit
           #                    (e.g. the player statistics form)
           # round_winners=True, when each round has a real winner (a hand won),
           #                     not when rounds are turns or score entries
           # player_stats_factory="games.mygame.playerstats:player_stats",
           # match_details_factory="games.mygame.playerstats:match_details",
           #                    see "Player statistics" below
       )
   )
   ```

6. (Optional) add a `settings.py` to expose per-game preferences in the
   settings dialog:

   ```python
   # games/mygame/settings.py
   from PySide6.QtCore import QCoreApplication

   # Strings registered for lupdate extraction:
   QCoreApplication.translate("MyGameSettings", "End score")
   QCoreApplication.translate(
       "MyGameSettings", "Score a player must reach to end the game"
   )

   game_settings = {
       "mygame_top_score": {
           "value": 100,
           "type": "int",  # "int", "float", "bool", or "str"
           "min": 1,
           "max": 1000,
           "displayname": "End score",
           "description": "Score a player must reach to end the game",
           "context": "MyGameSettings",  # Qt translation context
       },
   }
   ```

   Then point `GameDefinition` at it by adding
   `settings_factory="games.mygame.settings:game_settings"` as a keyword
   argument. Settings are discovered lazily the first time the dialog opens —
   no other files need editing.

   For `bool` settings with two named states, use `"choices": ["Label when False", "Label when True"]`
   (displayed as a toggle button). For `str` settings with a fixed set of
   values, use `"choices": ["opt1", "opt2", ...]` (displayed as a combo box).

   Common settings shared across games (dealer policy, turn time) are defined
   in `core/engine/common_settings.py` and can be imported directly:

   ```python
   from core.engine.common_settings import DEALER_POLICY_SETTING

   game_settings = {
       "mygame_dealer_policy": DEALER_POLICY_SETTING,
       ...
   }
   ```

   Shared strings are translated once under the `"GameSettings"` context and
   live in the core translation catalogue (`core/resources/i18n/core_<locale>.ts`).

7. (Optional) drop assets into `games/<name>/{icons,styles,i18n}`.
   For per-player bonus or piece buttons, `ColourBonusButton` (in
   `core.ui.game`) draws an SVG icon in the player's colour: a tinted disc
   while its count is zero, a solid disc with a white icon once it is set,
   and a corner badge for counts above one. Draw the icon's shape with the
   placeholder colours `currentColor` (body), `#2B2B2B` (outlines),
   `#3C3C3C` (solid details) and `#FFFFFF` (accents), with no background;
   see `games/catan/icons/` and `games/azul/icons/`. For
   translations run `python utils/build_translations.py` — it compiles the
   catalogues and rebuilds resources automatically. For non-translation assets
   (icons, stylesheets) run `python utils/build_resources.py` directly.
8. Add a test (a save/resume round-trip and a winner-rule check) under `tests/`.

Existing games make good templates — e.g. `games/ratuki/` for a simple
score-to-a-target game, `games/skullking/` for one with bidding and custom
statistics.

## Player statistics
The player statistics screen (`core/ui/playerstats.py`, queries in
`core/engine/playerstats.py`) shows one player across every game, or one game.
Only finished matches count.

**Performance index.** Raw win rates do not compare across player counts, so
the screen rates wins against chance: each match expects `1 / players` wins,
and a win shared by `n` players earns `1 / n`. The index is earned ÷ expected:
`1.00×` wins exactly as often as chance, `2.00×` twice as often. Matches
without a winner are left out of both sides. The game quick statistics show
the same index next to the victory ratio.

**Round performance.** The same index over rounds, for the games registered
with `round_winners=True`. Each round expects `1 / players in it`; players
already out of a match (e.g. eliminated in Remigio) have no `Round` row, so the
count follows them.

**Nemesis and favourite victim.** An opponent met in at least
`RIVAL_MIN_MATCHES` matches (3) with a losing record against them (more of
their wins than yours) can be the nemesis, ranked by how often they won. The
favourite victim is the mirror, with a winning record. An even record is
neither, so no opponent holds both.

**What a game can add**, through optional `GameDefinition` fields:

- `short_name`: up to 4 letters naming the game where the full name does not
  fit (the recent form markers). Defaults to the name's first three letters.
- `round_winners`: adds the round performance card (see above).
- `player_stats_factory`: `"module:function"` of
  `function(game, nick) -> list[PlayerStat]`, the game's own cards when that
  game is selected (`PlayerStat` is in `core/engine/playerstats.py`). Return
  translated, formatted text, with a `tip` only for what the card does not
  already say. Highest, lowest and average score are added for every game, so
  do not repeat them. Prefer reusing the game's stats engine queries; see
  `games/parchis/playerstats.py`.
- `match_details_factory`: `"module:function"` of
  `function(match_ids) -> {match id: {nick: text}}`, extra text shown after
  each player's score in the recent form tooltips; see
  `games/phase10/details.py`.

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
Optional but recommended: install the hooks once:

```
uv run pre-commit install
```

The hooks run automatically on every `git commit` and cover:

* **ruff** — lint + format (uses the project's own ruff via `uv run`, matching CI)
* **basedpyright** — type checking
* **build-translations** — syncs and compiles all `.ts` catalogues; the commit is
  **blocked** if any strings are unfinished (see [I18N support](#i18n-support)).

Run them manually against everything with:

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

   - If **all strings are already translated** and any `.qm` file changed,
     the script automatically runs `build_resources.py` — nothing else to do.
     If no `.qm` content changed the resource rebuild is skipped.
   - If **new unfinished strings are found**, the script prints the exact
     `pyside6-linguist` command(s) needed (one per translation unit) and
     **exits with an error** — which also blocks a commit if run via the
     pre-commit hook. Run each printed command, translate the flagged strings,
     then re-run `build_translations.py` to recompile and rebuild resources.

## Resources (styles, icons, translations)
Resources are **auto-discovered** and compiled into `core/resources_rc.py`. You
never edit `resources.qrc` by hand — it is generated as a temporary intermediate
and deleted automatically after compilation. After adding, changing, or removing
any icon, stylesheet, or compiled translation (`.qm`), run:

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

### Rules sheets
A game may ship a quick-reference rules sheet, shown by the 📖 button on its
board:

* `games/<name>/rules/<doc>_<locale>.md` — Markdown, one file per language
  (e.g. `catan_en_GB.md`). A missing translation falls back to the language
  root and then to `en_GB`, so languages can be added one at a time.
* Point the game at it with `rules_doc="<doc>"` (and optionally `rules_url=` for
  the publisher's rule book, opened in the system browser) on its
  `GameDefinition`. Games without `rules_doc` show no button.
* Write sheets in your own words — do not copy or bundle publisher text/PDFs.

### Per-game stylesheets
A game may ship an optional stylesheet that is layered on top of the global
theme, scoped to that game's widget:

* `games/<name>/styles/<name>.qss` — applied for any theme, or
* `games/<name>/styles/<name>.light.qss` / `<name>.dark.qss` — theme-specific
  (preferred over the plain file when present).

`<name>` is the game's package directory name. The stylesheet is applied
automatically when the game's board is opened and re-applied on theme changes.
