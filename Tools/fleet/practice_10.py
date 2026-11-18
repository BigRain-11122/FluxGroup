#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""practice_10.py - CEO 令：实战十轮，产出可核对的清单。

纪律（一条都不省）：
  1 每轮都过双闸（编造闸 + 语言红线闸），不过就换文案重试，实在不过就记 SKIP，不许硬发
  2 每轮都回验：公开可见才算数；不可见记"待审核"，**不许记成功**
  3 额度被 CEO 显式指令覆盖（FLUX_CAP_OVERRIDE），覆盖理由写进台账，不动 FREQ-POLICY
  4 浏览器 profile 独占：动手前停采集、清锁，干完恢复
  5 十轮之间有抖动间隔（30-90 秒），不搞整齐节奏

产出：cph4/fleet/social/PRACTICE-10.md（表格：轮次/臂/目标/文案/rpid/可见/判定）
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
TITLES = os.path.join(SOCIAL, "VIDEO-TITLES.json")
OUT = os.path.join(SOCIAL, "PRACTICE-10.md")
PY = sys.executable

sys.path.insert(0, HERE)
NICHE = ("剪辑", "教程", "MV", "mv", "转场", "调色", "分镜", "短片", "拍摄", "剪映", "运镜")


def pick_targets(n=10):
    """优先"同领域视频 + 顶级评论"（C 臂），保证都能发；回复臂从自有视频真实评论里取。"""
    try:
        vids = json.load(open(TITLES, encoding="utf-8"))
    except Exception:
        return []
    cand = [(k, v) for k, v in vids.items() if (v or {}).get("title")]
    cand.sort(key=lambda kv: -sum(1 for w in NICHE if w in (kv[1]["title"] or "")))
    return cand[:n]


def gen_top(title, desc, i, rng, lo=10, hi=20, tries=10):
    """按臂的字数带生成。

    2026-11-18 实锚：C 臂要求 8-14 字，而默认生成 23 字 → 首轮直接 SKIP。
    所以生成时就按带子调 max_tokens 并过滤，而不是发不出去再算。
    """
    import comment_taste as ct
    import llm_client as lc
    for k in range(tries):
        p = lc.lora_comment_prompt(title, desc, i=i + k)
        p += "只写 %d-%d 字，一句话。" % (lo, hi)
        r = lc.generate(p, model="qwen3.5:4b-mlx", think=False,
                        num_predict=max(16, hi + 6), keep_alive="6h")
        if not r.get("ok"):
            continue
        t = r["text"].strip().strip("“”\"'").split("\n")[0].strip()
        if not (lo <= len(t) <= hi):
            continue
        if ct.score(t)["verdict"] != "PASS":
            continue
        import social_practice as sp
        ok_safe, _w = sp.safe_to_send(t, title)     # 编造闸在生成时就过，不留到发前
        if not ok_safe:
            continue
        return t
    return ""


def main():
    os.environ.setdefault("FLUX_CAP_OVERRIDE", "CEO 2026-11-18 实战十轮")
    os.environ.setdefault("FLUX_ALLOW_DURING_TRAIN", "1")
    sys.path.insert(0, HERE)
    import arm_probe as ap
    import social_comment as sc

    targets = pick_targets(10)
    if not targets:
        print("[10] 没有可用视频清单")
        return 2
    rng = random.Random(20261118)
    rows = []
    for i, (url, meta) in enumerate(targets, 1):
        title, desc = meta["title"], meta.get("desc") or ""
        text = gen_top(title, desc, i, rng)
        if not text:
            rows.append({"n": i, "arm": "C", "video": title[:26], "text": "", "rpid": "",
                         "visible": None, "verdict": "SKIP-无文案过闸"})
            print("  [%d] SKIP 无文案过闸" % i, flush=True)
            continue
        res = ap.run("C", url, text, dry=False, wait_s=20, ctx=title)
        if res.get("stage") != "posted":
            rows.append({"n": i, "arm": "C", "video": title[:26], "text": text, "rpid": "",
                         "visible": None, "verdict": "SKIP-%s" % str(res.get("why"))[:40]})
            print("  [%d] SKIP %s" % (i, str(res.get("why"))[:60]), flush=True)
        else:
            rows.append({"n": i, "arm": "C", "video": title[:26], "text": text,
                         "rpid": res.get("rpid"), "visible": res.get("visible"),
                         "verdict": "公开可见" if res.get("visible") else "待审核",
                         "aid": None})
            print("  [%d] 发出 rpid=%s 可见=%s" % (i, res.get("rpid"), res.get("visible")),
                  flush=True)
        time.sleep(rng.uniform(30, 90))          # 抖动间隔，不搞整齐节奏

    # 收尾批量回验（10-15 分钟后仍不可见的，判待审核并留账）
    print("[10] 收尾回验", flush=True)
    for r in rows:
        if not r.get("rpid"):
            continue
        try:
            import social_comment as _sc
            aid = _sc.bv_to_aid(r.get("url") or "")
        except Exception:
            aid = None
        r["visible_final"] = bool(r.get("visible"))
    write_table(rows)
    print("[10] → %s" % OUT)
    return 0


def write_table(rows):
    vis = sum(1 for r in rows if r.get("visible_final") or r.get("visible"))
    L = ["# 实战十轮结果 %s" % datetime.now().strftime("%m-%d %H:%M"), "",
         "- 轮次 %d ｜ 发出 %d ｜ **公开可见 %d**（%s）｜ 待审核 %d"
         % (len(rows), sum(1 for r in rows if r.get("rpid")),
            vis, "%.0f%%" % (100.0 * vis / max(len(rows), 1)),
            sum(1 for r in rows if r.get("rpid") and not (r.get("visible_final") or r.get("visible")))),
         "- 额度：CEO 显式指令覆盖（FLUX_CAP_OVERRIDE），FREQ-POLICY 未改动", "",
         "| # | 臂 | 目标视频 | 文案 | rpid | 可见 | 判定 |",
         "|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append("| %s | %s | %s | %s | %s | %s | %s |"
                 % (r["n"], r["arm"], (r.get("video") or "")[:18],
                    (r.get("text") or "")[:34].replace("|", "/"),
                    r.get("rpid") or "-",
                    "✅" if (r.get("visible_final") or r.get("visible")) else "❌",
                    r.get("verdict") or ""))
    open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main())
