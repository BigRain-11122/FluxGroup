# -*- coding: utf-8 -*-
"""
status · 一页总览（自动生成，别手改）

python tools/status.py          生成 STATUS.md
python tools/status.py --check  检查 STATUS.md 是否过期（过期返回 1）

数据来源：modules/*/module.json、TASKS.json、BACKLOG.md、世界运行时数据。
"""
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "STATUS.md")
MOD = os.path.join(ROOT, "modules")


def say(m):
    print(m, flush=True)


def load(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def modules():
    out = []
    if not os.path.isdir(MOD):
        return out
    for mid in sorted(os.listdir(MOD)):
        mj = os.path.join(MOD, mid, "module.json")
        if os.path.exists(mj):
            out.append(load(mj))
    return out


def world_facts():
    regions = load(os.path.join(MOD, "m-w1-regions", "data", "regions.json"), {"regions": []})["regions"]
    people = load(os.path.join(MOD, "m-p1-census", "data", "people.json"), {"people": []})["people"]
    mem = load(os.path.join(MOD, "m-p2-memory", "data", "memory.json"), {"memories": []})["memories"]
    t = load(os.path.join(MOD, "m-w2-clock", "data", "time.json"), {"day": 0})
    ev = 0
    ep = os.path.join(MOD, "m-w2-clock", "data", "events.jsonl")
    if os.path.exists(ep):
        with open(ep, encoding="utf-8", errors="replace") as f:
            ev = sum(1 for line in f if line.strip())
    return {"day": t.get("day", 0), "regions": len(regions), "people": len(people),
            "memories": len(mem), "events": ev}


def backlog_items():
    p = os.path.join(ROOT, "BACKLOG.md")
    if not os.path.exists(p):
        return []
    items = []
    for line in open(p, encoding="utf-8"):
        m = re.match(r"\|\s*\**B(\d+)\**\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", line)
        if m:
            items.append({"id": "B" + m.group(1), "what": m.group(2), "module": m.group(3), "why": m.group(4)})
    return items


def build():
    mods = modules()
    tasks = load(os.environ.get("SILICON_BOARD") or os.path.join(ROOT, "TASKS.json"), {"tasks": []})["tasks"]
    facts = world_facts()
    bl = backlog_items()

    runnable = [m for m in mods if m.get("status") in ("usable", "stable")]
    empty = [m for m in mods if m.get("status") == "empty"]
    done_ids = {t["id"] for t in tasks if t.get("status") == "done"}
    doing = [t for t in tasks if t.get("status") == "doing"]
    todo = [t for t in tasks if t.get("status") == "todo"]

    ready, blocked = [], []
    for t in todo:
        miss = [d for d in (t.get("depends_on") or []) if d not in done_ids]
        (blocked if miss else ready).append((t, miss))

    L = []
    L.append("# 总览（自动生成，别手改）")
    L.append("")
    L.append(f"> 生成时间 {time.strftime('%Y-%m-%d %H:%M')} · 世界第 **{facts['day']}** 天 · "
             f"{facts['regions']} 区 · {facts['people']} 人 · {facts['events']} 条事件 · {facts['memories']} 条记忆")
    L.append(">")
    L.append("> 重新生成：`python tools/status.py`　查过期：`python tools/status.py --check`")
    L.append("")

    L.append("## 一 现在能不能干活")
    L.append("")
    L.append(f"- 可执行模块 **{len(runnable)}** / 登记 **{len(mods)}**（空位 {len(empty)} 个，是预告不是交付）")
    L.append(f"- 进行中任务 **{len(doing)}** · 可领 **{len(ready)}** · 被前置卡住 **{len(blocked)}** · 已完成 **{len(done_ids)}**")
    if doing:
        L.append("- 正在做：" + "、".join(f"{t['id']}（{t.get('claimed_by')}）" for t in doing))
    L.append("")

    L.append("## 二 现在就能领的活")
    L.append("")
    if ready:
        L.append("| 任务 | 模块 | 是什么 | 怎么验 |")
        L.append("|---|---|---|---|")
        for t, _ in ready:
            L.append(f"| {t['id']} | {t['module']} | {t['title']} | `{t.get('verify','')}` |")
    else:
        L.append("没有可领的活：要么全在别人手里，要么被前置卡住。")
    L.append("")

    if blocked:
        L.append("### 被卡住的")
        L.append("")
        for t, miss in blocked:
            L.append(f"- {t['id']} {t['title']} —— 等 {', '.join(miss)} 做完")
        L.append("")

    L.append("## 三 模块进度")
    L.append("")
    L.append("| 模块 | 名称 | 状态 | 下一步 |")
    L.append("|---|---|---|---|")
    mark = {"usable": "可用", "stable": "稳定", "building": "在写", "empty": "空位"}
    for m in mods:
        L.append(f"| `{m['id']}` | {m['name']} | {mark.get(m.get('status'), m.get('status'))} | {m.get('next','')} |")
    L.append("")

    L.append("## 四 已完成的任务")
    L.append("")
    if done_ids:
        for t in tasks:
            if t.get("status") == "done":
                dv = (t.get("deliveries") or [{}])[-1]
                L.append(f"- {t['id']} {t['title']} —— 交付于 {time.strftime('%m-%d %H:%M', time.localtime(dv.get('at', 0)))}")
    else:
        L.append("还没有已交付的任务。")
    L.append("")

    L.append("## 五 有问题的 / 还没做的")
    L.append("")
    if bl:
        L.append("| 编号 | 要做的事 | 模块 | 为什么卡着 |")
        L.append("|---|---|---|---|")
        for b in bl:
            L.append(f"| {b['id']} | {b['what']} | {b['module']} | {b['why']} |")
    else:
        L.append("待建清单为空。")
    L.append("")

    L.append("## 六 建议顺序")
    L.append("")
    n = 0
    for t, _ in ready[:3]:
        n += 1
        L.append(f"{n}. 领 {t['id']}（{t['title']}）")
    if blocked:
        n += 1
        L.append(f"{n}. 先解锁：{(blocked[0][0]['depends_on'] or ['?'])[0]}")
    n += 1
    L.append(f"{n}. 清待建里风险最高的那条（看第五节第一行）")
    L.append("")

    L.append("## 七 怎么维护")
    L.append("")
    L.append("- 任何任务状态变化后，重跑 `python tools/status.py`。")
    L.append("- `ready.py` 会检查本页是否过期，过期就不算就绪。")
    L.append("- 本页只汇总，不存事实；事实在 `TASKS.json`、`modules/*/module.json`、`BACKLOG.md`。")

    return "\n".join(L) + "\n"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    text = build()
    if len(sys.argv) >= 2 and sys.argv[1] == "--check":
        if not os.path.exists(OUT):
            say("✗ 没有 STATUS.md，先跑 python tools/status.py")
            return 1
        def _strip(s):
            return "\n".join(x for x in s.splitlines() if not x.startswith("> 生成时间"))
        cur = open(OUT, encoding="utf-8").read()
        if _strip(cur) != _strip(text):
            say("✗ STATUS.md 已过期，请重跑 python tools/status.py")
            return 1
        say("✓ STATUS.md 是最新的")
        return 0
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    say(f"✓ 已生成 {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
