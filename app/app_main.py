"""Compatibility shim for legacy dashboard launchers.

Older scripts start ``uvicorn app_main:app`` from this directory. The real
dashboard now lives in ``Dashboard/server.py``; keep this module as an import
bridge so stale launch paths cannot serve the deprecated v1.0 static shell.
"""

from __future__ import annotations

import sys
from pathlib import Path

DASHBOARD_ROOT = Path(__file__).resolve().parents[1]
if str(DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_ROOT))

from server import app  # noqa: E402,F401
