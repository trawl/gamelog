"""Helpers for the timestamps stored in the database."""

from __future__ import annotations

import datetime


def parse_db_time(value: object) -> datetime.datetime | None:
    """Parse a stored timestamp (with or without UTC offset) to an aware UTC
    datetime, or ``None`` when it is missing or unreadable."""
    if not value or str(value) == "None":
        return None
    text = str(value)
    for fmt in ("%Y-%m-%d %H:%M:%S.%f%z", "%Y-%m-%d %H:%M:%S%z"):
        try:
            return datetime.datetime.strptime(text, fmt).astimezone(datetime.UTC)
        except ValueError:
            continue
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.datetime.strptime(text, fmt).replace(tzinfo=datetime.UTC)
        except ValueError:
            continue
    return None
