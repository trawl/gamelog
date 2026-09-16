"""core.ui.game — game-tab sub-package.

Re-exports every public name so that existing imports of the form
``from core.ui.game import GameWidget`` continue to work unchanged.
"""

from core.ui.game.colours import PlayerColours
from core.ui.game.input import (
    BonusButton,
    ClickableCounter,
    GameInputWidget,
    ScoreSpinBox,
    SpaceFilter,
)
from core.ui.game.matchedit import MatchTimesEditDialog
from core.ui.game.player import CardWidget, GamePlayerWidget, IconLabel
from core.ui.game.plots import PlotView
from core.ui.game.rounds import (
    GameRoundPlot,
    GameRoundsDetail,
    GameRoundTable,
    ToggleGroupBox,
)
from core.ui.game.stats import (
    AbstractQuickStatsBox,
    GeneralQuickStats,
    ParticularQuickStats,
    QuickStatsTW,
    StatsTable,
)
from core.ui.game.utils import GameNotImplementedException, SleepBlocker
from core.ui.game.widget import GameWidget

__all__ = [
    "AbstractQuickStatsBox",
    "GeneralQuickStats",
    "MatchTimesEditDialog",
    "ParticularQuickStats",
    "PlotView",
    "QuickStatsTW",
    "StatsTable",
    "BonusButton",
    "CardWidget",
    "ClickableCounter",
    "GameInputWidget",
    "GameNotImplementedException",
    "GamePlayerWidget",
    "GameRoundPlot",
    "GameRoundsDetail",
    "GameRoundTable",
    "GameWidget",
    "IconLabel",
    "PlayerColours",
    "ScoreSpinBox",
    "SleepBlocker",
    "SpaceFilter",
    "ToggleGroupBox",
]
