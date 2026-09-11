"""Parchis combo scoring: any action past the first in a single entry counts,
goals and kills alike."""

import pytest

from games.parchis.model import ParchisEntry, ParchisMatch


@pytest.mark.parametrize(
    ("score", "kills", "expected_combo"),
    [
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (1, 1, 1),
        (0, 2, 1),
        (0, 3, 2),
        (2, 2, 3),
        (4, 3, 6),
    ],
)
def test_combo_formula_matches_spec(score, kills, expected_combo):
    match = ParchisMatch(["Alice"])
    entry = ParchisEntry(1)
    entry.addInfo("Alice", score, {"kills": [f"victim{i}" for i in range(kills)]})
    match.rounds.append(entry)

    assert match.getComboTally()["Alice"] == expected_combo


def test_combo_tally_sums_across_entries():
    match = ParchisMatch(["Alice", "Bob"])
    e1 = ParchisEntry(1)
    e1.addInfo("Alice", 0, {"kills": ["Bob", "Bob"]})  # combo = 1
    e2 = ParchisEntry(2)
    e2.addInfo("Alice", 4, {"kills": []})  # combo = 3
    match.rounds.extend([e1, e2])

    assert match.getComboTally()["Alice"] == 4
