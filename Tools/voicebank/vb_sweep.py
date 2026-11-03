# -*- coding: utf-8 -*-
"""vb_sweep.py - enumerate one uploader's videos via keyword sweep (412-safe).

The space API is blocked for this node even with buvid cookies, so we sweep titles the
channel actually uses and keep only rows whose mid matches.
"""
import json
import sys

from bilibili_api import search, sync

MID = int(sys.argv[1])
OUT = sys.argv[2]
KWS = sys.argv[3].split(",")

rows, seen = {}, set()
for kw in KWS:
    for page in (1, 2, 3):
        try:
            r = sync(search.search_by_type(kw, search_type=search.SearchObjectType.VIDEO, page=page))
        except Exception as e:
            print("kw=%s page=%d ERR %r" % (kw, page, e))
            break
        res = (r or {}).get("result") or []
        if not res:
            break
        new = 0
        for v in res:
            if int(v.get("mid") or 0) != MID:
                continue
            bv = v.get("bvid")
            if not bv or bv in seen:
                continue
            seen.add(bv)
            new += 1
            rows[bv] = {"bvid": bv, "title": (v.get("title") or "").replace(
                '<em class="keyword">', "").replace("</em>", ""),
                "length": v.get("duration"), "play": v.get("play"),
                "created": v.get("pubdate")}
        print("kw=%s p%d new=%d total=%d" % (kw, page, new, len(rows)), flush=True)

json.dump({"mid": MID, "count": len(rows), "videos": list(rows.values())},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("TOTAL", len(rows))