"""Text glyphs for icon-style buttons, with emoji substitutes.

Buttons without text labels use single characters. Android's system fonts lack
many of the technical symbols (``⎋`` ``⎌`` ``↻`` ...) so they render as empty
boxes there, while its emoji font is always present. Pass each literal through
:func:`platform_glyph` to get the emoji stand-in. Android always gets it; the
other platforms get it while :data:`EMOJI_EVERYWHERE` is set (an experiment to
compare the look), otherwise the original character.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QAbstractButton, QGraphicsOpacityEffect

from core.platform_info import is_android

# Use the emoji on every platform, not only where the originals are missing.
EMOJI_EVERYWHERE = True

# Forces emoji presentation for characters that are text by default.
_EMOJI = "\N{VARIATION SELECTOR-16}"

_EMOJI_GLYPHS = {
    "▶": f"▶{_EMOJI}",
    "▷": "📂",
    "⬆": f"⬆{_EMOJI}",
    "⬇": f"⬇{_EMOJI}",
    "⏸": f"⏸{_EMOJI}",
    "⏺": "✅",
    "⏹": "🏁",
    "⎋": "🚪",
    "⎌": f"↩{_EMOJI}",
    "↻": "🔄",
    "↺": "🔄",
    "⌫": f"🗑{_EMOJI}",
    "✕": "❌",
    "♟↕": "👥",
    "☷": "📋",
    "∿": "📈",
    "σ": "📊",
    "∑": "🧮",
    "#": "🎲",
    "⏱": f"⏱{_EMOJI}",
}


def platform_glyph(glyph: str) -> str:
    """The emoji replacement for ``glyph`` where it applies, else ``glyph`` itself."""
    if EMOJI_EVERYWHERE or is_android():
        return _EMOJI_GLYPHS.get(glyph, glyph)
    return glyph


# Colour emoji ignore the palette, so a disabled button would keep its full
# colour. Fade the whole button instead.
_DISABLED_OPACITY = 0.35
_FILTER_PROPERTY = "_emojiDimming"
_EMOJI_TEXTS = frozenset(_EMOJI_GLYPHS.values()) | {"⚙️", "📖", "🗂", "📊"}


class _DimmingFilter(QObject):
    """Re-applies the fade when a button is enabled or disabled."""

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.EnabledChange and isinstance(
            watched, QAbstractButton
        ):
            sync_emoji_dimming(watched)
        return False


def sync_emoji_dimming(button: QAbstractButton) -> None:
    """Fade ``button`` while it is disabled and labelled with a colour emoji."""
    dim = button.text() in _EMOJI_TEXTS and not button.isEnabled()
    has_effect = isinstance(button.graphicsEffect(), QGraphicsOpacityEffect)
    if dim and not has_effect:
        effect = QGraphicsOpacityEffect(button)
        effect.setOpacity(_DISABLED_OPACITY)
        button.setGraphicsEffect(effect)
    elif not dim and has_effect:
        # None removes the effect; the bundled stub does not allow it.
        button.setGraphicsEffect(None)  # pyright: ignore[reportArgumentType]


def set_button_text(button: QAbstractButton, text: str) -> None:
    """``button.setText(text)``, keeping emoji labels faded while disabled.

    Use it for buttons that may show an emoji (see :func:`platform_glyph`) and
    can be disabled.
    """
    if not button.property(_FILTER_PROPERTY):
        button.installEventFilter(_DimmingFilter(button))
        button.setProperty(_FILTER_PROPERTY, True)
    button.setText(text)
    sync_emoji_dimming(button)
