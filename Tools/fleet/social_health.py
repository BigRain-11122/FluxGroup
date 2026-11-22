#!/usr/bin/env python3
"""social_health.py — 养号线健康哨兵：一次回答"现在健康吗、哪里不健康"。

判据原则（都是踩过的坑）：
- **进程活着 ≠ 在干活**：daemon 有 pid 但一天零动作，要判黄并说明原因（非时段/未登录/锁僵尸）。
- **锁与哨兵会变僵尸**：崩掉的会话留下 BILI-MID-*.lock 与 AGENT-SESSION-*，
  会让下一场白等 180 秒甚至永远拦训练；超过 3 小时且 pid 已死就可清。
- **swap 只认增量**：历史存量 1.8GB 稳定不算病，几十分钟涨几百 MB 才是。
- **磁盘**：训练产物每轮约 130MB，只报告不自动删（删要人判）。

用法：
  python3 Tools/fleet/social_health.py            # 报告（默认）
  python3 Tools/fleet/social_health.py --fix      # 修可确定的僵尸（锁/哨兵/闲置模型）
  python3 Tools/fleet/social_health.py --json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
STATE = os.path.join(ROOT, ".codely-cli", "state")
ACC = os.path.expanduser("~/.fluxgroup/bili-accounts.json")
LEDGER = os.path.join(SOCIAL, "USER-AGENT-LEDGER.jsonl")
PRACTICE = os.path.join(SOCIAL, "practice-log.jsonl")
OUT = os.path.join(STATE, "HEALTH.json")
PERSONAS = os.path.join(SOCIAL, "ACCOUNT-PERSONAS.json")


def _load(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return d if d is not None else {}


def _rows(limit=None):
    rows = []
    try:
        for line in open(LEDGER, encoding="utf-8"):
            if line.strip():
                rows.append(json.loads(line))
    except FileNotFoundError:
        pass
    return rows[-limit:] if limit else rows


def _rows_file(path, limit=None):
    rows = []
    try:
        for line in open(path, encoding="utf-8"):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    except FileNotFoundError:
        pass
    return rows[-limit:] if limit else rows


def daemons():
    out = {}
    try:
        txt = subprocess.run(["launchctl", "list"], capture_output=True, text=True,
                             timeout=15).stdout
        for line in txt.splitlines():
            if "com.fluxgroup.agent-" in line:
                parts = line.split()
                alias = parts[2].replace("com.fluxgroup.agent-", "")
                pid = parts[0]
                out[alias] = int(pid) if pid.isdigit() else None
    except Exception:
        pass
    return out


def accounts():
    d = _load(ACC, {})
    return {k: v for k, v in (d.get("accounts") or {}).items() if isinstance(v, dict)}


def activity_today(alias_uname):
    """alias_uname 可以是单个标识或一组标识（alias 与 uname 都要认）。

    落账口径不统一是历史事实：USER-AGENT-LEDGER 写 uname，practice-log 写 alias（FLUX_ACCOUNT）。
    只认一种就会把另一种当成"别人的行"，于是再次出现"实发 9 条、HEALTH 记 0"。
    """
    ids = {str(x) for x in (alias_uname if isinstance(alias_uname, (set, list, tuple))
                            else [alias_uname]) if x}
    today = datetime.now().strftime("%Y-%m-%d")
    c = {"session": 0, "watch": 0, "like": 0, "danmaku": 0, "comment": 0, "need_login": 0}
    last = ""
    for r in _rows():
        if r.get("account") and str(r.get("account")) not in ids:
            continue
        ts = str(r.get("ts") or "")
        if ts.startswith(today) and r.get("action") in c:
            c[r["action"]] += 1
        if ts > last:
            last = ts
    # 真实发帖落 practice-log（USER-AGENT-LEDGER 只有看/赞/弹幕），不并进来
    # "今日评论数"就恒为 0——2026-11-22 实锚：当天真发 9 条，HEALTH 记 acct1=0/acct3=0，
    # 于是 SD05 配额判据永远绿。行里没有 account 的历史记录计入 comment_unknown，不硬摊给某个号。
    unknown = 0
    for r in _rows_file(PRACTICE):
        if r.get("action") != "post" or not str(r.get("ts") or "").startswith(today):
            continue
        acct = r.get("account")
        if acct and str(acct) not in ids:
            continue
        if acct:
            c["comment"] += 1
        else:
            unknown += 1
        ts = str(r.get("ts") or "")
        if ts > last:
            last = ts
    c["comment_unknown"] = unknown
    return c, last


def personas():
    return _load(PERSONAS, {})


def in_hours(per, now=None):
    hrs = (per or {}).get("hours") or []
    if not hrs:
        return True
    h = (now or datetime.now()).hour
    return any(abs(h - x) <= 1 or abs(h - x) >= 23 for x in hrs)


def swap_mb():
    try:
        out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True,
                             text=True, timeout=10).stdout
        return float(re.search(r"used = ([0-9.]+)M", out).group(1))
    except Exception:
        return 0.0


def stale_files():
    """僵尸锁/哨兵：pid 已死，或超过 3 小时。"""
    dead = []
    for f in os.listdir(STATE) if os.path.isdir(STATE) else []:
        if not (f.startswith("BILI-MID-") and f.endswith(".lock")) and \
           not f.startswith("AGENT-SESSION-"):
            continue
        p = os.path.join(STATE, f)
        try:
            pid = int(open(p, encoding="utf-8").read().strip() or 0)
        except Exception:
            pid = 0
        alive = False
        if pid:
            try:
                os.kill(pid, 0)
                alive = True
            except Exception:
                alive = False
        old = time.time() - os.path.getmtime(p) > 3 * 3600
        if not alive or old:
            dead.append((f, pid, old, alive))
    return dead


def train_state():
    sent = os.path.join(STATE, "TRAIN-EXCLUSIVE")
    running = bool(subprocess.run(["pgrep", "-f", "mlx_lm lora"],
                                  capture_output=True).returncode == 0)
    age = (time.time() - os.path.getmtime(sent)) / 60 if os.path.exists(sent) else None
    runs = os.path.join(ROOT, "cph4", "fleet", "social", "train", "RUNS")
    n, size = 0, 0
    try:
        for d in os.listdir(runs):
            p = os.path.join(runs, d)
            if os.path.isdir(p):
                n += 1
                for root, _, files in os.walk(p):
                    for f in files:
                        size += os.path.getsize(os.path.join(root, f))
    except Exception:
        pass
    return {"running": running, "sentinel": bool(age is not None),
            "sentinel_min": round(age, 1) if age is not None else None,
            "runs": n, "runs_gb": round(size / 1e9, 2)}


def check():
    acc, per, dm = accounts(), personas(), daemons()
    items, worst = [], "green"
    for alias, a in acc.items():
        if not a.get("mid"):
            continue
        # 备用 profile（primary=False）本来就不该有 daemon：它是主 profile 坏掉时的替补，
        # 不参与日常运行。判红它等于把"备用"当成"掉线"。
        if a.get("primary") is False:
            continue
        name = a.get("uname") or str(a.get("mid"))
        pid = dm.get(alias)
        c, last = activity_today({str(alias), str(name)})
        p = per.get(a.get("persona") or alias) or {}
        alive = bool(pid)
        acts = c["like"] + c["danmaku"] + c["comment"]
        lvl = "green"
        why = ""
        if not alive:
            lvl, why = "red", "daemon 未运行（launchd 未装载或已退出）"
        elif c["need_login"]:
            lvl, why = "red", "登录态失效（需人工登录一次）"
        elif in_hours(p) and acts == 0 and c["session"] == 0:
            lvl, why = "yellow", "在活跃时段但今天零动作（看锁僵尸/登录/配额）"
        elif acts == 0:
            lvl, why = "yellow", "今天零动作（可能不在时段，属正常）"
        items.append({"alias": alias, "name": name, "pid": pid, "alive": alive,
                      "today": c, "last_ts": last, "in_hours": in_hours(p),
                      "level": lvl, "why": why})
        worst = "red" if (lvl == "red" or worst == "red") else (
            "yellow" if (lvl == "yellow" or worst == "yellow") else worst)

    dead = stale_files()
    sw = swap_mb()
    tr = train_state()
    if dead:
        worst = "yellow" if worst == "green" else worst
    if not tr["running"] and tr["sentinel"] and (tr["sentinel_min"] or 0) > 60:
        worst = "red" if worst != "red" else worst
    rep = {"ts": datetime.now().isoformat(timespec="seconds"), "level": worst,
           "accounts": items, "stale": [d[0] for d in dead],
           "swap_mb": sw, "train": tr}
    return rep


def fix(rep):
    done = []
    for f, pid, _old, alive in stale_files():
        try:
            os.remove(os.path.join(STATE, f))
            done.append("清理僵尸 %s（pid=%s 存活=%s）" % (f, pid, alive))
        except Exception as e:
            done.append("清理失败 %s：%s" % (f, e))
    # 训练哨兵在有训练在跑时绝不清（那会让两条线同时抢 GPU）。
    # 但判据不能用"等满 3 小时"——2026-11-21 实锚：训练 21:50 结束、哨兵里的 pid 20909
    # 已死，出稿却一直记 skip why=training-gpu 让路一小时多。哨兵里本来就写了 pid，判它死活最快。
    tr = rep.get("train") or {}
    if tr.get("sentinel") and not tr.get("running"):
        sent = os.path.join(STATE, "TRAIN-EXCLUSIVE")
        pid, dead = None, False
        try:
            parts = open(sent, encoding="utf-8").read().split()
            pid = int(parts[-1]) if parts and parts[-1].isdigit() else None
        except Exception:
            pass
        if pid:
            try:
                os.kill(pid, 0)
            except Exception:
                dead = True
        if dead or (tr.get("sentinel_min") or 0) > 180:
            try:
                os.remove(sent)
                done.append("清理僵尸训练哨兵（pid=%s 存活=%s，挂了 %.0f 分钟）"
                            % (pid, not dead, tr.get("sentinel_min") or 0))
            except Exception as e:
                done.append("清理僵尸哨兵失败：%s" % e)
    # swap 高→卸闲置 ollama 模型（复用看门狗的动作，不杀训练）
    if rep.get("swap_mb", 0) > 2048:
        try:
            import train_guard
            freed = train_guard.unload_idle()
            done.append("swap %.0fMB 偏高 → 卸闲置模型 %s" % (rep["swap_mb"], freed or "无"))
        except Exception as e:
            done.append("卸载模型失败：%s" % e)
    return done


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rep = check()
    if a.fix:
        rep["fixed"] = fix(rep)
        rep = check()
    try:
        os.makedirs(STATE, exist_ok=True)
        json.dump(rep, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print("[health] %s ｜ swap %.0fMB ｜ 训练 %s ｜ 产物 %d 轮/%.1fGB"
              % (rep["level"].upper(), rep["swap_mb"],
                 "运行中" if rep["train"]["running"] else "空闲",
                 rep["train"]["runs"], rep["train"]["runs_gb"]))
        for it in rep["accounts"]:
            t = it["today"]
            print("  %-8s pid=%-7s %s ｜ 场%d 看%d 赞%d 弹%d 评%d ｜ %s"
                  % (it["alias"], it["pid"], it["level"].upper(), t["session"], t["watch"],
                     t["like"], t["danmaku"], t["comment"], it["why"] or "正常"))
        if rep["stale"]:
            print("  僵尸：%s" % ", ".join(rep["stale"]))
        for line in rep.get("fixed") or []:
            print("  [fix] %s" % line)
    return 0 if rep["level"] != "red" else 1


if __name__ == "__main__":
    sys.exit(main())
