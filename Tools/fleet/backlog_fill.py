# -*- coding: utf-8 -*-
"""Shim. The LIVE implementation is Tools/backlog_fill.py -- that is the one
master_agent.py and lane_agent.py import (they put os.path.dirname(HERE)=Tools on
sys.path). Keeping two copies drifted apart for real: on 2026-10-30 fixes landed here
while the workers loaded the other file, so nothing changed for them. Do not add logic
here; add it to Tools/backlog_fill.py.
"""
import os
import sys

_TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

from backlog_fill import (  # noqa: E402,F401
    fill, _fill_manifest, _git_paths, _tool_ok, _checkable,
)
