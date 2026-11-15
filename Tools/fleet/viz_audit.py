#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""viz_audit.py - 可视化体检与自愈（主控台 http://127.0.0.1:8787 的持续优化面）

为什么要有它（2026-11-15 CEO「你本地建好持续优化可视化方方面面的自动化任务」）：
  看板本身会静默腐坏——数据源停了页面还是绿的、判定是 46 小时前的快照、
  队列里混进行解析的坏行、服务挂了浏览器只显示"无法连接"。这些都靠人发现，
  就等于没有持续优化。本工具把「可视化是否诚实、是否新鲜、是否可用」变成
  一组可复跑的断言，能自动修的当场修掉，修不了的写成待办。

检查面（8 项，逐项有判据与动作）：
  1. serve      8787 是否 200           → 自动 kickstart 一次
  2. bind       只听 127.0.0.1          → 只报告（改配置属人工）
  3. l0         PULSE.json 节拍龄 <150s → 只报告（L0 停了是大事）
  4. exec       各机判定龄期 <1h        → 陈旧计为 warn
  5. queue      队列每行 JSON 可解析    → 只报告（坏行会静默丢卡）
  6. mojibake   页面无 U+FFFD 替换符    → 只报告（编码坏了人眼先崩）
  7. panels     5 个面板 section 都在   → 只报告
  8. silent     FLEET-PAUSED 与 plist 数一致 → 只报告

用法：
  python3 Tools/fleet/viz_audit.py            # 一轮，修可修的
  python3 Tools/fleet/viz_audit.py --check    # 只看，不动
