"""Android detection and the guards that depend on it."""

import sys

from core.platform_info import is_android
from core.ui.game.utils import SleepBlocker


def test_is_android_follows_api_level_hook(monkeypatch):
    monkeypatch.delattr(sys, "getandroidapilevel", raising=False)
    assert not is_android()
    monkeypatch.setattr(sys, "getandroidapilevel", lambda: 34, raising=False)
    assert is_android()


def test_sleep_blocker_does_not_shell_out_on_android(monkeypatch):
    monkeypatch.setattr(sys, "getandroidapilevel", lambda: 34, raising=False)
    blocker = SleepBlocker()
    blocker.platform = "linux"
    calls = []
    monkeypatch.setattr(blocker, "_start_linux", lambda: calls.append("start"))
    monkeypatch.setattr(blocker, "_stop_linux", lambda: calls.append("stop"))
    blocker.start()
    blocker.stop()
    assert calls == []
