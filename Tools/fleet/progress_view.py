#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""progress_view.py - 自动推进的"事实页"：只说发生了什么，不下结论。

CEO 2026-11-05「你自动推进的过程我去哪看？给我看到事实的」。
事实来源全部是盘上物证，不采信任何自述：
  - 队列：最近完成/失败/退回的卡（含 owner、rc、failure 原文）
  - 回执：queue-receipts/ 最近若干份（含 rc、error_class）
  - 远端回执：state/remote-receipts/（远端失败原因）
  - 机队：state/lane-status/ 每机最后一次心跳（job/state/out_bytes/时间）
  - 每机最后产出：git log --grep "via <node>" 的时间
  - 探针：state/soak-summary.json
  - 发布：cph4/fleet/PROGRESS.md（人读）+ state/progress.json（机读，控制台读）

用法：
  python3 Tools/fleet/progress_view.py          # 生成两份
  python3 Tools/fleet/progress_view.py --json
Exit: 0
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
ST = os.path.join(F, "state")
Q = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
MD = os.path.join(F, "PROGRESS.md")
JS = os.path.join(ST, "progress.json")


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


def age(ts):
    try:
        return (datetime.now() - datetime.fromisoformat(str(ts))).total_seconds()
    except Exception:
        return 1e9


def node_output_h(node):
    try:
        out = subprocess.run(["git", "-C", ROOT, "log", "-1", "--format=%ct",
                              "--grep=via %s" % node],
                             capture_output=True, text=True, timeout=15).stdout.strip()
        return round((time.time() - int(out)) / 3600.0, 1) if out else None
    except Exception:
        return None


def collect(limit=15):
    cards = rows(Q)
    done = sorted([r for r in cards if r.get("state") == "DONE"],
                  key=lambda r: str(r.get("closed_at") or r.get("finished_at") or ""),
                  reverse=True)[:limit]
    failed = sorted([r for r in cards if r.get("state") == "FAILED"],
                    key=lambda r: str(r.get("finished_at") or ""), reverse=True)[:limit]
    released = [r for r in cards if r.get("release_reason")][-limit:]
    running = [r for r in cards if r.get("state") == "RUNNING"]
    openc = [r for r in cards if r.get("state") == "OPEN"]

    receipts = []
    fs = sorted(glob.glob(os.path.join(F, "queue-receipts", "*.json")),
                key=os.path.getmtime)[-limit:]
    for p in fs:
        d = jload(p)
        if isinstance(d, list):
            d = d[-1] if d else {}
        if not isinstance(d, dict):
            continue
        receipts.append({"file": os.path.basename(p), "node": d.get("node"),
                         "state": d.get("state"), "rc": d.get("rc"),
                         "error_class": d.get("error_class"),
                         "age_s": int(time.time() - os.path.getmtime(p))})
    remote = []
    for p in sorted(glob.glob(os.path.join(ST, "remote-receipts", "*.json")),
                    key=os.path.getmtime)[-limit:]:
        d = jload(p) or {}
        remote.append({"file": os.path.basename(p), "state": d.get("state"),
                       "rc": d.get("rc"), "error_class": d.get("error_class"),
                       "stderr_tail": (d.get("stderr_tail") or "")[-200:],
                       "cmd": (d.get("cmd") or "")[:120],
                       "age_s": int(time.time() - os.path.getmtime(p))})
    lanes = {}
    for p in glob.glob(os.path.join(ST, "lane-status", "*.json")):
        d = jload(p) or {}
        lanes[d.get("node") or os.path.basename(p)[:-5]] = {
            "state": d.get("state"), "job": d.get("job"),
            "out_bytes": d.get("out_bytes"),
            "age_s": int(age(d.get("received_at") or d.get("ts")))}
    workers = {n: node_output_h(n) for n in ("bm-a", "bm-b", "bm-c", "bm-m")}
    soak = jload(os.path.join(ST, "soak-summary.json"), {}) or {}
    # 2026-11-05 口径统一：队列 RUNNING 只代表"被认领"，不代表在干活。
    # 是否真在跑以 fleet-status 的逐卡判定为准（有 owner + 心跳新鲜 + 字节增长）。
    fs = jload(os.path.join(ST, "fleet-status.json"), {}) or {}
    verdict_of = {c.get("id"): c.get("verdict") for c in (fs.get("cards") or [])}
    real_running, claimed_only = [], []
    for r in running:
        item = {"id": r.get("id"), "owner": r.get("owner"), "line": r.get("line"),
                "verdict": verdict_of.get(r.get("id")) or "未判定"}
        (real_running if item["verdict"] == "RUNNING" else claimed_only).append(item)
    return {"ts": datetime.now().isoformat(timespec="seconds"),
            "running": real_running, "claimed_not_running": claimed_only,
            "open": len(openc),
            "recent_done": [{"id": r.get("id"), "owner": r.get("owner"),
                             "at": r.get("closed_at") or r.get("finished_at"),
                             "deliverable": r.get("deliverable")} for r in done],
            "recent_failed": [{"id": r.get("id"), "owner": r.get("owner"),
                               "rc": r.get("rc"), "error_class": r.get("error_class"),
                               "failure": (r.get("failure") or "")[:200],
                               "at": r.get("finished_at")} for r in failed],
            "recent_released": [{"id": r.get("id"), "by": r.get("released_by"),
                                 "why": r.get("release_reason")} for r in released],
            "receipts": receipts, "remote_receipts": remote,
            "lanes": lanes, "worker_last_output_h": workers,
            "soak": {"verdict": soak.get("verdict"), "green_pct": soak.get("green_pct"),
                     "samples": soak.get("samples"), "claimable_24h": soak.get("claimable_24h"),
                     "red": (soak.get("last") or {}).get("red")}}


