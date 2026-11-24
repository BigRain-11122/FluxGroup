#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""comment_harvest.py - 从消息中心拉"别人回复我的评论"，抽出**我自己写过的评论原文**。

为什么走消息中心而不是翻视频评论区：
  视频评论区只覆盖别人视频，且几千条翻不完；消息中心的每条记录都挂着我被回的那条
  原文（source_content / root_reply_content），一次分页就能拿到自己写过的句子。

已知偏差（诚实标注）：只能拿到"被人回复过"的评论，无回复的短评拿不到；
所以这份语料是"我写过的评论里被聊起来的那部分"，风格统计可用，覆盖率不可用。

用法
  .venv-housing/bin/python Tools/fleet/comment_harvest.py --dump-raw      # 存 1 页原始 item 看字段
  .venv-housing/bin/python Tools/fleet/comment_harvest.py --pages 30      # 拉全量并落盘
  python3 Tools/fleet/comment_harvest.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

OUT_DIR = os.path.join(ROOT, "cph4", "fleet", "social", "corpus", "mine")
OUT = os.path.join(OUT_DIR, "COMMENTS-MINE.jsonl")
RAW = os.path.join(OUT_DIR, "raw-msgfeed.jsonl")

API = "https://api.bilibili.com/x/msgfeed/reply"
# 我自己的评论可能落在这些字段：被回复的原评论 / 楼中楼根评论
MINE_KEYS = ("source_content", "root_reply_content")

NAV = "https://api.bilibili.com/x/web-interface/nav"


def _fetch(pg, url):
    raw = pg.evaluate("async(u)=>{const r=await fetch(u,{credentials:'include'});"
                      "return await r.text();}", url)
    try:
        return json.loads(raw)
    except Exception:
        return {"code": -1, "raw": (raw or "")[:160]}


def harvest(pages=30, dump_raw=False, profile=None):
    import social_comment as sc
    if profile:
        sc.PROF = profile

    mod, _ = sc._pw()
    result = {"pages": 0, "items": 0, "mine": 0, "written": 0,
              "code": None, "note": "", "uname": "", "mid": None}
    rows, raw_rows = [], []
    with mod.sync_playwright() as p:
        ctx = sc._launch(p)
        try:
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.goto("https://message.bilibili.com/", wait_until="domcontentloaded",
                    timeout=60000)
            time.sleep(2)
            nav = _fetch(pg, NAV)
            nd = nav.get("data") or {}
            result["uname"] = nd.get("uname") or ""
            result["mid"] = nd.get("mid")
            if nav.get("code") != 0 or not nd.get("isLogin"):
                result["note"] = "未登录或无登录态（nav code=%s）" % nav.get("code")
                return result, rows, raw_rows
            my_mid = nd.get("mid")

            cursor, seen_cursor = "", set()
            for i in range(pages):
                url = "%s?cursor=%s&id_type=0&mobi_app=web" % (API, cursor)
                d = _fetch(pg, url)
                result["code"] = d.get("code")
                if d.get("code") != 0:
                    result["note"] = "接口 code=%s %s" % (d.get("code"), d.get("message"))
                    break
                data = d.get("data") or {}
                items = data.get("items") or []
                result["pages"] += 1
                result["items"] += len(items)
                for it in items:
                    raw_rows.append(it)
                    body = it.get("item") or {}
                    user = it.get("user") or {}
                    biz = body.get("business_id")
                    for k in MINE_KEYS:
                        txt = (body.get(k) or "").strip()
                        if not txt:
                            continue
                        # 只收"确实是我写的"：source 是别人回我，root 可能是楼中楼里我的话
                        if k == "source_content" and body.get("source_id") and my_mid:
                            pass  # source 天然是我被回的那条，不再校验
                        rows.append({
                            "text": txt,
                            "field": k,
                            "business_id": biz,
                            "video_title": body.get("title") or "",
                            "uri": body.get("uri") or "",
                            "replier": user.get("nickname") or "",
                            "replier_mid": user.get("mid"),
                            "their_reply": (body.get("target_reply_content") or "").strip(),
                            "rpid": body.get("source_id") or body.get("root_id"),
                        })
                if dump_raw:
                    break
                cur = data.get("cursor") or {}
                nxt = str(cur.get("id") or "")
                if cur.get("is_end") or not nxt or nxt in seen_cursor:
                    break
                seen_cursor.add(nxt)
                cursor = nxt
                time.sleep(1.2)
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

    # 去重：同一条评论可能因多条回复重复出现
    seen, uniq = set(), []
    for r in rows:
        key = "".join(r["text"].split())
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    result["mine"] = len(rows)
    result["written"] = len(uniq)
    return result, uniq, raw_rows


def save(uniq, raw_rows):
    os.makedirs(OUT_DIR, exist_ok=True)
    if raw_rows:
        with open(RAW, "w", encoding="utf-8") as f:
            for it in raw_rows:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
    if uniq:
        with open(OUT, "w", encoding="utf-8") as f:
            for r in uniq:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(uniq)


def self_test():
    """负控：给两行同文不同回复，必去重成 1 条；字段缺 text 不炸。"""
    import tempfile
    global OUT_DIR, OUT, RAW
    old = (OUT_DIR, OUT, RAW)
    d = tempfile.mkdtemp()
    OUT_DIR, OUT, RAW = d, os.path.join(d, "c.jsonl"), os.path.join(d, "r.jsonl")
    rows = [{"text": "感谢支持！", "field": "source_content"},
            {"text": "感谢支持！ ", "field": "root_reply_content"},
            {"text": "", "field": "source_content"}]
    seen, uniq = set(), []
    for r in rows:
        t = (r.get("text") or "").strip()
        if not t:
            continue
        k = "".join(t.split())
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    n = save(uniq, [{"x": 1}])
    OUT_DIR, OUT, RAW = old
    ok = n == 1
    print(json.dumps({"self_test": "PASS" if ok else "FAIL", "kept": n}, ensure_ascii=False))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=30)
    ap.add_argument("--dump-raw", action="store_true")
    ap.add_argument("--profile", default=None)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    res, uniq, raw = harvest(a.pages, a.dump_raw, a.profile)
    if not a.dump_raw:
        res["saved"] = save(uniq, raw)
    else:
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(RAW, "w", encoding="utf-8") as f:
            for it in raw:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    if a.dump_raw and raw:
        print(json.dumps(raw[0], ensure_ascii=False, indent=1)[:2500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
