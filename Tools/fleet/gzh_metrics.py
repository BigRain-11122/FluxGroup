#!/usr/bin/env python3
"""数据回填与周复盘：把发布后的真实数据记下来，并回答「哪篇更值得写」。

为什么必须单独一个工具：所有闸都是「发布前」的判据，而真正该优化的是
**发布后**的三个数（2h 点击率 / 完读率 / 互动率）。没有回填，季末复盘只能凭印象，
等于前面建的闸全白建。

三个动作：
  --record   记一次数据（2h / 24h / 72h 三个检查点）
  --weekly   本周复盘：完读率排行、按四类分组对比、给你下周该调什么
  --fetch    从公众号后台抓（**需要登录态，未实测**，抓不到就如实报）

用法：
  gzh_metrics.py --record --date 2026-12-01 --at 2h --reads 320 --finish 58 --likes 6 --shares 3
  gzh_metrics.py --weekly
  gzh_metrics.py --self-test
退出码：0 正常 / 1 无数据 / 3 需登录态 / 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GZH = os.path.join(ROOT, "cph4", "fleet", "social", "gzh")
OWN = os.path.join(GZH, "METRICS-OWN.jsonl")
DRAFTS = os.path.join(GZH, "drafts")

POINTS = ("2h", "24h", "72h")
FIELDS = ("reads", "finish", "likes", "shares", "comments", "fans")


def load(path=None):
    path = path or OWN
    rows = []
    if not os.path.exists(path):
        return rows
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except Exception:  # noqa: BLE001
                continue
    return rows


def manifest_of(day):
    p = os.path.join(DRAFTS, day, "manifest.json")
    if not os.path.exists(p):
        return {}
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def record(day, at, **kw):
    """追加一条数据点。同一 (date, at) 重复记就覆盖（后写的胜）。"""
    if at not in POINTS:
        raise ValueError(f"检查点只能是 {POINTS}")
    row = {"ts": datetime.now().isoformat(timespec="seconds"), "date": day, "at": at}
    for k in FIELDS:
        if k in kw and kw[k] is not None:
            row[k] = kw[k]
    rows = [r for r in load() if not (r.get("date") == day and r.get("at") == at)]
    rows.append(row)
    rows.sort(key=lambda r: (r.get("date", ""), POINTS.index(r.get("at", "2h"))
                             if r.get("at") in POINTS else 9))
    with open(OWN, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return row, len(rows)


def weekly(rows, end=None, days=7):
    """本周复盘。返回 (report_lines, stats)。"""
    end = end or date.today()
    start = end - timedelta(days=days - 1)
    win = [r for r in rows
           if r.get("date") and start.isoformat() <= r["date"] <= end.isoformat()]
    if not win:
        return ["本周没有数据（先 --record）"], {}

    # 每篇取最终检查点（72h 优先）算完读率
    by_date = {}
    for r in win:
        d = r["date"]
        cur = by_date.get(d)
        rank = POINTS.index(r.get("at", "2h")) if r.get("at") in POINTS else -1
        if cur is None or rank > POINTS.index(cur.get("at", "2h")):
            by_date[d] = r

    lines = [f"周复盘 {start} → {end}（{len(by_date)} 篇有数据）", ""]
    lines.append(f"{'日期':11}{'类型':6}{'阅读':>7}{'完读':>6}{'互动率':>7}  题目")
    stats = {"n": len(by_date), "by_quadrant": {}}
    for d in sorted(by_date):
        r = by_date[d]
        m = manifest_of(d)
        q = m.get("quadrant") or "?"
        reads = r.get("reads") or 0
        finish = r.get("finish")
        inter = (r.get("likes") or 0) + (r.get("shares") or 0) + (r.get("comments") or 0)
        rate = (inter / reads * 100) if reads else 0
        lines.append(f"{d:11}{q:6}{reads:>7}{('%.0f%%' % finish) if finish is not None else '-':>6}"
                     f"{rate:>6.1f}%  {(m.get('topic') or '')[:22]}")
        stats["by_quadrant"].setdefault(q, []).append(
            {"finish": finish, "rate": rate, "reads": reads})

    lines.append("")
    # 按类型汇总：哪类完读最好
    agg = {}
    for q, items in stats["by_quadrant"].items():
        fin = [x["finish"] for x in items if x["finish"] is not None]
        agg[q] = {"n": len(items),
                  "finish_med": round(sorted(fin)[len(fin) // 2], 1) if fin else None,
                  "rate_avg": round(sum(x["rate"] for x in items) / len(items), 1)}
    stats["agg"] = agg
    lines.append("按类型：")
    for q, v in sorted(agg.items(), key=lambda kv: -(kv[1]["finish_med"] or 0)):
        lines.append(f"  {q:5} n={v['n']}  完读中位 {v['finish_med']}%  互动率 {v['rate_avg']}%")

    # 给建议：只给能落地的
    lines.append("")
    best = max(agg.items(), key=lambda kv: kv[1]["finish_med"] or -1)[0] if agg else None
    worst = min(agg.items(), key=lambda kv: kv[1]["finish_med"] or 999)[0] if agg else None
    if best:
        lines.append(f"下周要做的两件事：")
        lines.append(f"  1. {best} 类完读最高 → 下周至少加 1 篇同类（配比从别的类挪）")
        if worst and worst != best:
            lines.append(f"  2. {worst} 类完读最低 → 先别加量，把篇幅压到该类型区间下限再试")
    if len(by_date) < 3:
        lines.append("  注：本周少于 3 篇，上面两条只是方向，不足以据此调配比。")
    return lines, stats


def self_test():
    fails = []
    import tempfile
    global OWN
    keep = OWN

    # 1 记录与覆盖
    with tempfile.TemporaryDirectory() as td:
        OWN = os.path.join(td, "m.jsonl")
        record("2026-12-01", "2h", reads=100, finish=50, likes=2, shares=1)
        row, n = record("2026-12-01", "2h", reads=320, finish=58, likes=6, shares=3)
        if n != 1:
            fails.append(f"同一检查点覆盖失败，条数 {n}")
        if load()[0]["reads"] != 320:
            fails.append("覆盖后取值不是最后一次")

        # 2 检查点排序
        record("2026-12-01", "72h", reads=900, finish=52, likes=12, shares=8)
        rows = load()
        if [r["at"] for r in rows] != ["2h", "72h"]:
            fails.append(f"检查点排序错：{[r['at'] for r in rows]}")

        # 3 周复盘取最终检查点（不是 2h）
        lines, st = weekly(rows, end=date(2026, 12, 3), days=7)
        if st.get("n") != 1:
            fails.append(f"周复盘篇数错：{st.get('n')}")
        txt = "\n".join(lines)
        if "900" not in txt:
            fails.append("周复盘未取 72h 数据（取了 2h）")

        # 4 空周不崩
        lines2, st2 = weekly([], end=date(2026, 12, 3))
        if st2 != {} or "没有数据" not in "\n".join(lines2):
            fails.append("空周未正确提示")

        # 5 非法检查点必须拒
        try:
            record("2026-12-01", "5h", reads=1)
            fails.append("非法检查点未拒")
        except ValueError:
            pass

    OWN = keep
    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print("SELF-TEST OK 5/5  (记录覆盖/检查点排序/取最终点/空周/非法点)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--date", default=None)
    ap.add_argument("--at", default="2h", choices=POINTS)
    ap.add_argument("--reads", type=int, default=None)
    ap.add_argument("--finish", type=float, default=None, help="完读率，单位百分数")
    ap.add_argument("--likes", type=int, default=None)
    ap.add_argument("--shares", type=int, default=None)
    ap.add_argument("--comments", type=int, default=None)
    ap.add_argument("--fans", type=int, default=None)
    ap.add_argument("--weekly", action="store_true")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    if a.fetch:
        print("后台数据抓取需要登录态（公众号会话 4 小时过期）。")
        print("当前未实测这条路，不假装成功——请先用 --record 手工记，")
        print("等登录态自动化打通后再改为自动抓。")
        return 3

    if a.record:
        if not a.date:
            print("--record 需要 --date YYYY-MM-DD", file=sys.stderr)
            return 1
        row, total = record(a.date, a.at, reads=a.reads, finish=a.finish, likes=a.likes,
                            shares=a.shares, comments=a.comments, fans=a.fans)
        print(f"已记 {a.date} @{a.at}：{ {k: v for k, v in row.items() if k in FIELDS} }")
        print(f"台账共 {total} 条 → {OWN}")
        return 0

    if a.weekly:
        lines, st = weekly(load(), days=a.days)
        print("\n".join(lines))
        return 0 if st.get("n") else 1

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
