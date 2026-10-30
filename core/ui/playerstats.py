"""Player statistics: how one player does across every game."""

from __future__ import annotations

import datetime
import logging
from functools import partial
from html import escape

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QSize,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtGui import QMouseEvent, QResizeEvent, QShowEvent, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.engine.db import DatabaseError, db
from core.engine.history import (
    STATUS_FINISHED,
    STATUS_INTERRUPTED,
    players_with_matches,
)
from core.engine.playerstats import (
    FORM_LENGTH,
    RIVAL_MIN_MATCHES,
    Form,
    FormResult,
    GameBreakdown,
    HeadToHead,
    PlayerStat,
    PlayerSummary,
    favourite_victim,
    game_breakdown,
    game_player_stats,
    games_played_by,
    head_to_head,
    nemesis,
    player_form,
    player_full_name,
    player_summary,
    round_performance,
)
from core.engine.settings import appsettings
from core.registry import registry
from core.ui.explorer import SORT_ROLE, SortItem, _format_duration, status_colour
from core.ui.game.stats import SECTION_TITLE_STYLE
from core.ui.performance import NONE_TEXT, format_performance, performance_tooltip
from core.ui.tab import Tab
from core.ui.tablestyle import (
    ALIGN_TEXT,
    TABLE_STYLE,
    align_item,
    tabular_figures,
)

logger = logging.getLogger(__name__)

# Columns holding text (left-aligned); the others are figures.
GAMES_TEXT_COLUMNS = frozenset({0})
RIVALS_TEXT_COLUMNS = frozenset({0})
# The summary tiles in reading order, laid out this many to a row.
SUMMARY_KEYS = (
    "played",
    "wins",
    "winRate",
    "performance",
    "time",
    "favourite",
    "first",
    "last",
    "nemesis",
    "victim",
)
SUMMARY_COLUMNS = 5
# How much larger a tile's value is than its caption.
VALUE_SCALE = 1.4


def _percent(rate: float | None) -> str:
    return NONE_TEXT if rate is None else f"{rate:.0%}"


def _hours(seconds: int) -> str:
    """Time played rounded to whole hours; ``< 1 h`` for any shorter time."""
    hours = (int(seconds) + 1800) // 3600
    if hours == 0 and seconds > 0:
        return QCoreApplication.translate("PlayerStatsWidget", "< 1 h")
    return QCoreApplication.translate("PlayerStatsWidget", "{} h").format(hours)


def _day(moment: datetime.datetime | None) -> str:
    return moment.astimezone().strftime("%Y-%m-%d") if moment else NONE_TEXT


class ElidedLabel(QLabel):
    """Label that cuts a text too long for it short with an ellipsis, rather
    than widening its layout, and then shows it in full on hover."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._full = ""
        self._autoTip = True
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    def setFullText(self, text: str) -> None:
        self._full = text
        self._elide()

    def fullText(self) -> str:
        return self._full

    def setAutoTip(self, on: bool) -> None:
        """Whether to show the full text on hover when it is cut short; off
        when something else owns the tooltip."""
        self._autoTip = on
        self._elide()

    def _elide(self) -> None:
        # The ellipsis only shows once the label has a width to elide to.
        width = self.width()
        text = self._full
        if width > 1:
            text = self.fontMetrics().elidedText(
                self._full, Qt.TextElideMode.ElideRight, width
            )
        super().setText(text)
        if self._autoTip:
            self.setToolTip(self._full if text != self._full else "")

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._elide()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.FontChange:
            self._elide()  # the style sheet sets the size once polished

    def minimumSizeHint(self) -> QSize:
        return QSize(0, super().minimumSizeHint().height())


class FormMarker(QLabel):
    """A recent result as a coloured tag sharing the row with the others; it
    shows its full text when that fits, its short one otherwise. Clicking it
    asks to open the match."""

    clicked = Signal()
    # Horizontal padding on each side, as in the style sheet.
    PADDING = 4

    def __init__(self, full: str, short: str, parent: QWidget | None = None) -> None:
        super().__init__(short, parent)
        self.full, self.short = full, short
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(30)

    def _fit(self) -> None:
        room = self.width() - 2 * self.PADDING
        fits = self.fontMetrics().horizontalAdvance(self.full) <= room
        self.setText(self.full if fits else self.short)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._fit()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.FontChange:
            self._fit()  # the style sheet makes it bold once polished

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(
            event.position().toPoint()
        ):
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class StatTile(QFrame):
    """One summary figure: its value large, its caption small beneath it,
    both left-aligned. Styled by the theme through ``#statTile``."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("statTile")
        self._valueSize = 0
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(0)
        self.value = ElidedLabel(self)
        self.value.setObjectName("statValue")
        self.value.setFont(tabular_figures(self.value.font()))
        self.value.setAlignment(ALIGN_TEXT)
        layout.addWidget(self.value)
        self.caption = ElidedLabel(self)
        self.caption.setObjectName("statCaption")
        self.caption.setAlignment(ALIGN_TEXT)
        layout.addWidget(self.caption)

    def showEvent(self, event: QShowEvent) -> None:
        """Size the value relative to the caption, once the theme has set the
        text size: a style sheet cannot express "larger than the others"."""
        size = round(self.caption.fontInfo().pixelSize() * VALUE_SCALE)
        if size != self._valueSize:
            self._valueSize = size
            self.value.setStyleSheet(f"font-size: {size}px;")
        super().showEvent(event)

    def setCaption(self, text: str) -> None:
        self.caption.setFullText(text)

    def setValue(self, text: str) -> None:
        self.value.setFullText(text)

    def setTip(self, text: str | None) -> None:
        """Explain the tile; hovering over any part of it shows ``text``.

        Only for what the tile does not already say. Without a tip, a value or
        caption cut short is still shown in full on hover.
        """
        for label in (self.value, self.caption):
            label.setAutoTip(text is None)
            if text is not None:
                label.setToolTip(text)
        self.setToolTip(text or "")


