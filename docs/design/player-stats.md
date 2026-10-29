# Design: Player statistics screen

Status: ready for implementation · Target branch: off `develop`

## Goal

Add a **player-centred statistics screen**: pick one player and see how they do
across every game. This includes an overall summary, recent form, a per-game
breakdown and head-to-head records against other players.

Today's statistics are game-centred. `core/engine/stats.py` aggregates per
*game* and per player within that game, and they are only shown as quick stats
inside a game panel. Nothing answers "how is Rosa doing overall?" or "who beats
Rosa most often?".

## Scope

In scope (v1):

1. Qt-free engine module `core/engine/playerstats.py` with the queries and
   metric logic.
2. A new screen, `core/ui/playerstats.py`, that the new-game screen opens the
   same way it opens the match explorer.
3. Translations (en/es/ca) and tests.

Out of scope (do **not** build): game-specific player stats (bids, kills,
phases…), Elo or any other rating, score charts, links from the player list or
the match explorer, changes to the existing `StatsEngine` / quick stats. Also
leave the unused `core/ui/gamestats.py` placeholder alone.

## Read these first

Follow these patterns closely. The new code should look like it was written by
the same person.

| File | Why |
|------|-----|
| `core/engine/history.py` | **Template for the engine module**: Qt-free, frozen dataclasses, `db.execute` with bound `?` parameters, `parse_db_time`, and `games_with_matches` / `players_with_matches`. |
| `core/ui/explorer.py` | **Template for the screen**: a `Tab` subclass with a `backRequested` signal, `initUI` / `retranslateUI`, combos, a sortable table and `SortItem`, `_format_duration`, and refreshing on `showEvent`. |
| `core/ui/mainwindow.py` (`showExplorer`, `hideExplorer`, `__init__`, `retranslateUi`) | How a full screen is swapped in place of the new-game screen. |
| `core/ui/newgame.py` (`historyButton`, `showHistory`, `retranslateUI`) | Where the entry button goes. |
| `core/model/match.py` | `GenericMatch.FINISHED` and the other state constants. |
| `core/engine/db.py` | The schema (`Match`, `MatchPlayer`) and `db.execute` / `db.queryDict`. |
| `tests/test_history.py`, `tests/conftest.py` | Test fixtures (`gamedb`, `qapp`) and how matches are seeded. |
| `utils/developer_notes.md`, `utils/build_translations.py` | Translation workflow. |

## Data rules

These apply to every metric:

- **Only finished matches count**: `Match.state = GenericMatch.FINISHED`. Pass
  the constant as a bound parameter; don't hard-code `1`. Saved, cancelled and
  interrupted matches are ignored.
- **A win** is `MatchPlayer.winner = 1`. Ties exist: several rows of one match
  can have `winner = 1` (a "shared win"). A shared win counts as a win in the
  win counts and streaks. It counts as a *fraction* in the performance index
  (see below).
- **Never compare raw scores across games.** Some games are lowest-wins
  (Toma6), some use elimination (Remigio), and their ranges differ widely. Score
  figures appear only in the per-game table, as min / avg / max, with no "best"
  column, because the engine doesn't know which direction is good.
- **Match order** for form and streaks: `finished` ascending, then `idMatch`
  ascending.
- **Optional game filter.** Every public function takes
  `games: tuple[str, ...] = ()`, where empty means all games, the same as
  `MatchFilter.games` in `history.py`. When set, every section is restricted to
  those games.

### Performance index (the key metric)

Raw win % is misleading across player counts: winning 1 in 3 two-player
games is poor, while winning 1 in 3 six-player games is excellent. Define, over
the counted matches that have at least one winner:

- `expected = Σ 1 / n_players(match)`
- `earned   = Σ 1 / n_winners(match)`, summed over the matches this player won
- `performance = earned / expected`, or `None` when `expected == 0`

`1.0` means "wins exactly as often as chance predicts", `2.0` means "twice as
often". Across all players in one match, both sums add up to exactly 1, so the
index is fair. Show it to two decimals (e.g. `1.35×`) with a tooltip that
explains it. Matches where nobody has `winner = 1` count towards `played` but
are excluded from `expected` and `earned`.

## Engine: `core/engine/playerstats.py`

Module docstring in the style of `history.py`. Suggested API (names may be
tweaked, but keep it Qt-free and typed):

