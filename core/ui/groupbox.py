"""Tell the stylesheet which group boxes have no title.

The Windows stylesheet (``WINDOWS_GROUPBOX_CSS``) reserves room above every
``QGroupBox`` for its title. A box without one, such as the two big boxes of
the new-game screen, would then leave a centimetre of empty space above its
contents, so those are flagged here and the stylesheet gives them no room.

A selector on ``title`` itself cannot do this: Qt evaluates a group box's
rules when it is built, while its title is still empty, and does not
re-evaluate when the title is set.
"""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QGroupBox, QWidget

UNTITLED_PROPERTY = "untitled"


def mark_untitled_group_boxes(root: QWidget) -> None:
    """Flag every group box under ``root`` that has no title, and restyle them.

    Call it once the titles are set, before the boxes are first shown.
    """
    for box in root.findChildren(QGroupBox):
        untitled = not box.title()
        if bool(box.property(UNTITLED_PROPERTY)) == untitled:
            continue
        box.setProperty(UNTITLED_PROPERTY, untitled)
        style = box.style()
        style.unpolish(box)
        style.polish(box)
        # QGroupBox only recomputes its frame margins on a style change.
        QCoreApplication.sendEvent(box, QEvent(QEvent.Type.StyleChange))
        box.updateGeometry()
