"""Game-agnostic engine behaviour: roster management, dealer rotation and the
small wrappers that sit between the UI and the match model."""

from core.registry import registry


def _engine(game, players):
    engine = registry.create_engine(game)
    for player in players:
        engine.addPlayer(player)
    engine.begin()
    return engine


# --- Roster management -----------------------------------------------------


def test_get_game_max_players_reads_the_registered_limit(gamedb):
    engine = registry.create_engine("Ratuki")
    assert engine.getGameMaxPlayers() == 5


def test_set_list_players_accepts_a_pure_reordering(gamedb):
    engine = _engine("Ratuki", ["Ann", "Bob", "Cy"])
    engine.setListPlayers(["Cy", "Ann", "Bob"])
    assert engine.getListPlayers() == ["Cy", "Ann", "Bob"]


def test_set_list_players_rejects_a_different_player_set(gamedb):
    engine = _engine("Ratuki", ["Ann", "Bob", "Cy"])
    original = list(engine.getListPlayers())
    engine.setListPlayers(["Ann", "Bob"])  # drops Cy -- not a pure reordering
    assert engine.getListPlayers() == original


def test_get_score_from_player_is_zero_for_an_unknown_player(gamedb):
    engine = _engine("Ratuki", ["Ann", "Bob"])
    assert engine.getScoreFromPlayer("Nobody") == 0


# --- Match lifecycle wrappers -----------------------------------------------


def test_resume_returns_false_for_an_unknown_match(gamedb):
    engine = registry.create_engine("Ratuki")
    assert engine.resume(999999) is False


def test_cancel_match_is_a_noop_once_the_match_has_a_winner(gamedb):
    engine = _engine("Ratuki", ["Ann", "Bob"])
    engine.match.totalScores["Ann"] = 110  # >= top (100)
    engine.match.computeWinner()
    assert engine.getWinner() == "Ann"

    engine.cancelMatch()
    assert not engine.match.isCancelled()


def test_update_times_overwrites_and_persists_the_match_clock(gamedb):
    import datetime

    engine = _engine("Ratuki", ["Ann", "Bob"])
    start = datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC)
    finish = datetime.datetime(2024, 1, 1, 1, 0, 0, tzinfo=datetime.UTC)
    engine.updateTimes(start, finish, 3600)

    assert engine.getStartTime() == start
    assert engine.getFinishTime() == finish
    # Still running (no winner, not paused), so a hair of real time is added on top.
    assert 3600 <= engine.getGameSeconds() < 3600 + 5


# --- Dealer rotation ---------------------------------------------------------


def _play_round(engine, nround, scores, winner):
    engine.openRound(nround)
    engine.setRoundWinner(winner)
    for player, score in scores.items():
        engine.addRoundInfo(player, score, {})
    engine.commitRound()


def test_round_robin_dealer_advances_through_the_player_order(gamedb):
    engine = _engine("Ratuki", ["Ann", "Bob", "Cy"])
    engine.setDealingPolicy(engine.RRDealer)
    engine.setDealer("Ann")

    _play_round(engine, 1, {"Ann": 10, "Bob": 5, "Cy": 0}, "Ann")
    assert engine.getDealer() == "Bob"

    _play_round(engine, 2, {"Ann": 10, "Bob": 5, "Cy": 0}, "Ann")
    assert engine.getDealer() == "Cy"


def test_round_robin_dealer_wraps_around_to_the_first_player(gamedb):
    engine = _engine("Ratuki", ["Ann", "Bob", "Cy"])
    engine.setDealingPolicy(engine.RRDealer)
    engine.setDealer("Cy")

    _play_round(engine, 1, {"Ann": 10, "Bob": 5, "Cy": 0}, "Ann")
    assert engine.getDealer() == "Ann"


def test_delete_round_rolls_the_round_robin_dealer_back(gamedb):
    engine = _engine("Ratuki", ["Ann", "Bob", "Cy"])
    engine.setDealingPolicy(engine.RRDealer)
    engine.setDealer("Ann")

    _play_round(engine, 1, {"Ann": 10, "Bob": 5, "Cy": 0}, "Ann")
    assert engine.getDealer() == "Bob"

    engine.deleteRound(1)
    assert engine.getDealer() == "Ann"


def test_winner_dealer_hands_the_deal_to_last_rounds_winner(gamedb):
    engine = _engine("Ratuki", ["Ann", "Bob", "Cy"])
    engine.setDealingPolicy(engine.WinnerDealer)

    _play_round(engine, 1, {"Ann": 10, "Bob": 5, "Cy": 0}, "Bob")
    assert engine.getDealer() == "Bob"

    _play_round(engine, 2, {"Ann": 5, "Bob": 5, "Cy": 20}, "Cy")
    assert engine.getDealer() == "Cy"


def test_round_robin_dealer_stays_none_if_never_assigned(gamedb):
    engine = registry.create_engine("Ratuki")
    engine.addPlayer("Ann")
    engine.addPlayer("Bob")
    engine.setDealingPolicy(engine.NoDealer)  # begin() then skips picking a dealer
    engine.begin()
    assert engine.getDealer() is None

    engine.setDealingPolicy(engine.RRDealer)
    _play_round(engine, 1, {"Ann": 10, "Bob": 5}, "Ann")
    assert engine.getDealer() is None


def test_winner_dealer_falls_back_to_starting_dealer_once_rounds_are_deleted(gamedb):
    engine = _engine("Ratuki", ["Ann", "Bob", "Cy"])
    engine.setDealingPolicy(engine.WinnerDealer)
    starting_dealer = engine.getDealer()

    _play_round(engine, 1, {"Ann": 10, "Bob": 5, "Cy": 0}, "Bob")
    assert engine.getDealer() == "Bob"

    engine.deleteRound(1)  # no rounds left -- getRounds()[-1] would raise
    assert engine.getDealer() == starting_dealer


def test_dealer_rotation_freezes_once_a_winner_is_declared(gamedb):
    engine = _engine("Ratuki", ["Ann", "Bob", "Cy"])
    engine.setDealingPolicy(engine.RRDealer)
    engine.setDealer("Ann")

    _play_round(
        engine, 1, {"Ann": 110, "Bob": 5, "Cy": 0}, "Ann"
    )  # Ann reaches top (100)
    assert engine.getWinner() == "Ann"
    assert engine.getDealer() == "Ann"  # rotation stops once the match is decided
