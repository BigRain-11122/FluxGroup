# -*- coding: utf-8 -*-
"""Shim. The LIVE implementation is Tools/backlog_fill.py -- that is the one
master_agent.py and lane_agent.py import (they put os.path.dirname(HERE)=Tools on
sys.path). Keeping two copies drifted apart for real: on 2026-10-30 fixes landed here
while the workers loaded the other file, so nothing changed for them. Do not add logic
here; add it to Tools/backlog_fill.py.

2026-10-30 fix: a bare `from backlog_fill import fill` resolves to THIS file whenever
Tools/fleet is earlier on sys.path (inventory_guard.py runs from there), which raised
"cannot import name 'fill' from 'backlog_fill'" and starved bm-a every tick. Load the
real file by explicit path so the module identity can never be ambiguous.
"""
import importlib.util
import os

_TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REAL = os.path.join(_TOOLS, "backlog_fill.py")

_spec = importlib.util.spec_from_file_location("_live_backlog_fill", _REAL)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

fill = _mod.fill
_fill_manifest = _mod._fill_manifest
_git_paths = _mod._git_paths
_tool_ok = _mod._tool_ok
_checkable = _mod._checkable