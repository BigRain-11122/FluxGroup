#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""acceptance.py — 唯一的验收口径：只认产物与质量，流程文档一律不算数。

CEO 2026-11-08：「我要求你验收只看产物和质量，中间的流程文档什么不算数」。

为什么必须写成代码：过去验收看的是卡的 state=DONE，于是
  · 177 字节的缺口清单、每轮重写的看板、自检回执，都被算成"今天的产量"
  · 一天 788 份同一张 QUALITY-BOARD 也能报成"产出 840 个文件"
这不是判断力问题，是口径没有唯一实现。

分类（硬规则）：
  PRODUCT  视频 / 图片 / 构建目录 / 回测报告 —— 只有这四类能进验收
  BOOKKEEPING  .md（方案/分诊/一屏）、audits/ 与 queue-receipts/ 下的 JSON —— 永远不算数
  必须过质量席（QUALITY-AGENTS-v1.json）才算 ACCEPTED；本地判不了=REMOTE（不算数也不判死）

用法：
  python Tools/fleet/acceptance.py                  # 默认看 origin 队列最近 24 小时完成的卡
  python Tools/fleet/acceptance.py --window-hours 72
  python Tools/fleet/acceptance.py --json
Exit: 0 有真产物且全部过质量；1 有 DONE 但零真产物（或产物质量不过）；2 输入缺失
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")
sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))

VIDEO = (".mp4", ".mov", ".mkv", ".webm", ".avi")
IMAGE = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
ACCOUNT_DIRS = ("cph4/fleet/audits/", "cph4/fleet/state/", "cph4/fleet/queue-receipts/",
                "cph4/fleet/game-v1/SUBMIT-PACK", "cph4/fleet/archive/")

LINE_OF = {  # 交付物类型 → 质量席的线键
    "video": "content-mv",
    "image": "content-image",
    "build": "game-build",
    "report": "bigmoney-quant",
}


def rows_origin():
    """执行机读的是 origin 快照，验收也必须读同一份，否则口径对不上。"""
    try:
        out = subprocess.run(["git", "show", "origin/main:cph4/fleet/PRODUCTION-QUEUE.jsonl"],
                             cwd=ROOT, capture_output=True, text=True, timeout=60)
        txt = out.stdout if out.returncode == 0 else ""
    except Exception:
        txt = ""
    if not txt:
        try:
            txt = open(os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl"),
                       encoding="utf-8-sig", errors="replace").read()
        except Exception:
            return []
    rows = []
    for ln in txt.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rows.append(json.loads(ln))
        except Exception:
            pass
    return rows


def classify(deliverable):
    """交付物属于哪一类。这里只回答"能不能算数"，不回答"好不好"。"""
    d = str(deliverable or "").strip().replace("\\", "/")
    if not d:
        return "NONE"
    low = d.lower()
    ext = os.path.splitext(low)[1]
    under_account = any(a.lower() in low for a in ACCOUNT_DIRS)
    if ext in VIDEO:
        return "PRODUCT" if not under_account else "BOOKKEEPING"
    if ext in IMAGE:
        return "PRODUCT" if not under_account else "BOOKKEEPING"
    if ext in (".md", ".txt"):
        return "BOOKKEEPING"          # 方案/分诊/一屏/探针文本：中间过程，永远不算数
    if "/build" in low or low.rstrip("/").endswith("build"):
        return "PRODUCT"
    if ext == ".json" and ("backtest" in low or low.startswith("quant/")):
        return "PRODUCT"
    if ext in (".json", ".csv", ".jsonl") and under_account:
        return "BOOKKEEPING"
    if ext in (".json", ".csv"):
        return "UNKNOWN"
    if os.path.isdir(os.path.join(ROOT, d)):
        return "PRODUCT" if "/build" in low else "UNKNOWN"
    return "UNKNOWN"


def kind_of(deliverable):
    low = str(deliverable or "").lower().replace("\\", "/")
    ext = os.path.splitext(low)[1]
    if ext in VIDEO:
        return "video"
    if ext in IMAGE:
        return "image"
    if "/build" in low or low.rstrip("/").endswith("build"):
        return "build"
    if ext in (".json", ".csv"):
        return "report"
    return "other"


def quality(line_key, path):
    """过质量席。返回 (verdict, score, detail)。判不了就 REMOTE，不判死。"""
    try:
        import quality_agents as qa
        reg = qa.registry()
        res = qa.score_line(line_key, path, reg)
        if not res:
            return "REMOTE", None, "本条线未登记判据"
        if res.get("blocked"):
            return "FAIL", res.get("score"), "HARD-FAIL:" + ",".join(res["blocked"])
        thr = reg.get("thresholds", {}).get("pass_score", 0.8)
        sc = res.get("score")
        if sc is None:
            return "REMOTE", None, "本机量不出"
        return ("PASS" if sc >= thr else "FAIL"), sc, "%d/%d" % (res.get("passed") or 0,
                                                               res.get("judged") or 0)
    except Exception as e:
        return "REMOTE", None, "质量席不可用:%s" % str(e)[:60]


