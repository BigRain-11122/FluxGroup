#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_sync_probe.py — 机队同步与条线新鲜度探针（每轮自动报，不靠人看台账）。

CEO 2026-11-25：「各自管理自己的条线，能共享的要互相赋能，信息同步要非常好。」
同步好不好不能靠感觉，必须每轮算一次并落屏。

六项检查（每项都能被负控推翻）：
  1 softlinks   三条软链（gzh / accounts / BigLoom 根）是否解析得到
  2 lanes       各机车道文件最后更新距今几小时（过期=同步断）
  3 asks        问询卡：总数 / 有回执 / 逾期（>72h 未答 → BLOCKED-JUDGE）
  4 seats       席表完整性：每席必须有 duty/out/judge/cad；带数字的席必须 rule-only
  5 audit       体检硬项：断链、失效引用（其余为"债"，不算硬红）
  6 corpora     两本账行数（风格/产业/通用），0 行即异常

用法：
  python3 Tools/fleet/fleet_sync_probe.py --status     # 落 SYNC-STATUS.md 并打印
  python3 Tools/fleet/fleet_sync_probe.py --json       # 只出机读
  python3 Tools/fleet/fleet_sync_probe.py --self-test
退出码：0 无硬红 / 1 有硬红 / 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
GZH = os.path.join(ROOT, "cph4", "fleet", "social", "gzh")
BIGLOOM = os.path.expanduser("~/BigLoom")
OUT_MD = os.path.join(FLEET, "SYNC-STATUS.md")
OUT_JSON = os.path.join(ROOT, "cph4", "fleet", "state", "fleet-sync.json")
ASK_PREFIX = "ASK-"
OVERDUE_H = 72


def _now():
    return datetime.now()


def _j(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:                                   # noqa: BLE001
        return default


def _rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out


def check_softlinks():
    targets = {
        "gzh": os.path.join(ROOT, "cph4", "fleet", "social", "gzh"),
        "accounts": os.path.join(ROOT, "cph4", "fleet", "social", "ACCOUNTS-REGISTRY-v1.json"),
        "bigloom_root": BIGLOOM,
    }
    out = {}
    for k, p in targets.items():
        out[k] = {"path": p, "exists": os.path.exists(p),
                  "is_link": os.path.islink(p),
                  "target": os.readlink(p) if os.path.islink(p) else ""}
    bad = [k for k, v in out.items() if not v["exists"]]
    return out, bad


def check_lanes():
    d = os.path.join(FLEET, "lanes")
    rows = []
    if not os.path.isdir(d):
        return rows, "无 lanes 目录"
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".json"):
            continue
        p = os.path.join(d, fn)
        try:
            age_h = (_now() - datetime.fromtimestamp(os.path.getmtime(p))).total_seconds() / 3600
        except OSError:
            continue
        rows.append({"node": fn[:-5], "age_h": round(age_h, 1),
                     "stale": age_h > 24})
    return rows, ""


def check_asks():
    cards = []
    for fn in sorted(os.listdir(FLEET)):
        if fn.startswith(ASK_PREFIX) and fn.endswith(".jsonl"):
            cards += _rows(os.path.join(FLEET, fn))
    done = os.path.join(FLEET, "order-bus", "receipts")
    have = set()
    if os.path.isdir(done):
        for fn in os.listdir(done):
            if fn.endswith(".json"):
                j = _j(os.path.join(done, fn), {}) or {}
                have.add(j.get("_id") or fn[:-5])
    open_, overdue = [], []
    for c in cards:
        cid = c.get("_id") or ""
        answered = any(cid in h or h in cid for h in have) if have else False
        if answered:
            continue
        open_.append(cid)
        try:
            t = datetime.fromisoformat(c.get("added") or "")
            if (_now() - t).total_seconds() / 3600 > OVERDUE_H:
                overdue.append(cid)
        except ValueError:
            pass
    return {"total": len(cards), "answered": len(cards) - len(open_),
            "open": len(open_), "overdue": overdue, "open_ids": open_[:8]}


def check_seats():
    d = _j(os.path.join(FLEET, "AGENT-TEAMS-v1.json"), {}) or {}
    missing, num_bad, total = [], [], 0
    for station, seats in (d.get("teams") or {}).items():
        for s in seats:
            total += 1
            sid = s.get("id") or "?"
            for k in ("duty", "out", "judge", "cad"):
                # 按键是否存在判断，不用真假值：`out={}` / `judge={}` 是合法的
                # （2026-11-25 自检抓到，原本 {} 会被当成"缺字段"报假红）
                if k not in s or s.get(k) in (None, ""):
                    missing.append("%s/%s 缺 %s" % (station, sid, k))
            if s.get("numbers") == "rule-only" and not s.get("facts_cmd"):
                num_bad.append("%s/%s 标了 rule-only 却没给 facts_cmd" % (station, sid))
    return {"total": total, "missing": missing, "numbers_unbacked": num_bad}


