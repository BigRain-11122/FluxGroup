#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""master_patrol.py - 主控巡查智能体：偶尔检查、抽样验收、发现异常就出手。

对应 CEO 2026-11-11：「日常机队机器自己闭环管理和转验收，主控偶尔检查验收，
主控也有智能体巡查。」

一轮巡五件事（都基于盘上事实）：
  1 机器   状态、队列堆积、24h 无回执
  2 缺口   无承接工序、无产物契约、有卡没人干（复用 fleet_view 的判定）
  3 抽验   按 ACCEPTANCE-v1.json 的比例，抽最近的 DONE 回执重算哈希
  4 停摆   回执有、但产物没变（假完成复发）
  5 产出   本轮巡出结论写入 PATROL.md，异常转成文字待办

用法：
  python3 Tools/fleet/master_patrol.py            # 巡一轮，写 PATROL.md
  python3 Tools/fleet/master_patrol.py --json
  python3 Tools/fleet/master_patrol.py --sample-only
  python3 Tools/fleet/master_patrol.py --self-test
返回码：0 无异常 / 1 有异常待处理 / 2 抽验失败（最严重）/ 3 自检失败
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

sys.path.insert(0, HERE)
import station_shards as ss  # noqa: E402
import fleet_view  # noqa: E402

LEDGER = os.path.join("cph4", "fleet", "state", "acceptance-ledger.jsonl")


