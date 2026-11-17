#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_douyin.py - 抖音企业号只读接入（评论拉取），写行为在代码层就不存在。

CEO 2026-11-17 两条决定，这文件是它的落地：
  * 先接抖音企业号 → 走开放平台官方接口（企业号认证 + `video.comment` 权限）
  * 写行为全部只出草稿 → **本工具不实现任何发送/回复接口调用**（不是靠自觉，
    是真的没有那条代码路径）。草稿由 social_drafts 出，人工点发。

凭据（都不入库）：`~/.fluxgroup/douyin.json` 或环境变量
  {"client_key":"...","client_secret":"...","open_id":"...","access_token":"...","expires_at":epoch}
没有凭据 → rc=2 明确报"未授权"，**绝不假跑**（假绿比缺件更糟）。

已核接口（来自官方文档）：
  GET /video/comment/list/        评论列表      （scope video.comment，企业号）
  GET /video/comment/reply/list/  评论回复列表
  POST /video/comment/reply/      回复评论   ← 本工具**不调用**（CEO 令）
  POST /video/comment/top/        置顶评论   ← 本工具**不调用**
待核（未获文档确证，一律拒绝执行而不是猜路径）：
  私信列表/群消息/数据分析

Usage:
  python3 Tools/fleet/social_douyin.py --check
  python3 Tools/fleet/social_douyin.py --pull comments --item-id <视频ID> --out <dir>
  python3 Tools/fleet/social_douyin.py --self-test
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CRED = os.path.join(os.path.expanduser("~"), ".fluxgroup", "douyin.json")
BASE = "https://open.douyin.com"
COMMENT_LIST = "/video/comment/list/"


def load_cred(path=CRED):
    """凭据：env 优先，其次文件。返回 (cred, 缺失字段列表)。"""
    c = {}
    if os.path.exists(path):
        try:
            c = json.load(open(path, encoding="utf-8"))
        except Exception:
            c = {}
    for k, env in (("client_key", "DOUYIN_CLIENT_KEY"), ("client_secret", "DOUYIN_CLIENT_SECRET"),
                   ("open_id", "DOUYIN_OPEN_ID"), ("access_token", "DOUYIN_ACCESS_TOKEN")):
        if not c.get(k) and os.environ.get(env):
            c[k] = os.environ[env]
    need = [k for k in ("client_key", "client_secret", "open_id", "access_token") if not c.get(k)]
    return c, need


