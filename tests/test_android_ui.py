"""Android-specific UI behaviour, exercised on the desktop with a faked platform."""

import sys

import pytest
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout

from core.ui.dialogs import add_dismiss_button
from core.ui.glyphs import _ANDROID_GLYPHS, platform_glyph
from core.ui.theme import Theme, android_palette


@pytest.fixture
def android(monkeypatch):
    monkeypatch.setattr(sys, "getandroidapilevel", lambda: 34, raising=False)


@pytest.fixture
def desktop(monkeypatch):
    monkeypatch.delattr(sys, "getandroidapilevel", raising=False)


def test_glyphs_unchanged_on_desktop(desktop):
    assert all(platform_glyph(g) == g for g in _ANDROID_GLYPHS)


def test_glyphs_replaced_on_android(android):
    assert platform_glyph("⎋") == "🚪"
    assert platform_glyph("⎌").startswith("↩")
    # Anything not in the table passes through.
    assert platform_glyph("+") == "+"


def test_android_glyphs_differ_from_originals():
    assert all(original != new for original, new in _ANDROID_GLYPHS.items())


def test_dismiss_button_only_on_android(qapp, desktop):
    dialog = QDialog()
    layout = QVBoxLayout(dialog)
    assert add_dismiss_button(dialog, layout) is None
    assert dialog.findChildren(QDialogButtonBox) == []


def test_dismiss_button_rejects_dialog(qapp, android):
    dialog = QDialog()
    layout = QVBoxLayout(dialog)
    box = add_dismiss_button(dialog, layout, QDialogButtonBox.StandardButton.Cancel)
    assert box is not None
    results = []
    dialog.rejected.connect(lambda: results.append("rejected"))
    box.button(QDialogButtonBox.StandardButton.Cancel).click()
    assert results == ["rejected"]


def test_android_palette_follows_theme(qapp):
    dark = android_palette(Theme.DARK)
    light = android_palette(Theme.LIGHT)
    window = QPalette.ColorRole.Window
    assert dark.color(window).lightness() < 128 < light.color(window).lightness()
    text = QPalette.ColorRole.WindowText
    assert dark.color(text).lightness() > 128 > light.color(text).lightness()
