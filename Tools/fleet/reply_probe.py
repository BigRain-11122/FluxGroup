#!/usr/bin/env python3
"""reply_probe.py — 用 B 站新版评论接口（wbi/main, mode=2 仅按时间）精确找一条自己的评论。

为什么另起一条路（2026-11-20 调研）：
- 现有复核走旧接口 `/x/v2/reply?pn&sort=0/2` 只翻 3 页；热门视频几千条，必然漏。
- 官方文档（bilibili-API-collect）：`mode` 0/3=仅热度、1=热度+时间、**2=仅按时间**，
  分页要 `pagination_str={"offset":...}`，且接口需 wbi 签名（w_rid/wts）。
- 百科"评论审核"条：AI 复审平均 ~7 分钟、最长约 10 分钟；40 秒复核必然假否。
- 2025-03 起折叠评论被挪到**最末页**，"前几页查不到"≠被删，但对曝光而言等价于不可见。

用法：python3 Tools/fleet/reply_probe.py --aid 30870810 --rpid 324548766368 [--pages 5]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

MIXIN_TAB = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
             33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
             61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62,
             11, 36, 20, 34, 44, 52]


def mixin_key(img_url: str, sub_url: str) -> str:
    orig = os.path.basename(img_url).split(".")[0] + os.path.basename(sub_url).split(".")[0]
    return "".join(orig[i] for i in MIXIN_TAB)[:32]


def sign(params: dict, mix: str) -> str:
    params = dict(params, wts=int(time.time()))
    params.pop("w_rid", None)
    q = urllib.parse.urlencode(sorted(params.items()))
    params["w_rid"] = hashlib.md5((q + mix).encode()).hexdigest()
    return urllib.parse.urlencode(sorted(params.items()))


NAV = "https://api.bilibili.com/x/web-interface/nav"
MAIN = "https://api.bilibili.com/x/v2/reply/wbi/main"


def fetch(pg, url):
    raw = pg.evaluate("async(u)=>{const r=await fetch(u,{credentials:'include'});"
                      "return await r.text();}", url)
    try:
        return json.loads(raw)
    except Exception:
        return {"code": -1, "raw": (raw or "")[:120]}


def probe(aid, rpid, pages=5, mode=2, since=None):
    """since=发帖时刻(epoch)。按时间倒序翻到"最早一条已早于发帖时刻"即可停：
    那时我们这条若公开必然已扫过；扫不到 = 折叠到末页或仅自己可见（对曝光等价于不可见）。"""
    import social_comment as sc
    mod, _ = sc._pw()
    out = {"aid": aid, "rpid": str(rpid), "mode": mode, "pages": 0,
           "found": None, "first_page_ctimes": [], "oldest_ctime": None,
           "covered_since": False, "note": ""}
    with mod.sync_playwright() as p:
        ctx = sc._launch(p)
        try:
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.goto("https://www.bilibili.com/video/av%s" % aid,
                    wait_until="domcontentloaded", timeout=60000)
            time.sleep(2)
            nav = fetch(pg, NAV)
            wbi = ((nav.get("data") or {}).get("wbi_img") or {})
            img, sub = wbi.get("img_url") or "", wbi.get("sub_url") or ""
            if not img or not sub:
                out["note"] = "拿不到 wbi 密钥（未登录？nav code=%s）" % nav.get("code")
                return out
            mix = mixin_key(img, sub)
            wts = int(time.time()) + 60
            offset = ""
            for i in range(pages):
                params = {"oid": aid, "type": 1, "mode": mode, "plat": 1,
                          "web_location": 1315875, "wts": wts}
                if offset:
                    params["pagination_str"] = '{"offset":"%s"}' % offset.replace('"', '\\"')
                url = MAIN + "?" + sign(params, mix)
                d = fetch(pg, url)
                if d.get("code") not in (0, None):
                    out["note"] = "接口 code=%s %s" % (d.get("code"), d.get("message"))
                    return out
                data = d.get("data") or {}
                reps = data.get("replies") or []
                out["pages"] += 1
                ctimes = [r.get("ctime") or 0 for r in reps]
                if i == 0:
                    out["first_page_ctimes"] = ctimes[:5]
                if ctimes:
                    out["oldest_ctime"] = min(ctimes)
                if str(rpid) in [str(r.get("rpid")) for r in reps]:
                    out["found"] = True
                    out["note"] = "第 %d 页找到（mode=%d 时间序）" % (i + 1, mode)
                    return out
                if since and ctimes and min(ctimes) < since:
                    out["covered_since"] = True
                    out["found"] = False
                    out["note"] = ("已按时间翻到早于发帖时刻（%d 页），仍未出现 → "
                                   "折叠到末页或仅自己可见" % out["pages"])
                    return out
                cur = data.get("cursor") or {}
                nxt = cur.get("pagination_reply") or {}
                offset = nxt.get("next_offset") or ""
                if not offset or cur.get("is_end"):
                    out["found"] = False
                    out["note"] = "已到末页（共 %d 页）仍未出现" % out["pages"]
                    return out
            out["found"] = False
            out["note"] = "翻了 %d 页仍未覆盖到发帖时刻，**结论不成立**（需加大页数）" % out["pages"]
        finally:
            try:
                ctx.close()
            except Exception:
                pass
            try:
                import social_collect as _sc
                _sc.release_profile_lock(sc.PROF)
            except Exception:
                pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aid", required=True)
    ap.add_argument("--rpid", required=True)
    ap.add_argument("--pages", type=int, default=5)
    ap.add_argument("--mode", type=int, default=2)
    ap.add_argument("--since", type=str, default=None,
                    help="发帖时刻（2026-11-20T12:41:43 或 epoch 秒）；给了就能判'扫过没扫过'")
    a = ap.parse_args()
    since = None
    if a.since:
        try:
            since = int(a.since)
        except ValueError:
            from datetime import datetime
            since = int(datetime.fromisoformat(a.since).timestamp())
    print(json.dumps(probe(a.aid, a.rpid, a.pages, a.mode, since), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
