"""Database layer: parameterised SQL and error handling."""

import pytest

from core.engine.db import DatabaseError

APOSTROPHE = "O'Brien"
INJECTION = "Bobby'); DROP TABLE Player;--"


def test_names_with_apostrophes_are_stored_verbatim(gamedb):
    gamedb.addPlayer(APOSTROPHE, APOSTROPHE)
    assert APOSTROPHE in gamedb.getPlayerNicks()


def test_sql_injection_payload_is_inert(gamedb):
    gamedb.addPlayer(INJECTION, INJECTION)
    nicks = gamedb.getPlayerNicks()
    # The payload is stored as data; the Player table is untouched.
    assert INJECTION in nicks
    assert gamedb.execute("SELECT COUNT(*) AS c FROM Player").fetchone()["c"] == 1


def test_bad_query_raises_instead_of_exiting(gamedb):
    with pytest.raises(DatabaseError):
        gamedb.execute("SELECT * FROM NoSuchTable")
    # The process survives; subsequent queries still work.
    assert gamedb.execute("SELECT 1 AS one").fetchone()["one"] == 1


def test_favourite_roundtrip_with_apostrophe(gamedb):
    gamedb.addPlayer(APOSTROPHE, APOSTROPHE)
    assert gamedb.isPlayerFavourite(APOSTROPHE) is False
    gamedb.setPlayerFavourite(APOSTROPHE, True)
    assert gamedb.isPlayerFavourite(APOSTROPHE) is True
