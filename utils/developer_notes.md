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
  engine/                 engine hierarchy, stats, resume, db, settings,
                          dbtransfer (database export/import)
  ui/                     app shell, game sub-package (widgets, plots, stats), player sub-package;
                          also glyphs, windowmode, groupbox, dbtransfer (see "UI notes")
  platform_info.py        is_android()
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
main.py                   entry point pyside6-android-deploy expects (calls core.__main__.main)
utils/                    build_resources.py, build_translations.py, build_android.sh, android/
.github/workflows/        ci.yml, release-please.yml, android-apk.yml, ...
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
and a widget-construction smoke test for every game. The Android-specific
behaviour is tested on the desktop by faking the platform (`sys.getandroidapilevel`):
the guards, emoji glyphs and button fading, the touch gestures on the player
lists, database export/import, window mode and the Windows group box rule. It
needs the `dev` dependency group (installed automatically by `uv run`/`uv sync`).

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

## UI notes (all platforms)

* **Window mode** (`core/ui/windowmode.py`): the `fullscreen` setting, shown as
  "Window mode" in the settings dialog, is on by default. Off means a normal
  window on desktop (the size the user gave it) and a maximised one on Android.
  F11 toggles it and remembers the choice; the settings dialog applies it live.
* **No menu bar** except on macOS, where the system menu bar is a convention.
  Ctrl+Q is still a window action, the About dialog opens from the button at the
  bottom-left of the settings dialog, and the new-game screen has a 🚪 quit
  button. The six round buttons there sit in a 2x3 grid.
* **Button glyphs** (`core/ui/glyphs.py`): icon-only buttons pass their text
  through `platform_glyph()`, which swaps technical symbols for emoji (Android's
  fonts lack them, so they showed as empty boxes). `EMOJI_EVERYWHERE` applies the
  swap on every platform for a consistent look; set it to `False` to keep the
  original characters on desktop. Colour emoji ignore the palette, so a disabled
  button would keep its colour: set the text of any such button that can be
  disabled with `set_button_text()`, which fades it.
* **Windows group boxes**: Windows draws a plain line through a `QGroupBox`
  title, so `WINDOWS_GROUPBOX_CSS` (added on Windows only) draws the frame and
  reserves 36px above it for the title. Boxes without a title must not reserve
  it, or the new-game screen starts a centimetre lower than on other platforms.
  Qt evaluates a group box's rules when it is built, while its title is still
  empty, so a `[title=""]` selector cannot tell them apart. Instead `Tab` flags
  untitled boxes (`core/ui/groupbox.py`) on its first show, once the titles are
  set, and the rule skips the ones with the `untitled` property.
* **Database export/import** (settings dialog): `core/engine/dbtransfer.py`
  works on file paths and has no Qt. Export copies the live database with SQLite's
  backup API. Import validates the file (integrity check, expected tables), saves
  a backup of the current data in `backups/` beside the database (the last two
  are kept) and replaces the data in place; it is refused while a match is open.
  `core/ui/dbtransfer.py` holds the buttons and file dialogs and
  `NewGameWidget.reloadDatabase` refreshes the screens afterwards. Exports get a
  dated default name (`gamelog-YYYYMMDD-HHMM.db`). See the Android notes for what
  the system file picker needs.

## Android (tablet, experimental)

Target: landscape tablets, 64-bit ARM, Android 9 or later (API 28, the minimum
the Qt for Python tooling sets; it compiles against API 35). Qt 6.12 wheels from
download.qt.io, and the app runs on python-for-android's CPython. Phones are not
a goal. Only a **debug** APK is built: there is no release signing or `.aab` flow
yet. The supported way to get data in and out of the app is export/import in
the settings dialog (debug builds also allow `adb`, see below).

