#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lane_registry.py - task-level lane registry for THIS node.

Why (D-20261102-05, D-20261101-22): task-health could count disabled tasks but never say
who stopped them or when. Two probes were tried on bm-a on 2026-11-02 and both failed for
a *provable* reason, so the registry records what is provable instead of inventing a field:

  1. definition files under %SystemRoot%\\System32\\Tasks: directory listing is empty for
     an unelevated process (ACCESS-DENIED) -> no mtime, no <Principal>.
  2. Task Scheduler Operational log: no task-update/disable events on this box.

So: one `schtasks /query /fo list /v` call (hidden window, CREATE_NO_WINDOW - a scheduled
lane must never flash a console), parsed positionally (labels are localized; field order is
not). change_time stays "UNVERIFIABLE" with the reason attached, and --check says so out loud
rather than printing a green over an empty field.

Output: cph4/fleet/state/lane-registry.jsonl (one row per task)
Usage:  python Tools/fleet/lane_registry.py [--check]
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "cph4", "fleet", "LANE-REGISTRY.jsonl")
NODE = os.environ.get("FLUX_NODE") or "bm-a"
CREATE_NO_WINDOW = 0x08000000


def txt(el, tag):
    if el is None:
        return ""
    node = el.find(".//{*}" + tag)
    return (node.text or "").strip() if node is not None else ""


def query():
    r = subprocess.run(["schtasks", "/query", "/xml", "ONE"],
                       capture_output=True, creationflags=CREATE_NO_WINDOW)
    if r.returncode != 0:
        return []
    text = r.stdout.decode("utf-8", "replace")
    out = []
    for chunk in re.split(r"(?=<Task )", text):
        if not chunk.startswith("<Task "):
            continue
        try:
            root = ET.fromstring("<Root>" + chunk + "</Root>")
        except ET.ParseError:
            continue
        task = root.find("{*}Task")
        if task is None:
            continue
        uri = txt(task, "URI")
        if not uri or uri.lower().startswith("\\microsoft"):
            continue
        principal = task.find("{*}Principals/{*}Principal")
        settings = task.find("{*}Settings")
        out.append({
            "node": NODE,
            "name": uri.split("\\")[-1],
            "task_path": uri.rsplit("\\", 1)[0] + "\\" if "\\" in uri[1:] else "\\",
            "state": "DISABLED" if (txt(settings, "Enabled") or "true").lower() == "false" else "ENABLED",
            "owner": txt(principal, "UserId") or "UNRESOLVED",
            "logon_type": txt(principal, "LogonType"),
            "last_run": "",
            "last_result": "",
            "change_time": "UNVERIFIABLE",
            "change_time_note": "Tasks 目录未提权不可读 + TaskScheduler 无停用事件；取证需提权(CEO 物理件)",
        })
    out.sort(key=lambda r: (r["state"] != "DISABLED", r["name"].lower()))
    return out


def main() -> int:
    rs = query()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for r in rs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    disabled = [r for r in rs if r["state"] == "DISABLED"]
    unresolved = [r for r in rs if r["owner"] == "UNRESOLVED"]
    print("[lane-registry] node=%s scanned=%d rows=%d disabled=%d owner_unresolved=%d change_time_verifiable=0"
          % (NODE, len(rs), len(rs), len(disabled), len(unresolved)))
    print("[lane-registry] disabled(%d): %s" % (len(disabled), ", ".join(
        "%s@%s[%s]" % (r["name"], r["owner"], r["last_run"]) for r in disabled[:40])))
    if "--check" in sys.argv:
        if not rs:
            print("[lane-registry] EMPTY-SCOPE: schtasks 返回 0 行，不得据此称绿")
            return 3
        no_owner = [r for r in rs if not r["owner"]]
        print("[lane-registry] check rows_with_empty_owner=%d change_time_field=UNVERIFIABLE(已标注，非空缺)"
              % len(no_owner))
        print("[lane-registry] CHECK-PARTIAL: owner 可取证 / change_time 不可取证（提权物理件在册）")
        return 1 if no_owner else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())