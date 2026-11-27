#!/usr/bin/env python3
"""runtime_dump.py — 在模拟器里挂 Frida，dump 已解析的配置对象

前置：adb forward tcp:27042 tcp:27042；frida-server 已在设备运行。
用法: python Tools/recon/runtime_dump.py <package> <hook.js> <out.jsonl> [seconds]
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

import frida


def main() -> int:
    pkg, hook, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    seconds = int(sys.argv[4]) if len(sys.argv) > 4 else 90

    dev = frida.get_device_manager().add_remote_device("127.0.0.1:27042")
    print("device:", dev)

    pid = dev.spawn([pkg])
    print("spawned pid", pid)
    session = dev.attach(pid)
    script = session.create_script(Path(hook).read_text(encoding="utf-8"))

    n = {"rows": 0, "msgs": 0}
    fh = out.open("w", encoding="utf-8")

    def on_message(msg, data):
        n["msgs"] += 1
        if msg.get("type") == "send":
            payload = msg.get("payload")
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
            if isinstance(payload, dict) and "row" in payload:
                n["rows"] += 1
                if n["rows"] % 50 == 0:
                    print("rows", n["rows"])
        elif msg.get("type") == "error":
            fh.write(json.dumps({"error": msg.get("description")}, ensure_ascii=False) + "\n")

    script.on("message", on_message)
    script.load()
    dev.resume(pid)
    print("running", seconds, "s ...")
    t0 = time.time()
    while time.time() - t0 < seconds:
        time.sleep(2)
    fh.close()
    try:
        dev.kill(pid)
    except Exception:
        pass
    print(json.dumps({"ok": True, "rows": n["rows"], "msgs": n["msgs"], "out": str(out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())