def check_audit():
    a = _j(os.path.join(FLEET, "REPO-AUDIT.json"), {}) or {}
    s = a.get("summary") or {}
    if not s:
        return {"ran": False, "hard": None}
    hard = (s.get("dangling_link", 0) + s.get("stale_ref", 0))
    return {"ran": True, "hard": hard, "ts": a.get("ts"),
            "scanned": a.get("scanned_files"),
            "soft": {"orphan_stale": s.get("orphan_stale"),
                     "abs_path": s.get("abs_path"),
                     "duplicates": s.get("duplicates")}}


def check_corpora():
    def n(p):
        try:
            return sum(1 for l in open(p, encoding="utf-8") if l.strip())
        except FileNotFoundError:
            return -1
    return {"style": n(os.path.join(BIGLOOM, "gzh", "ARTICLES.jsonl")),
            "industry": n(os.path.join(BIGLOOM, "gzh", "ARTICLES-INDUSTRY.jsonl")),
            "generic": n(os.path.join(BIGLOOM, "collect", "ARTICLES-GENERIC.jsonl"))}


def status(verbose=True):
    links, bad_links = check_softlinks()
    lanes, lanes_why = check_lanes()
    asks = check_asks()
    seats = check_seats()
    audit = check_audit()
    corp = check_corpora()
    hard = []
    if bad_links:
        hard.append("软链断 %d 条：%s" % (len(bad_links), ",".join(bad_links)))
    if asks["overdue"]:
        hard.append("问询卡逾期 %d 张（>72h 无回执）" % len(asks["overdue"]))
    if seats["missing"]:
        hard.append("席表缺字段 %d 处" % len(seats["missing"]))
    if seats["numbers_unbacked"]:
        hard.append("数字席无据 %d 处" % len(seats["numbers_unbacked"]))
    if audit.get("ran") and (audit.get("hard") or 0) > 0:
        hard.append("体检硬项 %d 条（断链/失效引用）" % audit["hard"])
    if any(v <= 0 for v in (corp["style"], corp["industry"])):
        hard.append("语料两本账有 0 行：%s" % corp)
    res = {"ts": _now().isoformat(timespec="seconds"), "hard": hard,
           "softlinks": links, "lanes": lanes, "lanes_why": lanes_why,
           "asks": asks, "seats": seats, "audit": audit, "corpora": corp}
    if verbose:
        os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
        json.dump(res, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        open(OUT_MD, "w", encoding="utf-8").write(render(res))
        print("[sync] %s｜硬红 %d" % (res["ts"], len(hard)))
        for h in hard:
            print("   硬红：%s" % h)
    return res


def render(r):
    L = ["# 机队同步状态", "", "> 由 `Tools/fleet/fleet_sync_probe.py --status` 每轮生成，可复算。",
         "", "- 时间：%s" % r["ts"],
         "- **硬红 %d 条**%s" % (len(r["hard"]), "" if not r["hard"] else "（见下）"), ""]
    if r["hard"]:
        L += ["## 硬红", ""] + ["- %s" % h for h in r["hard"]] + [""]
    L += ["## 软链", "", "| 链 | 存在 | 类型 | 目标 |", "|---|---|---|---|"]
    for k, v in r["softlinks"].items():
        L.append("| %s | %s | %s | `%s` |" % (k, "✅" if v["exists"] else "❌",
                                              "symlink" if v["is_link"] else "实体", v["target"]))
    L += ["", "## 各机车道新鲜度", ""]
    if not r["lanes"]:
        L.append("（无车道文件：%s）" % (r["lanes_why"] or "-"))
    else:
        L += ["| 机 | 距今(小时) | 状态 |", "|---|---|---|"]
        for x in r["lanes"]:
            L.append("| %s | %s | %s |" % (x["node"], x["age_h"], "过期" if x["stale"] else "新"))
    a = r["asks"]
    L += ["", "## 问询与回执", "",
          "- 卡总数 %d｜已答 %d｜未答 %d｜逾期 %d" % (a["total"], a["answered"], a["open"], len(a["overdue"]))]
    if a["overdue"]:
        L.append("- 逾期（>72h，须记 BLOCKED-JUDGE）：%s" % "、".join(a["overdue"][:6]))
    s = r["seats"]
    L += ["", "## 席位", "", "- 总席 %d" % s["total"]]
    for m in s["missing"][:6]:
        L.append("- 缺字段：%s" % m)
    for m in s["numbers_unbacked"][:6]:
        L.append("- 数字无据：%s" % m)
    au = r["audit"]
    L += ["", "## 全仓体检", ""]
    if not au.get("ran"):
        L.append("（还没有 REPO-AUDIT.json，先跑 `python3 Tools/repo_audit.py --scan`）")
    else:
        L.append("- 扫 %s 个文件｜硬项 %s｜零引用(过时) %s｜绝对路径 %s｜重复 %s"
                 % (au.get("scanned"), au.get("hard"), au["soft"]["orphan_stale"],
                    au["soft"]["abs_path"], au["soft"]["duplicates"]))
    c = r["corpora"]
    L += ["", "## 两本账", "",
          "- 风格 %d 行｜产业 %d 行｜通用 %d 行" % (c["style"], c["industry"], c["generic"]), ""]
    return "\n".join(L)


# ---------------- 自检 ----------------

def self_test():
    import shutil
    import tempfile
    cases = []
    d = tempfile.mkdtemp(prefix="sync-")
    saved = (globals()["ROOT"], globals()["FLEET"], globals()["GZH"],
             globals()["BIGLOOM"], globals()["OUT_MD"], globals()["OUT_JSON"])
    try:
        os.makedirs(os.path.join(d, "cph4/fleet/social/gzh"), exist_ok=True)
        os.makedirs(os.path.join(d, "cph4/fleet/lanes"), exist_ok=True)
        os.makedirs(os.path.join(d, "cph4/fleet/order-bus/receipts"), exist_ok=True)
        os.makedirs(os.path.join(d, "cph4/fleet/state"), exist_ok=True)
        os.makedirs(os.path.join(d, "bl/gzh"), exist_ok=True)
        os.makedirs(os.path.join(d, "bl/collect"), exist_ok=True)
        globals()["ROOT"] = d
        globals()["FLEET"] = os.path.join(d, "cph4/fleet")
        globals()["GZH"] = os.path.join(d, "cph4/fleet/social/gzh")
        globals()["BIGLOOM"] = os.path.join(d, "bl")
        globals()["OUT_MD"] = os.path.join(d, "cph4/fleet/SYNC-STATUS.md")
        globals()["OUT_JSON"] = os.path.join(d, "cph4/fleet/state/fleet-sync.json")

        # 语料两本账
        open(os.path.join(d, "bl/gzh/ARTICLES.jsonl"), "w").write('{"a":1}\n')
        open(os.path.join(d, "bl/gzh/ARTICLES-INDUSTRY.jsonl"), "w").write('{"a":1}\n{"b":2}\n')
        open(os.path.join(d, "bl/collect/ARTICLES-GENERIC.jsonl"), "w").write('{"a":1}\n')
        # 席表：一席完整 + 一席缺 cad + 一席 rule-only 无 facts_cmd
        json.dump({"teams": {"control": [
            {"id": "OK", "duty": "d", "out": {}, "judge": {}, "cad": "每轮"},
            {"id": "MISS", "duty": "d", "out": {}, "judge": {}},
            {"id": "NUM", "duty": "d", "out": {}, "judge": {}, "cad": "每轮",
             "numbers": "rule-only"}]}},
            open(os.path.join(d, "cph4/fleet/AGENT-TEAMS-v1.json"), "w"))
        # 问询卡：一张已答 + 一张逾期未答
        now = datetime.now().isoformat(timespec="seconds")
        old = (datetime.now().replace(year=2020)).isoformat(timespec="seconds")
        rows = [{"_id": "ASK-X-01", "added": now}, {"_id": "ASK-X-02", "added": old}]
        open(os.path.join(d, "cph4/fleet/ASK-X-20260101.jsonl"), "w").write(
            "\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n")
        json.dump({"_id": "ASK-X-01", "verdict": "keep"},
                  open(os.path.join(d, "cph4/fleet/order-bus/receipts/ASK-X-01.json"), "w"))

        r = status(verbose=False)
        cases.append(("软链缺失被抓为硬红", any("软链断" in h for h in r["hard"])))
        cases.append(("逾期卡被抓到", "ASK-X-02" in r["asks"]["overdue"]))
        cases.append(("负控[已答卡] 不许算逾期", "ASK-X-01" not in r["asks"]["overdue"]))
        cases.append(("席表缺 cad 被抓到", any("缺 cad" in m for m in r["seats"]["missing"])))
        cases.append(("数字席无 facts_cmd 被抓到", len(r["seats"]["numbers_unbacked"]) == 1))
        cases.append(("负控[完整席] 不许报缺",
                      not any("OK 缺" in m for m in r["seats"]["missing"])))
        cases.append(("语料行数读对", r["corpora"]["industry"] == 2))
        cases.append(("没有体检文件时不硬报红", r["audit"]["ran"] is False))

        # 负控：把语料清空，必须报硬红
        open(os.path.join(d, "bl/gzh/ARTICLES.jsonl"), "w").close()
        r2 = status(verbose=False)
        cases.append(("负控[语料 0 行] 必须硬红", any("语料两本账" in h for h in r2["hard"])))
    finally:
        (globals()["ROOT"], globals()["FLEET"], globals()["GZH"],
         globals()["BIGLOOM"], globals()["OUT_MD"], globals()["OUT_JSON"]) = saved
        shutil.rmtree(d, ignore_errors=True)

    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", n))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.json:
        print(json.dumps(status(verbose=False), ensure_ascii=False, indent=1))
        return 0
    r = status(verbose=True)
    return 1 if r["hard"] else 0


if __name__ == "__main__":
    sys.exit(main())
