"""PlayerOrderDialog: the colour-swap logic in ``_pickColour`` and the
accept/reject decision in ``changeOrder``/``_colourMapChanged``."""

from unittest.mock import MagicMock

from PySide6.QtGui import QColor

from core.ui.player.order import PlayerOrderDialog

COLOURS = [QColor("red"), QColor("green"), QColor("blue"), QColor("yellow")]


class _FakeEngine:
    def __init__(self, players, dealer=None):
        self._players = list(players)
        self._dealer = dealer

    def getListPlayers(self):
        return self._players

    def getDealer(self):
        return self._dealer


def _stub_colour_dialog(chosen_index):
    """A drop-in for ``_ColourPickerDialog`` that always 'picks' ``chosen_index``."""

    class _Stub:
        def __init__(self, colours, colour_map, player, parent=None):
            pass

        def exec_(self):
            return True

        def chosenIndex(self):
            return chosen_index

    return _Stub


# --- _pickColour: swapping with whoever already has the chosen colour -------


def test_pick_colour_assigns_a_free_colour_directly(qapp, gamedb, monkeypatch):
    engine = _FakeEngine(["Ann", "Bob"])
    dialog = PlayerOrderDialog(
        engine, player_colours=COLOURS, colour_map={"Ann": 0, "Bob": 1}
    )
    monkeypatch.setattr(
        "core.ui.player.order._ColourPickerDialog", _stub_colour_dialog(2)
    )

    dialog._pickColour("Ann")

    assert dialog.getNewColourMap() == {"Ann": 2, "Bob": 1}


def test_pick_colour_bumps_the_player_who_had_it_to_the_first_free_slot(
    qapp, gamedb, monkeypatch
):
    engine = _FakeEngine(["Ann", "Bob"])
    dialog = PlayerOrderDialog(
        engine, player_colours=COLOURS, colour_map={"Ann": 0, "Bob": 1}
    )
    monkeypatch.setattr(
        "core.ui.player.order._ColourPickerDialog", _stub_colour_dialog(1)
    )

    dialog._pickColour("Ann")  # Ann wants Bob's colour (1)

    result = dialog.getNewColourMap()
    assert result["Ann"] == 1
    assert result["Bob"] == 0  # bumped to Ann's now-vacated colour


def test_pick_colour_swap_avoids_a_third_players_colour(qapp, gamedb, monkeypatch):
    engine = _FakeEngine(["Ann", "Bob", "Cy"])
    dialog = PlayerOrderDialog(
        engine, player_colours=COLOURS, colour_map={"Ann": 0, "Bob": 1, "Cy": 2}
    )
    monkeypatch.setattr(
        "core.ui.player.order._ColourPickerDialog", _stub_colour_dialog(1)
    )

    dialog._pickColour("Ann")  # Ann wants Bob's colour (1)

    result = dialog.getNewColourMap()
    assert result["Ann"] == 1
    assert result["Bob"] == 0  # first free slot -- not Cy's colour (2)
    assert result["Cy"] == 2


# --- changeOrder / _colourMapChanged: accept only on an actual change -------


def test_change_order_rejects_when_nothing_changed(qapp, gamedb):
    engine = _FakeEngine(["Ann", "Bob"])
    # A colour map matching the default order-based identity mapping, so only
    # order/dealer changes are under test here (see the dedicated colour-map
    # tests below for when no colours are tracked at all).
    dialog = PlayerOrderDialog(
        engine, player_colours=COLOURS, colour_map={"Ann": 0, "Bob": 1}
    )
    dialog.accept = MagicMock()
    dialog.reject = MagicMock()

    dialog.changeOrder()

    dialog.reject.assert_called_once()
    dialog.accept.assert_not_called()


def test_change_order_accepts_when_the_order_changed(qapp, gamedb):
    engine = _FakeEngine(["Ann", "Bob"])
    dialog = PlayerOrderDialog(
        engine, player_colours=COLOURS, colour_map={"Ann": 0, "Bob": 1}
    )
    dialog.accept = MagicMock()
    dialog.reject = MagicMock()

    model = dialog.pow._model
    model.removeRows(0, model.rowCount())
    model.addPlayer("Bob")
    model.addPlayer("Ann")

    dialog.changeOrder()

    dialog.accept.assert_called_once()
    dialog.reject.assert_not_called()


def test_colour_map_changed_is_false_for_the_default_identity_mapping(qapp, gamedb):
    engine = _FakeEngine(["Ann", "Bob"])
    dialog = PlayerOrderDialog(
        engine, player_colours=COLOURS, colour_map={"Ann": 0, "Bob": 1}
    )
    assert dialog._colourMapChanged() is False


def test_colour_map_changed_is_true_after_a_swap(qapp, gamedb):
    engine = _FakeEngine(["Ann", "Bob"])
    dialog = PlayerOrderDialog(
        engine, player_colours=COLOURS, colour_map={"Ann": 0, "Bob": 1}
    )
    dialog._colour_map = {"Ann": 1, "Bob": 0}
    assert dialog._colourMapChanged() is True


def test_colour_map_changed_is_true_when_no_colour_map_was_supplied(qapp, gamedb):
    """Without a ``colour_map``, ``_colour_map`` stays ``{}`` and never matches
    the order-based identity mapping -- ``changeOrder`` always accepts."""
    engine = _FakeEngine(["Ann", "Bob"])
    dialog = PlayerOrderDialog(engine)
    assert dialog._colourMapChanged() is True
