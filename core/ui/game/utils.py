"""Cross-platform sleep blocker and game exception."""

from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys


class SleepBlocker:
    """Cross-platform helper that keeps the screen and system awake."""

    def __init__(self) -> None:
        self.platform = sys.platform
        self.proc: subprocess.Popen | None = None
        self.active = False

        # Windows constants
        self.ES_CONTINUOUS = 0x80000000
        self.ES_SYSTEM_REQUIRED = 0x00000001
        self.ES_DISPLAY_REQUIRED = 0x00000002

    def start(self) -> None:
        """Block sleep/screensaver for the current platform."""
        if self.active:
            return

        if self.platform == "darwin":
            self._start_macos()
        elif self.platform.startswith("win"):
            self._start_windows()
        elif self.platform.startswith("linux"):
            self._start_linux()

        self.active = True

    def stop(self) -> None:
        """Release the sleep/screensaver block for the current platform."""
        if not self.active:
            return

        if self.platform == "darwin":
            self._stop_macos()
        elif self.platform.startswith("win"):
            self._stop_windows()
        elif self.platform.startswith("linux"):
            self._stop_linux()

        self.active = False

    # -------- macOS --------
    def _start_macos(self) -> None:
        self.proc = subprocess.Popen(
            ["caffeinate", "-dims", "-w", str(os.getpid())],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _stop_macos(self) -> None:
        if self.proc:
            self.proc.terminate()
            self.proc = None

    # -------- Windows --------
    def _start_windows(self) -> None:
        ctypes.windll.kernel32.SetThreadExecutionState(
            self.ES_CONTINUOUS | self.ES_SYSTEM_REQUIRED | self.ES_DISPLAY_REQUIRED
        )

    def _stop_windows(self) -> None:
        ctypes.windll.kernel32.SetThreadExecutionState(self.ES_CONTINUOUS)

    # -------- Linux (X11 only) --------
    def _start_linux(self) -> None:
        if shutil.which("xset"):
            subprocess.call(["xset", "s", "off"])
            subprocess.call(["xset", "-dpms"])

    def _stop_linux(self) -> None:
        if shutil.which("xset"):
            subprocess.call(["xset", "s", "on"])
            subprocess.call(["xset", "+dpms"])


class GameNotImplementedException(Exception):
    """Raised when a requested game has no concrete implementation."""
