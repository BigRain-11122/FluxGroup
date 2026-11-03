# -*- coding: utf-8 -*-
"""vb_space.py - enumerate an uploader's whole video list despite the 412 risk gate.

The space API answered 412 from this node because the request carried no buvid cookie.
Fetching buvid3/buvid4 from the fingerprint endpoint and passing them on a Credential
lifts that gate without any login.
"""
import json
import sys
import urllib.request

from bilibili_api import Credential, user, sync

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def buvid():
    req = urllib.request.Request("https://api.bilibili.com/x/frontend/finger/spi",
                                 headers={"User-Agent": UA, "Referer": "https://www.bilibili.com/"})
    with urllib.request.urlopen(req, timeout=20) as r:
        j = json.loads(r.read().decode("utf-8", "replace"))
    d = j.get("data") or {}
    return d.get("b_3"), d.get("b_4")


def main():
    mid = int(sys.argv[1])
    out = sys.argv[2]
    b3, b4 = buvid()
    cred = Credential(buvid3=b3, buvid4=b4)
    u = user.User(mid, credential=cred)
    rows = []
    for pn in range(1, 12):
        r = sync(u.get_videos(pn=pn, ps=30))
        lst = (r or {}).get("list") or {}
        vl = lst.get("vlist") or []
        if not vl:
            break
        for v in vl:
            rows.append({"bvid": v.get("bvid"), "title": v.get("title"),
                         "length": v.get("length"), "created": v.get("created"),
                         "play": v.get("play")})
        total = ((r or {}).get("page") or {}).get("count") or 0
        if len(rows) >= total:
            break
    json.dump({"mid": mid, "count": len(rows), "videos": rows},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("videos=%d buvid=%s" % (len(rows), bool(b3)))


main()