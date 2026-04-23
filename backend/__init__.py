"""Hangd analytics backend.

Shared package used by the legacy CLI scripts (Clean.py, Analytics.py, ...)
and by the web app's analysis worker. Single source of truth for chess
analysis logic.
"""

from __future__ import annotations

import sys

__version__ = "0.1.0"


# Windows consoles default to cp1252, which crashes on the unicode arrows /
# en-dashes / etc. that appear in our prescription text. Switch stdout/stderr
# to UTF-8 once at import time so every entry point inherits it.
for _stream in (sys.stdout, sys.stderr):
    reconfigure = getattr(_stream, "reconfigure", None)
    if reconfigure is not None:
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
