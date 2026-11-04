"""Runtime platform checks shared across the application."""

from __future__ import annotations

import sys


def is_android() -> bool:
    """True when running on Android.

    Android reports ``sys.platform == "linux"``, so desktop Linux code paths
    must check this first. CPython exposes ``sys.getandroidapilevel()`` only
    on Android builds.
    """
    return hasattr(sys, "getandroidapilevel")
