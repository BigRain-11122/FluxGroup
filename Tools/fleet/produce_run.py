#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""produce_run.py — 执行 + 就地验收：产物在哪，判定就在哪。

为什么（CEO 2026-11-08「闭环只认产出，而且是通过的产出」）：
  产物落在执行机上，主控看不到 → 验收永远是 0，等于没产出。
  所以执行环节必须自己判：跑完立刻分类（产物/文书）、过质量席、记字节与 sha，
  写一份 *-acceptance.json 回执。主控只读回执，不再依赖"能不能看到那个文件"。

回执字段：card, deliverable, class, verdict(PASS/FAIL/REJECT), score, bytes, sha256, ts, node
  REJECT = 交付物不是产物（文档/台账/回执）→ 永远不算产出
  FAIL   = 是产物但质量席不过
  PASS   = 产物且过质量席 → 唯一算产出的状态

用法（在执行机上）：
  python Tools/fleet/produce_run.py --card <card_id>
  python Tools/fleet/produce_run.py --cmd "..." --deliverable media/asset/x.png --line biggame
Exit: 0 PASS；1 FAIL/REJECT；3 缺输入（命令没跑成或产物没落盘）
"""
import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
RECEIPTS = os.path.join(FLEET, "queue-receipts")
sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_card(cid):
    try:
        out = subprocess.run(["git", "show", "origin/main:cph4/fleet/PRODUCTION-QUEUE.jsonl"],
                             cwd=ROOT, capture_output=True, text=True, timeout=60)
        txt = out.stdout
    except Exception:
        txt = ""
    if not txt:
        try:
            txt = open(os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl"),
                       encoding="utf-8-sig", errors="replace").read()
        except Exception:
            return None
    for ln in txt.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if r.get("id") == cid:
            return r
    return None


def judge(deliverable, line_hint=""):
    import acceptance as ac
    cls = ac.classify(deliverable)
    p = deliverable if os.path.isabs(deliverable) else os.path.join(ROOT, deliverable)
    res = {"class": cls, "deliverable": deliverable, "exists": os.path.exists(p),
           "verdict": "REJECT", "score": None, "bytes": 0, "sha256": "", "detail": ""}
    if not res["exists"]:
        res.update(verdict="FAIL", detail="产物未落盘")
        return res
    if os.path.isfile(p):
        res["bytes"] = os.path.getsize(p)
        res["sha256"] = sha(p)
    if cls != "PRODUCT":
        res["detail"] = "交付物不是产物（文档/台账/回执）"
        return res
    kind = ac.kind_of(deliverable)
    line_key = ac.LINE_OF.get(kind) or ("game-build" if line_hint == "biggame" else "content-image")
    v, sc, det = ac.quality(line_key, p)
    res.update(verdict=("PASS" if v == "PASS" else "FAIL"), score=sc,
               detail="%s %s" % (line_key, det))
    return res


def write_receipt(card_id, res):
    os.makedirs(RECEIPTS, exist_ok=True)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "card": card_id,
           "node": os.environ.get("COMPUTERNAME") or socket.gethostname(),
           **res}
    p = os.path.join(RECEIPTS, "%s-acceptance.json" % card_id)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    return p


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--card")
    ap.add_argument("--cmd")
    ap.add_argument("--deliverable")
    ap.add_argument("--line", default="")
    ap.add_argument("--timeout", type=int, default=7200)
    a = ap.parse_args(argv[1:])
    if a.card:
        c = load_card(a.card)
        if not c:
            print("[produce] E-INPUT 队列里没有这张卡：%s" % a.card)
            return 3
        cmd, deliv, line = c.get("cmd"), c.get("deliverable"), c.get("line") or ""
        cid = a.card
    else:
        cmd, deliv, line, cid = a.cmd, a.deliverable, a.line, a.card or "ad-hoc"
    if not cmd or not deliv:
        print("[produce] E-INPUT 缺 cmd 或 deliverable")
        return 3
    print("[produce] 执行: %s" % cmd[:120])
    r = subprocess.run(cmd, cwd=ROOT, shell=True, capture_output=True, text=True,
                       timeout=a.timeout)
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    print("[produce] 命令 rc=%d · 输出尾部: %s" % (r.returncode, out[-300:]))
    res = judge(deliv, line)
    p = write_receipt(cid, res)
    print("[produce] 判定 %s · class=%s · score=%s · %d 字节" %
          (res["verdict"], res["class"], res["score"], res["bytes"]))
    print("[produce] 回执 -> %s" % os.path.relpath(p, ROOT))
    if res["verdict"] == "PASS":
        return 0
    if not res["exists"] and r.returncode != 0:
        return 3
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))