def _j(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def _rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return out


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _sampled(root=None):
    p = os.path.join(root or ROOT, LEDGER)
    return {(r.get("station"), r.get("id")) for r in _rows(p)}


def sample(root=None, limit_override=None):
    """按配置抽验：重算哈希与回执比对。返回 (抽查结果列表, 失败数)。"""
    cfg = _j(os.path.join(root or ROOT, "cph4", "fleet", "ACCEPTANCE-v1.json"), {}) or {}
    per = cfg.get("sample_per_day") or {}
    done = _sampled(root)
    results, fails = [], 0
    for station, n in per.items():
        n = limit_override if limit_override is not None else n
        files = sorted(glob.glob(os.path.join(root or ROOT, "cph4", "fleet", "rt", station,
                                             "receipts", "*.json")),
                       key=os.path.getmtime, reverse=True)
        picked = 0
        for f in files:
            if picked >= n:
                break
            r = _j(f, {}) or {}
            key = (station, r.get("id"))
            if key in done:
                continue
            if str(r.get("verdict") or "").upper() not in ("DONE", "PASS", "MATCH"):
                continue
            picked += 1
            rec = {"station": station, "id": r.get("id"), "receipt": os.path.basename(f)}
            d = r.get("deliverable")
            p = os.path.join(root or ROOT, d) if d else ""
            if not d or not os.path.exists(p):
                rec.update({"pass": False, "why": "A1 产物不存在"}); fails += 1
            elif os.path.getsize(p) == 0:
                rec.update({"pass": False, "why": "A1 产物为空"}); fails += 1
            elif not r.get("sha256"):
                rec.update({"pass": False, "why": "A2 回执没写哈希（不可验）"}); fails += 1
            else:
                got = _sha(p)
                if got != r.get("sha256"):
                    rec.update({"pass": False, "why": "A2 哈希不一致"}); fails += 1
                elif str(r.get("judge") or "") in ("manual", "human"):
                    rec.update({"pass": False, "why": "A3 人判件被标 DONE"}); fails += 1
                else:
                    rec.update({"pass": True, "why": "A1/A2/A3 通过", "sha256": got})
            rec["ts"] = datetime.now().isoformat(timespec="seconds")
            results.append(rec)
    if results:
        p = os.path.join(root or ROOT, LEDGER)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return results, fails


def patrol(root=None, check_net=False):
    snap = fleet_view.snapshot(root, check_net=check_net)
    samples, fails = sample(root)
    issues = []
    for g in snap["gaps"]:
        issues.append({"kind": g["kind"], "who": g["who"], "why": g["why"]})
    for s in samples:
        if not s["pass"]:
            issues.append({"kind": "ACCEPTANCE-FAIL", "who": "%s/%s" % (s["station"], s["id"]),
                           "why": s["why"]})
    return {"ts": datetime.now().isoformat(timespec="seconds"),
            "machines": snap["machines"], "stages": snap["counts"],
            "samples": samples, "sample_fails": fails, "issues": issues}


def render(rep):
    L = ["# 主控巡查 %s" % rep["ts"], ""]
    L.append("## 一、机器")
    for m in rep["machines"]:
        q = m["queue"]
        L.append("- **%s（%s）** %s ｜ 席 %d ｜ 类型 %d ｜ 工序 %d ｜ 队列 O%d/R%d/D%d/B%d ｜ 回执 %s" % (
            m["machine"], m["station"], m["status"], m["seats"], m["task_types"], m["stages"],
            q["open"], q["running"], q["done"], q["blocked"],
            ("%.1fh 前" % m["last_receipt_h"]) if m["last_receipt_h"] is not None else "无"))
    L += ["", "## 二、任务面", "- 工序 %d 道，有产物契约 %d 道（缺 %d）" % (
        rep["stages"]["stages"], rep["stages"]["with_output"],
        rep["stages"]["stages"] - rep["stages"]["with_output"])]
    L += ["", "## 三、抽验（%d 件，失败 %d）" % (len(rep["samples"]), rep["sample_fails"])]
    if not rep["samples"]:
        L.append("- 本轮无待抽验件")
    for s in rep["samples"]:
        L.append("- %s %s/%s：%s" % ("PASS" if s["pass"] else "FAIL", s["station"], s["id"], s["why"]))
    L += ["", "## 四、需要出手"]
    if not rep["issues"]:
        L.append("- （无）")
    for i in rep["issues"]:
        L.append("- [%s] %s：%s" % (i["kind"], i["who"], i["why"]))
    return "\n".join(L) + "\n"


def self_test():
    import tempfile
    ok = total = 0

    def chk(n, c):
        nonlocal ok, total
        total += 1
        ok += 1 if c else 0
        print("%s %s" % ("ok  " if c else "FAIL", n))

    with tempfile.TemporaryDirectory() as td:
        b = os.path.join(td, "cph4", "fleet")
        rd = os.path.join(b, "rt", "visual", "receipts")
        os.makedirs(rd); os.makedirs(os.path.join(b, "state"))
        os.makedirs(os.path.join(td, "out"))
        json.dump({"sample_per_day": {"visual": 5}}, open(os.path.join(b, "ACCEPTANCE-v1.json"), "w"))

        good = os.path.join(td, "out", "good.bin"); open(good, "wb").write(b"abc")
        sha = _sha(good)
        json.dump({"id": "g1", "verdict": "DONE", "deliverable": "out/good.bin",
                   "sha256": sha, "judge": "path"},
                  open(os.path.join(rd, "g1.json"), "w"))
        json.dump({"id": "b1", "verdict": "DONE", "deliverable": "out/good.bin",
                   "sha256": "deadbeef", "judge": "path"},
                  open(os.path.join(rd, "b1.json"), "w"))
        json.dump({"id": "n1", "verdict": "DONE", "deliverable": "out/good.bin",
                   "judge": "path"},
                  open(os.path.join(rd, "n1.json"), "w"))
        json.dump({"id": "m1", "verdict": "DONE", "deliverable": "out/good.bin",
                   "sha256": sha, "judge": "manual"},
                  open(os.path.join(rd, "m1.json"), "w"))
        json.dump({"id": "x1", "verdict": "DONE", "deliverable": "out/none.bin",
                   "sha256": sha, "judge": "path"},
                  open(os.path.join(rd, "x1.json"), "w"))

        res, fails = sample(td)
        d = {r["id"]: r for r in res}
        chk("哈希一致 -> PASS", d["g1"]["pass"] is True)
        chk("哈希不一致 -> FAIL", d["b1"]["pass"] is False and "哈希" in d["b1"]["why"])
        chk("回执没哈希 -> FAIL", d["n1"]["pass"] is False and "没写哈希" in d["n1"]["why"])
        chk("人判件标 DONE -> FAIL", d["m1"]["pass"] is False and "人判" in d["m1"]["why"])
        chk("产物缺失 -> FAIL", d["x1"]["pass"] is False)
        chk("失败计数正确", fails == 4)

        res2, _ = sample(td)
        chk("已抽验的不重复抽（第二次为空）", res2 == [])
        chk("台账已落盘", os.path.exists(os.path.join(td, LEDGER)))

    print("[master_patrol] %d/%d" % (ok, total))
    return 0 if ok == total else 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--sample-only", action="store_true")
    ap.add_argument("--no-net", action="store_true", default=True)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.sample_only:
        res, fails = sample(a.root)
        print(json.dumps({"samples": res, "fails": fails}, ensure_ascii=False, indent=1))
        return 2 if fails else 0
    rep = patrol(a.root, check_net=not a.no_net)
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        txt = render(rep)
        p = os.path.join(a.root or ROOT, "cph4", "fleet", "PATROL.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(txt)
        print(txt, end="")
        print("\n[master_patrol] 写入 %s" % p)
    if rep["sample_fails"]:
        return 2
    return 1 if rep["issues"] else 0


if __name__ == "__main__":
    sys.exit(main())