```python
@dataclass(frozen=True)
class PlayerSummary:
    nick: str
    played: int
    wins: int  # including shared wins
    shared_wins: int
    win_rate: float | None  # wins / played, None if played == 0
    performance: float | None  # see "Performance index"
    time_played: int  # Σ Match.elapsed, seconds
    first_played: datetime.datetime | None  # min started
    last_played: datetime.datetime | None  # max finished
    favourite_game: str | None  # most played; ties -> most recently played


@dataclass(frozen=True)
class GameBreakdown:  # one row per game the player has played
    game: str
    played: int
    wins: int
    win_rate: float | None
    performance: float | None
    min_score: int
    avg_score: int  # rounded
    max_score: int
    time_played: int


@dataclass(frozen=True)
class Form:
    recent: tuple[bool, ...]  # last N results, oldest -> newest, True = win
    current_streak: int  # >0 winning streak length, <0 losing, 0 if none
    longest_win_streak: int
    longest_loss_streak: int


@dataclass(frozen=True)
class HeadToHead:  # one row per opponent sharing >= 1 counted match
    opponent: str
    together: int  # counted matches both played
    me_only: int  # player won, opponent did not
    them_only: int  # opponent won, player did not
    both: int  # shared victory between the two
    neither: int  # someone else won (or no winner)


FORM_LENGTH = 10
RIVAL_MIN_MATCHES = 3  # threshold for nemesis / favourite victim


def player_summary(nick: str, games: tuple[str, ...] = ()) -> PlayerSummary: ...
def game_breakdown(nick: str, games: tuple[str, ...] = ()) -> list[GameBreakdown]: ...
def player_form(
    nick: str, games: tuple[str, ...] = (), length: int = FORM_LENGTH
) -> Form: ...
def head_to_head(nick: str, games: tuple[str, ...] = ()) -> list[HeadToHead]: ...
def nemesis(rows: list[HeadToHead]) -> HeadToHead | None: ...
def favourite_victim(rows: list[HeadToHead]) -> HeadToHead | None: ...
def games_played_by(nick: str) -> list[str]: ...  # for the game combo
```

Notes:

- `game_breakdown` is sorted by `played` desc, then game name. `head_to_head`
  is sorted by `together` desc, then opponent nick.
- `nemesis` is the opponent with the highest `them_only`, considering only rows
  with `together >= RIVAL_MIN_MATCHES` and `them_only > 0`. Break ties by higher
  `them_only - me_only`, then by nick. `favourite_victim` mirrors it using
  `me_only`. Return `None` when nobody qualifies.
- An unknown nick, or a player with no counted matches, must return empty or
  zero results (`played == 0`, `None` rates, empty lists), not raise.
- Prefer a few clear SQL queries plus small Python loops over one clever query.
  Streaks and fractional wins are easier and safer in Python. A practical
  approach is one query that fetches this player's counted matches with
  `idMatch, Game_name, finished, elapsed, totalScore, winner, n_players,
  n_winners` (subqueries or a `GROUP BY` over `MatchPlayer`), then computes the
  summary, breakdown and form from it. Use a second query for head-to-head
  (self-join `MatchPlayer` on `idMatch`).
- Always bind parameters. Nicks may contain quotes (the tests use `O'Brien`).

## UI: `core/ui/playerstats.py`

`PlayerStatsWidget(Tab)` with `backRequested = Signal()`, structured like
`MatchExplorerWidget`.

Layout, top to bottom:

