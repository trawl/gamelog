"""Player statistics: how one player does across every game."""

from __future__ import annotations

import datetime
import logging

from PySide6.QtCore import QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QShowEvent, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSplitter,
    QTableView,
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
    Form,
    GameBreakdown,
    HeadToHead,
    PlayerSummary,
    favourite_victim,
    game_breakdown,
    games_played_by,
    head_to_head,
    nemesis,
    player_form,
    player_summary,
)
from core.engine.settings import appsettings
from core.ui.explorer import SORT_ROLE, SortItem, _format_duration, status_colour
from core.ui.performance import NONE_TEXT, format_performance, performance_tooltip
from core.ui.tab import Tab

logger = logging.getLogger(__name__)


def _percent(rate: float | None) -> str:
    return NONE_TEXT if rate is None else f"{rate:.0%}"


def _day(moment: datetime.datetime | None) -> str:
    return moment.astimezone().strftime("%Y-%m-%d") if moment else NONE_TEXT


class PlayerStatsWidget(Tab):
    """Screen with the figures of one player over all their finished matches.

    It emits :attr:`backRequested` when the user wants the new-game screen
    back; the main window decides what to show.
    """

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

        # Summary
        self.summaryBox = QGroupBox(self)
        body.addWidget(self.summaryBox)
        grid = QGridLayout(self.summaryBox)
        self.summaryLabels: dict[str, QLabel] = {}
        self.summaryValues: dict[str, QLabel] = {}
        for i, key in enumerate(
            (
                "played",
                "wins",
                "winRate",
                "performance",
                "time",
                "favourite",
                "first",
                "last",
            )
        ):
            row, column = divmod(i, 4)
            label = QLabel(self)
            value = QLabel(self)
            value.setStyleSheet("font-weight: bold;")
            grid.addWidget(label, row * 2, column)
            grid.addWidget(value, row * 2 + 1, column)
            self.summaryLabels[key] = label
            self.summaryValues[key] = value
        self.favouriteValue = self.summaryValues["favourite"]

        # Form
        self.formBox = QGroupBox(self)
        body.addWidget(self.formBox)
        formBox = QVBoxLayout(self.formBox)
        self.formLayout = QHBoxLayout()
        formBox.addLayout(self.formLayout)
        self.streakLabel = QLabel(self)
        formBox.addWidget(self.streakLabel)

        # Per-game and head-to-head tables
        splitter = QSplitter(Qt.Orientation.Vertical, self)
        body.addWidget(splitter, 1)
        self.gamesModel = QStandardItemModel(0, 9, self)
        self.gamesTable = self._table(self.gamesModel)
        self.gamesTable.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        splitter.addWidget(self.gamesTable)

        rivals = QWidget(self)
        rivalsLayout = QVBoxLayout(rivals)
        rivalsLayout.setContentsMargins(0, 0, 0, 0)
        self.nemesisLabel = QLabel(self)
        rivalsLayout.addWidget(self.nemesisLabel)
        self.victimLabel = QLabel(self)
        rivalsLayout.addWidget(self.victimLabel)
        self.rivalsModel = QStandardItemModel(0, 6, self)
        self.rivalsTable = self._table(self.rivalsModel)
        self.rivalsTable.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        rivalsLayout.addWidget(self.rivalsTable, 1)
        splitter.addWidget(rivals)

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

        self.summaryBox.setTitle(self.tr("Summary"))
        names = {
            "played": self.tr("Played"),
            "wins": self.tr("Wins"),
            "winRate": self.tr("Win rate"),
            "performance": self.tr("Performance"),
            "time": self.tr("Time played"),
            "favourite": self.tr("Favourite game"),
            "first": self.tr("First played"),
            "last": self.tr("Last played"),
        }
        for key, text in names.items():
            self.summaryLabels[key].setText(text)
        tip = performance_tooltip()
        self.summaryLabels["performance"].setToolTip(tip)
        self.summaryValues["performance"].setToolTip(tip)
        self.formBox.setTitle(self.tr("Form"))

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
        if self.playerCombo.count():
            self.refresh()
        else:
            self.updateEmpty()

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
            summary = player_summary(nick, games)
            form = player_form(nick, games)
            breakdown = game_breakdown(nick, games)
            rivals = head_to_head(nick, games)
        except DatabaseError:
            logger.exception("Could not read the statistics of %s", nick)
            return
        self.showSummary(summary, single=game is not None)
        self.showForm(form)
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
            "time": _format_duration(summary.time_played),
            "favourite": summary.favourite_game or NONE_TEXT,
            "first": _day(summary.first_played),
            "last": _day(summary.last_played),
        }
        for key, text in values.items():
            self.summaryValues[key].setText(text)
        self.summaryLabels["wins"].setToolTip(
            self.tr("Shared wins are shown in brackets")
        )
        self.summaryLabels["favourite"].setVisible(not single)
        self.favouriteValue.setVisible(not single)

    def showForm(self, form: Form) -> None:
        while (item := self.formLayout.takeAt(0)) is not None:
            if widget := item.widget():
                widget.deleteLater()
        win = status_colour(STATUS_FINISHED, self).name()
        loss = status_colour(STATUS_INTERRUPTED, self).name()
        for won in form.recent:
            marker = QLabel(self.tr("W") if won else self.tr("L"), self)
            marker.setAlignment(Qt.AlignmentFlag.AlignCenter)
            marker.setFixedSize(30, 30)
            marker.setStyleSheet(
                f"background: {win if won else loss}; color: white; "
                "font-weight: bold; border-radius: 4px;"
            )
            self.formLayout.addWidget(marker)
        self.formLayout.addStretch()

        if form.current_streak > 0:
            current = f"{form.current_streak}{self.tr('W')}"
        elif form.current_streak < 0:
            current = f"{-form.current_streak}{self.tr('L')}"
        else:
            current = NONE_TEXT
        self.streakLabel.setText(
            "   ".join(
                (
                    self.tr("Current streak: {}").format(current),
                    self.tr("Longest winning streak: {}").format(
                        form.longest_win_streak
                    ),
                    self.tr("Longest losing streak: {}").format(
                        form.longest_loss_streak
                    ),
                )
            )
        )

    def showGames(self, rows: list[GameBreakdown]) -> None:
        self._fill(
            self.gamesTable,
            self.gamesModel,
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
        enemy = nemesis(rows)
        self.nemesisLabel.setVisible(enemy is not None)
        if enemy:
            self.nemesisLabel.setText(
                self.tr("Nemesis: {} (lost {} of {})").format(
                    enemy.opponent, enemy.them_only, enemy.together
                )
            )
        victim = favourite_victim(rows)
        self.victimLabel.setVisible(victim is not None)
        if victim:
            self.victimLabel.setText(
                self.tr("Favourite victim: {} (won {} of {})").format(
                    victim.opponent, victim.me_only, victim.together
                )
            )

    @staticmethod
    def _fill(
        table: QTableView, model: QStandardItemModel, rows: list[list[SortItem]]
    ) -> None:
        """Replace the rows of ``model``, keeping the table's sort order."""
        table.setSortingEnabled(False)
        model.removeRows(0, model.rowCount())
        for row in rows:
            model.appendRow(row)
        table.setSortingEnabled(True)
