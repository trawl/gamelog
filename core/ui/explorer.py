"""Match explorer: browse, filter and reopen every stored match."""

from __future__ import annotations

import datetime
import logging
from typing import Any, cast

from PySide6.QtCore import QDate, QModelIndex, QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QShowEvent, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from core.engine.db import DatabaseError
from core.engine.history import (
    STATUS_CANCELLED,
    STATUS_FINISHED,
    STATUS_INTERRUPTED,
    STATUS_SAVED,
    STATUSES,
    MatchFilter,
    MatchSummary,
    find_matches,
    games_with_matches,
    players_with_matches,
)
from core.engine.settings import appsettings
from core.ui.tab import Tab
from core.ui.tablestyle import align_item, tabular_figures

logger = logging.getLogger(__name__)

# Roles holding the value a column sorts by, and the match id of a row.
SORT_ROLE = Qt.ItemDataRole.UserRole
ID_ROLE = Qt.ItemDataRole.UserRole + 1
STATE_ROLE = Qt.ItemDataRole.UserRole + 2

# Date-range presets and the "any date" sentinel of the date editors.
ANY_DATE = QDate(2000, 1, 1)
PRESET_ANY, PRESET_TODAY, PRESET_WEEK, PRESET_MONTH, PRESET_YEAR, PRESET_CUSTOM = range(
    6
)

# Outcomes offered as toggles (Cancelled also covers interrupted matches) and
# the ones shown until the user asks for more.
FILTER_STATUSES = (STATUS_FINISHED, STATUS_SAVED, STATUS_CANCELLED)
DEFAULT_STATUSES = (STATUS_FINISHED, STATUS_SAVED)
CONTROL_HEIGHT = 36

# Columns holding text (left-aligned): game, status, winner and players. The
# others (date, time, rounds) are figures.
TEXT_COLUMNS = frozenset({1, 2, 3, 4})

# Status colours as (for light themes, for dark themes).
STATUS_COLOURS = {
    STATUS_FINISHED: (QColor("#2e8b57"), QColor("#3cb371")),
    STATUS_SAVED: (QColor("#1f5fbf"), QColor("#7fb2ff")),
    STATUS_CANCELLED: (QColor("#707070"), QColor("#a0a0a0")),
    STATUS_INTERRUPTED: (QColor("#b36b00"), QColor("#e0a040")),
}


def status_colour(status: str, widget: QWidget) -> QColor:
    """The colour of ``status`` that reads well on ``widget``'s background."""
    light, dark = STATUS_COLOURS[status]
    return dark if widget.palette().window().color().lightness() < 128 else light


