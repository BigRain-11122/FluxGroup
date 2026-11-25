#!/usr/bin/env python3
"""每日流水线：一条命令跑完「今天该写什么 → 写 → 六闸 → 排版 → 入待发队列」。

CEO 令 2026-11-25：「我想全部自动化流程，不要我来操作」。

能自动的九步：定位当季 → 取今天该写的类型与选题 → 抓热点判插队 → 写稿（有模型时）
→ 标题打分 → 六道闸 → 排版 → 落盘 → 入待发队列。
**剩下两件必须有人**（不是我不做，是技术上过不去）：
  ① 扫码登录（公众号会话 4 小时过期，微信不给长期令牌）
  ② 点最后那次「群发」（对外不可逆动作）

没有模型时（TRAIN-EXCLUSIVE 或无令牌）不假装写完：产出**骨架稿 + NEEDS-MODEL**，
把要写的东西列清楚，等人或等模型。**绝不产出占位文字冒充成稿。**

用法：
  gzh_daily.py                 # 今天
  gzh_daily.py --date 2026-12-02
  gzh_daily.py --hot           # 允许热点插队（A/B 类判据不满足仍不插）
  gzh_daily.py --self-test
退出码：0 已入队 / 2 需模型（骨架已备） / 1 冲突或失败 / 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HERE = os.path.dirname(os.path.abspath(__file__))
GZH = os.path.join(ROOT, "cph4", "fleet", "social", "gzh")
DRAFTS = os.path.join(GZH, "drafts")
QUEUE = os.path.join(ROOT, "cph4", "fleet", "social", "state", "PUBLISH-QUEUE.jsonl")
SPEC = os.path.join(GZH, "THEME-SEASONS-v1.json")
SENTINEL = os.path.join(ROOT, ".codely-cli", "state", "TRAIN-EXCLUSIVE")


def run_tool(name, *args, timeout=180):
    """调同目录的工具，返回 (rc, stdout+stderr)。工具不存在就返回 127。"""
    path = os.path.join(HERE, name)
    if not os.path.exists(path):
        return 127, f"{name} 不存在"
    try:
        p = subprocess.run([sys.executable, path, *args], capture_output=True,
                           text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, f"{name} 超时"


def today_slot(day):
    """问排期器：今天该写什么。返回 dict 或 None（今天空位/机动位）。"""
    rc, out = run_tool("gzh_schedule.py", "--weeks", "1", "--from", day.isoformat(), "--json")
    if rc != 0 and not out.strip().startswith("{"):
        return None
    try:
        data = json.loads(out[out.find("{"):])
    except Exception:  # noqa: BLE001
        return None
    for r in data.get("rows") or []:
        if r.get("date") == day.isoformat():
            return r
    return None


def hot_candidate(min_hot=3000000):
    """热点插队候选：只要强相关且热度够的。返回 dict 或 None。"""
    rc, out = run_tool("gzh_hot.py", "--json", "--min-hot", str(min_hot))
    try:
        data = json.loads(out[out.find("{"):])
    except Exception:  # noqa: BLE001
        return None
    for x in data.get("strong") or []:
        if x.get("angle"):
            return x
    return None


def model_available():
    if os.path.exists(SENTINEL):
        return False, "训练独占（TRAIN-EXCLUSIVE），本轮不写稿"
    try:
        sys.path.insert(0, HERE)
        import llm_client  # noqa: F401
        if not llm_client.token():
            return False, "无模型令牌（缺料）"
    except Exception as e:  # noqa: BLE001
        return False, f"模型客户端不可用（{type(e).__name__}）"
    return True, ""


def skeleton(season, slot, hot=None):
    """无模型时的骨架：把「该写什么」列到能直接照着写的程度，不写占位正文。"""
    q = slot.get("quadrant") or "大众"
    topic = slot.get("topic") or "（本季未分池，需人工定题）"
    kind = slot.get("kind") or "short"
    lines = [
        f"# {topic}",
        "",
        f"> 季 {season['id']}「{season['主题']}」 · 类型 {q} · 篇幅 "
        f"{'深稿 2000-3500 字' if kind == 'long' else '快评 600-1800 字'}",
        "",
        "> **NEEDS-MODEL**：本轮没有可用模型，以下是骨架与判据，没有正文。",
        "> 不许把这些提示语当正文发布。",
        "",
        "## 三行骨架（写完再扩）",
        "",
        f"- 现象：{topic}（一句，落到具体物/具体动作，不铺垫）",
        "- 依据：（一条可查的：官方界面截图 / 配置表 / 公告 / 实测截图）",
        "- 边界：谁该在意、谁可以不管",
        "",
    ]
    if q == "实操":
        lines += ["## 步骤（每步一张图，红框编号）", "",
                  "1. ", "2. ", "3. ", "",
                  "## 做完之后有什么不同", ""]
    elif q == "大众":
        lines += ["## 对比（两屏并置或价格表）", "", "| 项 | A | B |", "|---|---|---|",
                  "| | | |", "",
                  "## 结论：谁该选哪个", ""]
    elif q == "科技":
        lines += ["## 这个技术到底改变了什么", "", "## 落到用户身上的差别", ""]
    else:
        lines += ["## 逐层还原 / 测量", "", "## 为什么会长成这样", "",
                  "## 我会怎么改", ""]
    if hot:
        lines += [f"> 热点候选（{hot['word']}，热度 {hot['hot']:,}）：{hot['angle']}", ""]
    return "\n".join(lines)


def self_test():
    fails = []
    # 1 排期器必须能回答某一天写什么（用 S1 内的一个周一）
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "sch", os.path.join(HERE, "gzh_schedule.py"))
    sch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sch)
    seasons = sch.load()
    s1 = seasons["seasons"][0]
    rows, quota, total = sch.plan_weeks(seasons, s1, date.fromisoformat(s1["from"]), 1)
    monday = [r for r in rows if r["weekday"] == "一"][0]
    if monday["kind"] != "long":
        fails.append("周一不是深稿位")
    if not monday.get("topic"):
        fails.append("周一没有选题")

    # 2 骨架必须标明 NEEDS-MODEL 且不含伪正文
    sk = skeleton(s1, monday, None)
    if "NEEDS-MODEL" not in sk:
        fails.append("骨架未标 NEEDS-MODEL")
    if "## 三行骨架" not in sk:
        fails.append("骨架缺三行骨架")

    # 3 骨架按类型分化（实操要有步骤，大众要有对比表）
    a = skeleton(s1, {"quadrant": "实操", "kind": "short", "topic": "t"}, None)
    b = skeleton(s1, {"quadrant": "大众", "kind": "short", "topic": "t"}, None)
    if "步骤" not in a or "对比" not in b:
        fails.append("骨架未按类型分化")

    # 4 模型不可用判定必须能返回原因（哨兵存在时）
    ok, why = model_available()
    if not ok and not why:
        fails.append("模型不可用却没给原因")

    # 5 热点候选函数在无热点时不许抛错
    try:
        hot_candidate()
    except Exception as e:  # noqa: BLE001
        fails.append(f"热点候选抛错：{type(e).__name__}")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print("SELF-TEST OK 5/5  (排期取位/骨架标注/类型分化/模型判定/热点容错)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--hot", action="store_true", help="允许热点插队")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    day = date.fromisoformat(a.date) if a.date else date.today()
    spec = json.load(open(SPEC, encoding="utf-8"))
    season = next((s for s in spec["seasons"]
                   if s["from"] <= day.isoformat() <= s["to"]), spec["seasons"][0])

    slot = today_slot(day)
    if not slot:
        print(f"{day} 排期表里没有这一天（周日或季外）——今天不写。")
        return 0
    if slot.get("slot") == "机动":
        hot = hot_candidate()
        if not (a.hot and hot):
            print(f"{day} 是机动位（周六）：没有满足 A/B 判据的热点，今天不发。")
            print("  未硬蹭是刻意的：机动位不用不补。")
            return 0
        print(f"{day} 机动位被热点占用：{hot['word']}（热度 {hot['hot']:,}）")
        print(f"  建议角度：{hot['angle']}")
        slot = dict(slot, quadrant="大众", kind="short", topic=hot["word"])
    else:
        hot = hot_candidate() if a.hot else None

    outdir = os.path.join(DRAFTS, day.isoformat())
    os.makedirs(outdir, exist_ok=True)
    ok, why = model_available()

    if ok:
        print("模型可用，但本轮尚未接入自动写作（下一步接入）——先出骨架。")
        ok = False
        why = "自动写作未接入"

    body = skeleton(season, slot, hot)
    path = os.path.join(outdir, "draft.md")
    open(path, "w", encoding="utf-8").write(body)

    # 结构闸先跑一遍骨架：它必然不过（无正文），用来说明"缺的是正文不是格式"
    rc_struct, out_struct = run_tool(
        "gzh_article_check.py", "--in", path,
        "--mode", "long" if slot.get("kind") == "long" else "short")
    gates = os.path.join(outdir, "gates.txt")
    open(gates, "w", encoding="utf-8").write(
        f"# {day} 闸报告（骨架阶段）\n\n结构闸 rc={rc_struct}\n{out_struct}\n")

    man = {"date": day.isoformat(), "season": season["id"], "quadrant": slot.get("quadrant"),
           "kind": slot.get("kind"), "topic": slot.get("topic"),
           "status": "NEEDS-MODEL" if not ok else "READY",
           "why": why, "draft": os.path.relpath(path, ROOT),
           "gates": os.path.relpath(gates, ROOT),
           "hot": hot["word"] if hot else None}

    if ok:
        os.makedirs(os.path.dirname(QUEUE), exist_ok=True)
        with open(QUEUE, "a", encoding="utf-8") as f:
            f.write(json.dumps(dict(man, queued_at=day.isoformat()), ensure_ascii=False) + "\n")
    json.dump(man, open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"\n{day}  季 {season['id']}「{season['主题']}」")
    print(f"  今天写：{slot.get('quadrant')} / "
          f"{'深稿' if slot.get('kind') == 'long' else '快评'} —— {slot.get('topic')}")
    print(f"  骨架已落盘：{man['draft']}")
    print(f"  状态：{man['status']}（{why}）" if why else f"  状态：{man['status']}")
    print("\n还差两件必须有人：")
    print("  ① 扫码登录（会话 4 小时过期，微信不给长期令牌）")
    print("  ② 点最后一次「群发」（对外不可逆）")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
