"""Catan scoreboard widgets: per-player holdings tracker, round table and plot."""

from __future__ import annotations

from typing import cast

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QByteArray, QCoreApplication, QFile, QPoint, QRectF, QSize
from PySide6.QtGui import (
    QColor,
    QFont,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidgetItem,
    QWidget,
)

from core.ui.game import (
    BonusButton,
    GameInputWidget,
    GameNotImplementedException,
    GameRoundPlot,
    GameRoundsDetail,
    GameRoundTable,
    GameWidget,
    StatsTable,
)
from games.catan.engine import CatanEngine
from games.catan.model import CatanRound

# The colours of the pieces in the box (white drawn grey, to show on any theme).
_CATAN_COLOURS = [
    QColor(243, 124, 33),  # Orange
    QColor(150, 150, 150),  # White
    QColor(220, 30, 30),  # Red
    QColor(50, 100, 210),  # Blue
    QColor(0, 150, 60),  # Green
    QColor(140, 80, 200),  # Purple
    QColor(150, 95, 45),  # Brown
]

# Holdings tracked with a counter (the rest are awards held by one player).
COUNTERS = ("settlements", "cities", "vpcards")

# Icon of the button tracking each holding.
ICONS = {
    "settlements": "catan_settlement",
    "cities": "catan_city",
    "vpcards": "catan_vp",
    "longestroad": "catan_road",
    "largestarmy": "catan_army",
}

# Holding names, translated in the "CatanInputWidget" context.
LABELS = {
    "settlements": "Settlements",
    "cities": "Cities",
    "longestroad": "Longest road",
    "largestarmy": "Largest army",
    "vpcards": "VP cards",
}
QCoreApplication.translate("CatanInputWidget", "Settlements")
QCoreApplication.translate("CatanInputWidget", "Cities")
QCoreApplication.translate("CatanInputWidget", "Longest road")
QCoreApplication.translate("CatanInputWidget", "Largest army")
QCoreApplication.translate("CatanInputWidget", "VP cards")


def holdingLabel(key: str) -> str:
    return QCoreApplication.translate("CatanInputWidget", LABELS[key])


class CatanWidget(GameWidget):
    """Scoreboard tab for Catan, tracking every player's victory points."""

    player_colours = _CATAN_COLOURS

    def createEngine(self) -> None:
        if self.game != "Catan":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = CatanEngine()

    def initUI(self) -> None:
        """Build the board; every edit of the holdings is committed at once."""
        super().initUI()
        self.commitRoundButton.hide()
        cast("CatanInputWidget", self.gameInput).edited.connect(self.autoCommit)
        self.retranslateUI()

    def createGameInputWidget(self, parent: QWidget | None = None) -> CatanInputWidget:
        return CatanInputWidget(self.engine, parent)

    def createRoundsDetail(self, parent: QWidget | None = None) -> CatanRoundsDetail:
        return CatanRoundsDetail(self.engine, parent)

    def getPlayerExtraInfo(self, player: str) -> dict:
        """Return the holding changes entered for ``player``."""
        return cast("CatanInputWidget", self.gameInput).getChanges()[player]

    def checkPlayerScore(
        self, player: str, score: int, extras: dict | None = None
    ) -> bool:
        # Points can be lost (e.g. a stolen longest road), so any value goes.
        return score is not None

    def commitRoundSanityCheck(self, interactive: bool = False) -> bool:
        """Check that some holding changed and that awards have one holder."""
        gameInput = cast("CatanInputWidget", self.gameInput)
        if not gameInput.hasChanges():
            return False
        states = gameInput.getStates()
        awards = cast("CatanEngine", self.engine).getAwards()
        return all(sum(state[a] for state in states.values()) <= 1 for a in awards)

    def autoCommit(self) -> None:
        """Commit the holdings as soon as they are edited."""
        if self.commitRoundSanityCheck() and not self.engine.getWinner():
            self.commitRound()

    def undoCommit(self) -> None:
        """Roll back the last change without asking: edits commit instantly,
        so undoing is the everyday way to fix a slip."""
        if not self.engine.getRounds():
            return
        self.engine.deleteRound(len(self.engine.getRounds()))
        self.updatePanel()

    def setRoundTitle(self) -> None:
        # Every edit is a round, so a round number would mean nothing.
        self.roundTitleLabel.setText(self.engine.getGame() or "")