class MultiChoiceButton(QToolButton):
    """Drop-down button offering a checkable list; none checked means 'any'."""

    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = ""
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.setMinimumHeight(CONTROL_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.menu_ = QMenu(self)
        self.setMenu(self.menu_)
        self.clearAction = self.menu_.addAction("")
        self.clearAction.triggered.connect(self.clearChecked)
        self.list = QListWidget(self.menu_)
        self.list.setMinimumWidth(180)
        self.list.setFixedHeight(240)
        self.list.itemClicked.connect(self._toggle)
        listAction = QWidgetAction(self.menu_)
        listAction.setDefaultWidget(self.list)
        self.menu_.addAction(listAction)

    def setTitle(self, title: str, clearText: str) -> None:
        self._title = title
        self.clearAction.setText(clearText)
        self._refreshText()

    def setChoices(self, choices: list[str]) -> None:
        """Replace the options, keeping the ones still available checked."""
        keep = set(self.checked())
        self.list.blockSignals(True)
        self.list.clear()
        for choice in choices:
            item = QListWidgetItem(choice, self.list)
            checked = choice in keep
            item.setCheckState(
                Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
            )
        self.list.blockSignals(False)
        self._refreshText()

    def checked(self) -> list[str]:
        return [
            item.text()
            for i in range(self.list.count())
            if (item := self.list.item(i)).checkState() == Qt.CheckState.Checked
        ]

    def reset(self) -> None:
        """Uncheck everything without announcing a change."""
        for i in range(self.list.count()):
            self.list.item(i).setCheckState(Qt.CheckState.Unchecked)
        self._refreshText()

    def clearChecked(self) -> None:
        self.reset()
        self.changed.emit()

    def _toggle(self, item: QListWidgetItem) -> None:
        item.setCheckState(
            Qt.CheckState.Unchecked
            if item.checkState() == Qt.CheckState.Checked
            else Qt.CheckState.Checked
        )
        self._refreshText()
        self.changed.emit()

    def _refreshText(self) -> None:
        chosen = self.checked()
        if not chosen:
            summary = self.tr("All")
        elif len(chosen) == 1:
            summary = chosen[0]
        else:
            summary = self.tr("{} selected").format(len(chosen))
        self.setText(f"{self._title}: {summary} ▾")


class SortItem(QStandardItem):
    """Table cell that sorts by a separate key (so dates and durations order
    properly rather than alphabetically)."""

    def __init__(self, text: str, key: Any = None) -> None:
        super().__init__(text)
        self.setEditable(False)
        self.setData(text.lower() if key is None else key, SORT_ROLE)


def _format_duration(seconds: int) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    return f"{hours:02}:{remainder // 60:02}"


class MatchExplorerWidget(Tab):
    """Screen listing every stored match with filters to narrow it down.

    It emits :attr:`openRequested` for the match to open and
    :attr:`backRequested` when the user wants the new-game screen back; the
    main window decides what to show.
    """

    openRequested = Signal(int, str)  # match id, game
    backRequested = Signal()

    COLUMNS = ("Started", "Game", "Status", "Winner", "Players", "Time", "Rounds")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.matches: list[MatchSummary] = []
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
        self.countLabel = QLabel(self)
        header.addWidget(self.countLabel)

        self.filterBox = QGroupBox(self)
        layout.addWidget(self.filterBox)
        filters = QVBoxLayout(self.filterBox)

        # Who and what
        row = QHBoxLayout()
        filters.addLayout(row)
        self.gamesButton = MultiChoiceButton(self)
        row.addWidget(self.gamesButton)
        self.playersButton = MultiChoiceButton(self)
        row.addWidget(self.playersButton)
        self.playersModeCombo = QComboBox(self)
        row.addWidget(self.playersModeCombo)
        self.winnerLabel = QLabel(self)
        row.addWidget(self.winnerLabel)
        self.winnerCombo = QComboBox(self)
        self.winnerCombo.setMinimumContentsLength(8)
        self.winnerCombo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        row.addWidget(self.winnerCombo)
        row.addStretch()

        # Outcome and length
        row = QHBoxLayout()
        filters.addLayout(row)
        self.statusButtons: dict[str, QPushButton] = {}
        for status in FILTER_STATUSES:
            button = QPushButton(self)
            button.setCheckable(True)
            button.setChecked(status in DEFAULT_STATUSES)
            colour = status_colour(status, self).name()
            button.setStyleSheet(
                f"QPushButton:checked {{ border-bottom: 3px solid {colour}; }}"
            )
            button.toggled.connect(self.refresh)
            row.addWidget(button)
            self.statusButtons[status] = button
        row.addSpacing(16)
        self.durationLabel = QLabel(self)
        row.addWidget(self.durationLabel)
        self.durationSpin = QSpinBox(self)
        self.durationSpin.setRange(0, 24 * 60)
        self.durationSpin.setSingleStep(5)
        self.durationSpin.setMinimumHeight(CONTROL_HEIGHT)
        self.durationSpin.setMinimumWidth(190)
        self.durationSpin.setStyleSheet("QSpinBox { padding: 2px 8px; }")
        row.addWidget(self.durationSpin)
        row.addStretch()

        # Dates
        row = QHBoxLayout()
        filters.addLayout(row)
        self.periodCombo = QComboBox(self)
        self.periodCombo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        self.periodCombo.setMinimumHeight(CONTROL_HEIGHT)
        row.addWidget(self.periodCombo)
        self.fromLabel = QLabel(self)
        row.addWidget(self.fromLabel)
        self.fromEdit = self._dateEdit()
        row.addWidget(self.fromEdit)
        self.toLabel = QLabel(self)
        row.addWidget(self.toLabel)
        self.toEdit = self._dateEdit()
        row.addWidget(self.toEdit)
        # The range only shows when the user picks a custom one.
        for widget in (self.fromLabel, self.fromEdit, self.toLabel, self.toEdit):
            widget.hide()
        row.addStretch()
        self.resetButton = QPushButton(self)
        self.resetButton.clicked.connect(self.resetFilters)
        row.addWidget(self.resetButton)

        # Results
        self.model = QStandardItemModel(0, len(self.COLUMNS), self)
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setSortRole(SORT_ROLE)
        self.table = QTableView(self)
        self.table.setModel(self.proxy)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setFont(tabular_figures(self.table.font()))
        self.table.verticalHeader().hide()
        self.table.setWordWrap(False)
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header_view.setStretchLastSection(False)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(self.openIndex)
        self.table.activated.connect(self.openIndex)
        self.table.selectionModel().selectionChanged.connect(self.updateOpenButton)
        layout.addWidget(self.table, 1)

        self.hintLabel = QLabel(self)
        layout.addWidget(self.hintLabel)
        self.openButton = QPushButton(self)
        self.openButton.setMinimumHeight(48)
        self.openButton.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.openButton.clicked.connect(self.openSelected)
        layout.addWidget(self.openButton)

        # Wire the filters last, so building them does not trigger queries.
        self.gamesButton.changed.connect(self.refresh)
        self.playersButton.changed.connect(self.refresh)
        self.playersModeCombo.currentIndexChanged.connect(self.refresh)
        self.winnerCombo.currentIndexChanged.connect(self.refresh)
        self.durationSpin.valueChanged.connect(self.refresh)
        self.periodCombo.currentIndexChanged.connect(self.onPeriodChanged)
        self.fromEdit.dateChanged.connect(self.refresh)
        self.toEdit.dateChanged.connect(self.refresh)

        self.table.sortByColumn(0, Qt.SortOrder.DescendingOrder)

    def _dateEdit(self) -> QDateEdit:
        edit = QDateEdit(self)
        edit.setCalendarPopup(True)
        edit.setDisplayFormat("yyyy-MM-dd")
        edit.setMinimumDate(ANY_DATE)
        edit.setDate(ANY_DATE)
        edit.setMinimumHeight(CONTROL_HEIGHT)
        edit.setMinimumWidth(170)
        edit.setStyleSheet("QDateEdit { padding: 2px 8px; }")
        return edit

    def retranslateUI(self) -> None:
        """Re-apply translated texts after a language or settings change."""
        words = appsettings["text_in_buttons"]
        self.backButton.setText(self.tr("Back") if words else "←")
        self.backButton.setToolTip(self.tr("Back to the new game screen"))
        self.titleLabel.setText(self.tr("Match history"))
        self.filterBox.setTitle(self.tr("Filters"))

        self.gamesButton.setTitle(self.tr("Game"), self.tr("Clear selection"))
        self.playersButton.setTitle(self.tr("Players"), self.tr("Clear selection"))
        self._setCombo(
            self.playersModeCombo,
            [self.tr("who all took part"), self.tr("any of whom took part")],
        )
        self.winnerLabel.setText(self.tr("Won by"))
        self._fillWinners()

        names = {
            STATUS_FINISHED: self.tr("Finished"),
            STATUS_SAVED: self.tr("Saved"),
            STATUS_CANCELLED: self.tr("Cancelled"),
            STATUS_INTERRUPTED: self.tr("Interrupted"),
        }
        for status, button in self.statusButtons.items():
            button.setText(names[status])
            button.setMinimumHeight(CONTROL_HEIGHT)
        self.durationLabel.setText(self.tr("At least"))
        self.durationSpin.setSuffix(self.tr(" min"))
        self.durationSpin.setSpecialValueText(self.tr("any length"))

        self._setCombo(
            self.periodCombo,
            [
                self.tr("All history"),
                self.tr("Today"),
                self.tr("Last 7 days"),
                self.tr("Last 30 days"),
                self.tr("This year"),
                self.tr("Custom range"),
            ],
        )
        self.periodCombo.setMinimumWidth(self.periodCombo.sizeHint().width())
        self.fromLabel.setText(self.tr("From"))
        self.toLabel.setText(self.tr("To"))
        for edit in (self.fromEdit, self.toEdit):
            edit.setSpecialValueText(self.tr("any"))
        self.resetButton.setText(self.tr("Reset filters") if words else "✕")
        self.resetButton.setToolTip(self.tr("Reset filters"))

        labels = (
            self.tr("Started"),
            self.tr("Game"),
            self.tr("Status"),
            self.tr("Winner"),
            self.tr("Players"),
            self.tr("Time"),
            self.tr("Rounds"),
        )
        self.model.setHorizontalHeaderLabels(list(labels))
        for column in range(len(labels)):
            if header := self.model.horizontalHeaderItem(column):
                align_item(header, column, TEXT_COLUMNS)
        self._statusNames = names
        self.updateOpenButton()
        self.hintLabel.setText(self.tr("Double-click a match to open it"))
        if self.matches:
            self.populate()

    @staticmethod
    def _setCombo(combo: QComboBox, texts: list[str]) -> None:
        """Set the texts of a fixed-choice combo, keeping its selection."""
        current = max(combo.currentIndex(), 0)
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(texts)
        combo.setCurrentIndex(current)
        combo.blockSignals(False)

    def _fillWinners(self) -> None:
        """List the players as possible winners, keeping the current choice."""
        current = self.winnerCombo.currentData()
        self.winnerCombo.blockSignals(True)
        self.winnerCombo.clear()
        self.winnerCombo.addItem(self.tr("anyone"), None)
        for nick in players_with_matches():
            self.winnerCombo.addItem(nick, nick)
        index = self.winnerCombo.findData(current)
        self.winnerCombo.setCurrentIndex(max(index, 0))
        self.winnerCombo.blockSignals(False)

    # --- Filtering ---------------------------------------------------------

    def currentFilter(self) -> MatchFilter:
        """The filter described by the controls."""
        chosen = tuple(s for s, b in self.statusButtons.items() if b.isChecked())
        if STATUS_CANCELLED in chosen:
            # Matches left running by a crash were never completed either.
            chosen += (STATUS_INTERRUPTED,)
        return MatchFilter(
            games=tuple(self.gamesButton.checked()),
            # All four buttons checked is the same as no restriction.
            statuses=chosen,
            players=tuple(self.playersButton.checked()),
            all_players=self.playersModeCombo.currentIndex() == 0,
            winner=self.winnerCombo.currentData(),
            date_from=self._date(self.fromEdit),
            date_to=self._date(self.toEdit),
            min_minutes=self.durationSpin.value(),
        )

    @staticmethod
    def _date(edit: QDateEdit) -> datetime.date | None:
        date = edit.date()
        return None if date == ANY_DATE else cast("datetime.date", date.toPython())

    def onPeriodChanged(self) -> None:
        """Fill the date range for the chosen period, or let the user edit it."""
        preset = self.periodCombo.currentIndex()
        today = QDate.currentDate()
        start, end = {
            PRESET_TODAY: (today, today),
            PRESET_WEEK: (today.addDays(-6), today),
            PRESET_MONTH: (today.addDays(-29), today),
            PRESET_YEAR: (QDate(today.year(), 1, 1), today),
        }.get(preset, (ANY_DATE, ANY_DATE))
        custom = preset == PRESET_CUSTOM
        for edit in (self.fromEdit, self.toEdit):
            edit.blockSignals(True)
        if not custom:
            self.fromEdit.setDate(start)
            self.toEdit.setDate(end)
        for widget in (self.fromLabel, self.fromEdit, self.toLabel, self.toEdit):
            widget.setVisible(custom)
        for edit in (self.fromEdit, self.toEdit):
            edit.blockSignals(False)
        self.refresh()

    def resetFilters(self) -> None:
        """Clear every filter."""
        for widget in (
            self.gamesButton,
            self.playersButton,
            self.playersModeCombo,
            self.winnerCombo,
            self.durationSpin,
            self.periodCombo,
            *self.statusButtons.values(),
        ):
            widget.blockSignals(True)
        self.gamesButton.reset()
        self.playersButton.reset()
        self.playersModeCombo.setCurrentIndex(0)
        self.winnerCombo.setCurrentIndex(0)
        self.durationSpin.setValue(0)
        self.periodCombo.setCurrentIndex(PRESET_ANY)
        for status, button in self.statusButtons.items():
            button.setChecked(status in DEFAULT_STATUSES)
        for widget in (
            self.gamesButton,
            self.playersButton,
            self.playersModeCombo,
            self.winnerCombo,
            self.durationSpin,
            self.periodCombo,
            *self.statusButtons.values(),
        ):
            widget.blockSignals(False)
        self.onPeriodChanged()

    def _reloadChoices(self) -> None:
        self.gamesButton.setChoices(games_with_matches())
        self.playersButton.setChoices(players_with_matches())
        self._fillWinners()

    # --- Results -----------------------------------------------------------

    def showEvent(self, event: QShowEvent) -> None:
        """Reload the choices and the list whenever the screen is shown, as
        matches may have been played or saved since."""
        self._reloadChoices()
        self.refresh()
        super().showEvent(event)

    def refresh(self, *_args: object) -> None:
        """Query the archive with the current filters and show the result."""
        try:
            self.matches = find_matches(self.currentFilter())
        except DatabaseError:
            logger.exception("Could not read the match history")
            self.matches = []
        self.populate()

    def populate(self) -> None:
        """Fill the table from ``self.matches``."""
        selected = self.selectedMatchId()
        self.table.setSortingEnabled(False)
        self.model.removeRows(0, self.model.rowCount())
        for match in self.matches:
            self.model.appendRow(self._row(match))
        self.table.setSortingEnabled(True)
        self.countLabel.setText(self.tr("{} matches").format(len(self.matches)))
        if selected is not None:
            self.selectMatch(selected)
        self.updateOpenButton()

    def _row(self, match: MatchSummary) -> list[SortItem]:
        started = match.started.astimezone() if match.started else None
        start_text = started.strftime("%Y-%m-%d %H:%M") if started else "—"
        winners = ", ".join(
            f"{w.nick} ({w.score})" if len(match.winners) == 1 else w.nick
            for w in match.winners
        )
        players = " · ".join(
            f"{'★ ' if p.winner else ''}{p.nick} {p.score}" for p in match.players
        )
        status = match.status

        items = [
            SortItem(start_text, started.timestamp() if started else 0),
            SortItem(match.game),
            SortItem(self._statusNames[status], STATUSES.index(status)),
            SortItem(winners or "—"),
            SortItem(players, len(match.players)),
            SortItem(_format_duration(match.elapsed), match.elapsed),
            SortItem(str(match.rounds), match.rounds),
        ]
        for column, item in enumerate(items):
            align_item(item, column, TEXT_COLUMNS)
        items[2].setForeground(QBrush(status_colour(status, self)))
        items[4].setToolTip(players)
        for item in items:
            item.setData(match.idMatch, ID_ROLE)
            item.setData(match.state, STATE_ROLE)
        return items

    def selectedMatchId(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        return rows[0].data(ID_ROLE) if rows else None

    def selectMatch(self, idMatch: int) -> None:
        """Re-select ``idMatch`` after the list was rebuilt, if still shown."""
        for row in range(self.proxy.rowCount()):
            index = self.proxy.index(row, 0)
            if index.data(ID_ROLE) == idMatch:
                self.table.selectRow(row)
                return

    # --- Opening -----------------------------------------------------------

    def _matchById(self, idMatch: int | None) -> MatchSummary | None:
        return next((m for m in self.matches if m.idMatch == idMatch), None)

    def updateOpenButton(self, *_args: object) -> None:
        """Label the open button for what it would do with the selection."""
        match = self._matchById(self.selectedMatchId())
        words = appsettings["text_in_buttons"]
        if match is not None and match.status == STATUS_SAVED:
            text, glyph = self.tr("Resume"), "▶"
        else:
            text, glyph = self.tr("Open"), "▷"
        self.openButton.setText(text if words else glyph)
        self.openButton.setStyleSheet("QPushButton { font-size: 24px; }")
        self.openButton.setToolTip(text)
        self.openButton.setEnabled(match is not None)

    def openIndex(self, index: QModelIndex) -> None:
        self.openMatch(index.data(ID_ROLE))

    def openSelected(self) -> None:
        idMatch = self.selectedMatchId()
        if idMatch is not None:
            self.openMatch(idMatch)

    def openMatch(self, idMatch: int) -> None:
        match = self._matchById(idMatch)
        if match is not None:
            self.openRequested.emit(match.idMatch, match.game)
