# -*- coding: utf-8 -*-
"""vb_discover.py - turn a voice-bank bucket into a candidate BV list (CPU-only, any node).

Why this exists: vb_worker.py builds a corpus from BV ids it is *given*, but nothing in
the fleet produced those ids, so the whole voice-bank line sat blocked on "nobody assigned
BV numbers" (bm-c readiness receipt, 2026-10-31). This is that missing first step: search
Bilibili for long-form, speech-heavy material per bucket and write a candidate list a
human/brain can approve before any download happens.

Design rules:
  * no download here - discovery only, so a wrong bucket costs no bandwidth;
  * every candidate keeps its measured facts (duration / play count / uploader), so the
    approval decision is made on evidence, not on titles;
  * output is a plain JSON + the `jobs_<voice>.txt` side file vb_worker already accepts;
  * if bilibili_api is missing or the network is blocked, exit 0 with status=BLOCKED and
    a reason, because a discovery failure must never look like "no candidates exist".

Usage (on a node that has bilibili-api-python; bm-b / bm-c):
  python Tools/voicebank/vb_discover.py --voice v01 --keywords 播客,有声书 --pages 1 \\
      --out cph4/fleet/voicebank/discover
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

# Speech-heavy buckets from VOICE-BANK-PLAN §三. Duration window is the "long enough to be
# worth denoising" band: under 4 min a single video rarely yields 8 min of clean speech,
# over 60 min is usually a compilation with many speakers (fails the single-speaker gate).
MIN_S, MAX_S = 240, 3600


def discover(keywords, pages=1, per_page=20):
    """Return (candidates, status, note). Never raises: discovery must report, not crash."""
    try:
        from bilibili_api import search, sync
    except Exception as e:
        return [], "BLOCKED", "bilibili_api not installed: %s" % str(e)[:120]
    out = []
    for kw in keywords:
        for page in range(1, pages + 1):
            try:
                res = sync(search.search_by_type(
                    kw, search_type=search.SearchObjectType.VIDEO,
                    page=page, page_size=per_page))
            except Exception as e:
                return out, "PARTIAL", "search failed for '%s': %s" % (kw, str(e)[:120])
            for it in (res or {}).get("result") or []:
                dur = str(it.get("duration") or "")
                try:
                    m, s = dur.split(":")[:2]
                    secs = int(m) * 60 + int(s)
                except Exception:
                    secs = 0
                if not (MIN_S <= secs <= MAX_S):
                    continue
                out.append({
                    "bvid": it.get("bvid") or "",
                    "title": (it.get("title") or "").replace("<em class=\"keyword\">", "").replace("</em>", ""),
                    "seconds": secs,
                    "play": it.get("play"),
                    "author": it.get("author"),
                    "keyword": kw,
                })
    return out, "OK", "%d candidates in %d-%ds band" % (len(out), MIN_S, MAX_S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True, help="bucket id, e.g. v01")
    ap.add_argument("--keywords", required=True, help="comma separated Chinese keywords")
    ap.add_argument("--pages", type=int, default=1)
    ap.add_argument("--out", default=os.path.join(ROOT, "cph4", "fleet", "voicebank", "discover"))
    a = ap.parse_args()

    kws = [k.strip() for k in a.keywords.split(",") if k.strip()]
    cands, status, note = discover(kws, a.pages)
    os.makedirs(a.out, exist_ok=True)
    stamp = datetime.now().isoformat(timespec="seconds")

    # de-dup by bvid, keep the first (highest ranked) occurrence
    seen, uniq = set(), []
    for c in cands:
        if c["bvid"] and c["bvid"] not in seen:
            seen.add(c["bvid"])
            uniq.append(c)

    payload = {"voice": a.voice, "keywords": kws, "status": status, "note": note,
               "generated_at": stamp, "count": len(uniq), "candidates": uniq}
    jpath = os.path.join(a.out, "discover_%s.json" % a.voice)
    with open(jpath, "w", encoding="utf-8", newline="") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    jobs = os.path.join(a.out, "jobs_%s.txt" % a.voice)
    with open(jobs, "w", encoding="utf-8", newline="") as f:
        for c in uniq:
            f.write("%s\t%d\t%s\n" % (c["bvid"], c["seconds"], c["title"][:80]))

    print(json.dumps({"voice": a.voice, "status": status, "count": len(uniq),
                      "json": os.path.relpath(jpath, ROOT),
                      "jobs": os.path.relpath(jobs, ROOT), "note": note},
                     ensure_ascii=False))
    # BLOCKED is an environment fact, not a tool failure: exit 0 so the fleet does not
    # retry it in a loop, but the receipt still says "no candidates were evaluated".
    return 0


if __name__ == "__main__":
    sys.exit(main())