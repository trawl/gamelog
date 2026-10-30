"""Player-centred statistics: how one player does across every game.

This is the read side of the player statistics screen. It carries no Qt
dependency. Only finished matches count, scores are never compared across
games, and the performance index adjusts win counts for the number of players
so that results compare fairly between games.
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass, field

from core.engine.db import db
from core.engine.history import PlayerResult
from core.engine.timeutil import parse_db_time
from core.model.match import GenericMatch
from core.registry import registry

logger = logging.getLogger(__name__)

FORM_LENGTH = 10
# Opponents met fewer times than this are never a nemesis or favourite victim.
RIVAL_MIN_MATCHES = 3


@dataclass(frozen=True)
class PlayerSummary:
    nick: str
    played: int
    wins: int  # including shared wins
    shared_wins: int
    win_rate: float | None  # wins / played, None if played == 0
    performance: float | None  # see _performance
    time_played: int  # seconds
    first_played: datetime.datetime | None
    last_played: datetime.datetime | None
    favourite_game: str | None  # most played; ties -> most recently played


@dataclass(frozen=True)
class PlayerStat:
    """One card of a player's statistics in a game: already translated and
    formatted text. ``tip`` is only for what the card does not already say."""

    caption: str
    value: str
    tip: str | None = None


@dataclass(frozen=True)
class GameBreakdown:
    """One row per game the player has played."""

    game: str
    played: int
    wins: int
    win_rate: float | None
    performance: float | None
    min_score: int
    avg_score: int
    max_score: int
    time_played: int


@dataclass(frozen=True)
class FormResult:
    """One of the latest matches: its outcome and what it was."""

    won: bool
    game: str
    finished: datetime.datetime | None
    players: tuple[PlayerResult, ...]  # everyone who took part, in seat order
    idMatch: int = 0
    # Extra text per nick the game wants shown with the match (see
    # ``GameDefinition.match_details``), such as Phase 10's completed phases.
    extras: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Form:
    recent: tuple[FormResult, ...]  # last results, oldest -> newest
    current_streak: int  # >0 winning streak, <0 losing streak, 0 if none
    longest_win_streak: int
    longest_loss_streak: int


@dataclass(frozen=True)
class HeadToHead:
    """The record against one opponent over the matches both played."""

    opponent: str
    together: int
    me_only: int  # the player won, the opponent did not
    them_only: int  # the opponent won, the player did not
    both: int  # shared victory between the two
    neither: int  # someone else won (or nobody did)


@dataclass(frozen=True)
class _Played:
    """One counted match of the player."""

    idMatch: int
    game: str
    started: datetime.datetime | None
    finished: datetime.datetime | None
    elapsed: int
    score: int
    won: bool
    n_players: int
    n_winners: int


def _games_clause(games: tuple[str, ...]) -> tuple[str, tuple]:
    """SQL condition (over ``Match m``) restricting to ``games``, if any."""
    if not games:
        return "", ()
    return f" AND m.Game_name IN ({','.join('?' * len(games))})", tuple(games)


def _played(nick: str, games: tuple[str, ...]) -> list[_Played]:
    """The finished matches of ``nick`` in play order."""
    extra, extra_params = _games_clause(games)
    cur = db.execute(
        "SELECT m.idMatch, m.Game_name, m.started, m.finished, m.elapsed, "
        "mp.totalScore, mp.winner, "
        "(SELECT COUNT(*) FROM MatchPlayer a WHERE a.idMatch=m.idMatch) "
        "AS n_players, "
        "(SELECT COUNT(*) FROM MatchPlayer a "
        "WHERE a.idMatch=m.idMatch AND a.winner=1) AS n_winners "
        "FROM Match m JOIN MatchPlayer mp ON mp.idMatch=m.idMatch "
        f"WHERE mp.nick=? AND m.state=?{extra} "
        "ORDER BY m.finished, m.idMatch",
        (nick, GenericMatch.FINISHED, *extra_params),
    )
    return [
        _Played(
            idMatch=row["idMatch"],
            game=str(row["Game_name"]),
            started=parse_db_time(row["started"]),
            finished=parse_db_time(row["finished"]),
            elapsed=int(row["elapsed"] or 0),
            score=int(row["totalScore"] or 0),
            won=row["winner"] == 1,
            n_players=int(row["n_players"]),
            n_winners=int(row["n_winners"]),
        )
        for row in cur
    ]


def _performance(matches: list[_Played]) -> float | None:
    """Wins relative to what chance predicts: 1.0 is par, 2.0 twice as often.

    Matches with no winner are left out of both sides of the ratio.
    """
    expected = sum(1 / m.n_players for m in matches if m.n_winners > 0)
    if expected == 0:
        return None
    earned = sum(1 / m.n_winners for m in matches if m.won)
    return earned / expected


def _rate(wins: int, played: int) -> float | None:
    return wins / played if played else None


def _favourite(matches: list[_Played]) -> str | None:
    """Most played game; ties go to the one played most recently."""
    counts: dict[str, int] = {}
    for m in matches:  # in play order, so the last seen is the most recent
        counts[m.game] = counts.get(m.game, 0) + 1
    if not counts:
        return None
    last = {m.game: i for i, m in enumerate(matches)}
    return max(counts, key=lambda g: (counts[g], last[g]))


def player_summary(nick: str, games: tuple[str, ...] = ()) -> PlayerSummary:
    """Overall figures of ``nick`` over the counted matches."""
    matches = _played(nick, games)
    wins = sum(m.won for m in matches)
    started = [m.started for m in matches if m.started]
    finished = [m.finished for m in matches if m.finished]
    return PlayerSummary(
        nick=nick,
        played=len(matches),
        wins=wins,
        shared_wins=sum(m.won and m.n_winners > 1 for m in matches),
        win_rate=_rate(wins, len(matches)),
        performance=_performance(matches),
        time_played=sum(m.elapsed for m in matches),
        first_played=min(started, default=None),
        last_played=max(finished, default=None),
        favourite_game=_favourite(matches),
    )


def game_breakdown(nick: str, games: tuple[str, ...] = ()) -> list[GameBreakdown]:
    """One row per game ``nick`` has played, most played first."""
    by_game: dict[str, list[_Played]] = {}
    for m in _played(nick, games):
        by_game.setdefault(m.game, []).append(m)

    rows = []
    for game, matches in by_game.items():
        scores = [m.score for m in matches]
        wins = sum(m.won for m in matches)
        rows.append(
            GameBreakdown(
                game=game,
                played=len(matches),
                wins=wins,
                win_rate=_rate(wins, len(matches)),
                performance=_performance(matches),
                min_score=min(scores),
                avg_score=round(sum(scores) / len(scores)),
                max_score=max(scores),
                time_played=sum(m.elapsed for m in matches),
            )
        )
    rows.sort(key=lambda r: (-r.played, r.game))
    return rows


def player_form(
    nick: str, games: tuple[str, ...] = (), length: int = FORM_LENGTH
) -> Form:
    """The latest results of ``nick`` and their winning and losing streaks."""
    played = _played(nick, games)
    results = [m.won for m in played]

    longest = {True: 0, False: 0}
    run = 0
    previous: bool | None = None
    for result in results:
        run = run + 1 if result == previous else 1
        previous = result
        longest[result] = max(longest[result], run)

    current = 0
    if results:
        current = run if results[-1] else -run
    latest = played[-length:] if length > 0 else []
    players = _players_of([m.idMatch for m in latest])
    extras = _extras_of(latest)
    return Form(
        recent=tuple(
            FormResult(
                m.won,
                m.game,
                m.finished,
                players.get(m.idMatch, ()),
                m.idMatch,
                extras.get(m.idMatch, {}),
            )
            for m in latest
        ),
        current_streak=current,
        longest_win_streak=longest[True],
        longest_loss_streak=longest[False],
    )


def _extras_of(matches: list[_Played]) -> dict[int, dict[str, str]]:
    """What each game adds about the matches ``matches``, asked only for the
    games that have something to add and only for these matches."""
    by_game: dict[str, list[int]] = {}
    for m in matches:
        by_game.setdefault(m.game, []).append(m.idMatch)
    extras: dict[int, dict[str, str]] = {}
    for game, ids in by_game.items():
        definition = registry.get(game)
        if definition is not None:
            extras.update(definition.match_details(ids))
    return extras


def _players_of(ids: list[int]) -> dict[int, tuple[PlayerResult, ...]]:
    """Everyone who played each of the matches ``ids``, in seat order."""
    if not ids:
        return {}
    cur = db.execute(
        "SELECT idMatch, nick, totalScore, winner FROM MatchPlayer "
        f"WHERE idMatch IN ({','.join('?' * len(ids))}) ORDER BY idMatch, rowid",
        tuple(ids),
    )
    players: dict[int, list[PlayerResult]] = {}
    for row in cur:
        players.setdefault(row["idMatch"], []).append(
            PlayerResult(
                str(row["nick"]), int(row["totalScore"] or 0), row["winner"] == 1
            )
        )
    return {idMatch: tuple(rows) for idMatch, rows in players.items()}


def head_to_head(nick: str, games: tuple[str, ...] = ()) -> list[HeadToHead]:
    """The record of ``nick`` against every opponent met in a counted match,
    most met first."""
    extra, extra_params = _games_clause(games)
    cur = db.execute(
        "SELECT o.nick AS opponent, mp.winner AS mine, o.winner AS theirs "
        "FROM Match m "
        "JOIN MatchPlayer mp ON mp.idMatch=m.idMatch "
        "JOIN MatchPlayer o ON o.idMatch=m.idMatch AND o.nick<>mp.nick "
        f"WHERE mp.nick=? AND m.state=?{extra}",
        (nick, GenericMatch.FINISHED, *extra_params),
    )
    records: dict[str, list[int]] = {}
    for row in cur:
        mine, theirs = row["mine"] == 1, row["theirs"] == 1
        # together, me_only, them_only, both, neither
        record = records.setdefault(str(row["opponent"]), [0, 0, 0, 0, 0])
        record[0] += 1
        if mine and theirs:
            record[3] += 1
        elif mine:
            record[1] += 1
        elif theirs:
            record[2] += 1
        else:
            record[4] += 1

    rows = [HeadToHead(opponent, *record) for opponent, record in records.items()]
    rows.sort(key=lambda r: (-r.together, r.opponent))
    return rows


def nemesis(rows: list[HeadToHead]) -> HeadToHead | None:
    """The opponent who beats the player most often, if any qualifies.

    Only opponents met often enough and with a losing record count, so an
    opponent is never both nemesis and favourite victim."""
    candidates = [
        r for r in rows if r.together >= RIVAL_MIN_MATCHES and r.them_only > r.me_only
    ]
    return min(
        candidates,
        key=lambda r: (-r.them_only, -(r.them_only - r.me_only), r.opponent),
        default=None,
    )


def favourite_victim(rows: list[HeadToHead]) -> HeadToHead | None:
    """The opponent the player beats most often, if any qualifies: met often
    enough, with a winning record."""
    candidates = [
        r for r in rows if r.together >= RIVAL_MIN_MATCHES and r.me_only > r.them_only
    ]
    return min(
        candidates,
        key=lambda r: (-r.me_only, -(r.me_only - r.them_only), r.opponent),
        default=None,
    )


def games_played_by(nick: str) -> list[str]:
    """Names of the games ``nick`` has a finished match in."""
    cur = db.execute(
        "SELECT DISTINCT m.Game_name FROM Match m "
        "JOIN MatchPlayer mp ON mp.idMatch=m.idMatch "
        "WHERE mp.nick=? AND m.state=? ORDER BY m.Game_name",
        (nick, GenericMatch.FINISHED),
    )
    return [str(row["Game_name"]) for row in cur]


def player_full_name(nick: str) -> str:
    """The full name stored for ``nick``, or the nick itself without one."""
    cur = db.execute("SELECT fullName FROM Player WHERE nick=?", (nick,))
    row = cur.fetchone()
    return str(row["fullName"]) if row and row["fullName"] else nick


def engine_row(game: str, nick: str) -> dict:
    """The statistics row of ``nick`` in ``game`` from the game's own stats
    engine, with every column the game adds; empty when there is none."""
    engine = registry.create_stats_engine(game)
    engine.update()
    rows = engine.getPlayerGameStats(game) or []
    return next((r for r in rows if r["nick"] == nick), {})


def game_player_stats(nick: str, game: str) -> list[PlayerStat]:
    """The cards the game adds for ``nick``, none for games without any."""
    definition = registry.get(game)
    return definition.player_stats(nick) if definition else []


@dataclass(frozen=True)
class RoundPerformance:
    """Rounds won against what chance predicts, as the performance index does
    for matches: 1.0 is par, 2.0 twice as often."""

    index: float | None  # None when no round had a winner
    won: int
    played: int


def round_performance(nick: str, game: str) -> RoundPerformance:
    """How often ``nick`` wins a round of ``game``, weighing each round by the
    players in it: those already out of a match have no row for it."""
    cur = db.execute(
        "SELECT r.winner, "
        "(SELECT COUNT(*) FROM Round a "
        "WHERE a.idMatch=r.idMatch AND a.idRound=r.idRound) AS n_players, "
        "(SELECT COUNT(*) FROM Round a "
        "WHERE a.idMatch=r.idMatch AND a.idRound=r.idRound AND a.winner=1) "
        "AS n_winners "
        "FROM Round r JOIN Match m ON m.idMatch=r.idMatch "
        "WHERE m.state=? AND m.Game_name=? AND r.nick=?",
        (GenericMatch.FINISHED, game, nick),
    )
    rows = list(cur)
    decided = [r for r in rows if r["n_winners"] > 0]
    expected = sum(1 / r["n_players"] for r in decided)
    earned = sum(1 / r["n_winners"] for r in decided if r["winner"] == 1)
    won = sum(1 for r in rows if r["winner"] == 1)
    return RoundPerformance(earned / expected if expected else None, won, len(rows))


def rounds_per_match(nick: str, game: str) -> float | None:
    """Average number of rounds of the finished ``game`` matches of ``nick``."""
    cur = db.execute(
        "SELECT AVG(n) AS rounds FROM ("
        "SELECT COUNT(DISTINCT r.idRound) AS n FROM Round r "
        "JOIN Match m ON m.idMatch=r.idMatch "
        "WHERE m.state=? AND m.Game_name=? AND r.idMatch IN ("
        "SELECT idMatch FROM MatchPlayer WHERE nick=?) GROUP BY r.idMatch)",
        (GenericMatch.FINISHED, game, nick),
    )
    row = cur.fetchone()
    return None if row is None or row["rounds"] is None else float(row["rounds"])
