"""How the statistics tables align and draw their cells.

Text columns (names, games, statuses) are left-aligned; figure columns (counts,
percentages, scores, durations, dates, the performance index) are right-aligned
with fixed-width digits so they line up. The alignment is a property of the
column, decided by the screen that knows what the column holds, and is shared by
its header and by every cell, placeholders included.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import Protocol

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

_VCENTER = Qt.AlignmentFlag.AlignVCenter
ALIGN_TEXT = Qt.AlignmentFlag.AlignLeft | _VCENTER
ALIGN_FIGURE = Qt.AlignmentFlag.AlignRight | _VCENTER


class _Aligned(Protocol):
    """A table or model item (``QTableWidgetItem``, ``QStandardItem``)."""

    def setTextAlignment(self, alignment: Qt.AlignmentFlag, /) -> None: ...


def column_alignment(column: int, text_columns: Collection[int]) -> Qt.AlignmentFlag:
    """Alignment of ``column``: left when it holds text, right otherwise."""
    return ALIGN_TEXT if column in text_columns else ALIGN_FIGURE


def align_item(item: _Aligned, column: int, text_columns: Collection[int]) -> None:
    """Align a cell or header item with its column."""
    item.setTextAlignment(column_alignment(column, text_columns))


def tabular_figures(font: QFont) -> QFont:
    """A copy of ``font`` with fixed-width digits, where Qt supports them.

    The font feature API exists from Qt 6.7; older versions silently keep the
    proportional digits.
    """
    tabular = QFont(font)
    if hasattr(QFont, "Tag") and hasattr(tabular, "setFeature"):
        tabular.setFeature(QFont.Tag("tnum"), 1)
    return tabular
