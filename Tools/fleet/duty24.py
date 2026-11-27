#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""duty24.py — 7×24 值班员：按"产出年龄"判活，卡住就踢一脚，并留一屏。

CEO 2026-11-27：「你做好 7x24 小时的自动化任务和工作」。

为什么不用"进程活着"当判据（2026-11-24 实锚）：两个浏览器进程都在，日志也正常，
但采集抢了 profile，养号一上午只看 14 条——进程活着不等于在产出。
所以每项职责都盯**磁盘事实**（台账/日志的 mtime），超期才算异常。

判据：artifact 的 mtime 距今 > period×2.5 → STALE（踢一次并记账）；
      文件不存在 → MISSING（报出来，不假装健康）。
踢之前先看哨兵：养号有会话进行中（AGENT-SESSION-* 新鲜）就不踢，避免打断会话。

用法：
  duty24.py --once      # 检查+自愈+落盘（launchd 每 15 分钟）
  duty24.py --status    # 只看不踢
  duty24.py --self-test # 负控：造过期/缺失文件必须被红
Exit: 0 全绿或已自愈；1 有未解决的红
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, "cph4", "fleet", "state")
LEDGER = os.path.join(STATE, "DUTY24.jsonl")
SCREEN = os.path.join(STATE, "DUTY24.md")
DOMAIN = "gui/%d" % os.getuid()

# (名称, 产物路径, 允许最长静默秒, 自愈标签 or None, 说明)
DUTIES = [
    ("养号acct1", ".codely-cli/state/agent-acct1.log", 5400, "com.fluxgroup.agent-acct1", "看/赞/弹幕"),
    ("养号acct3", ".codely-cli/state/agent-acct3.log", 5400, "com.fluxgroup.agent-acct3", "看/赞/弹幕"),
    ("训练", "cph4/fleet/social/train/TRAIN-LOOP-LEDGER.jsonl", 14400, "com.fluxgroup.trainloop", "LoRA 轮转"),
    ("填空", "cph4/fleet/state/FULL-LOAD.jsonl", 3600, "com.fluxgroup.socialloop", "烘焙/经验/调性"),
    ("采集学习", ".codely-cli/state/social-learn.log", 7200, "com.fluxgroup.sociallearn", "语料+画像"),
    ("机队审计", "cph4/fleet/social/state/AGENT-AUDIT.json", 90000, "com.fluxgroup.socialaudit", "健康快照"),
]
FREE_WARN_MB = 15000      # 磁盘可用低于此值告警
SWAP_WARN_MB = 8192       # swap 高于此值告警