def balanced_columns(count: int, width: int, min_width: int, spacing: int) -> int:
    """Columns for ``count`` cards: as few rows as cards of ``min_width`` fit
    in ``width``, with the cards spread evenly over them (4 + 4 rather than
    5 + 3, say)."""
    if count <= 0:
        return 1
    fit = max(1, (width + spacing) // (min_width + spacing))
    rows = -(-count // fit)
    return -(-count // rows)


class CardGrid(QGroupBox):
    """Stat tiles in balanced rows, as many to a row as the width allows."""

    MIN_TILE_WIDTH = 150
    SPACING = 10

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.grid = QGridLayout(self)
        self.grid.setSpacing(self.SPACING)
        self.tiles: list[StatTile] = []
        self._columns = 0

    def setTiles(self, tiles: list[StatTile]) -> None:
        for tile in self.tiles:
            self.grid.removeWidget(tile)
            tile.setParent(None)  # gone at once, not when the event loop runs
            tile.deleteLater()
        self.tiles = tiles
        self._columns = 0
        self._layout()

    def _layout(self) -> None:
        margins = self.grid.contentsMargins()
        width = self.contentsRect().width() - margins.left() - margins.right()
        columns = balanced_columns(
            len(self.tiles), width, self.MIN_TILE_WIDTH, self.SPACING
        )
        if columns == self._columns:
            return
        self._columns = columns
        for tile in self.tiles:
            self.grid.removeWidget(tile)
        for i, tile in enumerate(self.tiles):
            row, column = divmod(i, columns)
            self.grid.addWidget(tile, row, column)
        for column in range(self.grid.columnCount()):
            self.grid.setColumnStretch(column, 1 if column < columns else 0)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._layout()


class FoldableSection(QWidget):
    """A titled group that folds away under its title, leaving its room to
    whatever follows it. Clicking the title folds or unfolds it."""

    def __init__(self, body: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.header = QToolButton(self)
        self.header.setCheckable(True)
        self.header.setChecked(True)
        self.header.setAutoRaise(True)
        self.header.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.header.setArrowType(Qt.ArrowType.DownArrow)
        self.header.setStyleSheet(
            SECTION_TITLE_STYLE.replace("QLabel", "QToolButton")
            + " QToolButton { border: none; }"
        )
        self.header.toggled.connect(self.setOpen)
        layout.addWidget(self.header, 0, Qt.AlignmentFlag.AlignLeft)
        self.body = body
        body.setParent(self)
        layout.addWidget(body)

    def setTitle(self, text: str) -> None:
        self.header.setText(text)

    def title(self) -> str:
        return self.header.text()

    def isOpen(self) -> bool:
        return self.header.isChecked()

    def setOpen(self, open_: bool) -> None:
        self.header.setChecked(open_)
        self.header.setArrowType(
            Qt.ArrowType.DownArrow if open_ else Qt.ArrowType.RightArrow
        )
        self.body.setVisible(open_)


class TableStack(QWidget):
    """Stacks tables, each as tall as its content, one under the other.

    When they do not all fit, the height is shared in proportion to their row
    counts, each keeping room for a few rows (or all of them if fewer) so that
    none collapses. Whatever is left over stays empty below the tables.
    """

    MIN_ROWS = 3
    SPACING = 16

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.tables: list[QTableView] = []
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def addTable(self, table: QTableView) -> None:
        table.setParent(self)
        table.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tables.append(table)

    @staticmethod
    def rowCount(table: QTableView) -> int:
        model = table.model()
        return model.rowCount() if model else 0

    def heightFor(self, table: QTableView, rows: int) -> int:
        """Height of ``table`` showing its first ``rows`` rows and its header."""
        total = sum(table.rowHeight(i) for i in range(min(rows, self.rowCount(table))))
        return (
            table.horizontalHeader().sizeHint().height()
            + total
            + 2 * (table.frameWidth())
        )

    def contentHeight(self, table: QTableView) -> int:
        return self.heightFor(table, self.rowCount(table))

    def minimumHeightOf(self, table: QTableView) -> int:
        return self.heightFor(table, self.MIN_ROWS)

    def _shown(self) -> list[QTableView]:
        return [t for t in self.tables if not t.isHidden()]

    def heights(self, available: int) -> list[int]:
        """Height of each shown table when ``available`` is all there is."""
        shown = self._shown()
        wanted = [self.contentHeight(t) for t in shown]
        if sum(wanted) <= available:
            return wanted
        heights = [
            min(self.minimumHeightOf(t), w) for t, w in zip(shown, wanted, strict=True)
        ]
        rows = [max(self.rowCount(t), 1) for t in shown]
        spare = available - sum(heights)
        # Hand the spare height out by row count, never past a table's content.
        while spare > 0:
            open_ = [i for i in range(len(shown)) if heights[i] < wanted[i]]
            if not open_:
                break
            weight = sum(rows[i] for i in open_)
            given = 0
            for i in open_:
                give = min(wanted[i] - heights[i], max(1, spare * rows[i] // weight))
                give = min(give, spare - given)
                heights[i] += give
                given += give
            if given == 0:
                break
            spare -= given
        return heights

    def relayout(self) -> None:
        shown = self._shown()
        y = 0
        gaps = self.SPACING * max(len(shown) - 1, 0)
        for table, height in zip(
            shown, self.heights(self.height() - gaps), strict=True
        ):
            table.setGeometry(0, y, self.width(), height)
            y += height + self.SPACING
        self.updateGeometry()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.relayout()

    def minimumSizeHint(self) -> QSize:
        shown = self._shown()
        height = sum(self.minimumHeightOf(t) for t in shown)
        return QSize(0, height + self.SPACING * max(len(shown) - 1, 0))


class PlayerStatsWidget(Tab):
    """Screen with the figures of one player over all their finished matches.

    It emits :attr:`backRequested` when the user wants the new-game screen
    back; the main window decides what to show.
    """

    openRequested = Signal(int, str)  # match id, game
    backRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.initUI()
        self.retranslateUI()

    # --- Layout ------------------------------------------------------------

    def initUI(self) -> None:
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        layout.addLayout(header)
        self.backButton = QPushButton(self)
        self.backButton.clicked.connect(self.backRequested.emit)
        header.addWidget(self.backButton)
        self.titleLabel = QLabel(self)
        self.titleLabel.setStyleSheet("font-size: 24px; font-weight: bold;")
        header.addWidget(self.titleLabel, 1)
        self.playerCombo = QComboBox(self)
        self.playerCombo.setMinimumContentsLength(10)
        self.playerCombo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        header.addWidget(self.playerCombo)
        self.gameCombo = QComboBox(self)
        self.gameCombo.setMinimumContentsLength(10)
        self.gameCombo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        header.addWidget(self.gameCombo)

        self.emptyLabel = QLabel(self)
        self.emptyLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.emptyLabel, 1)

        self.content = QWidget(self)
        layout.addWidget(self.content, 1)
        body = QVBoxLayout(self.content)
        body.setContentsMargins(0, 0, 0, 0)

        # Summary, under the player's name. Each group folds away under its
        # title to leave the tables more room.
        self.summaryBox = QGroupBox(self)
        self.summarySection = FoldableSection(self.summaryBox, self)
        body.addWidget(self.summarySection)
        grid = QGridLayout(self.summaryBox)
        grid.setSpacing(10)
        for column in range(SUMMARY_COLUMNS):
            grid.setColumnStretch(column, 1)
        self.summaryGrid = grid
        self.summaryTiles = {key: StatTile(self) for key in SUMMARY_KEYS}
        self.summaryLabels = {k: t.caption for k, t in self.summaryTiles.items()}
        self.summaryValues = {k: t.value for k, t in self.summaryTiles.items()}
        self.favouriteValue = self.summaryValues["favourite"]
        self._layoutSummary(single=False)

        # The player's cards for the chosen game, only there when there is one
        self.gameBox = CardGrid(self)
        self.gameSection = FoldableSection(self.gameBox, self)
        body.addWidget(self.gameSection)
        self.gameSection.hide()

        # Form
        self.formBox = QGroupBox(self)
        self.formSection = FoldableSection(self.formBox, self)
        body.addWidget(self.formSection)
        formBox = QVBoxLayout(self.formBox)
        self.formLayout = QHBoxLayout()
        formBox.addLayout(self.formLayout)
        streaks = QHBoxLayout()
        streaks.setSpacing(CardGrid.SPACING)
        self.streakTiles = {
            key: StatTile(self) for key in ("current", "longestWin", "longestLoss")
        }
        for tile in self.streakTiles.values():
            streaks.addWidget(tile, 1)
        formBox.addLayout(streaks)

        # Per-game and head-to-head tables, each as tall as its rows. A splitter
        # would only let the user undo that, so the stack sizes them itself.
        self.tableStack = TableStack(self)
        body.addWidget(self.tableStack, 1)
        self.gamesModel = QStandardItemModel(0, 9, self)
        self.gamesTable = self._table(self.gamesModel)
        self.gamesTable.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.tableStack.addTable(self.gamesTable)
        self.rivalsModel = QStandardItemModel(0, 6, self)
        self.rivalsTable = self._table(self.rivalsModel)
        self.rivalsTable.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.tableStack.addTable(self.rivalsTable)

        # Wire the combos last, so filling them does not trigger queries.
        self.playerCombo.currentIndexChanged.connect(self.onPlayerChanged)
        self.gameCombo.currentIndexChanged.connect(self.refresh)

    def _table(self, model: QStandardItemModel) -> QTableView:
        proxy = QSortFilterProxyModel(self)
        proxy.setSourceModel(model)
        proxy.setSortRole(SORT_ROLE)
        table = QTableView(self)
        table.setModel(proxy)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.setFont(tabular_figures(table.font()))
        table.setStyleSheet(TABLE_STYLE)
        table.verticalHeader().hide()
        table.setWordWrap(False)
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(False)
        return table

    def retranslateUI(self) -> None:
        """Re-apply translated texts after a language or settings change."""
        words = appsettings["text_in_buttons"]
        self.backButton.setText(self.tr("Back") if words else "←")
        self.backButton.setToolTip(self.tr("Back to the new game screen"))
        self.titleLabel.setText(self.tr("Player statistics"))
        self.emptyLabel.setText(self.tr("No finished matches yet"))
        self.playerCombo.setToolTip(self.tr("Player"))
        self.gameCombo.setToolTip(self.tr("Game"))

        names = {
            "played": self.tr("Played"),
            "wins": self.tr("Wins"),
            "winRate": self.tr("Win rate"),
            "performance": self.tr("Performance"),
            "time": self.tr("Time played"),
            "favourite": self.tr("Favourite game"),
            "first": self.tr("First played"),
            "last": self.tr("Last played"),
            "nemesis": self.tr("Nemesis"),
            "victim": self.tr("Favourite victim"),
        }
        for key, text in names.items():
            self.summaryTiles[key].setCaption(text)
        tip = performance_tooltip()
        self.summaryTiles["performance"].setTip(tip)
        streaks = {
            "current": self.tr("Current streak"),
            "longestWin": self.tr("Longest winning streak"),
            "longestLoss": self.tr("Longest losing streak"),
        }
        for key, text in streaks.items():
            self.streakTiles[key].setCaption(text)
        self.formSection.setTitle(self.tr("Recent form"))

        self.gamesModel.setHorizontalHeaderLabels(
            [
                self.tr("Game"),
                self.tr("Played"),
                self.tr("Wins"),
                self.tr("Win %"),
                self.tr("Performance"),
                self.tr("Min"),
                self.tr("Avg"),
                self.tr("Max"),
                self.tr("Time"),
            ]
        )
        self.rivalsModel.setHorizontalHeaderLabels(
            [
                self.tr("Opponent"),
                self.tr("Together"),
                self.tr("Won"),
                self.tr("Lost"),
                self.tr("Shared"),
                self.tr("Neither"),
            ]
        )
        self._alignHeaders(self.gamesModel, GAMES_TEXT_COLUMNS)
        self._alignHeaders(self.rivalsModel, RIVALS_TEXT_COLUMNS)
        if self.playerCombo.count():
            self.refresh()
        else:
            self.updateEmpty()

    @staticmethod
    def _alignHeaders(model: QStandardItemModel, text_columns: frozenset[int]) -> None:
        for column in range(model.columnCount()):
            if header := model.horizontalHeaderItem(column):
                align_item(header, column, text_columns)

    # --- Choices -----------------------------------------------------------

    def showEvent(self, event: QShowEvent) -> None:
        """Reload the players whenever the screen is shown, as matches may
        have been finished since."""
        self._reloadPlayers()
        self._reloadGames()
        self.refresh()
        super().showEvent(event)

    def _reloadPlayers(self) -> None:
        """List the players with finished matches, favourites first, keeping
        the current one selected if still there."""
        current = self.playerCombo.currentData()
        try:
            nicks = players_with_matches()
            favourites = {n for n in nicks if db.isPlayerFavourite(n)}
        except DatabaseError:
            logger.exception("Could not read the players")
            nicks, favourites = [], set()
        nicks.sort(key=lambda n: (n not in favourites, n.lower()))
        self.playerCombo.blockSignals(True)
        self.playerCombo.clear()
        for nick in nicks:
            self.playerCombo.addItem(f"★ {nick}" if nick in favourites else nick, nick)
        self.playerCombo.setCurrentIndex(max(self.playerCombo.findData(current), 0))
        self.playerCombo.blockSignals(False)

    def _reloadGames(self) -> None:
        """List the games of the chosen player, keeping the current one."""
        current = self.gameCombo.currentData()
        nick = self.playerCombo.currentData()
        try:
            games = games_played_by(nick) if nick else []
        except DatabaseError:
            logger.exception("Could not read the games of %s", nick)
            games = []
        self.gameCombo.blockSignals(True)
        self.gameCombo.clear()
        self.gameCombo.addItem(self.tr("All games"), None)
        for game in games:
            self.gameCombo.addItem(game, game)
        self.gameCombo.setCurrentIndex(max(self.gameCombo.findData(current), 0))
        self.gameCombo.blockSignals(False)

    def onPlayerChanged(self, *_args: object) -> None:
        self._reloadGames()
        self.refresh()

    def updateEmpty(self) -> None:
        empty = self.playerCombo.count() == 0
        self.emptyLabel.setVisible(empty)
        self.content.setVisible(not empty)
        self.playerCombo.setEnabled(not empty)
        self.gameCombo.setEnabled(not empty)

    # --- Results -----------------------------------------------------------

    def refresh(self, *_args: object) -> None:
        """Query the statistics of the chosen player and game and show them."""
        self.updateEmpty()
        nick = self.playerCombo.currentData()
        if not nick:
            return
        game = self.gameCombo.currentData()
        games = (game,) if game else ()
        try:
            name = player_full_name(nick)
            summary = player_summary(nick, games)
            form = player_form(nick, games)
            breakdown = game_breakdown(nick, games)
            rivals = head_to_head(nick, games)
        except DatabaseError:
            logger.exception("Could not read the statistics of %s", nick)
            return
        self.summarySection.setTitle(name)
        self.showSummary(summary, single=game is not None)
        self.showGameStats(nick, game, breakdown)
        self.showForm(form, single=game is not None)
        self.gamesTable.setVisible(game is None)
        self.showGames(breakdown)
        self.showRivals(rivals)

    def showSummary(self, summary: PlayerSummary, single: bool) -> None:
        wins = str(summary.wins)
        if summary.shared_wins:
            wins += f" ({summary.shared_wins})"
        values = {
            "played": str(summary.played),
            "wins": wins,
            "winRate": _percent(summary.win_rate),
            "performance": format_performance(summary.performance),
            "time": _hours(summary.time_played),
            "favourite": summary.favourite_game or NONE_TEXT,
            "first": _day(summary.first_played),
            "last": _day(summary.last_played),
        }
        for key, text in values.items():
            self.summaryTiles[key].setValue(text)
        self.summaryTiles["wins"].setTip(
            self.tr("Shared wins are shown in brackets")
            if summary.shared_wins
            else None
        )
        self.summaryTiles["time"].setTip(_format_duration(summary.time_played))
        self._layoutSummary(single)

    def showGameStats(
        self, nick: str, game: str | None, breakdown: list[GameBreakdown]
    ) -> None:
        """The cards of ``nick`` in ``game``: the scores every game has, then
        what the game adds. Hidden, and taking no room, across all games."""
        self.gameSection.setVisible(game is not None)
        if game is not None:
            self.gameSection.setTitle(game)
        if game is None:
            self.gameBox.setTiles([])
            return
        cards = self._scoreCards(breakdown[0] if breakdown else None)
        try:
            cards += self._roundCards(nick, game)
            cards += game_player_stats(nick, game)
        except DatabaseError:
            logger.exception("Could not read the %s cards of %s", game, nick)
        tiles = []
        for card in cards:
            tile = StatTile(self.gameBox)
            tile.setCaption(card.caption)
            tile.setValue(card.value)
            tile.setTip(card.tip)
            tiles.append(tile)
        self.gameBox.setTiles(tiles)

    def _scoreCards(self, row: GameBreakdown | None) -> list[PlayerStat]:
        """Highest, lowest and average final score. The captions stay neutral:
        in some games a low score is the good one."""
        if row is None:
            return []
        return [
            PlayerStat(self.tr("Highest score"), str(row.max_score)),
            PlayerStat(self.tr("Lowest score"), str(row.min_score)),
            PlayerStat(self.tr("Average score"), str(row.avg_score)),
        ]

    def _roundCards(self, nick: str, game: str) -> list[PlayerStat]:
        """Round performance, for the games whose rounds have a real winner."""
        definition = registry.get(game)
        if not (definition and definition.round_winners):
            return []
        rounds = round_performance(nick, game)
        if not rounds.played:
            return []
        tip = self.tr(
            "Rounds won compared with what chance predicts for the players in "
            "each round: 1.00× means winning exactly as often as chance.\n"
            "{} of {} rounds won"
        )
        return [
            PlayerStat(
                self.tr("Round performance"),
                format_performance(rounds.index),
                tip.format(rounds.won, rounds.played),
            )
        ]

    def _layoutSummary(self, single: bool) -> None:
        """Lay the tiles out in rows, leaving out the favourite game when a
        single game is shown, so the others close up around it."""
        shown = [k for k in SUMMARY_KEYS if not (single and k == "favourite")]
        for tile in self.summaryTiles.values():
            self.summaryGrid.removeWidget(tile)
            tile.setVisible(False)
        for i, key in enumerate(shown):
            row, column = divmod(i, SUMMARY_COLUMNS)
            self.summaryGrid.addWidget(self.summaryTiles[key], row, column)
            self.summaryTiles[key].setVisible(True)

    def showForm(self, form: Form, single: bool) -> None:
        """Show the latest results, newest first. Across all games each marker
        names its game; with a single game it says won or lost."""
        while (item := self.formLayout.takeAt(0)) is not None:
            if widget := item.widget():
                widget.setParent(None)  # gone at once, not when the event loop runs
                widget.deleteLater()
        win = status_colour(STATUS_FINISHED, self).name()
        loss = status_colour(STATUS_INTERRUPTED, self).name()
        for result in reversed(form.recent):
            if single:
                full = (
                    self.tr("Won", "one match")
                    if result.won
                    else self.tr("Lost", "one match")
                )
                short = self.tr("W") if result.won else self.tr("L")
            else:
                definition = registry.get(result.game)
                full = result.game
                short = definition.code if definition else result.game[:3]
            marker = FormMarker(full, short, self)
            marker.clicked.connect(
                partial(self.openRequested.emit, result.idMatch, result.game)
            )
            marker.setAlignment(Qt.AlignmentFlag.AlignCenter)
            marker.setFixedHeight(30)
            marker.setStyleSheet(
                f"background: {win if result.won else loss}; color: white; "
                "font-weight: bold; border-radius: 4px; "
                f"padding: 0px {FormMarker.PADDING}px;"
            )
            marker.setToolTip(self._formTip(result, single))
            self.formLayout.addWidget(marker, 1)
        # The markers share the row as if it were full, so a short history
        # keeps the same marker width rather than stretching over the row.
        for _ in range(FORM_LENGTH - len(form.recent)):
            self.formLayout.addStretch(1)

        if form.current_streak > 0:
            current = f"{form.current_streak}{self.tr('W')}"
        elif form.current_streak < 0:
            current = f"{-form.current_streak}{self.tr('L')}"
        else:
            current = NONE_TEXT
        self.streakTiles["current"].setValue(current)
        self.streakTiles["longestWin"].setValue(str(form.longest_win_streak))
        self.streakTiles["longestLoss"].setValue(str(form.longest_loss_streak))

    def _formTip(self, result: FormResult, single: bool) -> str:
        """The match behind a form marker: its game (across all games), when
        it finished and how everyone scored, the winners in bold."""
        lines = []
        if not single:
            lines.append(f"<b>{escape(result.game)}</b>")
        if result.finished:
            lines.append(_day(result.finished))
        for player in result.players:
            name = escape(player.nick)
            if player.winner:
                name = f"<b>{name}</b>"
            line = f"{name}: {player.score}"
            if extra := result.extras.get(player.nick):
                line += f" · {escape(extra)}"
            lines.append(line)
        lines.append(self.tr("Click to open the match"))
        return "<br>".join(lines)

    def showGames(self, rows: list[GameBreakdown]) -> None:
        self._fill(
            self.gamesTable,
            self.gamesModel,
            GAMES_TEXT_COLUMNS,
            [
                [
                    SortItem(r.game),
                    SortItem(str(r.played), r.played),
                    SortItem(str(r.wins), r.wins),
                    SortItem(_percent(r.win_rate), r.win_rate or 0),
                    SortItem(format_performance(r.performance), r.performance or 0),
                    SortItem(str(r.min_score), r.min_score),
                    SortItem(str(r.avg_score), r.avg_score),
                    SortItem(str(r.max_score), r.max_score),
                    SortItem(_format_duration(r.time_played), r.time_played),
                ]
                for r in rows
            ],
        )

    def showRivals(self, rows: list[HeadToHead]) -> None:
        self._fill(
            self.rivalsTable,
            self.rivalsModel,
            RIVALS_TEXT_COLUMNS,
            [
                [
                    SortItem(r.opponent),
                    SortItem(str(r.together), r.together),
                    SortItem(str(r.me_only), r.me_only),
                    SortItem(str(r.them_only), r.them_only),
                    SortItem(str(r.both), r.both),
                    SortItem(str(r.neither), r.neither),
                ]
                for r in rows
            ],
        )
        self.showRival("nemesis", nemesis(rows), lost=True)
        self.showRival("victim", favourite_victim(rows), lost=False)
        self.tableStack.relayout()

    def showRival(self, key: str, rival: HeadToHead | None, lost: bool) -> None:
        """Fill the nemesis or favourite-victim tile; the record against the
        opponent is its tooltip."""
        tile = self.summaryTiles[key]
        if rival is None:
            tile.setValue(NONE_TEXT)
            need = (
                self.tr(
                    "Needs at least {} matches against the same opponent, with more losses than wins"
                )
                if lost
                else self.tr(
                    "Needs at least {} matches against the same opponent, with more wins than losses"
                )
            )
            tile.setTip(need.format(RIVAL_MIN_MATCHES))
            return
        tile.setValue(rival.opponent)
        template = (
            self.tr("Lost {} of {} matches against this opponent")
            if lost
            else self.tr("Won {} of {} matches against this opponent")
        )
        count = rival.them_only if lost else rival.me_only
        tile.setTip(f"{rival.opponent}\n{template.format(count, rival.together)}")

    @staticmethod
    def _fill(
        table: QTableView,
        model: QStandardItemModel,
        text_columns: frozenset[int],
        rows: list[list[SortItem]],
    ) -> None:
        """Replace the rows of ``model``, keeping the table's sort order."""
        table.setSortingEnabled(False)
        model.removeRows(0, model.rowCount())
        for row in rows:
            for column, item in enumerate(row):
                align_item(item, column, text_columns)
            model.appendRow(row)
        table.setSortingEnabled(True)
