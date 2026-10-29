"""Presentation of the chance-adjusted performance index, shared by the player
statistics screen and the game quick statistics."""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication

NONE_TEXT = "—"


def format_performance(value: float | None) -> str:
    """The index to two decimals (``1.35×``), or a dash when undefined."""
    return NONE_TEXT if value is None else f"{value:.2f}×"


def performance_tooltip() -> str:
    """Explanation of what the index means, in the current language."""
    return QCoreApplication.translate(
        "Performance",
        "Wins compared with what chance predicts for the number of players: "
        "1.00× means winning exactly as often as chance, 2.00× twice as often.",
    )