1. **Toolbar row**: a back button (same style as the explorer's), a **player**
   combo (from `players_with_matches()`, with favourites first if that is
   trivial via `db.isPlayerFavourite`, otherwise alphabetical), and a **game**
   combo ("All games" + `games_played_by(nick)`). Changing either combo
   refreshes everything.
2. **Summary**: a compact grid of label/value pairs: Played, Wins (with shared
   wins in brackets when > 0), Win rate, Performance (with a tooltip
   explaining 1.0×), Time played (reuse or move the explorer's
   `_format_duration`; don't duplicate it), Favourite game, First / last played
   (local date, formatted like the explorer's dates). Hide "Favourite game"
   when a single game is selected.
3. **Form**: the last 10 results as a row of small coloured W / L markers
   (reuse the explorer's status-colour approach so it respects light/dark
   themes), followed by "Current streak", "Longest winning streak" and "Longest
   losing streak".
4. **Per game** table (hidden when a single game is selected): Game, Played,
   Wins, Win %, Performance, Min, Avg, Max, Time. Sortable with numeric sort
   keys (`SortItem`).
5. **Head to head** table: Opponent, Together, Won (`me_only`), Lost
   (`them_only`), Shared (`both`), Neither. Sortable. Above it, one line:
   "Nemesis: X (lost N of M)" / "Favourite victim: Y (won N of M)", omitted when
   `None`.

Put sections 4 and 5 in a vertical `QSplitter` or a scroll area so the window
stays usable at the app's default size. Show a short "No finished matches yet"
message instead of empty widgets when the player list is empty.

Refresh the player list in `showEvent`, as the explorer does, so newly finished
matches appear. Keep the selected player if they still exist.

### Wiring

- `core/ui/newgame.py`: add `statsButton` next to `historyButton`, with the same
  size policy, text `📊` and tooltip `self.tr("Player statistics")`, and a
  `showPlayerStats()` that calls `self._parent.showPlayerStats()`.
- `core/ui/mainwindow.py`: create `self.playerStatsTab = PlayerStatsWidget(self)`
  next to `explorerTab`, connect `backRequested` to `hidePlayerStats`, add it to
  `verticalLayout` hidden, and add it to `retranslateUi`. Add
  `showPlayerStats` / `hidePlayerStats` mirroring `showExplorer` /
  `hideExplorer`, with window title `self.tr("Gamelog - Player statistics")`.
- Every user-visible string goes through `self.tr(...)`.

## Translations

1. `uv run utils/build_translations.py` (lupdate + lrelease).
2. Fill the new `<message>` entries in `core/resources/i18n/core_es_ES.ts` and
   `core_ca_ES.ts` with proper Spanish and Catalan (edit the XML directly,
   remove `type="unfinished"`). `en_GB` entries can stay as the source text.
3. Re-run `uv run utils/build_translations.py` to compile the `.qm` files, then
   `uv run utils/build_resources.py` to regenerate `core/resources_rc.py`.

## Tests: `tests/test_playerstats.py`

Engine tests: seed rows directly with `db.execute` into `Match` (with
`state=GenericMatch.FINISHED`, `started`, `finished`, `elapsed`) and
`MatchPlayer`, using a small helper such as
`_match(game, {nick: (score, winner)}, finished=..., state=...)`. This keeps the
numbers exact. Add one end-to-end test that plays a real Ratuki match through
the engine, like `_finished_ratuki` in `tests/test_history.py`, and checks it
shows up.

Cover at least:

- Only finished matches count (seed a saved and a cancelled one too).
- Performance math: e.g. one win in a 2-player match + one loss in a 4-player
  match → expected 0.75, earned 1, performance ≈ 1.333.
- Shared win: counted in `wins` and `shared_wins`, and contributes `1/k` to
  `earned`.
- Matches with no winner count as played but are excluded from performance.
- Form: order by `finished`; current, longest-win and longest-loss streaks;
  `recent` is capped at `length`.
- Head-to-head buckets (`me_only`, `them_only`, `both`, `neither`); nemesis /
  victim thresholds and tie-breaks; `None` when nobody qualifies.
- Game filter restricts every function.
- Unknown player / no matches → zeros and empty lists, no exception.
- A nick with a quote (`O'Brien`).
- Widget smoke test (`qapp` + `gamedb`): build `PlayerStatsWidget`, seed data,
  trigger `showEvent` / select a player, and assert the tables have the expected
  row counts. Also check that the main window toggles between the new-game
  screen and the stats screen (see `tests/test_mainwindow.py`).

## Definition of done

- `uv run pytest` passes (whole suite).
- `uv run ruff check .` and `uv run ruff format --check .` are clean.
- `uv run basedpyright` reports no new errors in the touched files.
- The app runs with `uv run gamelog.pyw`: the 📊 button opens the screen, combos
  work, back returns to the new-game screen, and switching language updates the
  screen's text.
- README "Features" gains a short bullet for player statistics.
- Work on a feature branch cut from `develop`. Commits use Conventional Commits
  (e.g. `feat: player statistics screen`), because release-please builds the
  changelog from them. Don't push or open a PR unless asked: `develop` is merged
  into `main` by the maintainer.
- Always use `uv run`, never bare `python`.
