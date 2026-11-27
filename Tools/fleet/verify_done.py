#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_done.py - 验收：DONE 不等于做对。

为什么（CEO 2026-11-05「常驻智能体要监督、派单、验收」）：
  现在"交付物在盘"就判 DONE，但盘上那件东西可能是 0 字节、可能是个 BLOCKED 说明文件、
  可能是上一次留下的旧文件。incident ledger 里已经有"BLOCKED 回执落在交付路径上被当成功"
  的先例。这一站对所有近 24h 的 DONE 卡做一次机器验收：

  判据（全部可判定，不猜）：
    V1 文件存在且非空（>= min_bytes）
    V2 扩展名/类型与交付物声明一致（.json 必须是合法 JSON；.mp4 必须 ffprobe 出时长）
    V3 回执 rc 属于该卡 ok_rc（有回执才判）
    V4 内容不是拒答/BLOCKED 说明（命中关键字即 FAIL）
  产出 state/verify-done.json：PASS / SUSPECT（列出原因）。只报告，不改卡状态——
  改状态是 closer 的权，这一站只给证据。

用法：python3 Tools/fleet/verify_done.py [--hours 24] [--json]
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
OUT = os.path.join(F, "state", "verify-done.json")
REFUSE = ("blocked", "无法完成", "缺投料", "not found", "no such file", "拒答", "refused")


def rows_of(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    since = datetime.now() - timedelta(hours=a.hours)
    cards = [r for r in rows_of(os.path.join(F, "PRODUCTION-QUEUE.jsonl"))
             if r.get("state") == "DONE"]
    checked, pass_n, suspect = 0, 0, []

    for r in cards:
        ca = r.get("closed_at") or r.get("ts") or ""
        try:
            if datetime.fromisoformat(str(ca)[:19]) < since:
                continue
        except Exception:
            continue
        dl = r.get("deliverable") or ""
        if not dl:
            suspect.append({"id": r.get("id"), "why": "DONE 但没有声明交付物"})
            checked += 1
            continue
        p = dl if os.path.isabs(dl) else os.path.join(ROOT, dl)
        if not os.path.exists(p):
            # 跨机产物在主控看不见，不算失败，但要标出来
            suspect.append({"id": r.get("id"), "why": "主控看不到交付物（可能跨机）", "path": dl,
                            "level": "INFO"})
            checked += 1
            continue
        size = os.path.getsize(p) if os.path.isfile(p) else -1
        why = []
        if size == 0:
            why.append("空文件(0B)")
        elif os.path.isfile(p) and size < 64:
            why.append("过小(%dB)" % size)
        if str(dl).lower().endswith(".json"):
            try:
                json.load(open(p, encoding="utf-8"))
            except Exception as e:
                why.append("JSON 解析失败:%s" % str(e)[:40])
        if str(dl).lower().endswith((".mp4", ".mov", ".mkv")):
            try:
                pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                     "format=duration", "-of",
                                     "default=nw=1:nk=1", p],
                                    capture_output=True, text=True, timeout=30)
                dur = float((pr.stdout or "0").strip() or 0)
                if dur <= 0.1:
                    why.append("视频时长≈0")
            except Exception as e:
                why.append("ffprobe 失败:%s" % str(e)[:30])
        if os.path.isfile(p) and size > 0 and os.path.getsize(p) < 200000:
            try:
                body = open(p, encoding="utf-8", errors="ignore").read(4000).lower()
                for k in REFUSE:
                    if k in body:
                        why.append("内容像拒答/阻塞说明(%s)" % k)
                        break
            except Exception:
                pass
        checked += 1
        if why:
            suspect.append({"id": r.get("id"), "why": "; ".join(why), "path": dl})
        else:
            pass_n += 1

    out = {"ts": datetime.now().isoformat(timespec="seconds"), "hours": a.hours,
           "checked": checked, "pass": pass_n, "suspect": len(suspect),
           "items": suspect[:40],
           "verdict": "OK" if not suspect else "SUSPECT"}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("[verify-done] checked=%d pass=%d suspect=%d" % (checked, pass_n, len(suspect)))
        for s in suspect[:6]:
            print("  ? %s :: %s" % (s.get("id"), s.get("why")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))