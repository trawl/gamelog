"""Widget-level smoke tests: every game's board builds and its update paths
run without raising (guards against regressions like the Phase10 one)."""

import pytest

from core.registry import registry

GAME_NAMES = sorted(d.name for d in registry.definitions())
PLAYERS = ["O'Brien", "Alice"]

# Methods whose exception handling is subtle across games (dealer / score /
# winner / detail-group hooks); they must run cleanly on every widget.
UPDATE_METHODS = [
    "setRoundTitle",
    "updateScores",
    "unsetDealer",
    "setDealer",
    "updatePlayerOrder",
    "setWinner",
    "updatePanel",
]


@pytest.mark.parametrize("game", GAME_NAMES)
def test_widget_builds(qapp, gamedb, game):
    widget = registry.create_widget(game, PLAYERS, None, None)
    assert widget is not None
    assert widget.engine is not None
    assert set(widget.engine.getListPlayers()) == set(PLAYERS)


@pytest.mark.parametrize("game", GAME_NAMES)
def test_widget_update_paths(qapp, gamedb, game):
    widget = registry.create_widget(game, PLAYERS, None, None)
    for method in UPDATE_METHODS:
        getattr(widget, method)()  # must not raise
    widget.detailGroup.updateStats()  # exercises the stats query path too
