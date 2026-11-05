#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset_pull.py - 执行机自取素材（不依赖主控分发）。

契约：卡片可带 inputs: [{rel, root, sha256, dest}]，执行机先拉再跑。
  - 本地已有且 sha 一致 → SKIP
  - 取不到 → rc=3 + E-BLOCKED-INPUT（合法缺料，不消耗三次失败预算）
  - 回执写 cph4/fleet/queue-receipts/asset-pull-<card>.json

用法：
  python3 Tools/fleet/asset_pull.py --rel store/00/x.jpg [--dest media/inbox/x.jpg] [--sha256 ...]
  python3 Tools/fleet/asset_pull.py --card <card_id>
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RECEIPTS = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
DEFAULT_BASE = os.environ.get("FLUX_ASSET_BASE") or "http://100.75.133.10:8790"


def token():
    t = os.environ.get("FLUX_ASSET_TOKEN")
    if t:
        return t.strip()
    p = os.path.expanduser("~/.fluxgroup-asset-token")
    return open(p).read().strip() if os.path.exists(p) else ""


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def pull_one(item, base, timeout=180):
    root = item.get("root", "assets")
    rel = str(item.get("rel", "")).lstrip("/")
    if not rel:
        return False, "缺 rel"
    dest = item.get("dest") or os.path.join("media", "inbox", os.path.basename(rel))
    dest_abs = dest if os.path.isabs(dest) else os.path.join(ROOT, dest)
    want = (item.get("sha256") or "").lower()
    if os.path.isfile(dest_abs):
        got = sha256(dest_abs)
        if not want or got == want:
            return True, "SKIP 已在本地(%d bytes)" % os.path.getsize(dest_abs)
        print("[pull] 本地 sha 不符，重拉 %s" % dest)
    url = "%s/%s/%s" % (base.rstrip("/"), root, rel)
    os.makedirs(os.path.dirname(dest_abs) or ".", exist_ok=True)
    tmp = dest_abs + ".part"
    try:
        req = urllib.request.Request(url)
        tok = token()
        if tok:
            req.add_header("X-Flux-Token", tok)
        with urllib.request.urlopen(req, timeout=timeout) as r, open(tmp, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
    except urllib.error.HTTPError as e:
        if os.path.exists(tmp):
            os.remove(tmp)
        return False, "HTTP %s %s" % (e.code, url)
    except Exception as e:
        if os.path.exists(tmp):
            os.remove(tmp)
        return False, "不可达 %s (%s)" % (url, str(e)[:60])
    got = sha256(tmp)
    if want and got != want:
        os.remove(tmp)
        return False, "sha 不符 want=%s got=%s" % (want[:12], got[:12])
    os.replace(tmp, dest_abs)
    return True, "GET %d bytes sha=%s" % (os.path.getsize(dest_abs), got[:12])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rel")
    ap.add_argument("--root", default="assets")
    ap.add_argument("--dest")
    ap.add_argument("--sha256")
    ap.add_argument("--card")
    ap.add_argument("--base", default=DEFAULT_BASE)
    a = ap.parse_args(argv)

    items = []
    if a.card:
        q = os.path.join(ROOT, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
        found = None
        if os.path.isfile(q):
            with open(q, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                    except Exception:
                        continue
                    if d.get("id") == a.card:
                        found = d
                        break
        if not found:
            print("[pull] 队列里没有卡 %s（rc=2）" % a.card)
            return 2
        items = found.get("inputs") or []
        if not items:
            print("[pull] 卡 %s 无 inputs（rc=0，无需取料）" % a.card)
            return 0
    elif a.rel:
        it = {"rel": a.rel, "root": a.root}
        if a.dest:
            it["dest"] = a.dest
        if a.sha256:
            it["sha256"] = a.sha256
        items = [it]
    else:
        print("[pull] 需要 --rel 或 --card")
        return 2

    ok_n, bad = 0, []
    for it in items:
        ok, why = pull_one(it, a.base)
        print("[pull] %s -> %s" % (it.get("rel"), why))
        if ok:
            ok_n += 1
        else:
            bad.append({"rel": it.get("rel"), "why": why})

    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": "asset-pull", "card": a.card,
           "requested": len(items), "ok": ok_n, "failed": bad, "base": a.base,
           "verdict": "PASS" if not bad else "BLOCKED", "rc": 0 if not bad else 3,
           "error_class": None if not bad else "E-BLOCKED-INPUT"}
    os.makedirs(RECEIPTS, exist_ok=True)
    name = a.card or ("adhoc-%d" % int(time.time()))
    with open(os.path.join(RECEIPTS, "asset-pull-%s.json" % name), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1, sort_keys=True)
    if bad:
        print("[pull] BLOCKED：%d 项取不到（E-BLOCKED-INPUT，不计失败次数）" % len(bad))
        return 3
    print("[pull] PASS：%d 项就位" % ok_n)
    return 0


if __name__ == "__main__":
    sys.exit(main())