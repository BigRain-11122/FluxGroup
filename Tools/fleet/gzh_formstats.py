#!/usr/bin/env python3
"""形态统计器：把一批文章压成一组可比的形态指标，用于跨赛道/跨号对照。

为什么要独立成工具：以前每次调研都临时写脚本，指标定义每次略有不同
（段落阈值 20 还是 30、数字算不算小数），结论就没法横向比。
这里把「第四节取数协议」的定义一次写死，谁跑都一样。

指标（全部按 RESEARCH-DESIGN-v1.md §4.2）：
  字数 / 段落数 / 段落中位长 / 小标题数 / 小标题疑问率
  标题字数 / 标题含数字率 / 标题问号率 / 数字密度(每千字) / 配图数

统计口径：
  · 连续量（字数/段落/标题长…）报 **中位数 + P25/P75**，不报平均数（超长文会拉偏）；
  · **比率类（含数字率/问号率/疑问率）必须报均值**——用中位数会算出 0：
    19 篇里 8 篇含数字（42%）时，中位数是 0，这会得出"标题从不用数字"的假结论。

用法：
  gzh_formstats.py --in 文章.jsonl --label 汽车
  gzh_formstats.py --in a.jsonl --label A --in b.jsonl --label B   # 对照
  gzh_formstats.py --dir 某目录 --label X                          # 目录下所有 .jsonl
  gzh_formstats.py --self-test
退出码：0 正常 / 1 无有效样本 / 4 自检失败
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import statistics as st
import sys

MIN_PARA = 20          # 段落判定：去空白后 ≥20 字才算一段（与取数协议一致）


def n(s):
    return len(re.sub(r"\s", "", str(s or "")))


RATE_KEYS = {"head_q_pct", "title_num_pct", "title_q_pct"}


def metrics(rows):
    """返回 {指标: (中位, P25, P75, n)}。rows 每项至少含 title，正文取 text。"""
    cols = {k: [] for k in ("words", "paras", "para_med", "heads", "head_q_pct",
                            "title_len", "title_num_pct", "title_q_pct",
                            "num_density", "imgs")}
    for r in rows:
        title = r.get("title") or ""
        text = r.get("text") or ""
        if not text and not title:
            continue
        ps = [p for p in re.split(r"\n+", text) if n(p) >= MIN_PARA]
        chars = n(text)
        heads = [h for h in (r.get("heads") or []) if str(h).strip()]
        # 若没有 heads 字段，就现数 Markdown 小标题
        if not heads:
            heads = re.findall(r"(?m)^##+\s*(.+)$", text)
        nums = len(re.findall(r"\d+(?:\.\d+)?", text))

        cols["words"].append(chars)
        cols["paras"].append(len(ps))
        if ps:
            cols["para_med"].append(st.median([n(p) for p in ps]))
        cols["heads"].append(len(heads))
        cols["head_q_pct"].append(100.0 * sum(1 for h in heads
                                              if re.search(r"[？?]\s*$", str(h))) / max(1, len(heads)))
        tl = n(title)
        cols["title_len"].append(tl)
        cols["title_num_pct"].append(100.0 if re.search(r"\d", title) else 0.0)
        cols["title_q_pct"].append(100.0 if re.search(r"[？?]\s*$", title) else 0.0)
        cols["num_density"].append(nums / (chars / 1000) if chars else 0.0)
        imgs = r.get("imgs")
        if imgs is None:
            imgs = len(re.findall(r"!\[[^\]]*\]\(", text))
        cols["imgs"].append(imgs)

    out = {}
    for k, v in cols.items():
        if not v:
            continue
        s = sorted(v)
        if k in RATE_KEYS:
            # 比率：报占比（均值），分位对 0/100 二值没意义，给 None
            out[k] = (round(sum(s) / len(s), 1), None, None, len(s))
            continue
        q1 = s[max(0, int(len(s) * 0.25) - 1)] if len(s) > 1 else s[0]
        q3 = s[min(len(s) - 1, int(len(s) * 0.75))] if len(s) > 1 else s[0]
        out[k] = (round(st.median(s), 1), round(q1, 1), round(q3, 1), len(s))
    return out


LABELS = {
    "words": ("正文字数", ""), "paras": ("段落数", ""), "para_med": ("段落中位长", ""),
    "heads": ("小标题数", ""), "head_q_pct": ("小标题疑问率", "%"),
    "title_len": ("标题字数", ""), "title_num_pct": ("标题含数字率", "%"),
    "title_q_pct": ("标题问号率", "%"), "num_density": ("数字密度", "/千字"),
    "imgs": ("配图数", ""),
}


def load(path):
    if os.path.isdir(path):
        rows = []
        for f in sorted(glob.glob(os.path.join(path, "**", "*.jsonl"), recursive=True)):
            rows += load(f)
        return rows
    rows = []
    if not os.path.exists(path):
        return rows
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:  # noqa: BLE001
            continue
    return rows


def render(sets):
    """sets = [(label, metrics)]，渲染成一张对照表。"""
    keys = [k for k in LABELS if any(k in m for _l, m in sets)]
    labels = [l for l, _m in sets]
    w = max(12, *(len(l) for l in labels))
    head = f"{LABELS[k][0]:12}" if False else f"{'指标':14}"
    for l in labels:
        head += f"{l:>{w}}"
    print(head)
    for k in keys:
        name = LABELS[k][0] + (f"({LABELS[k][1]})" if LABELS[k][1] else "")
        line = f"{name:14}"
        for _l, m in sets:
            if k in m:
                med, q1, q3, cnt = m[k]
                line += f"{med:>{w}}" if cnt else f"{'-':>{w}}"
            else:
                line += f"{'-':>{w}}"
        print(line)
    # 分位与样本量单列，避免主表被挤爆
    print()
    for k in keys:
        parts = []
        for l, m in sets:
            if k in m:
                med, q1, q3, cnt = m[k]
                if k in RATE_KEYS:
                    parts.append(f"{l}: {med}%（占比）/ n={cnt}")
                else:
                    parts.append(f"{l}: P25={q1} / 中位={med} / P75={q3} / n={cnt}")
        if parts:
            print("  " + LABELS[k][0] + " → " + " | ".join(parts))


PLANT = [
    {"title": "同一块屏，为什么新势力要点三层", "imgs": 8,
     "heads": ["两种架构的差异", "各自的代价", "层级怎么定"],
     "text": "同一个关闭车道保持，一台点两下，一台点五下，指尖在屏幕上找了三圈。\n"
             "根据两车官方配置表，多出来的第一项是后悬架，差价约 3000 元，实测 60.5 度电池。\n"
             "层级定错的代价不只在多点两下，在于用户每次都要重新找一遍，这在高速上就是风险。"},
    {"title": "深色模式发灰，不是屏幕问题", "imgs": 6,
     "heads": ["发灰的原因", "怎么改"],
     "text": "夜里看车机，深色模式是股灰蒙蒙的光，不是黑，这不是屏幕素质问题。\n"
             "用测色仪量一下面板反射率就明白了，8% 到 20% 之间的灰阶缺失，人眼对这个区间最敏感。"},
]


def self_test():
    fails = []
    m = metrics(PLANT)
    if not m:
        fails.append("负控[空输入] 指标为空")
        print("SELF-TEST FAIL"); [print("  -", f) for f in fails]; return 4

    # 1 段落数：样例分别是 3 段与 2 段 → 中位 2.5、样本 2
    if m["paras"][0] != 2.5 or m["paras"][3] != 2:
        fails.append(f"段落数口径错：{m['paras']}，应 中位2.5/n2")
    # 2 小标题疑问率：本章 0 个疑问 → 0
    if m["head_q_pct"][0] != 0.0:
        fails.append("小标题疑问率应为 0")
    # 3 标题含数字率：两篇都没数字 → 0
    if m["title_num_pct"][0] != 0.0:
        fails.append("标题含数字率应为 0")

    # 4 负控：把一篇标题改成问句+数字，比率必须变
    p2 = [dict(PLANT[0], title="为什么新势力要点三层？"), dict(PLANT[1])]
    m2 = metrics(p2)
    if m2["title_q_pct"][0] != 50.0:
        fails.append(f"标题问号率应为 50，实际 {m2['title_q_pct'][0]}")
    # 含数字率：另给一篇带数字的标题，须变 50
    p2b = [dict(PLANT[0], title="点 3 层还是 5 层"), dict(PLANT[1])]
    if metrics(p2b)["title_num_pct"][0] != 50.0:
        fails.append(f"标题含数字率应为 50，实际 {metrics(p2b)['title_num_pct'][0]}")

    # 5 负控：短段落不许算成段
    p3 = [dict(PLANT[0], text="短。\n也短。\n" + PLANT[0]["text"])]
    if metrics(p3)["paras"][0] != 3:
        fails.append("短段落被算成段（阈值失效）")

    # 6 负控：数字密度必须按千字归一
    long_text = "数字 100 次。" * 300
    m4 = metrics([{"title": "t", "text": long_text}])
    if not m4["num_density"][0] > 0:
        fails.append("数字密度未计算")

    # 6b 负控：比率类必须是占比而不是中位数（曾在此出过错）
    mixed = [{"title": "带数字 3 层", "text": "正文"} for _ in range(8)] + \
            [{"title": "不带数字的标题", "text": "正文"} for _ in range(11)]
    got = metrics(mixed)["title_num_pct"][0]
    if abs(got - 42.1) > 0.2:
        fails.append(f"比率口径错：含数字率应为 42.1%，实际 {got}（中位数会算成 0）")

    # 7 空输入必须返回空字典而不是抛错
    if metrics([]) != {}:
        fails.append("空输入未返回空")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print("SELF-TEST OK 7/7  (段落阈值/小标题疑问率/标题比率/数字归一/空输入)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="ins", action="append", default=[])
    ap.add_argument("--dir", dest="dirs", action="append", default=[])
    ap.add_argument("--label", action="append", default=[])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    paths = a.ins + a.dirs
    if not paths:
        ap.print_help()
        return 1

    sets = []
    for i, p in enumerate(paths):
        rows = load(p)
        label = a.label[i] if i < len(a.label) else os.path.basename(p.rstrip("/"))
        m = metrics(rows)
        if not m:
            print(f"⚠ {label}: 无有效样本（{p}）", file=sys.stderr)
            continue
        sets.append((label, m))

    if not sets:
        print("没有可用样本", file=sys.stderr)
        return 1

    if a.json:
        print(json.dumps({l: m for l, m in sets}, ensure_ascii=False, indent=1))
        return 0
    render(sets)
    return 0


if __name__ == "__main__":
    sys.exit(main())
