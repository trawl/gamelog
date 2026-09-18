"""PlayerList.addItem: rejecting duplicate players and enforcing the
max-player cap."""

from core.ui.player.list import PlayerList


def test_add_item_accepts_a_new_player(qapp, gamedb):
    widget = PlayerList()
    assert widget.addItem("Ann") is True
    assert widget._model.retrievePlayers() == ["Ann"]


def test_add_item_rejects_a_duplicate_player(qapp, gamedb):
    widget = PlayerList()
    widget.addItem("Ann")
    assert widget.addItem("Ann") is False
    assert widget._model.retrievePlayers() == ["Ann"]


def test_add_item_rejects_once_max_players_is_reached(qapp, gamedb):
    widget = PlayerList()
    widget.setMaxPlayers(2)
    assert widget.addItem("Ann") is True
    assert widget.addItem("Bob") is True
    assert widget.addItem("Cy") is False
    assert widget._model.retrievePlayers() == ["Ann", "Bob"]


def test_add_item_has_no_cap_when_max_players_is_none(qapp, gamedb):
    widget = PlayerList()
    for name in ["Ann", "Bob", "Cy", "Deb"]:
        assert widget.addItem(name) is True


def test_can_accept_item_reflects_the_cap(qapp, gamedb):
    widget = PlayerList()
    widget.setMaxPlayers(1)
    assert widget._canAcceptItem() is True
    widget.addItem("Ann")
    assert widget._canAcceptItem() is False
