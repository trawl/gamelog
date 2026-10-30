"""The cards of a player in a single game: the scores every game has and what
each game adds from its own stored data."""

import pytest
from PySide6.QtWidgets import QApplication

from core.engine.db import db
from core.registry import GameDefinition, registry
from tests.test_playerstats import _match

NICK = "O'Brien"  # quoted, to prove everything is bound


def _round(idMatch, nick, idRound, score):
    db.execute(
        "INSERT INTO Round (idRound, idMatch, nick, winner, score) VALUES (?,?,?,0,?)",
        (idRound, idMatch, nick, score),
    )


def _stat(idMatch, nick, idRound, key, value):
    db.execute(
        "INSERT INTO RoundStatistics (idMatch, nick, idRound, key, value) "
        "VALUES (?,?,?,?,?)",
        (idMatch, nick, idRound, key, str(value)),
    )


def _kill(idMatch, nick, idRound, seq, target):
    db.execute(
        "INSERT INTO RoundEvents (idMatch, nick, idRound, seq, eventType, target) "
        "VALUES (?,?,?,?,'kill',?)",
        (idMatch, nick, idRound, seq, target),
    )


def _cards(game, nick=NICK):
    definition = registry.get(game)
    assert definition is not None
    return {c.caption: c for c in definition.player_stats(nick)}


def _duel(game, nick=NICK, score=50, won=True, **kwargs):
    return _match(game, {nick: (score, won), "Bob": (10, not won)}, **kwargs)


# --- The hook ----------------------------------------------------------------


def test_games_without_cards_return_an_empty_list(gamedb):
    plain = GameDefinition("Plain", 2, "", "", "x:Y", "x:Y", "x:Y")

    assert plain.player_stats(NICK) == []


def test_a_game_without_data_has_no_cards_or_defaults_to_zero(gamedb):
    assert _cards("Azul") == {}
    assert _cards("Qwirkle") == {}
    assert _cards("Pocha") == {}
    assert _cards("Remigio") == {}


# --- Games with cards ----------------------------------------------------------


def test_azul_shows_the_max_bonus(gamedb):
    from games.azul.model import AzulMatch

    key, points = next(iter(AzulMatch.bonuses.items()))
    idMatch = _duel("Azul")
    _round(idMatch, NICK, 1, 20)
    _stat(idMatch, NICK, 1, key, 2)

    assert _cards("Azul")["Max bonus"].value == str(2 * points)


def test_carcassonne_shows_the_best_total_per_kind(gamedb):
    first, second = _duel("Carcassonne"), _duel("Carcassonne")
    for idMatch, scores in ((first, (4, 6)), (second, (5, 1))):
        for i, score in enumerate(scores, start=1):
            _round(idMatch, NICK, i, score)
            _stat(idMatch, NICK, i, "kind", "City")
    _round(first, "Bob", 9, 99)  # someone else's record
    _stat(first, "Bob", 9, "kind", "City")

    cards = _cards("Carcassonne")
    assert cards["Best city"].value == "10"
    assert "Road" not in " ".join(cards)


def test_parchis_cards_and_kill_rivals(gamedb):
    one, two = _duel("Parchis"), _duel("Parchis")
    kills = [(NICK, "Bob"), (NICK, "Bob"), (NICK, "Cy"), ("Cy", NICK), ("Bob", NICK)]
    for seq, (killer, target) in enumerate(kills, 1):
        _round(one, killer, seq, 0)
        _kill(one, killer, seq, 1, target)
    _round(two, "Cy", 1, 0)
    _kill(two, "Cy", 1, 1, NICK)

    cards = _cards("Parchis")
    assert cards["Max kills"].value == "3"
    assert cards["Killed most"].value == "Bob"
    assert cards["Killed most"].tip == "2 kills"
    assert cards["Killed most by"].value == "Cy"  # two kills, ahead of Bob's one
    assert cards["Killed most by"].tip == "2 kills"
    assert "Best combo" in cards


def test_phase10_shows_phases_and_the_average(gamedb):
    for phases in (3, 5):
        idMatch = _duel("Phase10")
        for phase in range(1, phases + 1):
            _stat(idMatch, NICK, phase, "PhaseCompleted", phase)
            _stat(idMatch, NICK, phase, "PhaseAimed", 2)

    cards = _cards("Phase10")
    assert cards["Fewest phases"].value == "3"
    assert cards["Damned phase"].value == "2"
    assert cards["Phases per match"].value == "4.0"


def test_pocha_shows_hits_and_rounds(gamedb):
    for scores in ((10, 15, -5), (20, -10, -10)):
        idMatch = _duel("Pocha")
        for i, score in enumerate(scores, start=1):
            _round(idMatch, NICK, i, score)

    cards = _cards("Pocha")
    assert cards["Max hits"].value == "2"
    assert cards["Min hits"].value == "1"
    assert cards["Best round"].value == "20"
    assert cards["Worst round"].value == "-10"


