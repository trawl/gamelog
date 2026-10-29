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


# Room left empty on each side of a cell and of a title, so that values do not
# touch the gridlines. It is a style sheet padding, which the item delegates
# count in their size hints, so columns are sized with it.
CELL_PADDING = 6
CELL_STYLE = f"QTableView::item {{ padding: 0px {CELL_PADDING}px; }}"


# The same for the tables that keep the native look of their headers.
TABLE_STYLE = (
    f"{CELL_STYLE} QHeaderView::section:horizontal {{ padding: 4px {CELL_PADDING}px; }}"
)


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
