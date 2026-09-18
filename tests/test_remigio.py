"""Remigio-specific rules: the close-type score multiplier, reinstating a
player after a round is undone, and the dealer rotation skipping players
who are already out."""

from core.registry import registry


def started_match(players):
    match = registry.create_match("Remigio")
    match.setPlayers(list(players))
    match.startMatch()
    return match


# --- Close type: closing the hand multiplies every player's round score ------


def test_close_type_above_one_multiplies_every_players_round_score():
    match = started_match(["Ann", "Bob"])
    rnd = match.createRound(1)
    rnd.setWinner("Ann")
    rnd.addInfo("Ann", 5, {"closeType": 3})
    rnd.addInfo("Bob", -3)
    match.addRound(rnd)

    assert rnd.getPlayerScore("Ann") == 15
    assert rnd.getPlayerScore("Bob") == -9
    assert match.totalScores == {"Ann": 15, "Bob": -9}


def test_default_close_type_leaves_scores_unchanged():
    match = started_match(["Ann", "Bob"])
    rnd = match.createRound(1)
    rnd.setWinner("Ann")
    rnd.addInfo("Ann", 5)  # no closeType supplied -> stays at the default (1)
    rnd.addInfo("Bob", -3)
    match.addRound(rnd)

    assert rnd.getPlayerScore("Ann") == 5
    assert rnd.getPlayerScore("Bob") == -3


# --- Deleting a round can bring an eliminated player back into the match ----


def test_delete_round_reinstates_a_player_back_under_the_top():
    match = started_match(["Ann", "Bob"])
    rnd = match.createRound(1)
    rnd.setWinner("Bob")
    rnd.addInfo("Ann", 110)  # over the top (100) -> eliminated
    rnd.addInfo("Bob", 5)
    match.rounds.append(rnd)
    match.totalScores["Ann"] += 110
    match.totalScores["Bob"] += 5
    match.computeWinner()
    assert match.isPlayerOff("Ann")

    match.deleteRound(1)
    assert not match.isPlayerOff("Ann")
    assert "Ann" in match.getActivePlayers()


def test_delete_round_leaves_a_still_eliminated_player_off():
    match = started_match(["Ann", "Bob", "Cy"])
    rnd = match.createRound(1)
    rnd.setWinner("Bob")
    rnd.addInfo("Ann", 110)
    rnd.addInfo("Bob", 5)
    rnd.addInfo("Cy", 0)
    match.rounds.append(rnd)
    match.totalScores["Ann"] += 110
    match.totalScores["Bob"] += 5
    match.computeWinner()
    assert match.isPlayerOff("Ann")

    rnd2 = match.createRound(2)
    rnd2.setWinner("Bob")
    rnd2.addInfo("Ann", 105)  # over the top on its own, even without round 1
    rnd2.addInfo("Bob", 0)
    rnd2.addInfo("Cy", 0)
    match.rounds.append(rnd2)
    match.totalScores["Ann"] += 105

    match.deleteRound(1)
    assert match.isPlayerOff("Ann")


# --- Dealer rotation must skip players already eliminated -------------------


def test_dealer_rotation_skips_an_eliminated_player(gamedb):
    engine = registry.create_engine("Remigio")
    for player in ["Ann", "Bob", "Cy"]:
        engine.addPlayer(player)
    engine.begin()
    engine.setDealingPolicy(engine.RRDealer)
    engine.setDealer("Ann")

    engine.match.totalScores["Bob"] = 110  # over the top (100)
    engine.match.computeWinner()
    assert engine.isPlayerOff("Bob")

    engine.updateRRDealer()
    assert engine.getDealer() == "Cy"  # Bob is skipped


def test_dealer_rotation_back_also_skips_an_eliminated_player(gamedb):
    engine = registry.create_engine("Remigio")
    for player in ["Ann", "Bob", "Cy"]:
        engine.addPlayer(player)
    engine.begin()
    engine.setDealingPolicy(engine.RRDealer)
    engine.setDealer("Ann")

    engine.match.totalScores["Bob"] = 110
    engine.match.computeWinner()
    assert engine.isPlayerOff("Bob")

    engine.updateRRDealer(back=True)
    assert engine.getDealer() == "Cy"  # stepping back from Ann also skips Bob
