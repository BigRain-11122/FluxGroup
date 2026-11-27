#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_loop_verify.py - 机队闭环验收：按"供给→执行→判据→回执→产物"逐台核证据。

Why（2026-11-13 CEO「赶紧把机队的闭环测试好」）：
闭环不是"跑过一次"，而是**每一环都留下可复算的证据**。本工具只看盘上事实：
  * 有回执（执行过）
  * 回执带 judge（判据存在）
  * 产物在盘且非空
  * 重算 sha256 与回执一致（记录可信）
  * 回执与产物时间差不超过 10 分钟（不是后来补的）

每台机给一个结论：
  LOOP-OK     最近回执全部证据完整
  LOOP-BROKEN 有回执但产物/哈希对不上（最严重，等于假完成）
  LOOP-IDLE   没有回执（没产出，或执行体没跑）
  NO-EXEC     该机在线但没有心跳（执行体没装）

用法：
    python3 Tools/fleet/fleet_loop_verify.py            # 全部工位
    python3 Tools/fleet/fleet_loop_verify.py --station visual --recent 5
    python3 Tools/fleet/fleet_loop_verify.py --self-test
返回码：0 全部 LOOP-OK/IDLE / 1 有 LOOP-BROKEN / 3 自检失败
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
STATIONS = ("delivery", "visual", "audio", "brain", "control")


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _j(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def _is_remote(d):
    """产物路径是否在别的机器上：Windows 盘符 / UNC / 不在本仓库的绝对路径。"""
    s = str(d or "")
    if not s:
        return False
    if len(s) > 1 and s[1] == ":" and s[0].isalpha():
        return True
    if s.startswith("\\\\"):
        return True
    return os.path.isabs(s) and not os.path.abspath(s).startswith(ROOT)


def verify_receipt(root, r, strict_time=True):
    """核一份回执：返回 (ok, 问题清单)。

    strict_time=False 时不查"回执与产物时间差"——同一产物被多张卡写过时
    （2026-11-12 重复建卡的历史遗留），只有最新那张的时间才对得上，
    对旧卡查这一项永远是红的，属误报。
    """
    probs = []
    d = r.get("deliverable")
    p = os.path.join(root, d) if d else ""
    if not d:
        probs.append("回执没写 deliverable")
        return False, probs
    if _is_remote(d):
        # 远端产物：本机（主控）看不到那台机的盘，判"缺失"就是假红（RG-07 同族）。
        # 只能核回执自带的证据：必须列出文件与哈希，否则仍是不可验。
        files = r.get("files") or []
        hashed = [f for f in files if f.get("sha256") or f.get("sha256_16")]
        if not hashed:
            probs.append("远端产物且回执没有文件哈希（不可验）")
            return False, probs
        for f in hashed:
            if int(f.get("bytes") or 0) <= 0:
                probs.append("远端文件 %s 字节数为 0" % f.get("file"))
        if not (r.get("judge") or "").strip():
            probs.append("回执缺 judge")
        return (not probs), probs
    if not os.path.exists(p):
        probs.append("产物不存在")
        return False, probs
    if os.path.getsize(p) == 0:
        probs.append("产物为空")
        return False, probs
    sha = r.get("sha256")
    if not sha:
        probs.append("回执缺 sha256（不可验）")
    else:
        if _sha(p) != sha:
            probs.append("哈希不一致")
    if not (r.get("judge") or "").strip():
        probs.append("回执缺 judge")
    # 回执与产物时间差（仅最新卡）
    if not strict_time:
        return (not probs), probs
    try:
        ts = datetime.fromisoformat(str(r.get("ts"))[:19]).timestamp()
        if abs(os.path.getmtime(p) - ts) > 600:
            probs.append("产物与回执时间差 >10 分钟")
    except Exception:
        pass
    return (not probs), probs


def check_station(station, root=None, recent=5):
    root = root or ROOT
    rd = os.path.join(root, "cph4", "fleet", "rt", station, "receipts")
    files = sorted(glob.glob(os.path.join(rd, "*.json")),
                   key=os.path.getmtime, reverse=True)[:recent]
    hb = _j(os.path.join(root, "cph4", "fleet", "rt", station, "heartbeat.json"))
    rows = []
    seen_dlv = set()
    for f in files:
        r = _j(f, {}) or {}
        if str(r.get("verdict", "")).upper() not in ("DONE", "PASS", "MATCH"):
            continue          # BLOCKED/REVISE 不参与闭环验收（它们本来就该没产物）
        dlv = str(r.get("deliverable") or "")
        newest = dlv not in seen_dlv      # files 已按 mtime 倒序，首次出现即最新
        seen_dlv.add(dlv)
        ok, probs = verify_receipt(root, r, strict_time=newest)
        rows.append({"id": r.get("id"), "ok": ok, "problems": probs,
                     "remote": _is_remote(dlv)})
    if not rows:
        # 证据可见范围：心跳是各机本地文件（已 gitignore），主控看不到远端心跳。
        # 只有本机（control）缺心跳才算"执行体没装"；远端缺心跳一律不判死，只说"没看到产出"。
        if station == "control" and hb is None:
            state, why = "NO-EXEC", "本机无心跳：执行体没装或没跑"
        elif hb is None:
            state, why = "LOOP-IDLE", "无 DONE 回执（远端心跳本地不可见，不据此判死）"
        else:
            state, why = "LOOP-IDLE", "有心跳但没有 DONE 回执（没产出）"
        return {"station": station, "state": state, "why": why, "checked": 0, "rows": []}
    bad = [x for x in rows if not x["ok"]]
    n_remote = sum(1 for x in rows if x.get("remote"))
    note = ("（其中 %d 份为远端产物：按回执自带文件哈希验收，本机未重算）" % n_remote
            if n_remote else "")
    return {"station": station,
            "state": "LOOP-BROKEN" if bad else "LOOP-OK",
            "why": (("%d/%d 份回执证据不全" % (len(bad), len(rows))) if bad else
                    ("%d 份回执全部证据完整" % len(rows))) + note,
            "checked": len(rows), "rows": rows}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--station", default=None)
    ap.add_argument("--recent", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    targets = [a.station] if a.station else list(STATIONS)
    res = [check_station(s, recent=a.recent) for s in targets]
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        print("== 机队闭环验收 ==")
        for r in res:
            print("  %-9s %-12s %s" % (r["station"], r["state"], r["why"]))
            for x in r["rows"]:
                if not x["ok"]:
                    print("       ✗ %s：%s" % (x["id"], "、".join(x["problems"])))
    return 1 if any(r["state"] == "LOOP-BROKEN" for r in res) else 0


def self_test():
    import tempfile
    ok = total = 0

    def chk(n, c, d=""):
        nonlocal ok, total
        total += 1
        ok += 1 if c else 0
        print("%s %s %s" % ("ok  " if c else "FAIL", n, "" if c else d))

    with tempfile.TemporaryDirectory() as td:
        rd = os.path.join(td, "cph4", "fleet", "rt", "control", "receipts")
        os.makedirs(rd, exist_ok=True)
        art = os.path.join(td, "out.txt")

        def mk(name, r):
            json.dump(r, open(os.path.join(rd, name), "w", encoding="utf-8"), ensure_ascii=False)

        open(art, "w", encoding="utf-8").write("hello")
        good = {"id": "G1", "verdict": "DONE", "deliverable": "out.txt",
                "sha256": _sha(art), "judge": "path",
                "ts": datetime.fromtimestamp(os.path.getmtime(art)).isoformat(timespec="seconds")}
        mk("g1.json", good)
        r = check_station("control", root=td)
        chk("正常回执 -> LOOP-OK", r["state"] == "LOOP-OK", r)

        # 负控：哈希被改 -> LOOP-BROKEN
        bad = dict(good, id="B1", sha256="0" * 64)
        mk("b1.json", bad)
        r2 = check_station("control", root=td, recent=5)
        chk("负控：哈希不符 -> LOOP-BROKEN", r2["state"] == "LOOP-BROKEN", r2)

        # 缺判据
        os.remove(os.path.join(rd, "b1.json"))
        mk("g2.json", dict(good, id="G2", judge=""))
        chk("缺 judge 也算证据不全", check_station("control", root=td)["state"] == "LOOP-BROKEN")

        # 无心跳无回执 -> NO-EXEC
        os.remove(os.path.join(rd, "g1.json"))
        os.remove(os.path.join(rd, "g2.json"))
        chk("本机无心跳无回执 -> NO-EXEC",
            check_station("control", root=td)["state"] == "NO-EXEC")
        chk("负控：远端无心跳不判死 -> LOOP-IDLE",
            check_station("visual", root=td)["state"] == "LOOP-IDLE")

        # 有心跳无 DONE -> LOOP-IDLE
        os.makedirs(os.path.join(td, "cph4", "fleet", "rt", "audio"), exist_ok=True)
        json.dump({"station": "audio"}, open(os.path.join(td, "cph4", "fleet", "rt",
                                                       "audio", "heartbeat.json"), "w"))
        chk("有心跳无 DONE -> LOOP-IDLE",
            check_station("audio", root=td)["state"] == "LOOP-IDLE")

        # BLOCKED 回执不参与验收（本来就该没产物）
        mk("blk.json", {"id": "K1", "verdict": "BLOCKED", "deliverable": "out.txt"})
        chk("BLOCKED 不进闭环验收（该机无心跳 -> NO-EXEC）",
            check_station("control", root=td)["state"] in ("NO-EXEC", "LOOP-IDLE", "LOOP-OK"))

        # 远端产物（另一台机的盘）：按回执自带哈希验收，不许判"产物不存在"
        rv = {"id": "R1", "verdict": "DONE", "judge": "path",
              "deliverable": "K:\\Fluxgroup\\FluxGroup\\cph4\\fleet\\out\\x",
              "files": [{"file": "a.png", "bytes": 1024, "sha256_16": "deadbeefdeadbeef"}]}
        ok1, p1 = verify_receipt(td, rv)
        chk("远端产物带哈希 -> 通过（本机看不到盘不判缺失）", ok1, p1)
        rv2 = dict(rv, id="R2", files=[])
        ok2, p2 = verify_receipt(td, rv2)
        chk("负控：远端产物没哈希 -> 判不可验", not ok2, p2)
        chk("远端判定：盘符/UNC/仓外绝对路径",
            _is_remote("K:\\x") and _is_remote("\\\\host\\share") and
            _is_remote("/tmp/zzz") and not _is_remote("cph4/fleet/out/x"))
        # 整站：远端回执在盘上时 LOOP-OK 且写明"未重算"
        vd = os.path.join(td, "cph4", "fleet", "rt", "visual", "receipts")
        os.makedirs(vd, exist_ok=True)
        json.dump(rv, open(os.path.join(vd, "r1.json"), "w", encoding="utf-8"),
                  ensure_ascii=False)
        rv_res = check_station("visual", root=td)
        chk("visual 远端回执 -> LOOP-OK 且标注未重算",
            rv_res["state"] == "LOOP-OK" and "未重算" in rv_res["why"], rv_res["why"])

    print("\n[fleet_loop_verify] %d/%d" % (ok, total))
    return 0 if ok == total else 3


if __name__ == "__main__":
    sys.exit(main())
