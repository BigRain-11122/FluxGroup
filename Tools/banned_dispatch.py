#!/usr/bin/env python3
# banned_dispatch.py -- turn gate hits into remediation work orders
# Authority: D-20260930-41 section 1.2 ; pairs with Tools/banned_direction_gate.py
#
# CEO (external auditor) ruling applied here: a hit is NOT a death sentence. Each hit gets a
# 7-day window to supply an exception statement (new_data or new_mechanism + citation of the
# BAN id). No statement by the deadline -> the batch is rejected and the cells already burned
# are booked as waste. Rationale: killing outright would also kill genuine novelty.
#
# Usage: python Tools/banned_dispatch.py [--days 30] [--out docs/audits]
import argparse, glob, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import banned_direction_gate as gate

ROOT = gate.ROOT
REG = gate.load_reg()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "audits"))
    a = ap.parse_args()

    cutoff = time.time() - a.days * 86400
    d = os.path.join(ROOT, "quant", "bigmoney", "research")
    files = [f for f in glob.glob(os.path.join(d, "**", "*.md"), recursive=True)
             if os.path.getmtime(f) > cutoff]

    rows = []
    for f in files:
        got, hits, err = gate.verdict_for(f, REG)
        if got != "REJECT":
            continue
        for h in hits:
            if h["exception_stated"]:
                continue
            rows.append({
                "file": os.path.relpath(f, ROOT).replace("\\", "/"),
                "ban_id": h["id"],
                "direction": h["name"],
                "deadline_days": 7,
                "action_required": "supply exception statement: new_data or new_mechanism + cite " + h["id"],
            })
    rows.sort(key=lambda r: (r["ban_id"], r["file"]))

    by_dir = {}
    for r in rows:
        by_dir.setdefault(r["ban_id"], []).append(r)

    os.makedirs(a.out, exist_ok=True)
    jpath = os.path.join(a.out, "banned-dispatch.json")
    with open(jpath, "w", encoding="utf-8") as f:
        json.dump({"generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "window_days": a.days,
                   "total_hits": len(rows), "by_direction": {k: len(v) for k, v in by_dir.items()},
                   "orders": rows}, f, ensure_ascii=False, indent=1)

    mpath = os.path.join(a.out, "banned-dispatch-20260930.md")
    with open(mpath, "w", encoding="utf-8") as f:
        f.write("# 禁开方向命中件派工单（D-20260930-41 §1.2）\n\n")
        f.write(f"> 生成 {time.strftime('%Y-%m-%d %H:%M')}｜窗口 {a.days} 天｜命中 {len(rows)} 件\n")
        f.write("> **裁定（外审拍板）**：命中不等于判死。每件有 **7 天**补例外论证"
                "（**新数据** 或 **新机制论证** ＋引用 BAN 编号）。到期未补 = 判不受理，"
                "已烧格数计入浪费。\n")
        f.write("> 理由：直接判死会把真创新一起误杀。\n\n")
        f.write("## 汇总\n\n| 方向 | 命中件数 |\n|---|---|\n")
        for k in sorted(by_dir, key=lambda x: -len(by_dir[x])):
            f.write(f"| {k} {by_dir[k][0]['direction']} | {len(by_dir[k])} |\n")
        f.write("\n## 派工明细\n\n| 件 | 命中 | 需补 | 时限 |\n|---|---|---|---|\n")
        for r in rows:
            f.write(f"| `{r['file']}` | {r['ban_id']} | {r['action_required']} | 7 天 |\n")
        f.write("\n## 复跑\n\n```\npython Tools/banned_dispatch.py --days 30\n```\n")

    print(f"hits={len(rows)} by_direction={ {k: len(v) for k, v in by_dir.items()} }")
    print(f"-> {os.path.relpath(jpath, ROOT)}")
    print(f"-> {os.path.relpath(mpath, ROOT)}")


if __name__ == "__main__":
    main()