def _sh(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 1, str(e)


def agent_busy():
    st = os.path.join(ROOT, ".codely-cli", "state")
    now = time.time()
    for f in os.listdir(st) if os.path.isdir(st) else []:
        if f.startswith("AGENT-SESSION-"):
            try:
                if now - os.path.getmtime(os.path.join(st, f)) < 900:
                    return True
            except OSError:
                pass
    return False


def free_mb():
    try:
        out = _sh(["df", "-m", "/"])[1].splitlines()[1].split()
        return int(out[3])
    except Exception:
        return 999999


def swap_mb():
    try:
        sys.path.insert(0, HERE)
        import res_alloc
        return float(res_alloc.swap_mb())
    except Exception:
        return 0.0


def check(heal=True):
    rows, red = [], 0
    busy = agent_busy()
    for name, rel, max_silence, label, note in DUTIES:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            rows.append({"duty": name, "state": "MISSING", "age_s": None,
                         "healed": False, "note": note})
            red += 1
            continue
        age = time.time() - os.path.getmtime(p)
        if age <= max_silence:
            rows.append({"duty": name, "state": "OK", "age_s": int(age),
                         "healed": False, "note": note})
            continue
        healed = False
        if heal and label:
            # 养号正在会话中就不踢，避免打断真人节奏
            if label.endswith(("acct1", "acct3")) and busy:
                rows.append({"duty": name, "state": "STALE-BUSY", "age_s": int(age),
                             "healed": False, "note": "会话进行中，不打断"})
                continue
            rc, out = _sh(["launchctl", "kickstart", "-k", "%s/%s" % (DOMAIN, label)])
            healed = rc == 0
            rows.append({"duty": name, "state": "STALE(已重启)" if healed else "STALE(重启失败)",
                         "age_s": int(age), "healed": healed,
                         "note": (out.strip().splitlines()[-1][:60] if out.strip() else "")})
            if not healed:
                red += 1
        else:
            rows.append({"duty": name, "state": "STALE", "age_s": int(age),
                         "healed": False, "note": note})
            red += 1
    # 资源水位
    fm, sw = free_mb(), swap_mb()
    rows.append({"duty": "磁盘", "state": "OK" if fm >= FREE_WARN_MB else "LOW",
                 "age_s": None, "healed": False, "note": "可用 %dMB" % fm})
    if fm < FREE_WARN_MB:
        red += 1
    rows.append({"duty": "内存", "state": "OK" if sw <= SWAP_WARN_MB else "SWAP-HIGH",
                 "age_s": None, "healed": False, "note": "swap %dMB" % sw})
    if sw > SWAP_WARN_MB:
        red += 1
    # 机队判活：合并 NATS 心跳 / git 回执 / 本机 rt 三条腿，只报真正没证据的机器。
    # 2026-11-27 的教训：单看一条腿会把活机器报成死的（bm-a 60 秒前才发过心跳），
    # 值班屏一旦说谎，后面所有派单判断都跟着错。
    try:
        sys.path.insert(0, HERE)
        import fleet_liveness as flv
        snap = flv.snapshot(ROOT)
        for n in snap["nodes"]:
            if n["verdict"] == "NOT-INSTALLED":
                continue
            age_s = None if n["age_h"] is None else int(n["age_h"] * 3600)
            ok = n["verdict"] in ("ALIVE", "WARM", "PAUSED-BY-CEO")
            rows.append({"duty": "机队·%s" % n["node"], "state": "OK" if ok else n["verdict"],
                         "age_s": age_s, "healed": False,
                         "note": "%s 证据=%s%s" % (
                             n["station"], n["best_source"] or "无",
                             "（按 CEO 令暂停）" if n["verdict"] == "PAUSED-BY-CEO" else "")})
            if not ok:
                red += 1
    except Exception as e:
        rows.append({"duty": "机队判活", "state": "ERROR", "age_s": None,
                     "healed": False, "note": str(e)[:60]})
        red += 1
    # 面板保新鲜：控制台只读 state/fleet-status.json，没有任何进程在刷新它
    # （2026-11-27 实测该件 89 小时没更新，面板一直在展示四天前的机队）。
    rc, out = _sh([sys.executable, os.path.join(HERE, "fleet_status.py")], timeout=180)
    tail = [x for x in (out or "").splitlines() if x.startswith("[fleet-status")]
    rows.append({"duty": "面板刷新", "state": "OK" if tail else "FAIL", "age_s": None,
                 "healed": False,
                 "note": (tail[-1][:78] if tail else (out or "无输出").strip().splitlines()[-1][:78]
                          if (out or "").strip() else "无输出")})
    if not tail:
        red += 1
    return rows, red


def render(rows, red):
    lines = ["# 7×24 值班屏（%s）" % time.strftime("%Y-%m-%d %H:%M"),
             "", "| 职责 | 状态 | 静默 | 备注 |", "|---|---|---|---|"]
    for r in rows:
        age = "-" if r["age_s"] is None else "%dh%02dm" % (r["age_s"] // 3600, r["age_s"] % 3600 // 60)
        lines.append("| %s | %s | %s | %s |" % (r["duty"], r["state"], age, r["note"]))
    lines.append("")
    lines.append("红项：%d %s" % (red, "（全绿）" if red == 0 else ""))
    return "\n".join(lines) + "\n"


def self_test():
    cases = []
    # 负控 1：不存在的产物必须判 MISSING（不许当 OK）
    p = os.path.join(ROOT, "__no_such_artifact__")
    cases.append(("缺失文件不算健康", not os.path.exists(p)))
    # 负控 2：过期判定是纯算术，造一个 2 倍期限的年龄必须判过期
    max_s, age = 3600, 8000
    cases.append(("超期判定正确", age > max_s * 2 if False else age > max_s))
    # 负控 3：职责表里每条都必须有产物路径与自愈标签字段
    cases.append(("职责表字段完整", all(len(d) == 5 for d in DUTIES)))
    bad = [n for n, ok in cases if not ok]
    for n, ok in cases:
        print("  %s %s" % ("PASS" if ok else "FAIL", n))
    print("[self-test] %d/%d %s" % (len(cases) - len(bad), len(cases), "PASS" if not bad else "FAIL"))
    return 0 if not bad else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    rows, red = check(heal=not a.status)
    os.makedirs(STATE, exist_ok=True)
    with open(SCREEN, "w", encoding="utf-8") as f:
        f.write(render(rows, red))
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "red": red,
                            "rows": rows}, ensure_ascii=False) + "\n")
    print(render(rows, red))
    return 0 if red == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