### What differs in the code
* **`is_android()`** (`core/platform_info.py`): Android reports
  `sys.platform == "linux"`, so check this before any Linux branch. It is used by
  `linux_desktop` (skipped), `SleepBlocker` (does nothing: there is no wake lock
  yet), the About dialog's git hash lookup, the database location
  (`db._app_data_dir()` asks Qt for the app's private storage) and the main window.
* **Theme**: `main()` selects the Fusion style, and `ThemeManager` sets an
  explicit light/dark palette (`android_palette()`), because Qt's Android platform
  theme does not follow the colour scheme. The stylesheet follows the theme being
  applied rather than what Qt reports.
* **Pop-ups have no close button**: `add_dismiss_button()` (`core/ui/dialogs.py`)
  adds a Close or Cancel button on Android only, beside OK/Create where there is
  one. Any new dialog needs one.
* **Touch**: a finger can neither right-click nor, on Android, start a Qt drag, so
  `PlayerList` (`core/ui/player/list.py`) treats a long press (`LONG_PRESS_MS`) on
  a row as both. Release in place is the right-click action (toggle favourite, or
  set the dealer in a match); moving reorders live; releasing over the twin list
  moves the player across. Double-tap still moves a player between lists. Only
  touch-synthesised mouse events (`QMouseEvent.source()`) take this path, so a
  real mouse is unaffected.
* **System file picker**: it returns `content://` URLs that only Qt's `QFile` can
  open, and `QFileDialog.fileSelected` is not emitted for them, so the dialogs
  listen to `urlSelected` and keep the URL fully percent-encoded (a name like
  `gamelog.db (2)` must stay `%20`). The picker may also report one selection
  twice, so each dialog handles only the first. Files are staged in the database's
  folder because Android has no usable temp directory, and several open modes are
  tried because providers differ. If you save over an existing name without
  tapping that file, the picker invents a name (`gamelog.db (1)`) for a file that
  does not exist; the error then tells the user to select the existing file.
  Reading and writing can take seconds, so a busy pop-up is shown meanwhile.

### Building the APK locally
You need JDK 17 or later (the tool checks; on macOS `brew install openjdk@17`) and
the `android` dependency group (`uv sync --group android`). Then:

```
utils/build_android.sh
```

It downloads the PySide6/shiboken6 Android wheels from download.qt.io on first use,
verifies their sha256 and caches them in `~/.cache/gamelog/android-wheels` (the
version is `PYSIDE_ANDROID_VERSION`; see the script header for the other
overrides). The tool downloads the NDK into `~/.pyside6_android_deploy` and
buildozer the SDK. The script regenerates the git-ignored `pysidedeploy.spec` with
`--init` every time (it holds machine-specific paths), pins the app icon
(`core/resources/icons/cards.png`; the default is a `.icns`), then builds from it.
The tool exposes no orientation option, so landscape and the version (read from
`core/_version.py`, which release-please bumps) go in through buildozer's
`SECTION_KEY` environment overrides. The APK lands in `dist/`. The tool wipes
`.buildozer/` and `deployment/` at the start of every run.

### python-for-android patches
The Qt bootstrap's `PythonActivity` needs three fixes, which `build_android.sh`
applies to a local copy of python-for-android at the commit the tool pins:

* `onActivityResult` never calls `super.onActivityResult`, so Qt never receives the
  result of an activity it started. The system file picker behind `QFileDialog`
  returned and the app froze with the dialog still "open".
* `onKeyDown` treats every key as Back, which swallowed keyboard input (fixed
  upstream in kivy/python-for-android#3376, after the pinned commit).
* The system bars and the window behind them are coloured to the system's
  light/dark mode (`utils/android/system_bars.java.snippet`), so the navigation
  bar is not white under a dark app.

Buildozer clones python-for-android itself, so the script keeps the patched copy in
`~/.cache/gamelog/python-for-android` and has git serve that clone (`insteadOf`,
set through the environment so no git config is touched), with `APP_P4A_COMMIT`
pointing at the patched commit. Drop this once upstream fixes the bootstrap.

### Signing and installing
APKs only install over each other if they share a signature. Local builds use
`~/.android/debug.keystore` and CI installs the same file from the
`ANDROID_DEBUG_KEYSTORE_BASE64` secret. Create it once (Android's default debug
key settings, so no further configuration is needed):

```
keytool -genkeypair -keystore debug.keystore -storepass android -alias androiddebugkey \
  -keypass android -keyalg RSA -keysize 2048 -validity 10000 \
  -dname "CN=Android Debug,O=Android,C=US"
base64 -i debug.keystore | gh secret set ANDROID_DEBUG_KEYSTORE_BASE64
```

Copy the same file to `~/.android/debug.keystore`, keep a backup outside the
repository (`*.keystore` and `*.jks` are git-ignored) and do not lose it. Without
the secret the workflow still builds, with a warning and a fresh signature.
Install with `adb install -r dist/Gamelog-*.apk`. On `INSTALL_FAILED_UPDATE_INCOMPATIBLE`
the installed app has another signature: export its data, `adb uninstall
org.gamelog.gamelog`, install, then import.

### Debugging on a device
* **Python log**: raise "Log level" to `INFO` or `DEBUG` in the settings dialog,
  then `adb logcat -s python:*`. Tracebacks from Qt slots end up there too.
* **System side** (picker, activities, crashes): `adb logcat -v time` filtered for
  `FATAL|AndroidRuntime|ActivityManager|onActivityResult`.
* **The database** (debug builds are debuggable, so `run-as` works; a release build
  would not allow it). Pull: `adb exec-out run-as org.gamelog.gamelog cat
  files/gamelog.db > backup.db`. Push: stop the app, `adb push` the file to
  `/data/local/tmp/`, then `adb shell run-as org.gamelog.gamelog cp
  /data/local/tmp/gamelog.db files/gamelog.db`. Importing from the settings
  dialog is safer, as it validates the file.

### Building on GitHub
`.github/workflows/android-apk.yml` runs `utils/build_android.sh` on an Ubuntu
runner (JDK 17, the autotools packages python-for-android needs including
`libltdl-dev`, and "y" fed to buildozer's SDK licence prompt, which nobody can
answer on a runner). `release-please.yml` calls it when Release Please creates a
release and attaches the debug APK to that release (events from the default token
cannot start a separate workflow, hence the call). It can also be run by hand from
the Actions tab for any branch or tag, optionally attaching the result to a
release, and the APK is always kept as a workflow artifact (`gamelog-apk`). A
manual run needs the workflow file on the default branch, and "Use workflow from"
picks which branch's copy runs. The SDK/NDK, wheels, python-for-android, buildozer
and Gradle downloads are cached; a cold build takes about 11 minutes. The caches
are per branch, so one saved by a run on another branch is not seen by `main`.

### Known gaps
* The screen is not kept awake on Android (`SleepBlocker` has no Android branch).
* Debug builds only; no `.aab`, release signing or Play Store.
* Full screen hides the system bars, but they come back whenever the on-screen
  keyboard opens, so "maximised" may suit the tablet better.
* Layouts are for tablets, not phones.
