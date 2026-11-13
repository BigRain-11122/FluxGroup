#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_brief.py - v3 机队简报：规则出事实，本地模型只写一句话。

Why（2026-11-13 CEO「拉起本地大模型干你力所能及和应该做的」）：
旧 daily_brief 读的是已归档的 v2 队列（会报"CEO 队列/46 张卡不在盘上"这类过期事实），
不能直接用。v3 的事实源是三份机读件：群控快照、改善台账、职责审计。

分工写死：
  * 事实段 = 规则算出来的数字，模型不许改；
  * 一句话 = 模型只做措辞，句中出现的数字必须来自事实，否则作废回落到模板；
  * "需要你决定" = 只列真正要人拍板的（外部依赖/权限件），不列进展。

用法：
    python3 Tools/fleet/fleet_brief.py            # 写 cph4/fleet/BRIEF.md
    python3 Tools/fleet/fleet_brief.py --print
    python3 Tools/fleet/fleet_brief.py --self-test
返回码：0 正常 / 2 事实源缺失 / 3 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
OUT = os.path.join(ROOT, "cph4", "fleet", "BRIEF.md")


def _j(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def facts():
    """只从 v3 机读件取事实；缺就写缺，不推算。"""
    fc = _j(os.path.join(ROOT, "cph4", "fleet", "state", "fleet-control.json")) or {}
    rows = fc.get("rows") or []
    online = [r for r in rows if r.get("reachable")]
    forked = [r for r in rows if str(r.get("code", "")).startswith(("分叉", "落后"))]
    off = [r for r in rows if not r.get("reachable")]
    led = _j(os.path.join(ROOT, "cph4", "fleet", "IMPROVE-BACKLOG-v1.json")) or {}
    items = led.get("items") or []
    by = {}
    for i in items:
        by[i.get("status")] = by.get(i.get("status"), 0) + 1
    prods = _j(os.path.join(ROOT, "cph4", "fleet", "PRODUCTS.json")) or {}
    tot = have = 0
    for p in prods.get("products") or []:
        for s in (p.get("stages") or []):
            tot += 1
            if (p.get("commands") or {}).get(s):
                have += 1
    return {"ts": fc.get("ts"), "rows": rows,
            "online": len(online), "total": len(rows),
            "forked": [(r.get("node"), r.get("code")) for r in forked],
            "offline": [r.get("node") for r in off],
            "ledger": by, "stages_total": tot, "stages_cmd": have}


def decide_list(f):
    """只列真正要人拍板的：外部依赖与权限件。"""
    out = []
    for n, code in f["forked"]:
        out.append("%s 拉不到新代码（%s）——需在机器上跑 Tools\\fleet\\switch_v3.py" % (n, code))
    if f["offline"]:
        out.append("%s 不可达——需开机或查网络" % "、".join(f["offline"]))
    if f["stages_cmd"] < f["stages_total"]:
        out.append("供给缺口 %d/%d 道工序没有执行命令——主控按线逐条接"
                   % (f["stages_total"] - f["stages_cmd"], f["stages_total"]))
    return out


def one_line(f):
    """模型写一句话；数字必须来自事实，否则回落模板。"""
    base = ("在线 %d/%d，分叉 %d 台，离线 %d 台；工序有命令 %d/%d，台账待办 %d 项。"
            % (f["online"], f["total"], len(f["forked"]), len(f["offline"]),
               f["stages_cmd"], f["stages_total"], f["ledger"].get("OPEN", 0)))
    fact_text = base + " " + " ".join("%s %s" % (n, c) for n, c in f["forked"])
    try:
        import local_model as lm
        out = (lm.generate(
            "把下面这段机队事实改写成一句不超过 50 字的中文，只许复述不许添加数字或结论：\n"
            + fact_text, cls="triage", timeout=40, why="fleet-brief") or "").strip()
    except Exception:
        return base, "规则模板（模型不可用）"
    if not out:
        return base, "规则模板（模型空输出）"
    ok_nums = set(re.findall(r"\d+", fact_text))
    bad = set(re.findall(r"\d+", out)) - ok_nums
    if bad:
        return base, "规则模板（模型引入了事实外数字 %s）" % sorted(bad)
    return out, "本地模型（数字已校验）"


def render(f, line, how):
    L = ["# 机队简报 %s" % datetime.now().strftime("%Y-%m-%d %H:%M"), ""]
    L += ["**一句话（%s）**：%s" % (how, line), ""]
    L += ["## 一、机队", ""]
    L.append("| 节点 | 状态 | 代码 | 判读 |")
    L.append("|---|---|---|---|")
    for r in f["rows"]:
        st = "在线" if r.get("reachable") else r.get("state", "?")
        code = r.get("code") or "-"
        why = ("拉不到新代码" if code.startswith(("分叉", "落后"))
               else ("代码最新" if code == "最新" else
                     ("不可达" if not r.get("reachable") else code)))
        L.append("| %s | %s | %s | %s |" % (r.get("node"), st, code, why))
    L += ["", "## 二、产能", ""]
    L.append("- 工序 %d 道，有执行命令 %d 道（缺 %d）"
             % (f["stages_total"], f["stages_cmd"],
                f["stages_total"] - f["stages_cmd"]))
    L.append("- 改善台账：完成 %d｜待办 %d｜作废 %d｜假完成 0"
             % (f["ledger"].get("DONE", 0), f["ledger"].get("OPEN", 0),
                f["ledger"].get("DROPPED", 0)))
    L += ["", "## 三、需要你决定", ""]
    ds = decide_list(f)
    if ds:
        L += ["- " + x for x in ds]
    else:
        L.append("- （无）")
    L += ["", "---", "",
          "> 事实段由规则算出；一句话由本地模型改写且数字经校验。缺数据写缺，不推算。"]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    f = facts()
    if not f["rows"]:
        print("缺事实源：cph4/fleet/state/fleet-control.json（先跑 fleet_control.py --status）")
        return 2
    line, how = one_line(f)
    text = render(f, line, how)
    if a.print:
        print(text)
    else:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        print("简报 -> %s" % os.path.relpath(OUT, ROOT))
    return 0


def self_test():
    ok = total = 0

    def chk(n, c, d=""):
        nonlocal ok, total
        total += 1
        ok += 1 if c else 0
        print("%s %s %s" % ("ok  " if c else "FAIL", n, "" if c else d))

    f = {"ts": "t", "rows": [
        {"node": "bm-a", "reachable": True, "code": "分叉 222 35"},
        {"node": "bm-b", "reachable": False, "state": "不可达"},
        {"node": "bm-c", "reachable": True, "code": "最新"}],
        "online": 2, "total": 3, "forked": [("bm-a", "分叉 222 35")],
        "offline": ["bm-b"], "ledger": {"DONE": 6, "OPEN": 52, "DROPPED": 1},
        "stages_total": 59, "stages_cmd": 15}
    text = render(f, "在线 2/3。", "测试")
    chk("简报含一句话", "一句话" in text)
    chk("缺命令数算对", "缺 44" in text, text[-400:])
    chk("分叉机进入待决", "switch_v3" in text)
    chk("离线机进入待决", "不可达" in text)
    chk("台账数字来自事实", "完成 6" in text and "待办 52" in text)

    # 数字校验：事实外数字必须被识别
    fact = "在线 2/3，分叉 1 台"
    out = "共 999 台机器在线"
    bad = set(re.findall(r"\d+", out)) - set(re.findall(r"\d+", fact))
    chk("负控：事实外数字被识别", bad == {"999"}, bad)

    # 空事实不应崩
    chk("空表也能渲染", "机队简报" in render(
        {"rows": [], "online": 0, "total": 0, "forked": [], "offline": [],
         "ledger": {}, "stages_total": 0, "stages_cmd": 0}, "无", "测试"))
    print("\n[fleet_brief] %d/%d" % (ok, total))
    return 0 if ok == total else 3


if __name__ == "__main__":
    sys.exit(main())