def render(d):
    def hh(v):
        return "-" if v is None else ("%.1fh" % v)

    L = ["# 自动推进事实页", "",
         "> 生成：%s（每轮主控脉自动刷新；只列盘上事实，无结论、无自评）" % d["ts"], "",
         "## 一、现在在跑（队列 RUNNING）", ""]
    if d["running"]:
        L += ["| 卡 | 机器 | 线 |", "|---|---|---|"]
        L += ["| %s | %s | %s |" % (r["id"], r["owner"] or "-", r["line"] or "-")
              for r in d["running"]]
    else:
        L.append("（无）")
    if d.get("claimed_not_running"):
        L += ["", "已认领但无心跳（不算在跑，须查）：", ""]
        L += ["- %s（%s，%s）" % (c["id"], c["owner"] or "-", c["verdict"])
              for c in d["claimed_not_running"]]
    L += ["", "待派 OPEN：%d 张" % d["open"], "",
          "## 二、机队实况（每机最后一次心跳 + 最后产出）", "",
          "| 机器 | 心跳状态 | 在跑的卡 | out_bytes | 心跳龄 | 最后产出 |",
          "|---|---|---|---|---|---|"]
    for n, v in sorted(d["lanes"].items()):
        L.append("| %s | %s | %s | %s | %ss | %s |"
                 % (n, v.get("state"), v.get("job") or "-", v.get("out_bytes"),
                    v.get("age_s"), hh(d["worker_last_output_h"].get(n))))
    for n, v in sorted(d["worker_last_output_h"].items()):
        if n not in d["lanes"]:
            L.append("| %s | 无心跳件 | - | - | - | %s |" % (n, hh(v)))
    L += ["", "## 三、最近完成（含谁跑的）", ""]
    if d["recent_done"]:
        L += ["| 卡 | 机器 | 时间 | 产物 |", "|---|---|---|---|"]
        L += ["| %s | %s | %s | %s |" % (r["id"], r["owner"] or "-", r["at"] or "-",
                                         (r["deliverable"] or "-"))
              for r in d["recent_done"]]
    else:
        L.append("（无）")
    L += ["", "## 四、最近失败（附原因原文）", ""]
    if d["recent_failed"]:
        L += ["| 卡 | 机器 | rc | 定性 | 原因（原文截断） |", "|---|---|---|---|---|"]
        L += ["| %s | %s | %s | %s | %s |" % (r["id"], r["owner"] or "-", r["rc"],
                                              r["error_class"] or "-",
                                              (r["failure"] or "-").replace("|", "/").replace("\n", " ")[:120])
              for r in d["recent_failed"]]
    else:
        L.append("（无）")
    L += ["", "## 五、远端回执（失败原因能不能回到主控）", ""]
    if d["remote_receipts"]:
        L += ["| 回执 | 状态 | rc | 定性 | 命令 | stderr |", "|---|---|---|---|---|---|"]
        L += ["| %s | %s | %s | %s | %s | %s |"
              % (r["file"], r["state"], r["rc"], r["error_class"] or "-",
                 (r["cmd"] or "-")[:60].replace("|", "/"),
                 (r["stderr_tail"] or "-").replace("|", "/").replace("\n", " ")[:100])
              for r in d["remote_receipts"]]
    else:
        L.append("（无：远端还没有回执落盘）")
    L += ["", "## 六、最近退回的卡（谁退的、为什么）", ""]
    if d["recent_released"]:
        L += ["| 卡 | 退回者 | 原因 |", "|---|---|---|"]
        L += ["| %s | %s | %s |" % (r["id"], r["by"] or "-", r["why"] or "-")
              for r in d["recent_released"]]
    else:
        L.append("（无）")
    s = d["soak"]
    L += ["", "## 七、24h 运转探针", "",
          "- 结论：%s｜绿 %s%%｜采样 %d 次｜够不够判 24h：%s"
          % (s.get("verdict"), s.get("green_pct"), int(s.get("samples") or 0),
             "是" if s.get("claimable_24h") else "否"),
          "- 当前红项：%s" % (", ".join(s.get("red") or []) or "无"), "",
          "---", "查看面板：http://127.0.0.1:8787/ （首页含本页链接）"]
    return "\n".join(L) + "\n"


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    d = collect()
    os.makedirs(ST, exist_ok=True)
    json.dump(d, open(JS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(MD, "w", encoding="utf-8").write(render(d))
    if a.json:
        print(json.dumps(d, ensure_ascii=False, indent=1))
    else:
        print("[progress] %s 在跑 %d｜待派 %d｜远端回执 %d｜探针 %s"
              % (d["ts"], len(d["running"]), d["open"], len(d["remote_receipts"]),
                 d["soak"].get("verdict")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))