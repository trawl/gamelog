"""Android-specific UI behaviour, exercised on the desktop with a faked platform."""

import sys

import pytest
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGraphicsOpacityEffect,
    QPushButton,
    QVBoxLayout,
)

from core.ui import glyphs
from core.ui.dialogs import add_dismiss_button
from core.ui.glyphs import _EMOJI_GLYPHS, platform_glyph, set_button_text
from core.ui.theme import Theme, android_palette


@pytest.fixture
def android(monkeypatch):
    monkeypatch.setattr(sys, "getandroidapilevel", lambda: 34, raising=False)


@pytest.fixture
def desktop(monkeypatch):
    monkeypatch.delattr(sys, "getandroidapilevel", raising=False)


def test_glyphs_unchanged_on_desktop_without_emoji_everywhere(desktop, monkeypatch):
    monkeypatch.setattr(glyphs, "EMOJI_EVERYWHERE", False)
    assert all(platform_glyph(g) == g for g in _EMOJI_GLYPHS)


def test_glyphs_replaced_on_desktop_with_emoji_everywhere(desktop, monkeypatch):
    monkeypatch.setattr(glyphs, "EMOJI_EVERYWHERE", True)
    assert platform_glyph("⎋") == "🚪"


def test_glyphs_replaced_on_android(android, monkeypatch):
    monkeypatch.setattr(glyphs, "EMOJI_EVERYWHERE", False)
    assert platform_glyph("⎋") == "🚪"
    assert platform_glyph("⎌").startswith("↩")
    # Anything not in the table passes through.
    assert platform_glyph("+") == "+"


def test_android_glyphs_differ_from_originals():
    assert all(original != new for original, new in _EMOJI_GLYPHS.items())


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


def test_disabled_emoji_button_is_faded(qapp):
    button = QPushButton()
    set_button_text(button, "🚪")
    assert button.graphicsEffect() is None

    button.setEnabled(False)
    effect = button.graphicsEffect()
    assert isinstance(effect, QGraphicsOpacityEffect)
    assert effect.opacity() < 1

    button.setEnabled(True)
    assert button.graphicsEffect() is None


def test_text_label_is_never_faded(qapp):
    button = QPushButton()
    button.setEnabled(False)
    set_button_text(button, "Leave Match")
    assert button.graphicsEffect() is None


def test_fade_follows_the_label_changing_while_disabled(qapp):
    button = QPushButton()
    button.setEnabled(False)
    set_button_text(button, "🚪")
    assert button.graphicsEffect() is not None
    set_button_text(button, "Leave Match")
    assert button.graphicsEffect() is None


class _FakeWindow:
    def __init__(self):
        self.calls = []

    def showFullScreen(self):
        self.calls.append("fullscreen")

    def showMaximized(self):
        self.calls.append("maximised")

    def showNormal(self):
        self.calls.append("normal")


@pytest.mark.parametrize(
    ("android_device", "fullscreen", "expected"),
    [
        (True, False, ["maximised"]),
        (True, True, ["fullscreen"]),
        (False, False, ["normal"]),
        (False, True, ["fullscreen"]),
    ],
)
def test_window_mode_follows_the_setting(
    monkeypatch, android_device, fullscreen, expected
):
    from core.ui import windowmode

    monkeypatch.setattr(windowmode, "is_android", lambda: android_device)
    monkeypatch.setattr(windowmode, "appsettings", {"fullscreen": fullscreen})
    window = _FakeWindow()
    windowmode.apply_window_mode(window)  # type: ignore[arg-type]
    assert window.calls == expected


def test_toggle_fullscreen_flips_and_applies_the_setting(monkeypatch):
    from core.ui import windowmode

    stored = {"fullscreen": False}

    class Stub(dict):
        def set(self, key, value):
            self[key] = value

    monkeypatch.setattr(windowmode, "is_android", lambda: False)
    monkeypatch.setattr(windowmode, "appsettings", Stub(stored))
    window = _FakeWindow()
    windowmode.toggle_fullscreen(window)  # type: ignore[arg-type]
    windowmode.toggle_fullscreen(window)  # type: ignore[arg-type]
    assert window.calls == ["fullscreen", "normal"]


def test_window_mode_setting_is_offered_with_platform_wording():
    from core.engine.settings import default_settings

    setting = default_settings["fullscreen"]
    assert setting["value"] is False
    # Desktop here: the non-full-screen choice is a normal window.
    assert setting["choices"] == ["windowed", "full screen"]