class CatanInputWidget(GameInputWidget):
    """Holdings tracker: one box per player, pre-filled with their holdings.

    ``edited`` is emitted once per user edit, after any award has changed
    hands, so the whole edit can be committed as a single round.
    """

    player_colours = _CATAN_COLOURS
    edited = QtCore.Signal()

    def initUI(self) -> None:
        self.widgetLayout = QGridLayout(self)
        for player in self.engine.getListPlayers():
            piw = CatanPlayerInputWidget(
                player,
                cast("CatanEngine", self.engine),
                self.playerColour(player),
                self,
            )
            self.playerInputList[player] = piw
            piw.changed.connect(self.changed)
            piw.edited.connect(self.edited)
            piw.awardClaimed.connect(self.awardClaimed)
        self.placePlayerInputs()
        self.reset()

    def placePlayerInputs(self) -> None:
        """Lay the player boxes out in rows of at most three, as even as possible.

        Up to 3 players share one row; 4 make two rows of 2, 5 a row of 3 and
        one of 2, and 6 two rows of 3.
        """
        players = self.engine.getListPlayers()
        rows = -(-len(players) // 3)
        columns = -(-len(players) // rows)
        for i, player in enumerate(players):
            self.widgetLayout.addWidget(
                self.playerInputList[player], i // columns, i % columns
            )

    def retranslateUI(self) -> None:
        for piw in self.playerInputList.values():
            piw.retranslateUI()

    def reset(self) -> None:
        """Load every player's committed holdings into their box."""
        engine = cast("CatanEngine", self.engine)
        for player, piw in self.playerInputList.items():
            state = engine.getPlayerState(player)
            piw.setState(state, state)
        self.changed.emit()

    def awardClaimed(self, award: str, player: str) -> None:
        """Take ``award`` away from everyone but ``player``."""
        for other, piw in self.playerInputList.items():
            if other != player:
                piw.releaseAward(award)

    def getStates(self) -> dict[str, dict[str, int]]:
        return {p: piw.getState() for p, piw in self.playerInputList.items()}

    def getChanges(self) -> dict[str, dict[str, int]]:
        return {p: piw.getChanges() for p, piw in self.playerInputList.items()}

    def hasChanges(self) -> bool:
        return any(piw.hasChanges() for piw in self.playerInputList.values())

    # Nobody may have gained points, so this widens the base return to None.
    def getWinner(self) -> str | None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Return the player gaining the most points this round, if any."""
        winner = None
        maxscore = 0
        for player, score in self.getScores().items():
            if score > maxscore:
                winner = player
                maxscore = score
        return winner

    def updatePlayerOrder(self) -> None:
        for piw in self.playerInputList.values():
            self.widgetLayout.removeWidget(piw)
            piw.setColour(self.playerColour(piw.getPlayer()))
        self.placePlayerInputs()


# Colour placeholders in the piece SVGs.
_BODY = "currentColor"
_OUTLINE = "#2B2B2B"
_DETAIL = "#3C3C3C"
_ROADLINE = "#FFFFFF"

_svgTemplates: dict[str, str] = {}
_pieceRenderers: dict[tuple[str, str, bool], QSvgRenderer] = {}


def pieceRenderer(icon: str, colour: QColor, held: bool) -> QSvgRenderer | None:
    """Return ``icon``'s piece in ``colour``, or white for a solid disc if held."""
    if icon not in _svgTemplates:
        _svgTemplates[icon] = ""
        svg = QFile(f":/icons/{icon}.svg")
        if svg.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            _svgTemplates[icon] = bytes(svg.readAll().data()).decode()
            svg.close()
    if not _svgTemplates[icon]:
        return None
    key = (icon, colour.name(), held)
    if key not in _pieceRenderers:
        if held:
            tokens = {
                _BODY: "#FFFFFF",
                _OUTLINE: colour.darker(180).name(),
                _DETAIL: "#FFFFFF",
                _ROADLINE: colour.name(),
            }
        else:
            # A milder outline and same-colour details keep the piece
            # legible on the dark theme as well as the light one.
            tokens = {
                _BODY: colour.name(),
                _OUTLINE: colour.darker(140).name(),
                _DETAIL: colour.name(),
                _ROADLINE: "#FFFFFF",
            }
        # Swap via unique markers so one replacement never feeds another.
        svg = _svgTemplates[icon]
        for i, token in enumerate(tokens):
            svg = svg.replace(token, f"@{i}@")
        for i, value in enumerate(tokens.values()):
            svg = svg.replace(f"@{i}@", value)
        _pieceRenderers[key] = QSvgRenderer(QByteArray(svg.encode()))
    return _pieceRenderers[key]


def paintPiece(
    painter: QPainter, rect: QRectF, icon: str, colour: QColor, held: bool
) -> None:
    """Paint ``icon`` in ``rect``: a white piece on a solid player-colour disc
    if held, else a player-colour piece on a faintly tinted disc."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    if held:
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(colour)
    else:
        fill = QColor(colour)
        fill.setAlpha(20)
        border = QColor(colour)
        border.setAlpha(100)
        painter.setPen(QPen(border, 1.5))
        painter.setBrush(fill)
    painter.drawEllipse(rect)
    renderer = pieceRenderer(icon, colour, held)
    if renderer:
        renderer.render(painter, rect)
    painter.restore()


class CatanBonusButton(BonusButton):
    """Bonus button showing how many of a piece a player holds.

    Like the app's checkable player buttons, it is a disc tinted with the
    player colour while the player holds none, and a solid disc with a white
    piece once they hold some; the count shows as a corner badge. A left click
    asks for one more, a right click for one less; the owner decides whether
    the step is allowed and sets the resulting value.
    """

    stepped = QtCore.Signal(int)

    def __init__(
        self,
        bonus_name: str,
        maximum: int = 1,
        colour: QColor | None = None,
        size: int = 48,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(bonus_name, maximum, colour, size, parent)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.clicked.disconnect(self.plusone)
        self.clicked.connect(lambda: self.stepped.emit(1))

    def setColour(self, colour: QColor) -> None:
        super().setColour(colour)
        self.update()

    def setValue(self, value: int) -> None:
        """Show ``value`` as the count; any count makes the disc solid."""
        self.count = value
        self.setChecked(value > 0)
        self.update()

    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == QtCore.Qt.MouseButton.RightButton:
            self.stepped.emit(-1)
            return
        super().mousePressEvent(e)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint the disc, the piece and, for counters, the count badge."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colour = QColor(self.highlight_colour)
        if not self.isEnabled():
            colour = QColor(150, 150, 150)
        held = self.count > 0
        disc = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        paintPiece(painter, disc, self.bonus_name, colour, held)

        if self.maximum > 1 and held:
            diameter = self.width() * 0.5
            badge = QRectF(
                self.width() - diameter, self.height() - diameter, diameter, diameter
            )
            badgeColour = colour.darker(150)
            painter.setPen(QPen(QColor("white"), 1.5))
            painter.setBrush(badgeColour)
            painter.drawEllipse(badge.adjusted(1, 1, -1, -1))
            painter.setPen(QColor("white"))
            font = QFont("Arial")
            font.setBold(True)
            font.setPixelSize(round(diameter * 0.75))
            painter.setFont(font)
            painter.drawText(
                badge, QtCore.Qt.AlignmentFlag.AlignCenter, str(self.count)
            )
        painter.end()


class CatanPlayerInputWidget(QGroupBox):
    """One player's holdings: counters and award toggles, titled by the player."""

    changed = QtCore.Signal()
    edited = QtCore.Signal()
    awardClaimed = QtCore.Signal(str, str)

    def __init__(
        self,
        player: str,
        engine: CatanEngine,
        colour: QColor | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.player = player
        self.engine = engine
        self.pcolour = colour if colour else QColor(0, 0, 0)
        self.limits = engine.getLimits()
        self.committed = dict.fromkeys(engine.getComponents(), 0)
        self.state = dict(self.committed)
        self.initUI()

    def initUI(self) -> None:
        self.setTitle(self.player)
        self.buttonsLayout = QHBoxLayout(self)
        self.bonusButtons: dict[str, CatanBonusButton] = {}
        for key in self.engine.getComponents():
            button = CatanBonusButton(
                ICONS[key], self.limits[key], self.pcolour, 48, self
            )
            if key in COUNTERS:
                button.stepped.connect(
                    lambda step, key=key: self.stepCounter(key, step)
                )
            else:
                button.stepped.connect(lambda _, key=key: self.toggleAward(key))
            self.bonusButtons[key] = button
            self.buttonsLayout.addWidget(button)

        self.setColour(self.pcolour)
        self.retranslateUI()

    def retranslateUI(self) -> None:
        for key, button in self.bonusButtons.items():
            button.setToolTip(holdingLabel(key))

    def setColour(self, colour: QColor) -> None:
        self.pcolour = colour
        r, g, b = colour.red(), colour.green(), colour.blue()
        self.setStyleSheet(f"""
            QGroupBox {{ font-size: 24px; font-weight: bold; color: rgb({r},{g},{b}); }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background-color: transparent;
            }}
        """)
        for button in self.bonusButtons.values():
            button.setColour(colour)

    def setState(self, committed: dict[str, int], current: dict[str, int]) -> None:
        """Set the committed holdings and the (possibly edited) current ones."""
        self.committed = dict(committed)
        self.state = dict(current)
        self.updatePanel()

    def stepCounter(self, key: str, step: int) -> None:
        """Change a counter by ``step``; a city replaces one of the settlements."""
        if not self.canStep(key, step):
            return
        self.state[key] += step
        if key == "cities":
            self.state["settlements"] -= step
        self.updatePanel()
        self.changed.emit()
        self.edited.emit()

    def canStep(self, key: str, step: int) -> bool:
        """Whether a counter can change by ``step`` within the piece limits."""
        value = self.state[key] + step
        if not 0 <= value <= self.limits[key]:
            return False
        if key == "cities":
            settlements = self.state["settlements"] - step
            return 0 <= settlements <= self.limits["settlements"]
        return True

    def toggleAward(self, key: str) -> None:
        """Grant or drop an award, claiming it from any other holder."""
        self.setAward(key, not self.state[key])
        self.edited.emit()

    def setAward(self, key: str, held: bool) -> None:
        """Grant or drop an award, claiming it from any other holder."""
        if self.state[key] == int(held):
            return
        self.state[key] = int(held)
        if held:
            self.awardClaimed.emit(key, self.player)
        self.updatePanel()
        self.changed.emit()

    def releaseAward(self, key: str) -> None:
        """Drop an award another player has just claimed."""
        self.setAward(key, False)

    def updatePanel(self) -> None:
        """Refresh the holding buttons."""
        for key, button in self.bonusButtons.items():
            button.setValue(self.state[key])

    def getPlayer(self) -> str:
        return self.player

    def getState(self) -> dict[str, int]:
        return dict(self.state)

    def getChanges(self) -> dict[str, int]:
        return {key: value - self.committed[key] for key, value in self.state.items()}

    def hasChanges(self) -> bool:
        return self.state != self.committed

    def getScore(self) -> int:
        """Return the victory points gained (or lost) by the pending changes."""
        return self.engine.victoryPoints(self.getChanges())


class CatanPieceHeader(QHeaderView):
    """Vertical header labelling each row with a piece icon.

    QHeaderView draws item icons at the style's small icon size whatever the
    view's icon size, so the pieces are painted here instead.
    """

    iconSize_ = 24
    colour = QColor(128, 128, 128)

    def __init__(self, icons: list[str], parent: QWidget | None = None) -> None:
        super().__init__(QtCore.Qt.Orientation.Vertical, parent)
        self.icons = icons

    def sizeHint(self) -> QSize:
        hint = super().sizeHint()
        hint.setWidth(self.iconSize_ + 12)
        return hint

    def paintSection(
        self, painter: QPainter, rect: QtCore.QRect, logicalIndex: int
    ) -> None:
        painter.save()
        super().paintSection(painter, rect, logicalIndex)
        painter.restore()
        if 0 <= logicalIndex < len(self.icons):
            size = min(self.iconSize_, rect.height() - 4)
            icon = QRectF(
                rect.center().x() - size / 2 + 1,
                rect.center().y() - size / 2 + 1,
                size,
                size,
            )
            paintPiece(painter, icon, self.icons[logicalIndex], self.colour, True)


class CatanRoundsDetail(GameRoundsDetail):
    """Rounds detail panel for Catan, adding a per-player holdings table."""

    def __init__(self, engine, parent: QWidget | None = None) -> None:
        self.bgcolors = [0xCCFF99, 0xFFCC99]
        super().__init__(engine, parent)

    def initUI(self) -> None:
        """Build the base tabs plus the holdings totals table."""
        super().initUI()
        self.totalsLabel = QLabel("", self)
        self.tableContainerLayout.addWidget(self.totalsLabel)
        self.totals = StatsTable(
            len(cast("CatanEngine", self.engine).getComponents()),
            len(self.engine.getPlayers()),
        )
        self.totals.setEditTriggers(StatsTable.EditTrigger.NoEditTriggers)
        # Rows are labelled by their piece, in a neutral colour.
        components = cast("CatanEngine", self.engine).getComponents()
        self.totals.setVerticalHeader(
            CatanPieceHeader([ICONS[key] for key in components], self.totals)
        )
        for row in range(len(components)):
            self.totals.setVerticalHeaderItem(row, QTableWidgetItem(""))
        self.tableContainerLayout.addWidget(self.totals)
        self.totals.setMaximumHeight(self.totals.sizeHint().height())

    def retranslateUI(self) -> None:
        for row, key in enumerate(cast("CatanEngine", self.engine).getComponents()):
            header = self.totals.verticalHeaderItem(row)
            if header:
                header.setToolTip(holdingLabel(key))
        self.totalsLabel.setText(self.tr("Totals"))
        super().retranslateUI()

    def updateRound(self) -> None:
        """Rebuild the base table and the holdings totals."""
        super().updateRound()
        engine = cast("CatanEngine", self.engine)
        players = engine.getListPlayers()
        self.totals.setHorizontalHeaderLabels(players)
        self.totals.clearContents()
        for col, player in enumerate(players):
            state = engine.getPlayerState(player)
            for row, key in enumerate(engine.getComponents()):
                if key in engine.getAwards():
                    text = "✓" if state[key] else ""
                else:
                    text = str(state[key])
                item = QTableWidgetItem(text)
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.totals.setItem(row, col, item)

    def createRoundTable(self, engine, parent: QWidget | None = None):
        return CatanRoundTable(self.engine, self.bgcolors, parent)

    def createRoundPlot(self, engine, parent: QWidget | None = None):
        return CatanRoundPlot(self.engine, self)


# Item data role holding a round-table cell's (score, colour, changes) to draw.
CHANGES_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1


def shownChanges(changes: dict[str, int]) -> dict[str, int]:
    """Return the changes worth showing: a city upgrade is shown as the city
    alone, without the settlement it replaced."""
    shown = dict(changes)
    shown["settlements"] = changes["settlements"] + changes["cities"]
    return {key: value for key, value in shown.items() if value}


class CatanChangesDelegate(QStyledItemDelegate):
    """Paints a round-table cell as the point change followed by piece icons.

    A gained piece shows solid, as on a held button; a lost one shows empty
    and crossed out; several of a kind are preceded by their count.
    """

    def paint(self, painter: QPainter, option, index) -> None:
        data = index.data(CHANGES_ROLE)
        if not data:
            super().paint(painter, option, index)
            return
        score, colour, changes = data
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.text = ""
        style = opt.widget.style() if opt.widget else QApplication.style()
        style.drawControl(
            QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget
        )

        foreground = index.data(QtCore.Qt.ItemDataRole.ForegroundRole)
        textColour = foreground.color() if foreground else opt.palette.text().color()
        rect = QRectF(opt.rect)
        iconSize = min(rect.height() - 6, 22)
        bold = QFont(opt.font)
        bold.setBold(True)
        parts = self._parts(score, changes)
        metrics = QtGui.QFontMetricsF(bold)
        gap = 4
        width = sum(
            metrics.horizontalAdvance(p) if isinstance(p, str) else iconSize
            for p in parts
        ) + gap * (len(parts) - 1)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(bold)
        painter.setPen(textColour)
        x = rect.center().x() - width / 2
        for part in parts:
            if isinstance(part, str):
                w = metrics.horizontalAdvance(part)
                painter.drawText(
                    QRectF(x, rect.top(), w, rect.height()),
                    QtCore.Qt.AlignmentFlag.AlignCenter,
                    part,
                )
            else:
                w = iconSize
                key, gained = part
                icon = QRectF(x, rect.center().y() - iconSize / 2, iconSize, iconSize)
                paintPiece(painter, icon, ICONS[key], colour, gained)
                if not gained:
                    painter.setPen(QPen(textColour, 2))
                    painter.drawLine(icon.bottomLeft(), icon.topRight())
            x += w + gap
        painter.restore()

    @staticmethod
    def _parts(score: int, changes: dict[str, int]) -> list:
        """Lay out a cell: the score text, then per change an optional count
        (text) and the piece (a ``(key, gained)`` tuple)."""
        parts: list = [f"{score:+d}"]
        for key, value in changes.items():
            if abs(value) > 1:
                parts.append(str(abs(value)))
            parts.append((key, value > 0))
        return parts


class CatanRoundTable(GameRoundTable):
    """Per-round table showing each player's point change and the pieces
    behind it."""

    def __init__(self, engine, bgcolors, parent: QWidget | None = None) -> None:
        self.bgcolors = bgcolors
        super().__init__(engine, parent)
        self.setItemDelegate(CatanChangesDelegate(self))

    def openTableMenu(self, position: QPoint) -> None:
        # Holdings build on each other, so only the last round can be deleted.
        if self.indexAt(position).row() != self.rowCount() - 1:
            return
        super().openTableMenu(position)

    def playerColour(self, player: str) -> QColor:
        """Return ``player``'s colour from the board, if this table is on one."""
        widget = self.parent()
        while widget is not None:
            if isinstance(widget, GameWidget):
                return widget.playerColour(player)
            widget = widget.parent()
        idx = self.engine.getListPlayers().index(player)
        return _CATAN_COLOURS[idx % len(_CATAN_COLOURS)]

    def insertRound(self, r) -> None:
        """Append a row for round ``r`` with each player's changes."""
        rnd = cast("CatanRound", r)
        i = rnd.getNumRound() - 1
        self.insertRow(i)
        for j, player in enumerate(self.engine.getListPlayers()):
            item = QTableWidgetItem()
            item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
            changes = shownChanges(rnd.getChanges(player))
            score = rnd.getPlayerScore(player)
            if changes:
                item.setData(CHANGES_ROLE, (score, self.playerColour(player), changes))
                item.setToolTip(
                    "\n".join(
                        f"{holdingLabel(key)}: {value:+d}"
                        for key, value in changes.items()
                    )
                )
            if score:
                background = self.bgcolors[0] if score > 0 else self.bgcolors[1]
                item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
                item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
            self.setItem(i, j, item)
        self.scrollToBottom()


class CatanRoundPlot(GameRoundPlot):
    """Victory points plot with the target points drawn as a limit line."""

    player_colours = _CATAN_COLOURS

    def updatePlot(self) -> None:
        super().updatePlot()
        if not self.isPlotInited():
            return
        initial = self.engine.victoryPoints(self.engine.getInitialState())
        scores = {}
        for player in self.engine.getPlayers():
            scores[player] = [initial]

        for rnd in self.engine.getRounds():
            for player in self.engine.getPlayers():
                accumscore = scores[player][-1] + rnd.getPlayerScore(player)
                scores[player].append(accumscore)

        self.canvas.clearPlotContents()
        self.canvas.addLimit(self.engine.getTop())
        for player in self.engine.getListPlayers():
            self.canvas.addSeries(scores[player], player)
