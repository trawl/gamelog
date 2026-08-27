# Gamelog

A cross-platform desktop app for keeping score across your favourite board and
card games — round-by-round scoreboards, live score plots, per-game statistics,
and pause/resume for matches that span several sittings.

[![CI](https://github.com/trawl/gamelog/actions/workflows/ci.yml/badge.svg)](https://github.com/trawl/gamelog/actions/workflows/ci.yml)

<!-- Screenshots: a couple here (scoreboard + statistics) would really help.
     e.g. ![Scoreboard](docs/scoreboard.png) -->

## Features

- **Ten games, one app** — a shared scoring framework with game-specific rules
  (see the table below).
- **Live scoreboard & plots** — enter each round and watch running totals and a
  score-over-time chart update instantly.
- **Statistics** — general and per-player stats plus game records, kept across
  all your matches.
- **Pause & resume** — save a match mid-game and pick it up later.
- **Dealer tracking** — automatic dealer rotation (round-robin or winner-deals).
- **Multi-language** — English, Spanish and Catalan.
- **Light & dark themes**, following the system appearance by default.
- **Cross-platform** — macOS, Linux and Windows.
- Keeps the screen awake while a match is in progress.

## Supported games

| Game | Players | Description |
|------|:-------:|-------------|
| Carcassonne | 6 | Tile-laying board game (home scoring) |
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
installed, clone this repository and run, from the project root:

```bash
uv run gamelog.pyw
```

`uv` will create a local virtual environment and install everything the first
time. Requires Python 3.12+ (uv fetches a suitable interpreter if needed).

## Configuration

- **Language, theme and log level** are set in the in-app settings dialog and
  persisted between runs.
- **Environment overrides** (handy for debugging): `GAMELOG_LOG_LEVEL`
  (e.g. `DEBUG`) raises verbosity, and `GAMELOG_DB` points the app at a specific
  database file.
- **Where scores live**: a local SQLite database — the project's `db/` folder in
  development, or your OS user-data directory when run as an installed app.

## Development

Development setup, the test suite, linting/pre-commit, translations and resource
building are documented in [utils/developer_notes.md](utils/developer_notes.md).

Quick reference:

```bash
uv run pytest                     # run the tests
uv run pytest --cov               # ...with coverage
uv run ruff check . && uv run ruff format --check .   # lint + format
uv run pre-commit install         # enable the git pre-commit hooks
```

### Adding a new game

The app is organised so that each game is a self-contained package under
`games/`, and adding one is essentially dropping in a directory — the framework
discovers and wires it up automatically. See the step-by-step guide in
[utils/developer_notes.md](utils/developer_notes.md#adding-a-new-game).

## Built with

- [Python](https://www.python.org/) 3.12+
- [PySide6](https://doc.qt.io/qtforpython/) (Qt for Python)
- [uv](https://github.com/astral-sh/uv) for environment and dependency management

## License

Released under the [MIT License](LICENSE).
