# -*- coding: utf-8 -*-
"""fact_check.py - 审查情报本身是否可信（不是审查产物，是审查结论的来源）。

Why: OSS 雷达自己会标「⚠星数超 10 万需人工核实」，但没人核。情报不可信 → 选错工具 →
整条线白干。这台机器只做一件事：把雷达里越界的数字拿去 GitHub API 对一遍，差异超阈值
判 STALE，对得上判 VERIFIED，并把回执写回库存，下次不用重复核。

Fail-soft by design: 无网/限流一律记 UNVERIFIED，绝不因此判「假」。
Usage: fact_check.py [--limit 15] [--stale-pct 10]
"""
import argparse
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STOCK = os.path.join(FLEET, "oss", "STOCKPILE.json")
OUT = os.path.join(FLEET, "state", "fact-check.json")
BIG_STARS = 100000


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return d


def api(full_name, timeout=12):
    url = "https://api.github.com/repos/" + full_name
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "fluxgroup-fact-check",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except Exception as e:
        return {"_error": str(e)[:120]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--stale-pct", type=float, default=10.0)
    a = ap.parse_args()

    d = jload(STOCK, {})
    items = (d or {}).get("items") or {}
    todo = []
    for k, v in items.items():
        if not isinstance(v, dict):
            continue
        stars = int(v.get("stars") or 0)
        need = stars >= BIG_STARS or "人工核实" in str(v.get("why") or "")
        if need and not v.get("verified_at"):
            todo.append((k, v))
    todo = todo[:a.limit]

    res, stale, verified, unknown = [], 0, 0, 0
    for k, v in todo:
        meta = api(k)
        if meta.get("_error"):
            unknown += 1
            res.append({"repo": k, "verdict": "UNVERIFIED", "err": meta["_error"]})
            continue
        want = int(v.get("stars") or 0)
        got = int(meta.get("stargazers_count") or 0)
        lic = ((meta.get("license") or {}) or {}).get("spdx_id") or ""
        pushed = str(meta.get("pushed_at") or "")
        pct = (abs(got - want) / want * 100.0) if want else 0.0
        ok = bool(got) and pct <= a.stale_pct
        if ok:
            verified += 1
        else:
            stale += 1
        res.append({"repo": k, "verdict": "VERIFIED" if ok else "STALE",
                    "stars_cached": want, "stars_api": got, "drift_pct": round(pct, 1),
                    "license_api": lic, "pushed_api": pushed})
        # 回写库存：核实过的打标，避免下次重核
        v["verified_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        v["verify"] = "VERIFIED" if ok else "STALE"
        v["stars_api"] = got

    if todo and not unknown:
        try:
            d["items"] = items
            with open(STOCK, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=1)
        except Exception:
            pass

    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "checked": len(todo),
           "verified": verified, "stale": stale, "unverified": unknown, "results": res}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("checked", "verified", "stale", "unverified")},
                     ensure_ascii=False))
    return 0 if not stale else 1


if __name__ == "__main__":
    sys.exit(main())