def http_json(url, params=None, timeout=20):
    q = ("?" + urllib.parse.urlencode(params)) if params else ""
    req = urllib.request.Request(url + q, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def pull_comments(cred, item_id, out_path, max_pages=5, count=50, fetch=None):
    """拉评论列表 → raw jsonl（ingest 的输入格式）。

    fetch 可注入（自检用假数据，不联网）。分页按 cursor 推进，遇到 has_more=false 停。
    """
    fetch = fetch or http_json
    rows, cursor, pages = [], 0, 0
    while pages < max_pages:
        d = fetch(BASE + COMMENT_LIST, {
            "open_id": cred.get("open_id"), "access_token": cred.get("access_token"),
            "item_id": item_id, "cursor": cursor, "count": count})
        data = (d.get("data") or {})
        lst = data.get("list") or []
        for it in lst:
            rows.append({
                "id": str(it.get("comment_id") or it.get("cid") or ""),
                "author": ((it.get("user") or {}).get("nickname") if isinstance(it.get("user"), dict)
                           else it.get("nickname")),
                "text": it.get("content") or it.get("text") or "",
                "thread": item_id,
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })
        pages += 1
        if not data.get("has_more"):
            break
        cursor = data.get("cursor") or (cursor + count)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return rows


def self_test():
    cases = []
    tmp = os.path.join(ROOT, ".codely-cli", "tmp", "douyin-selftest")
    os.makedirs(tmp, exist_ok=True)
    out = os.path.join(tmp, "douyin.comment.jsonl")

    # 1 缺凭据必须判未授权（不许假跑）
    cred, need = load_cred(os.path.join(tmp, "nope.json"))
    cases.append(("缺凭据必须报缺字段", not cred and len(need) == 4))

    # 2 分页：两页、第二页 has_more=false
    def fake(url, params=None, timeout=20):
        cur = int((params or {}).get("cursor") or 0)
        if cur == 0:
            return {"data": {"list": [{"comment_id": "c1", "content": "用什么软件剪的",
                                       "user": {"nickname": "阿岚"}}],
                             "has_more": True, "cursor": 50}}
        return {"data": {"list": [{"comment_id": "c2", "content": "求bgm名字",
                                   "user": {"nickname": "老猫"}}], "has_more": False}}

    rows = pull_comments({"open_id": "o", "access_token": "t"}, "v123", out, fetch=fake)
    cases.append(("分页必须拉满两页", len(rows) == 2 and {r["id"] for r in rows} == {"c1", "c2"}))
    cases.append(("必须写 ingest 兼容格式",
                  json.loads(open(out, encoding="utf-8").readline()).get("thread") == "v123"))

    # 3 max_pages 生效（防无限翻页）
    def loop(url, params=None, timeout=20):
        return {"data": {"list": [{"comment_id": "x", "content": "a"}], "has_more": True, "cursor": 1}}
    rows2 = pull_comments({"open_id": "o", "access_token": "t"}, "v1", out, max_pages=2, fetch=loop)
    cases.append(("翻页必须受 max_pages 限制", len(rows2) == 2))

    # 4 写行为：命令行必须拒绝（CEO 令：只出草稿）
    rc = main(["--reply", "c1", "--text", "不存在的路径"])
    cases.append(("写行为必须被拒", rc == 4))

    # 5 待核能力：私信必须拒绝而不是猜
    rc2 = main(["--pull", "dm"])
    cases.append(("私信待核必须拒绝", rc2 == 3))

    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="凭据是否就绪（不联网）")
    ap.add_argument("--pull", choices=["comments", "dm", "data"], default=None)
    ap.add_argument("--item-id", default=None)
    ap.add_argument("--out", default="cph4/fleet/social/raw")
    ap.add_argument("--reply", default=None, help="（占位）回复评论：本工具不支持")
    ap.add_argument("--text", default=None)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)

    if a.self_test:
        return self_test()

    # CEO 令：写行为全部只出草稿 —— 这里直接拒绝，不存在"悄悄发出去"的路径
    if a.reply:
        print("[douyin] 拒绝：写行为（回复评论）不在本工具范围内。"
              "草稿用 social_drafts 产出，发送由 CEO 或授权人执行（2026-11-17 令）")
        return 4
    if a.pull in ("dm", "data"):
        print("[douyin] 待核：%s 的官方接口路径与权限未获文档确证，先不实现（不猜路径）。"
              "确认后在此补实现。" % a.pull)
        return 3

    cred, need = load_cred()
    if need:
        print("[douyin] 未授权：缺 %s（写 ~/.fluxgroup/douyin.json 或设环境变量）"
              % ",".join(need))
        return 2
    if a.check:
        exp = cred.get("expires_at")
        left = (int(exp) - int(time.time())) // 60 if exp else None
        print("[douyin] 凭据齐备 open_id=%s... token剩余=%s"
              % (str(cred.get("open_id"))[:6], ("%d 分钟" % left) if left is not None else "未知"))
        return 0 if (left is None or left > 0) else 5
    if a.pull == "comments":
        if not a.item_id:
            print("[douyin] --pull comments 需要 --item-id")
            return 2
        out = os.path.join(a.out, "douyin.comment.jsonl")
        rows = pull_comments(cred, a.item_id, out)
        print("[douyin] 拉到 %d 条 -> %s（下一步：social_ingest --raw %s --out <dir>）"
              % (len(rows), out, a.out))
        return 0
    print("[douyin] 无事可做：用 --check / --pull comments --item-id <ID>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