def test_skull_king_shows_hit_percentages(gamedb):
    for hits in (4, 8):
        idMatch = _duel("Skull King")
        for i in range(hits):
            _round(idMatch, NICK, i + 1, 20)

    cards = _cards("Skull King")
    assert cards["Max hit %"].value == "80%"
    assert cards["Avg hit %"].value == "60%"
    assert cards["Best round"].value == "20"


def test_qwirkle_shows_plays_and_qwirkles(gamedb):
    idMatch = _duel("Qwirkle")
    for i, (score, qwirkles) in enumerate([(12, 1), (6, 0), (18, 2)], start=1):
        _round(idMatch, NICK, i, score)
        if qwirkles:
            _stat(idMatch, NICK, i, "qwirkles", qwirkles)

    cards = _cards("Qwirkle")
    assert cards["Best play"].value == "18"
    assert cards["Max Qwirkles"].value == "3"
    assert cards["Total Qwirkles"].value == "3"
    assert cards["Average play"].value == "12.0"


def test_scrabble_shows_plays_and_bonuses(gamedb):
    idMatch = _duel("Scrabble")
    for i, score in enumerate((30, 50), start=1):
        _round(idMatch, NICK, i, score)
        _stat(idMatch, NICK, i, "bonuses", 1)

    cards = _cards("Scrabble")
    assert cards["Best play"].value == "50"
    assert cards["Average play"].value == "40.0"
    assert cards["Max bonus"].value == "2"


def test_remigio_shows_how_rounds_were_closed(gamedb):
    idMatch = _duel("Remigio")
    for i, close in enumerate((1, 1, 2, 4), start=1):
        _stat(idMatch, NICK, i, "closeType", close)
    _stat(idMatch, "Bob", 9, "closeType", 3)  # not this player's

    cards = _cards("Remigio")
    assert cards["Closed with ×1"].value == "50%"
    assert cards["Closed with ×1"].tip == "2 of 4 rounds won"
    assert cards["Closed with ×2"].value == "25%"
    assert cards["Closed with ×3"].value == "0%"
    assert cards["Closed with ×4"].value == "25%"


def _rounds(idMatch, rounds):
    """Seed rounds, each mapping the players still in it to whether they won."""
    for idRound, players in enumerate(rounds, start=1):
        for nick, winner in players.items():
            db.execute(
                "INSERT INTO Round (idRound, idMatch, nick, winner, score) "
                "VALUES (?,?,?,?,0)",
                (idRound, idMatch, nick, int(winner)),
            )


def test_round_performance_follows_the_players_left(gamedb):
    from core.engine.playerstats import round_performance

    idMatch = _match(
        "Remigio", {NICK: (0, True), "Bob": (40, False), "Cy": (90, False)}
    )
    _rounds(
        idMatch,
        [
            {NICK: 1, "Bob": 0, "Cy": 0},  # three in it, this player wins
            {NICK: 0, "Bob": 1, "Cy": 0},
            {NICK: 1, "Bob": 0},  # Cy is out: two left, this player wins
        ],
    )

    rounds = round_performance(NICK, "Remigio")
    # Expected 1/3 + 1/3 + 1/2 rounds by chance, won 2.
    assert rounds.index == pytest.approx(2 / (1 / 3 + 1 / 3 + 1 / 2))
    assert (rounds.won, rounds.played) == (2, 3)
    assert round_performance(NICK, "Ratuki").played == 0


def test_round_performance_shares_a_tied_round(gamedb):
    from core.engine.playerstats import round_performance

    idMatch = _duel("Ratuki")
    _rounds(idMatch, [{NICK: 1, "Bob": 1}, {NICK: 0, "Bob": 0}])  # tie, no winner
    # Only the tied round counts: expected 1/2, earned 1/2.
    assert round_performance(NICK, "Ratuki").index == pytest.approx(1.0)


def _shown_cards(qapp, stats_screen, game):
    stats_screen.show()
    stats_screen.playerCombo.setCurrentIndex(stats_screen.playerCombo.findData(NICK))
    stats_screen.gameCombo.setCurrentIndex(stats_screen.gameCombo.findData(game))
    qapp.processEvents()
    return {t.caption.fullText(): t for t in stats_screen.gameBox.tiles}


def test_only_games_with_round_winners_rate_rounds(qapp, stats_screen):
    _rounds(_duel("Ratuki"), [{NICK: 1, "Bob": 0}, {NICK: 0, "Bob": 1}])
    _rounds(_duel("Scrabble"), [{NICK: 1, "Bob": 0}])

    ratuki = _shown_cards(qapp, stats_screen, "Ratuki")
    card = ratuki["Round performance"]
    assert card.value.fullText() == "1.00×"
    assert card.toolTip().endswith("1 of 2 rounds won")
    assert "Round performance" not in _shown_cards(qapp, stats_screen, "Scrabble")


