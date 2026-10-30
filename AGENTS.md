# AGENTS.md

Gamelog: a PySide6 (Qt 6) desktop scorekeeper for board and card games,
backed by SQLite. Python 3.12+, managed with uv.

## Read before you dig
- `utils/developer_notes.md` is the reference: project layout, adding a game,
  player statistics (metrics and per-game hooks), tests, i18n, resources.
  Read the section you need, not the whole file.
- `core/` is game-agnostic; each game is a self-contained package under
  `games/<name>/`, registered by a `GameDefinition` in its `__init__.py`.
  Never special-case a game in `core/`: add an optional `GameDefinition`
  field or factory instead (see `short_name`, `round_winners`,
  `player_stats_factory`, `match_details_factory`).

## Commands (always `uv run`, never bare `python`)
```
uv run pytest -q                          # full suite, ~25 s, headless
uv run pytest -q tests/test_x.py -k name  # iterate on this first
uv run ruff check . && uv run ruff format --check .
uv run basedpyright core tests games      # see the note below
uv run gamelog.pyw                        # run the app
```
CI runs the same checks plus a 55% coverage floor.

## Token economy
- Never open `core/resources_rc.py` (3.4 MB, generated), `*.qm` (binary) or
  whole `*.ts` catalogues. Grep for the string you need.
- Locate code with `grep -n` and read line ranges; most UI files are long.
- Run the targeted tests while iterating, and the full suite once at the end.
- Render screens only for visual changes, and once: build the widget with
  `QT_QPA_PLATFORM=offscreen`, `show()`, `processEvents()`, then
  `widget.grab().save("out.png")` and look at the image. Inspect geometry in
  tests where you can instead.

## Conventions
- Conventional Commits; `feat`/`fix` titles feed release-please's changelog
  and CI lints PR titles. Work on `develop` (or a branch from it); `develop`
  is merged into `main` by the maintainer. Don't push or open PRs unless asked.
- Every user-visible string goes through `self.tr()` /
  `QCoreApplication.translate()`, translated for en_GB, es_ES and ca_ES.
- Statistics count finished matches only (`GenericMatch.FINISHED`, bound as a
  parameter). Bind every SQL value; nicks can contain quotes (`O'Brien`).
- Theme colours belong in `core/resources/styles/{light,dark}.qss`; don't
  hard-code light-only colours in widgets.
- Tooltips only for information the widget doesn't already show.
- Statistics tables: text columns left-aligned, figures right-aligned
  (`core/ui/tablestyle.py`).

## Pitfalls
- Translations: run `uv run utils/build_translations.py`, fill the new
  entries in each `.ts`, run it again, then `uv run utils/build_resources.py`.
  lupdate pre-fills an identical source string from elsewhere and marks it
  unfinished: check it, and disambiguate same-text/different-meaning strings
  with a comment argument (`self.tr("Won", "one match")`).
- The pre-commit hook rebuilds translations and may rewrite `<location>` line
  numbers in `.ts` files, failing the commit: stage those files and commit
  again.
- `ParticularStatsEngine` rewrites every `WHERE` in its queries, subqueries
  included, and repeats parameters per `WHERE`. Keep subqueries free of
  `WHERE` or account for it.
- Agent worktrees under `.claude/worktrees/` make an unscoped
  `uv run basedpyright` (and its pre-commit hook) report thousands of
  unrelated errors. Scope it to `core tests games`, or remove stale worktrees.
- Qt tests: widgets added to a shown layout appear only after
  `qapp.processEvents()`, and layout changes can take two passes. Use the
  `gamedb` (fresh SQLite per test) and `qapp` fixtures from
  `tests/conftest.py`.