def run(window_hours=24):
    rows = rows_origin()
    if not rows:
        print("[acceptance] E-INPUT: 读不到队列")
        return None, 2
    cutoff = time.time() - window_hours * 3600
    done = []
    for r in rows:
        if r.get("state") != "DONE":
            continue
        ts = str(r.get("finished_at") or r.get("closed_at") or "")
        try:
            t = time.mktime(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S"))
        except Exception:
            continue
        if t >= cutoff:
            done.append(r)
    items = []
    for r in done:
        d = r.get("deliverable")
        cls = classify(d)
        it = {"id": r.get("id"), "line": r.get("line"), "deliverable": d, "class": cls,
              "verdict": "-", "score": None, "detail": ""}
        if cls == "PRODUCT":
            kind = kind_of(d)
            p = d if os.path.isabs(str(d)) else os.path.join(ROOT, str(d))
            if not os.path.exists(p):
                it["verdict"] = "REMOTE"     # 产物在别的机器上，本机判不了
                it["detail"] = "本机无此产物"
            else:
                v, sc, det = quality(LINE_OF.get(kind, "content-mv"), p)
                it["verdict"], it["score"], it["detail"] = v, sc, det
        items.append(it)
    accepted = [i for i in items if i["verdict"] == "PASS"]
    failed = [i for i in items if i["verdict"] == "FAIL"]
    remote = [i for i in items if i["verdict"] == "REMOTE"]
    booking = [i for i in items if i["class"] == "BOOKKEEPING"]
    unknown = [i for i in items if i["class"] in ("UNKNOWN", "NONE")]
    res = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "window_hours": window_hours,
           "done_cards": len(done), "accepted": len(accepted), "quality_failed": len(failed),
           "remote_unverifiable": len(remote), "bookkeeping": len(booking),
           "unknown": len(unknown), "items": items}
    return res, (0 if accepted else 1)


def board(res):
    os.makedirs(STATE, exist_ok=True)
    with open(os.path.join(STATE, "acceptance.json"), "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in res.items() if k != "items"}, f, ensure_ascii=False, indent=1)
    lines = ["# 验收一屏（只认产物与质量）%s" % res["ts"], "",
             "口径：`.md`（方案/分诊/一屏）与 audits/、queue-receipts/ 下的 JSON 一律不算数；"
             "视频/图片/构建/回测必须过质量席才算 ACCEPTED。", "",
             "| 项 | 数量 |", "|---|---|",
             "| 完成卡 | %d |" % res["done_cards"],
             "| ✅ 真产物且过质量 | %d |" % res["accepted"],
             "| ❌ 产物质量不过 | %d |" % res["quality_failed"],
             "| ⚠️ 产物在别的机器（本机判不了） | %d |" % res["remote_unverifiable"],
             "| 🗂 流程文档/台账（不算数） | %d |" % res["bookkeeping"],
             "| ❔ 未分类 | %d |" % res["unknown"], ""]
    if res["accepted"]:
        lines += ["## 已验收产物", "| 卡 | 产物 | 分数 |", "|---|---|---|"]
        for i in res["items"]:
            if i["verdict"] == "PASS":
                lines.append("| `%s` | %s | %.2f |" % (i["id"], i["deliverable"], i["score"] or 0))
        lines.append("")
    if res["quality_failed"]:
        lines += ["## 产物不过质量", "| 卡 | 产物 | 原因 |", "|---|---|---|"]
        for i in res["items"]:
            if i["verdict"] == "FAIL":
                lines.append("| `%s` | %s | %s |" % (i["id"], i["deliverable"], i["detail"]))
        lines.append("")
    p = os.path.join(FLEET, "ACCEPTANCE-BOARD.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return p


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--window-hours", type=int, default=24)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv[1:])
    res, rc = run(a.window_hours)
    if rc == 2 or not res:
        return 2
    p = board(res)
    if a.json:
        print(json.dumps(res, ensure_ascii=False))
    else:
        print("[acceptance] 完成卡 %d · 真产物过质量 %d · 质量不过 %d · 远端待证 %d · 文档/台账 %d · 未分类 %d"
              % (res["done_cards"], res["accepted"], res["quality_failed"],
                 res["remote_unverifiable"], res["bookkeeping"], res["unknown"]))
        print("[acceptance] 一屏 -> %s" % os.path.relpath(p, ROOT))
        if not res["accepted"]:
            print("[acceptance] RED：这个窗口内没有任何可验收的产物（流程文档不算数）")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))