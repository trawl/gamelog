"""Alignment of the statistics tables: text columns on the left, figures on the
right, for the header and the cells alike."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from tests.test_playerstats import _match

LEFT = Qt.AlignmentFlag.AlignLeft
RIGHT = Qt.AlignmentFlag.AlignRight
VCENTER = Qt.AlignmentFlag.AlignVCenter


def _is(item, horizontal):
    assert item is not None
    alignment = int(item.textAlignment())
    return bool(alignment & horizontal.value) and bool(alignment & VCENTER.value)


def _tabular(widget):
    if hasattr(QFont, "Tag"):
        assert widget.font().isFeatureSet(QFont.Tag("tnum"))


def _seed(game="Ratuki"):
    for i in range(4):
        _match(
            game,
            {"Ann": (10 + i, i % 2 == 0), "Bob": (5, i % 2 == 1), "Cy": (1, False)},
        )


# --- Game quick statistics ---------------------------------------------------


def _quick_table(game, qapp):
    from core.ui.game.stats import GeneralQuickStats

    box = GeneralQuickStats(game, None)
    return box, box.playerStatsTable


def test_quick_stats_align_text_left_and_figures_right(qapp, gamedb):
    _seed()
    box, table = _quick_table("Ratuki", qapp)
    keys = box.playerStatsKeys

    nick, played, perf = (keys.index(k) for k in ("nick", "played", "performance"))
    for column, side in ((nick, LEFT), (played, RIGHT), (perf, RIGHT)):
        assert _is(table.horizontalHeaderItem(column), side)
        assert all(_is(table.item(r, column), side) for r in range(table.rowCount()))
    # Titles keep wrapping, which the header only does when told per item.
    header = table.horizontalHeaderItem(played)
    assert header is not None
    assert int(header.textAlignment()) & Qt.TextFlag.TextWordWrap.value
    _tabular(table)

    matches = box.matchStatsTable
    assert all(_is(matches.horizontalHeaderItem(c), RIGHT) for c in range(4))
    assert all(_is(matches.item(0, c), RIGHT) for c in range(matches.columnCount()))


def test_game_specific_columns_are_figures_even_when_empty(qapp, gamedb):
    from games.azul.widget import AzulQSBox

    _seed("Azul")
    box = AzulQSBox("Azul", None)
    table = box.playerStatsTable
    box.updateContent()  # the game adds its columns after the first fill
    column = box.playerStatsKeys.index("maxbonus")

    assert _is(table.horizontalHeaderItem(column), RIGHT)
    cells = [table.item(r, column) for r in range(table.rowCount())]
    assert all(c is not None for c in cells)
    assert any(c.text() == "-" for c in cells if c)
    assert all(_is(c, RIGHT) for c in cells)


def test_header_height_still_fits_aligned_titles(qapp, gamedb):
    _seed()
    _box, table = _quick_table("Ratuki", qapp)
    table.resize(300, 200)
    table.fitColumns()

    header = table.horizontalHeader()
    assert header.height() >= table.fontMetrics().height()


# --- Player statistics -------------------------------------------------------


@pytest.fixture
def stats_screen(qapp, gamedb):
    from core.ui.playerstats import PlayerStatsWidget

    _seed()
    widget = PlayerStatsWidget()
    widget.show()
    return widget


def test_player_stats_tables_align_by_column(stats_screen):
    games, rivals = stats_screen.gamesModel, stats_screen.rivalsModel
    for model, table in (
        (games, stats_screen.gamesTable),
        (rivals, stats_screen.rivalsTable),
    ):
        assert model.rowCount() >= 1
        assert _is(model.horizontalHeaderItem(0), LEFT)
        assert _is(model.item(0, 0), LEFT)
        for column in range(1, model.columnCount()):
            assert _is(model.horizontalHeaderItem(column), RIGHT)
            assert _is(model.item(0, column), RIGHT)
        _tabular(table)


def test_player_stats_keeps_header_alignment_when_retranslated(stats_screen):
    stats_screen.retranslateUI()

    assert _is(stats_screen.gamesModel.horizontalHeaderItem(0), LEFT)
    assert _is(stats_screen.gamesModel.horizontalHeaderItem(3), RIGHT)


def test_player_stats_summary_tiles_are_all_left_aligned(stats_screen):
    labels, values = stats_screen.summaryLabels, stats_screen.summaryValues

    assert len(values) == 10
    for key in values:
        for label in (values[key], labels[key]):
            assert label.alignment() & LEFT
            assert not label.alignment() & RIGHT
    _tabular(values["played"])


# --- Match history -----------------------------------------------------------


def test_match_history_aligns_by_column(qapp, gamedb):
    from core.ui.explorer import MatchExplorerWidget

    _seed()
    explorer = MatchExplorerWidget()
    explorer.show()
    model = explorer.model

    assert model.rowCount() == 4
    # Started, Time and Rounds are figures; Game, Status, Winner, Players text.
    for column, side in enumerate((RIGHT, LEFT, LEFT, LEFT, LEFT, RIGHT, RIGHT)):
        assert _is(model.horizontalHeaderItem(column), side)
        assert _is(model.item(0, column), side)
    _tabular(explorer.table)


# --- Cell padding ------------------------------------------------------------


def _filled_stats_table(css):
    from PySide6.QtWidgets import QTableWidgetItem

    from core.ui.game.stats import StatsTable

    table = StatsTable()
    table.setColumnCount(2)
    table.setRowCount(1)
    table.setHorizontalHeaderLabels(["Name", "Total"])
    table.setItem(0, 0, QTableWidgetItem("Rosa"))
    table.setItem(0, 1, QTableWidgetItem("735"))
    if css is not None:
        table.setStyleSheet(css)
    return table


def test_cell_padding_is_part_of_the_column_size_hint(qapp):
    from core.ui.tablestyle import CELL_PADDING

    bare = _filled_stats_table("")
    padded = _filled_stats_table(None)  # as the table styles itself

    for column in range(2):
        grown = padded.sizeHintForColumn(column) - bare.sizeHintForColumn(column)
        assert grown >= 2 * CELL_PADDING


def test_values_are_not_cut_at_a_tight_width(qapp):
    table = _filled_stats_table(None)
    need = [table.sizeHintForColumn(c) for c in range(2)]
    table.verticalHeader().hide()
    table.show()
    table.resize(sum(need) + 4, 100)
    table.fitColumns()

    header = table.horizontalHeader()
    assert [header.sectionSize(c) for c in range(2)] >= need
    assert header.length() <= table.viewport().width()


def _padding_grows_hint(table, column):
    from core.ui.tablestyle import CELL_PADDING

    padded = table.sizeHintForColumn(column)
    table.setStyleSheet("")
    assert padded - table.sizeHintForColumn(column) >= 2 * CELL_PADDING


def test_match_history_is_padded(qapp, gamedb):
    from core.ui.explorer import MatchExplorerWidget

    _seed()
    explorer = MatchExplorerWidget()
    explorer.show()

    _padding_grows_hint(explorer.table, 5)


def test_player_stats_are_padded(qapp, gamedb):
    from core.ui.playerstats import PlayerStatsWidget

    _seed()
    widget = PlayerStatsWidget()
    widget.show()

    _padding_grows_hint(widget.rivalsTable, 1)
    _padding_grows_hint(widget.gamesTable, 1)
