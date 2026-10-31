"""Text glyphs for icon-style buttons, with Android-safe substitutes.

Buttons without text labels use single characters. Android's system fonts lack
many of the technical symbols (``⎋`` ``⎌`` ``↻`` ...) so they render as empty
boxes there, while its emoji font is always present. Pass each literal through
:func:`platform_glyph` to get the original on desktop and the emoji stand-in
on Android; tune the table below after checking a device.
"""

from __future__ import annotations

from core.platform_info import is_android

# Forces emoji presentation for characters that are text by default.
_EMOJI = "\N{VARIATION SELECTOR-16}"

_ANDROID_GLYPHS = {
    "▶": f"▶{_EMOJI}",
    "▷": "📂",
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
    """``glyph`` itself, or its Android-safe replacement when running there."""
    return _ANDROID_GLYPHS.get(glyph, glyph) if is_android() else glyph