def test_the_round_winner_games():
    flagged = {d.name for d in registry.definitions() if d.round_winners}
    assert flagged == {
        "Azul",
        "Azul Summer Pavilion",
        "Phase10",
        "Phase10Master",
        "Pocha",
        "Ratuki",
        "Remigio",
        "Skull King",
        "Toma6",
    }


def test_catan_counts_the_awards_held_at_the_end(gamedb):
    held, lost = _duel("Catan"), _duel("Catan")
    _stat(held, NICK, 1, "longestroad", 1)
    _stat(held, NICK, 2, "largestarmy", 1)
    _stat(held, NICK, 3, "largestarmy", -1)  # passed on again
    _stat(lost, NICK, 1, "longestroad", 1)
    _stat(lost, NICK, 2, "longestroad", -1)

    cards = _cards("Catan")
    assert cards["Longest road"].value == "1"
    assert cards["Largest army"].value == "0"


@pytest.mark.parametrize("game", ["Ratuki", "Toma6"])
def test_round_games_show_rounds_and_streak(gamedb, game):
    for score in (1, 2):
        idMatch = _duel(game)
        for i in range(1, 4 if score == 1 else 6):
            _round(idMatch, NICK, i, 1)
    _duel(game, won=False)

    cards = _cards(game)
    assert cards["Rounds per match"].value == "4.0"
    assert cards["Best winning streak"].value == "2"


# --- On the screen -------------------------------------------------------------


@pytest.fixture
def stats_screen(qapp, gamedb):
    from core.ui.playerstats import PlayerStatsWidget

    widget = PlayerStatsWidget()
    return widget


def test_the_group_shows_only_with_a_single_game(stats_screen):
    _duel("Ratuki", score=30)
    _duel("Ratuki", score=10)
    _duel("Toma6", score=5)
    stats_screen.show()
    QApplication.processEvents()
    stats_screen.playerCombo.setCurrentIndex(stats_screen.playerCombo.findData(NICK))

    assert not stats_screen.gameBox.isVisible()
    assert stats_screen.gameBox.tiles == []

    stats_screen.gameCombo.setCurrentIndex(stats_screen.gameCombo.findData("Ratuki"))
    QApplication.processEvents()
    assert stats_screen.gameBox.isVisible()
    shown = {
        t.caption.fullText(): t.value.fullText() for t in stats_screen.gameBox.tiles
    }
    assert shown["Highest score"] == "30"
    assert shown["Lowest score"] == "10"
    assert shown["Average score"] == "20"

    stats_screen.gameCombo.setCurrentIndex(0)
    assert not stats_screen.gameBox.isVisible()
    assert stats_screen.gameBox.tiles == []


@pytest.mark.parametrize(
    ("count", "width", "columns"),
    [
        (3, 1000, 3),  # one row, however wide
        (7, 1000, 4),  # six fit: 4 + 3 rather than 6 + 1
        (8, 1000, 4),  # 4 + 4 rather than 6 + 2
        (6, 1000, 6),
        (8, 1400, 8),  # all in one row when they fit
        (5, 320, 2),  # narrow: 2 + 2 + 1
        (4, 10, 1),
        (0, 1000, 1),
    ],
)
def test_balanced_columns(count, width, columns):
    from core.ui.playerstats import CardGrid, balanced_columns

    assert (
        balanced_columns(count, width, CardGrid.MIN_TILE_WIDTH, CardGrid.SPACING)
        == columns
    )


def test_the_cards_spread_evenly_over_the_rows(qapp, stats_screen):
    idMatch = _duel("Qwirkle")
    for i, score in enumerate((12, 6), start=1):
        _round(idMatch, NICK, i, score)
        _stat(idMatch, NICK, i, "qwirkles", 1)
    stats_screen.resize(1024, 700)
    stats_screen.show()
    stats_screen.playerCombo.setCurrentIndex(stats_screen.playerCombo.findData(NICK))
    stats_screen.gameCombo.setCurrentIndex(stats_screen.gameCombo.findData("Qwirkle"))
    qapp.processEvents()

    grid = stats_screen.gameBox.grid
    positions = [
        grid.getItemPosition(grid.indexOf(t))[:2] for t in stats_screen.gameBox.tiles
    ]
    assert len(positions) == 7  # three scores and four of Qwirkle's
    per_row: dict[int, int] = {}
    for row, _column in positions:
        per_row[row] = per_row.get(row, 0) + 1
    assert max(per_row.values()) - min(per_row.values()) <= 1
    # Only the cards that explain something have a tooltip.
    plain = stats_screen.gameBox.tiles[0]
    assert plain.toolTip() == ""
