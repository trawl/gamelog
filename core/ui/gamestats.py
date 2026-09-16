"""Top-level game-statistics tab widget."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from core.ui.game.stats import (  # noqa: F401 — re-exported for callers using the old path
    AbstractQuickStatsBox,
    GeneralQuickStats,
    ParticularQuickStats,
    QuickStatsTW,
    StatsTable,
)
from core.ui.tab import Tab


class GameStatsWidget(Tab):
    """Placeholder tab reserved for the full game-statistics view."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._parent = parent
        self.initUI()

    def initUI(self) -> None:
        self.retranslateUI()

    def retranslateUI(self) -> None:
        pass
