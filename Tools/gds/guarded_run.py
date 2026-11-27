#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""guarded_run.py — 带硬超时的进程运行器 + 渲染能力探测。

为什么需要它
------------
本会话真实事故：用 `Start-Process -Wait` 等一个无桌面的 GUI 进程，它永远不退出，
后台任务挂了 6.8 小时才被人停；同一类渲染基准重复三次，全空手而回。
根因不是"慢"，是**没有超时、没有能力探测、失败还重试**。

两个子命令
----------
  python Tools/gds/guarded_run.py --timeout 90 -- <command...>
      运行命令；超时杀进程树（taskkill /T /F），返回码 124，并写回执。

  python Tools/gds/guarded_run.py --probe-render
      探测本会话能否渲染（启动一个 GUI 程序看 10 秒内是否产生日志）。
      结果缓存到 .codely-cli/tmp/render-capability.json，供后续任务先查后跑。

回执目录：.codely-cli/tmp/guarded-run/
退出码：0 成功 / 124 超时 / 其它=子进程原码 / 2 参数错误 / 3 探测不可用
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TMP = ROOT / ".codely-cli" / "tmp"
RUNS = TMP / "guarded-run"
CAP = TMP / "render-capability.json"


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def kill_tree(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                       capture_output=True, text=True)
    else:
        try:
            os.killpg(os.getpgid(pid), 9)
        except Exception:  # noqa: BLE001
            pass


def run_guarded(cmd: list[str], timeout: float) -> int:
    RUNS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    receipt = RUNS / f"run-{stamp}.json"

    kwargs = {"stdout": subprocess.PIPE, "stderr": subprocess.STDOUT, "text": True,
              "encoding": "utf-8", "errors": "replace"}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True

    t0 = time.time()
    p = subprocess.Popen(cmd, **kwargs)
    timed_out = False
    out = ""
    try:
        out, _ = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        kill_tree(p.pid)
        try:
            out, _ = p.communicate(timeout=10)
        except Exception:  # noqa: BLE001
            out = ""

    rc = 124 if timed_out else (p.returncode if p.returncode is not None else -1)
    rec = {
        "cmd": cmd, "timeout_s": timeout, "timed_out": timed_out,
        "rc": rc, "elapsed_s": round(time.time() - t0, 1),
        "tail": (out or "")[-2000:], "at": now(),
    }
    receipt.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: rec[k] for k in ("timed_out", "rc", "elapsed_s")}, ensure_ascii=False))
    if not timed_out and out:
        print(out[-4000:])
    print(f"receipt={receipt.relative_to(ROOT)}")
    return rc


def probe_render(seconds: float = 10.0) -> int:
    """Try to start any GUI app and see if it produces a log; cache the answer."""
    TMP.mkdir(parents=True, exist_ok=True)
    exe = None
    for cand in (
        ROOT / "cph4/fleet/game-v2/projects/fold-001/game/Builds/FoldDemo.exe",
        ROOT / "gaming/MiniGame/09_吸嘟嘟GimmeAll/GimmeAll/Build/GimmeAll.exe",
    ):
        if cand.exists():
            exe = cand
            break

    result = {"probed_at": now(), "render_available": False, "why": "no candidate exe"}
    if exe is not None:
        log = TMP / "probe-player.log"
        if log.exists():
            log.unlink()
        try:
            p = subprocess.Popen([str(exe), "-quit", "-logFile", str(log)],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            deadline = time.time() + seconds
            while time.time() < deadline and not log.exists():
                time.sleep(0.5)
            started = log.exists() and log.stat().st_size > 0
            result.update({"exe": str(exe), "log_written": started,
                           "render_available": bool(started),
                           "why": "log written" if started else "no log within timeout"})
            if p.poll() is None:
                kill_tree(p.pid)
        except Exception as exc:  # noqa: BLE001
            result.update({"exe": str(exe), "why": f"launch failed: {exc}"})

    CAP.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0 if result["render_available"] else 3


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--probe-render", action="store_true")
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    args = ap.parse_args()

    if args.probe_render:
        return probe_render()

    cmd = [c for c in args.cmd if c != "--"]
    if not cmd:
        print(json.dumps({"error": "no command; use -- <cmd...> or --probe-render"},
                         ensure_ascii=False))
        return 2
    return run_guarded(cmd, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
