#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""practice_experience.py - 养号实战经验台账：把"发过什么、谁说的、可不可见"变成参数。

CEO 2026-11-19「实战经验积累…快点」。经验不能只躺在日志里，要能被生成侧消费：
  · 哪个人群、多长、什么车道发出去的，最后**公开可见**了？
  · 被拦的原因分布是什么（编造/品味/红线/重复）？
  · 结论直接给出"下一批优先用哪个人群 × 哪个长度带"，而不是形容词。

数据源（只读）：cph4/fleet/social/practice-log.jsonl
输出：
  cph4/fleet/social/PRACTICE-EXPERIENCE.md   人读一屏（含样本量与置信提示）
  cph4/fleet/social/PRACTICE-PARAMS.json     机读（供 practice_tick 取用）

自检（负控）：样本不足时必须说"样本不足"而不是给结论；visible=None 不得计入分母。
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
LEDGER = os.path.join(SOCIAL, "practice-log.jsonl")
OUT_MD = os.path.join(SOCIAL, "PRACTICE-EXPERIENCE.md")
OUT_JSON = os.path.join(SOCIAL, "PRACTICE-PARAMS.json")

MIN_N = 8          # 少于这么多条有结论的样本，一律不给"最佳区间"


def rows():
    out = []
    try:
        for line in open(LEDGER, encoding="utf-8"):
            if line.strip():
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


def band(n):
    if n <= 15:
        return "≤15"
    if n <= 20:
        return "16-20"
    if n <= 30:
        return "21-30"
    if n <= 50:
        return "31-50"
    return ">50"


def build(rs=None):
    rs = rows() if rs is None else rs
    posts, vis, lanes, reasons = {}, {}, {}, Counter()
    for r in rs:
        a = r.get("action")
        if a == "post" and r.get("rpid"):
            posts[str(r["rpid"])] = r
        elif a == "verify" and r.get("rpid") is not None and r.get("visible") is not None:
            vis[str(r["rpid"])] = bool(r["visible"])
        elif a == "lane" and r.get("rpid"):
            lanes[str(r["rpid"])] = r
        elif a in ("skip", "fail"):
            reasons[str(r.get("why") or "")[:28]] += 1

    judged = [(p, vis[k]) for k, p in posts.items() if k in vis]
    by_persona = defaultdict(lambda: [0, 0])     # persona -> [可见, 总数]
    by_band = defaultdict(lambda: [0, 0])
    by_lane = defaultdict(lambda: [0, 0])
    for p, ok in judged:
        per = (lanes.get(str(p.get("rpid"))) or {}).get("persona") or p.get("persona") or "-"
        ln = (lanes.get(str(p.get("rpid"))) or {}).get("lane") or p.get("lane") or "-"
        t = p.get("text") or ""
        for bucket, key in ((by_persona, per), (by_band, band(len(t))), (by_lane, ln)):
            bucket[key][1] += 1
            bucket[key][0] += 1 if ok else 0

    def rate(d):
        return {k: {"visible": v, "n": n, "rate": round(v / n, 2)} for k, (v, n) in d.items()}

    params = {
        "ts": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
        "judged_n": len(judged),
        "overall_rate": round(sum(1 for _, ok in judged if ok) / len(judged), 2) if judged else None,
        "by_persona": rate(by_persona), "by_band": rate(by_band), "by_lane": rate(by_lane),
        "reject_reasons": dict(reasons.most_common(8)),
        "enough": len(judged) >= MIN_N,
    }
    # 只在样本够时给"优先用谁"；否则明确留空，别让下游拿噪声当参数
    if params["enough"]:
        cand = [(v["rate"], k) for k, v in params["by_persona"].items() if v["n"] >= 3]
        params["prefer_persona"] = max(cand)[1] if cand else None
        candb = [(v["rate"], k) for k, v in params["by_band"].items() if v["n"] >= 3]
        params["prefer_band"] = max(candb)[1] if candb else None
    else:
        params["prefer_persona"] = None
        params["prefer_band"] = None
    return params


def render(p):
    L = ["# 养号实战经验台账 %s" % p["ts"][:16], "",
         "- 有明确结论的样本：**%d 条**（visible=None 的取数失败不计）｜整体可见率 %s"
         % (p["judged_n"], ("%.0f%%" % (100 * p["overall_rate"])) if p["overall_rate"] is not None else "-"), ""]
    if not p["enough"]:
        L += ["> ⚠ 样本不足（<%d 条），下面只是分布记录，**不作为参数依据**。" % MIN_N, ""]

    def table(name, d):
        if not d:
            return ["## %s" % name, "", "- 暂无数据", ""]
        out = ["## %s" % name, "", "| 键 | 可见 | 总数 | 可见率 |", "|---|---|---|---|"]
        for k, v in sorted(d.items(), key=lambda kv: -kv[1]["n"]):
            out.append("| %s | %d | %d | %.0f%% |" % (k, v["visible"], v["n"], 100 * v["rate"]))
        return out + [""]

    L += table("按人群（谁说的）", p["by_persona"])
    L += table("按长度带", p["by_band"])
    L += table("按车道", p["by_lane"])
    L += ["## 被拦原因 Top", ""]
    if p["reject_reasons"]:
        for k, v in p["reject_reasons"].items():
            L.append("- %d × %s" % (v, k))
    else:
        L.append("- 暂无")
    L += ["", "## 结论", ""]
    if p["prefer_persona"] or p["prefer_band"]:
        L.append("- 下一批优先：人群 `%s`、长度带 `%s`（依据上表可见率，样本已过 %d 条）"
                 % (p["prefer_persona"] or "-", p["prefer_band"] or "-", MIN_N))
    else:
        L.append("- 样本不足，暂不给优先级；继续按人群轮转累积证据。")
    L += ["", "> 机读：`PRACTICE-PARAMS.json`；原始账：`practice-log.jsonl`"]
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(L) + "\n")
    return OUT_MD


def self_test():
    ok, bad = [], []

    def chk(n, c):
        (ok if c else bad).append(n)

    rs = [{"action": "post", "rpid": "1", "text": "短句一条评论内容", "root": 0},
          {"action": "verify", "rpid": "1", "visible": True},
          {"action": "post", "rpid": "2", "text": "另一条短句评论内容", "root": 0},
          {"action": "verify", "rpid": "2", "visible": None}]      # 取数失败：不计分母
    p = build(rs)
    chk("visible=None 不计入分母", p["judged_n"] == 1)
    chk("样本不足时不给优先级", p["prefer_persona"] is None and p["enough"] is False)
    rs2 = [{"action": "post", "rpid": str(i), "text": "这是一条足够长的评论内容用于测试"} for i in range(10)] + \
          [{"action": "verify", "rpid": str(i), "visible": i % 2 == 0} for i in range(10)]
    p2 = build(rs2)
    chk("样本足够才给优先级", p2["enough"] is True)
    chk("可见率算对", abs(p2["overall_rate"] - 0.5) < 1e-6)
    for n in ok:
        print("  PASS", n)
    for n in bad:
        print("  FAIL", n)
    print("[exp] self-test %d/%d" % (len(ok), len(ok) + len(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    p = build()
    json.dump(p, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    render(p)
    print("[exp] 样本 %d 条｜整体可见率 %s｜%s"
          % (p["judged_n"], p["overall_rate"],
             ("优先人群=%s 优先带=%s" % (p["prefer_persona"], p["prefer_band"])) if p["enough"]
             else "样本不足，暂不给参数"))