退出码：0 全绿 / 1 本轮做了修复 / 2 有需人工项
"""
import argparse
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, "cph4", "fleet", "state")
OUT_JSON = os.path.join(STATE, "viz-audit.json")
OUT_MD = os.path.join(STATE, "VIZ-AUDIT.md")
URL = "http://127.0.0.1:8787/"
FIX_TS = [0.0]   # 本轮做过修复的时间（写回 json，供下一轮冷却判断）
LABEL = "com.fluxgroup.console"
PANELS = ("⓪ 今日实况", "① 需要你决定", "② 四线", "③ 机队", "④ 推进")
EXEC_STALE_S = 3600     # 「声称 healthy 却超过 1 小时没更新」= 假绿（今天 bm-c 是 46.8h）
# 主控脉单轮含慢阶段（fork_repair/blocker_loop 各 200s+），节拍间隔是 45s 但一轮可能
# 200-400s，用 150s 判停摆会把正常的一轮判成死——实测 421s 就是这种情况。
L0_STALE_S = 900


def sh(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        return 1, str(e)


def fetch(url, timeout=8):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read()
    except Exception as e:
        return 0, str(e).encode()


def age(path):
    try:
        return time.time() - os.path.getmtime(path)
    except Exception:
        return None


def audit():
    R = []

    def add(name, ok, detail, fixed=False, need_human=False):
        R.append({"name": name, "ok": bool(ok), "detail": detail,
                  "fixed": bool(fixed), "need_human": bool(need_human)})

    # 1. serve
    code, body = fetch(URL)
    if code != 200:
        # 改成每轮跑之后必须带冷却，否则服务持续挂时会每 45 秒重启一次（抖动）。
        last_fix = 0.0
        try:
            last_fix = float(json.load(open(OUT_JSON, encoding="utf-8")).get("fix_ts") or 0)
        except Exception:
            pass
        cooled = (time.time() - last_fix) < 300
        if not ARGS.check and not cooled:
            sh(["launchctl", "kickstart", "-k", "gui/%d/%s" % (os.getuid(), LABEL)])
            FIX_TS[0] = time.time()
            time.sleep(4)
            code2, body = fetch(URL)
            add("serve", code2 == 200,
                "8787 无响应 → 已 kickstart，现 %s" % ("200" if code2 == 200 else "仍不通"),
                fixed=(code2 == 200), need_human=(code2 != 200))
        else:
            add("serve", False,
                "8787 无响应（%s）" % ("--check 未修" if ARGS.check else "冷却中，5 分钟内已修过"),
                need_human=True)
    else:
        add("serve", True, "200 · %d KB" % (len(body) // 1024))

    html = body.decode("utf-8", "replace") if isinstance(body, bytes) else ""

    # 2. bind
    rc, out = sh(["lsof", "-nP", "-iTCP:8787", "-sTCP:LISTEN"])
    bind = "-"
    m = re.search(r"TCP\s+(\S+):8787", out)
    if m:
        bind = m.group(1)
    add("bind", bind in ("127.0.0.1", "localhost", "-"),
        "监听 %s（应只绑本机）" % bind, need_human=(bind not in ("127.0.0.1", "localhost", "-")))

    # 3. l0
    l0 = age(os.path.join(ROOT, "cph4", "fleet", "dispatcher", "PULSE.json"))
    add("l0", l0 is not None and l0 < L0_STALE_S,
        "主控脉节拍 %s" % ("%ds 前" % int(l0) if l0 is not None else "缺文件"),
        need_human=(l0 is None or l0 >= L0_STALE_S))

    # 4. exec 判定龄期：只抓「声称 healthy 却陈旧」的假绿。
    # 离线的机器不会再更新判定时间，那是状态不是故障（记忆：状态判决≠故障），
    # 把它算红就等于每天给自己造一条修不掉的告警。
    stale = []
    try:
        rv = json.load(open(os.path.join(STATE, "executor-revive.json"), encoding="utf-8"))
        for node, d in rv.items():
            d = d or {}
            v = str(d.get("verdict") or d.get("action") or "")
            try:
                a = time.time() - float(d.get("ts"))
            except Exception:
                stale.append("%s(无时间)" % node)
                continue
            if v == "healthy" and a > EXEC_STALE_S:
                stale.append("%s(healthy 但 %dh 前)" % (node, a // 3600))
    except Exception:
        stale.append("无判定文件")
    add("exec", not stale, "假绿 %d 项%s" % (len(stale), ("：" + "、".join(stale)) if stale else ""),
        need_human=bool(stale))

    # 5. queue 可解析性
    bad = 0
    qp = os.path.join(ROOT, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
    try:
        for ln in open(qp, encoding="utf-8"):
            ln = ln.strip()
            if not ln:
                continue
            try:
                json.loads(ln)
            except Exception:
                bad += 1
    except Exception:
        bad = -1
    add("queue", bad == 0, "坏行 %s" % ("读不到" if bad < 0 else bad), need_human=(bad != 0))

    # 6. 乱码
    moji = html.count("\ufffd")
    add("mojibake", moji == 0, "替换符 %d 个" % moji, need_human=(moji > 0))

    # 7. 面板完整性
    missing = [p for p in PANELS if p not in html]
    add("panels", not missing, "缺 %s" % ("、".join(missing) if missing else "无"), need_human=bool(missing))

    # 8. 静默边界一致性（用 glob 数，别 shell 出去——bash -lc 在 launchd 环境里取不到数字）
    paused = os.path.exists(os.path.join(ROOT, ".codely-cli", "state", "FLEET-PAUSED"))
    import glob
    nplist = len(glob.glob(os.path.expanduser("~/Library/LaunchAgents/com.fluxgroup.*.plist")))
    consistent = (paused and nplist <= 3) or (not paused)
    add("silent", consistent,
        "哨兵=%s · 自启 %d 项（白名单 3：pulse/console/ollamamodel）" % (paused, nplist),
        need_human=not consistent)

    return R


def render(rows, sec):
    bad = [r for r in rows if not r["ok"]]
    need = [r for r in rows if r["need_human"]]
    fixed = [r for r in rows if r["fixed"]]
    verdict = "GREEN" if not bad else ("FIXED" if fixed and len(fixed) >= len(bad) else "RED")
    lines = ["# 可视化体检（%s）" % time.strftime("%Y-%m-%d %H:%M:%S"),
             "",
             "**%s** · 8 面 · %d 过 / %d 需人工 · %d 本轮已修 · 用时 %.1fs" % (
                 verdict, len(rows) - len(bad), len(need), len(fixed), sec),
             "",
             "| 面 | 结果 | 说明 |", "|---|---|---|"]
    for r in rows:
        mark = "OK" if r["ok"] else ("已修" if r["fixed"] else "需人工")
        lines.append("| %s | %s | %s |" % (r["name"], mark, r["detail"]))
    return verdict, "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只看不动")
    global ARGS
    ARGS = ap.parse_args()
    t0 = time.time()
    rows = audit()
    verdict, md = render(rows, time.time() - t0)
    os.makedirs(STATE, exist_ok=True)
    try:
        json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "verdict": verdict,
                   "fix_ts": FIX_TS[0], "rows": rows}, open(OUT_JSON, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        open(OUT_MD, "w", encoding="utf-8").write(md)
    except Exception:
        pass
    print(md)
    if any(r["need_human"] for r in rows):
        return 2
    if any(r["fixed"] for r in rows):
        return 1
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
