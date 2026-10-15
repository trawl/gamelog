"""Browsing of every stored match: filtering, summaries and loading.

This is the read side of the match archive used by the match explorer. It
carries no Qt dependency; the UI turns a :class:`MatchFilter` into a list of
:class:`MatchSummary`.
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass, field

from core.engine.db import db
from core.engine.timeutil import parse_db_time
from core.model.match import GenericMatch

logger = logging.getLogger(__name__)

# Stored match states grouped the way the explorer presents them. Matches left
# running or paused (the app closed unexpectedly) are shown as interrupted.
STATUS_FINISHED = "finished"
STATUS_SAVED = "saved"
STATUS_CANCELLED = "cancelled"
STATUS_INTERRUPTED = "interrupted"

STATUSES = (STATUS_FINISHED, STATUS_SAVED, STATUS_CANCELLED, STATUS_INTERRUPTED)

_STATES_BY_STATUS = {
    STATUS_FINISHED: (GenericMatch.FINISHED,),
    STATUS_SAVED: (GenericMatch.SAVED,),
    STATUS_CANCELLED: (GenericMatch.CANCELLED,),
    STATUS_INTERRUPTED: (GenericMatch.RUNNING, GenericMatch.PAUSED),
}


def status_of(state: int | None) -> str:
    """Map a stored ``Match.state`` to one of :data:`STATUSES`."""
    for status, states in _STATES_BY_STATUS.items():
        if state in states:
            return status
    return STATUS_INTERRUPTED


@dataclass(frozen=True)
class MatchFilter:
    """Criteria narrowing the archive. An empty field means 'any'."""

    games: tuple[str, ...] = ()
    statuses: tuple[str, ...] = ()
    players: tuple[str, ...] = ()
    # With several players selected: require all of them (True) or any one.
    all_players: bool = True
    winner: str | None = None
    # Inclusive range of local calendar days on which the match started.
    date_from: datetime.date | None = None
    date_to: datetime.date | None = None
    min_minutes: int = 0


@dataclass(frozen=True)
class PlayerResult:
    nick: str
    score: int
    winner: bool


@dataclass
class MatchSummary:
    """What the explorer shows about one stored match."""

    idMatch: int
    game: str
    state: int
    started: datetime.datetime | None
    finished: datetime.datetime | None
    elapsed: int
    rounds: int
    players: list[PlayerResult] = field(default_factory=list)

    @property
    def status(self) -> str:
        return status_of(self.state)

    @property
    def winners(self) -> list[PlayerResult]:
        return [p for p in self.players if p.winner]


def _local_day_bound(day: datetime.date) -> str:
    """UTC timestamp text of the start of local calendar ``day``."""
    local = datetime.datetime.combine(day, datetime.time.min).astimezone()
    return local.astimezone(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")


def _where(flt: MatchFilter) -> tuple[str, tuple]:
    """Build the SQL conditions (over ``Match m``) and their parameters."""
    conditions: list[str] = []
    params: list = []

    if flt.games:
        conditions.append(f"m.Game_name IN ({','.join('?' * len(flt.games))})")
        params.extend(flt.games)

    if flt.statuses:
        states = [s for status in flt.statuses for s in _STATES_BY_STATUS[status]]
        conditions.append(f"m.state IN ({','.join('?' * len(states))})")
        params.extend(states)

    if flt.players:
        marks = ",".join("?" * len(flt.players))
        needed = len(flt.players) if flt.all_players else 1
        conditions.append(
            "(SELECT COUNT(*) FROM MatchPlayer p WHERE p.idMatch=m.idMatch "
            f"AND p.nick IN ({marks})) >= ?"
        )
        params.extend(flt.players)
        params.append(needed)

    if flt.winner:
        conditions.append(
            "EXISTS (SELECT 1 FROM MatchPlayer p WHERE p.idMatch=m.idMatch "
            "AND p.winner=1 AND p.nick=?)"
        )
        params.append(flt.winner)

    # Timestamps are stored as UTC text, so plain string comparison orders them.
    if flt.date_from:
        conditions.append("m.started >= ?")
        params.append(_local_day_bound(flt.date_from))
    if flt.date_to:
        conditions.append("m.started < ?")
        params.append(_local_day_bound(flt.date_to + datetime.timedelta(days=1)))

    if flt.min_minutes > 0:
        conditions.append("m.elapsed >= ?")
        params.append(flt.min_minutes * 60)

    return (" AND ".join(conditions) or "1=1"), tuple(params)


def find_matches(flt: MatchFilter | None = None) -> list[MatchSummary]:
    """Return the stored matches satisfying ``flt``, most recent first."""
    where, params = _where(flt or MatchFilter())

    matches: dict[int, MatchSummary] = {}
    cur = db.execute(
        "SELECT m.idMatch, m.Game_name, m.state, m.started, m.finished, m.elapsed "
        f"FROM Match m WHERE {where} ORDER BY m.started DESC, m.idMatch DESC",
        params,
    )
    for row in cur:
        matches[row["idMatch"]] = MatchSummary(
            idMatch=row["idMatch"],
            game=str(row["Game_name"]),
            state=int(row["state"] if row["state"] is not None else -1),
            started=parse_db_time(row["started"]),
            finished=parse_db_time(row["finished"]),
            elapsed=int(row["elapsed"] or 0),
            rounds=0,
        )

    in_selection = f"SELECT m.idMatch FROM Match m WHERE {where}"
    cur = db.execute(
        "SELECT idMatch, nick, totalScore, winner FROM MatchPlayer "
        f"WHERE idMatch IN ({in_selection}) ORDER BY idMatch, rowid",
        params,
    )
    for row in cur:
        matches[row["idMatch"]].players.append(
            PlayerResult(
                str(row["nick"]), int(row["totalScore"] or 0), bool(row["winner"])
            )
        )

    cur = db.execute(
        "SELECT idMatch, COUNT(DISTINCT idRound) AS n FROM Round "
        f"WHERE idMatch IN ({in_selection}) GROUP BY idMatch",
        params,
    )
    rounds = {row["idMatch"]: int(row["n"]) for row in cur}

    for idMatch, summary in matches.items():
        summary.rounds = rounds.get(idMatch, 0)
    return list(matches.values())


def games_with_matches() -> list[str]:
    """Names of the games that have at least one stored match."""
    cur = db.execute("SELECT DISTINCT Game_name FROM Match ORDER BY Game_name")
    return [str(row["Game_name"]) for row in cur]


def players_with_matches() -> list[str]:
    """Nicks of the players that took part in at least one stored match."""
    cur = db.execute("SELECT DISTINCT nick FROM MatchPlayer ORDER BY nick")
    return [str(row["nick"]) for row in cur]
