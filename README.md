# Gamelog

A cross-platform app (macOS, Linux, Windows and, experimentally, Android
tablets) for keeping score across your favourite board and card games —
round-by-round scoreboards, live score plots, per-game statistics, and
pause/resume for matches that span several sittings.

[![CI](https://github.com/trawl/gamelog/actions/workflows/ci.yml/badge.svg)](https://github.com/trawl/gamelog/actions/workflows/ci.yml)

<!-- Screenshots: a couple here (scoreboard + statistics) would really help.
     e.g. ![Scoreboard](docs/scoreboard.png) -->

## Features

- **Fourteen games, one app** — a shared scoring framework with game-specific rules
  (see the table below).
- **Live scoreboard & plots** — enter each round and watch running totals and a
  score-over-time chart update instantly.
- **Statistics** — general and per-player stats plus game records, kept across
  all your matches.
- **Rules at hand** — a quick-reference sheet for every game, opened from the 📖
  button on the new-game and scoreboard screens, with a link to the official rule
  book where one is available.
- **Pause & resume** — save a match mid-game and pick it up later.
- **Match history** — browse every match ever played from the new-game screen,
  filter by game, players, winner, date, length or outcome (finished, saved,
  cancelled), and open any of them: saved ones resume, finished ones show their
  final scoreboard.
- **Player statistics** — pick a player from the 📊 button on the new-game screen
  to see their summary, recent form, a per-game breakdown and head-to-head
  records, with a chance-adjusted performance index that compares fairly across
  different player counts.
- **Dealer tracking** — automatic dealer rotation (round-robin or winner-deals).
- **Multi-language** — English, Spanish and Catalan.
- **Light & dark themes**, following the system appearance by default.
- **Back up and move your data** — export the whole database to a file and import
  it again from the settings dialog, on every platform (handy for moving your
  history between a computer and a tablet).
- **Full screen by default**, with F11 to toggle it on desktop.
- **Cross-platform** — macOS, Linux and Windows, plus an experimental Android
  build for tablets (see [Android](#android-tablets-experimental)).
- Keeps the screen awake while a match is in progress (macOS, Windows and X11
  Linux; not yet on Android).

## Supported games

| Game | Players | Description |
|------|:-------:|-------------|
| Azul / Summer Pavilion | 4 | Tile-drafting board game, original and Summer Pavilion editions, with their end-of-game bonuses |
| Carcassonne | 6 | Tile-laying board game (home scoring) |
| Catan | 6 | Trading and building board game; tracks settlements, cities, longest road, largest army and VP cards |
| Parchís | 6 | Classic Spanish board game; tracks goals scored and kills per turn |
| Phase 10 / Master | 6 | Rummy-style card game, Standard and Master editions |
| Pocha | 6 | Spanish trick-taking / bidding card game |
| Qwirkle | 4 | Tile-matching game |
| Ratuki | 5 | Fast-paced card game |
| Remigio | 12 | Rummy-style card game (elimination) |
| Scrabble | 4 | Word game |
| Skull King | 8 | Trick-taking card game with bidding |
| Toma6 | 10 | "6 nimmt!"-style card game (lowest score wins) |

## Running Gamelog

The easiest way is with [uv](https://github.com/astral-sh/uv). Once it's
available, you can run Gamelog it directly from the repository without installation:

```bash
uvx https://github.com/trawl/gamelog.git
```

Alternatively, you can install it as a uv tool in your device:

```bash
uv tool install https://github.com/trawl/gamelog.git
gamelog
```

Or clone the repository and run from the project root:

```bash
uv run gamelog.pyw
```

In all this cases `uv` will create a local virtual environment and install
everything the first time. Requires Python 3.12+ (uv fetches a suitable 
interpreter if needed).

You may also install it as a traditional Python package and run it:

```bash
pip install https://github.com/trawl/gamelog.git
gamelog
```

On Linux, the app writes a small `gamelog.desktop` entry and its icon under
`~/.local/share` (or `$XDG_DATA_HOME`) the first time it runs to make it
available as an application from the launcher. The entry relaunches the app
the same way you last started it (via `uvx`, the installed `gamelog` command,
or `gamelog.pyw` from a checkout) and is refreshed on every run. Delete those
two files if you ever want to remove all traces of the app.

### Android (tablets, experimental)

Gamelog also runs on Android, built with Qt for Python's
`pyside6-android-deploy`. It is meant for tablets, in landscape; phones are not
a goal and the layouts will be cramped there. The package is a 64-bit ARM
(`arm64-v8a`) **debug** build for Android 9 or later, so it is not on the Play
Store and is installed by hand:

1. Download `Gamelog-<version>-arm64-v8a-debug.apk` from the release page, or build it yourself: see the Android section of
   [utils/developer_notes.md](utils/developer_notes.md#android-tablet-experimental).
2. Copy it to the tablet and open it (allowing installs from that source), or
   with the tablet connected over USB:

   ```bash
   adb install -r Gamelog-<version>-arm64-v8a-debug.apk
   ```

Some things work differently with a finger:

- **Player lists**: double-tap a player to move them between "available" and
  "selected". Long-press a player until the row highlights, then lift your finger
  for what a right-click does on desktop (toggle favourite, or set the dealer),
  or drag to reorder, or drag over the other list to move them across.
- **Pop-ups** have their own Close/Cancel button, as there is no window close
  button, and the new-game screen has a 🚪 quit button.
- **Your data** is in the app's private storage, which a file browser cannot see:
  use the export and import buttons (⬆ ⬇) at the bottom of the settings dialog to
  back it up or to copy a database from another device.
- **Updating**: a new APK installs over the old one only if both were signed with
  the same key (all official builds are). If Android says the signatures do not
  match, export your data first, uninstall the app, install the new one and import
  the data again.

## Configuration

- **Language, theme, log level and window mode** are set in the in-app settings
  dialog and persisted between runs. The window mode is full screen by default,
  or windowed (maximised on Android) if you prefer; on desktop F11 toggles it.
  The same dialog has the **Export/Import database** buttons and, at its
  bottom-left, the **About** button (there is no menu bar except on macOS).
- **Per-game options** — turn timers, end-score thresholds, dealer policy
  (round-robin or winner-deals), and other game-specific preferences are also
  configurable in the settings dialog, under each game's own section.
- **Environment overrides** (handy for debugging): `GAMELOG_LOG_LEVEL`
  (e.g. `DEBUG`) raises verbosity, and `GAMELOG_DB` points the app at a specific
  database file.
- **Where scores live**: a local SQLite database — the project's `db/` folder in
  development, or your OS user-data directory when run as an installed app (the
  app's private storage on Android). Importing a database replaces the current
  data after saving a backup of it in a `backups/` folder next to the database
  (the last two are kept).

## Development

Development setup, the test suite, linting/pre-commit, translations and resource
building are documented in [utils/developer_notes.md](utils/developer_notes.md).

Quick reference:

```bash
uv run pytest                     # run the tests
uv run pytest --cov               # ...with coverage
uv run ruff check . && uv run ruff format --check .   # lint + format
uv run pre-commit install         # enable the git pre-commit hooks
utils/build_android.sh            # build the Android APK into dist/ (see the notes)
```

### Adding a new game

The app is organised so that each game is a self-contained package under
`games/`, and adding one is essentially dropping in a directory — the framework
discovers and wires it up automatically. See the step-by-step guide in
[utils/developer_notes.md](utils/developer_notes.md#adding-a-new-game).

## Built with

- [Python](https://www.python.org/) 3.12+
- [PySide6](https://doc.qt.io/qtforpython/) (Qt for Python), on Android deployed
  with `pyside6-android-deploy` ([python-for-android](https://github.com/kivy/python-for-android)
  and [buildozer](https://github.com/kivy/buildozer) underneath)
- [uv](https://github.com/astral-sh/uv) for environment and dependency management

## License

Released under the [MIT License](LICENSE).
