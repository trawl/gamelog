"""Pocha's round sequence: card count and dealing direction per hand, and the
suit-type switch between the Spanish and French decks."""

from core.registry import registry


def test_default_suit_type_is_spanish():
    engine = registry.create_engine("Pocha")
    assert engine.getSuitType() == "spanish"


def test_direction_climbs_then_holds_a_suit_then_descends():
    engine = registry.create_engine("Pocha")
    assert engine.getDirection(1) == "going up"
    assert engine.getDirection(7) == "going up"
    assert engine.getDirection(8) == "coins"  # first of the four peak hands
    assert engine.getDirection(11) == "clubs"  # last of the four peak hands
    assert engine.getDirection(12) == "going down"
    assert engine.getDirection(18) == "going down"


def test_direction_falls_back_to_the_last_entry_past_the_final_round():
    engine = registry.create_engine("Pocha")
    assert engine.getDirection(99) == "going down"


def test_get_hands_returns_the_card_count_for_each_round():
    engine = registry.create_engine("Pocha")
    assert engine.getHands(1) == 1
    assert engine.getHands(8) == 8  # first of the four peak hands
    assert engine.getHands(18) == 1


def test_get_hands_falls_back_to_one_past_the_final_round():
    engine = registry.create_engine("Pocha")
    assert engine.getHands(99) == 1


def test_set_suit_type_switches_to_the_french_deck():
    engine = registry.create_engine("Pocha")
    engine.setSuitType("french")
    assert engine.getSuitType() == "french"
    assert engine.getDirection(8) == "diamonds"
    assert engine.getDirection(11) == "clovers"
