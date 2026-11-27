#!/usr/bin/env python3
"""attach_dump.py — 附着已运行进程并加载 Frida 代理，收集输出

用法: python Tools/recon/attach_dump.py <target> <agent.js> <out.jsonl> [seconds]
target 可为进程名或 pid。
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

import frida


def main() -> int:
    target, agent, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    seconds = int(sys.argv[4]) if len(sys.argv) > 4 else 60

    dev = frida.get_device_manager().add_remote_device("127.0.0.1:27042")
    tgt = int(target) if str(target).isdigit() else target
    session = dev.attach(tgt)
    script = session.create_script(agent.read_text(encoding="utf-8"))

    stats = {"rows": 0, "msgs": 0, "errors": 0}
    fh = out.open("w", encoding="utf-8")

    def on_message(msg, data):
        stats["msgs"] += 1
        if msg.get("type") == "send":
            payload = msg.get("payload")
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
            if isinstance(payload, dict):
                if "row" in payload:
                    stats["rows"] += 1
                if "err" in payload:
                    stats["errors"] += 1
                    print("ERR:", payload["err"])
        else:
            stats["errors"] += 1
            print("MSG:", msg.get("description", msg)[:300])

    script.on("message", on_message)
    script.load()
    print("attached; collecting", seconds, "s")
    t0 = time.time()
    while time.time() - t0 < seconds:
        time.sleep(2)
        if stats["rows"] % 200 == 0 and stats["rows"]:
            print("rows", stats["rows"])
    fh.close()
    print(json.dumps({"ok": True, **stats, "out": str(out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())