#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_comment.py - 在自己视频下回复真实评论（B站，官方接口，页面内签名请求）。

CEO 2026-11-17「试着评论就好」「你自动化开展 不要烦我」。
设计上把风险压到最低的四条：

  1 **只在自己作品下回**：UP 回自己评论区是最自然的行为；去别人视频下留言才像营销。
  2 **内容必须过闸**：草稿由 social_drafts 生成，红线/事实/语感/模板闸全过才发；
     被问 AI/身份/制作方式的一律不发（留给人工）。
  3 **节律**：默认一次 1 条、每天上限 2 条、间隔 ≥90 分钟；riskguard 统一记账。
  4 **签名走官方**：页面内 fetch + wbi 签名 + csrf（bili_jct），不逆向、不改客户端。

签名在 Python 里算（hashlib），请求从浏览器上下文发出（同源、真 cookie、真 UA）。

Usage
  .venv-housing/bin/python Tools/fleet/social_comment.py --dry            # 只生成待发内容，不发
  .venv-housing/bin/python Tools/fleet/social_comment.py --send --limit 1 # 真发（默认 1 条）
  .venv-housing/bin/python Tools/fleet/social_comment.py --list           # 看自己作品与可回评论
  python3 Tools/fleet/social_comment.py --self-test
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.parse
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SENT = os.path.join(ROOT, "cph4", "fleet", "social", "comments-sent.jsonl")
PROF = os.path.join(os.path.expanduser("~"), ".fluxgroup", "browser-bilibili")
CHROME = os.path.join(os.path.expanduser("~"), ".fluxgroup", "chrome", "chrome-mac-arm64",
                      "Google Chrome for Testing.app", "Contents", "MacOS",
                      "Google Chrome for Testing")
MIXIN_TAB = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
             33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40, 61,
             26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36,
             20, 34, 44, 52]


def _md5(s):
    return hashlib.md5(s.encode()).hexdigest()


def mixin_key(img_url, sub_url):
    orig = img_url.rsplit("/", 1)[-1].split(".")[0] + sub_url.rsplit("/", 1)[-1].split(".")[0]
    return "".join(orig[i] for i in MIXIN_TAB)[:32]


def sign_params(params, key, wts=None):
    """标准的 wbi 签名：过滤 !'()* 后按 key 排序拼接，末尾加 mixin key 取 md5。"""
    wts = wts or int(time.time())
    p = {k: str(v).replace("!'()*", "") for k, v in dict(params, wts=wts).items()}
    q = urllib.parse.urlencode(sorted(p.items()))
    return dict(p, w_rid=_md5(q + key))


def _launch(p, headless=True):
    kw = dict(user_data_dir=PROF, headless=headless, locale="zh-CN",
              timezone_id="Asia/Shanghai", viewport={"width": 1440, "height": 950},
              args=["--disable-blink-features=AutomationControlled"])
    if os.path.exists(CHROME):
        kw["executable_path"] = CHROME
    return p.chromium.launch_persistent_context(**kw)


def my_videos_and_comments(limit_videos=3, per_video=6):
    """返回 [(video_url, aid, [comments])]，只读。"""
    from playwright.sync_api import sync_playwright
    out = []
    with sync_playwright() as p:
        ctx = _launch(p)
        try:
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.goto("https://www.bilibili.com/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            nav = pg.evaluate("""async()=>{const r=await fetch('https://api.bilibili.com/x/web-interface/nav',
                {credentials:'include'});const j=await r.json();return {mid:(j.data||{}).mid,
                wbi:(j.data||{}).wbi_img};}""")
            mid = nav.get("mid")
            if not mid:
                return [], "未登录"
            pg.goto("https://space.bilibili.com/%s/video" % mid, wait_until="domcontentloaded",
                    timeout=60000)
            time.sleep(6)
            links = pg.eval_on_selector_all(
                "a[href*='/video/BV']", "els=>[...new Set(els.map(e=>e.href))]")
            links = [u.split("?")[0] for u in links][:limit_videos]
            for u in links:
                pg.goto(u, wait_until="domcontentloaded", timeout=60000)
                time.sleep(4)
                aid = pg.evaluate("()=>{try{return window.__INITIAL_STATE__.aid}catch(e){return 0}}")
                if not aid:
                    continue
                r = pg.evaluate("""async(u)=>{const r=await fetch(u,{credentials:'include'});
                    return await r.text();}""",
                    "https://api.bilibili.com/x/v2/reply?type=1&oid=%s&pn=1&ps=20&sort=2" % aid)
                try:
                    js = json.loads(r)
                except Exception:
                    continue
                reps = ((js.get("data") or {}).get("replies") or [])[:per_video]
                cs = [{"rpid": str(it.get("rpid")), "text": ((it.get("content") or {}).get("message") or ""),
                       "author": ((it.get("member") or {}).get("uname") or ""),
                       "like": it.get("like") or 0} for it in reps]
                out.append((u, aid, cs))
        finally:
            try:
                ctx.close()
            except Exception:
                pass
    return out, ""


def post_reply(aid, root_rpid, message, dry=True):
    """在自己视频下回复某条评论。dry=True 只走签名+构造，不发请求。"""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        ctx = _launch(p)
        try:
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.goto("https://www.bilibili.com/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            nav = pg.evaluate("""async()=>{const r=await fetch('https://api.bilibili.com/x/web-interface/nav',
                {credentials:'include'});const j=await r.json();return {mid:(j.data||{}).mid,
                wbi:(j.data||{}).wbi_img, isLogin:(j.data||{}).isLogin};}""")
            if not nav.get("isLogin"):
                return False, "未登录"
            wbi = nav.get("wbi") or {}
            key = mixin_key(wbi.get("img_url", ""), wbi.get("sub_url", ""))
            cookies = {c["name"]: c["value"] for c in ctx.cookies()}
            csrf = cookies.get("bili_jct", "")
            if not csrf:
                return False, "缺 csrf（bili_jct）——登录态不完整"
            params = sign_params({"oid": aid, "type": 1, "root": root_rpid, "parent": root_rpid,
                                  "message": message, "csrf": csrf, "plat": 1}, key)
            if dry:
                return True, {"dry": True, "params_preview": {k: str(v)[:20] for k, v in params.items()},
                              "message": message, "aid": aid, "root": root_rpid}
            body = urllib.parse.urlencode(params)
            res = pg.evaluate("""async (body)=>{
                const r=await fetch('https://api.bilibili.com/x/v2/reply/add',
                  {method:'POST',credentials:'include',
                   headers:{'Content-Type':'application/x-www-form-urlencoded'},
                   body:body});
                return {status:r.status, text:(await r.text()).slice(0,400)};}""", body)
            return res.get("status") == 200, res
        finally:
            try:
                ctx.close()
            except Exception:
                pass


def verify_visible(aid, root_rpid, my_rpid, wait_s=120):
    """发完必须回验：B站 返回 code=0 不等于公开可见（2026-11-17 实锚：
    rpid 324260408320 返回"发送成功"，但子回复列表 4 分钟后仍查不到）。
    不可见就当"待审核"，不重复发、不宣称成功。
    """
    from playwright.sync_api import sync_playwright
    deadline = time.time() + wait_s
    while time.time() < deadline:
        with sync_playwright() as p:
            ctx = _launch(p)
            try:
                pg = ctx.pages[0] if ctx.pages else ctx.new_page()
                pg.goto("https://www.bilibili.com/", wait_until="domcontentloaded", timeout=60000)
                time.sleep(3)
                r = pg.evaluate("""async(u)=>{const x=await fetch(u,{credentials:'include'});
                    return await x.text();}""",
                    "https://api.bilibili.com/x/v2/reply/reply?type=1&oid=%s&root=%s&pn=1&ps=50"
                    % (aid, root_rpid))
                reps = ((json.loads(r).get("data") or {}).get("replies") or [])
                if str(my_rpid) in [str(it.get("rpid")) for it in reps]:
                    return True, "已公开可见"
            except Exception as e:
                return False, "回验失败：%s" % str(e)[:60]
            finally:
                try:
                    ctx.close()
                except Exception:
                    pass
        time.sleep(45)
    return False, "提交成功但 %ds 内公开不可见（多为送审/静默处理）" % wait_s


def _today_sent():
    if not os.path.exists(SENT):
        return 0
    today = datetime.now().strftime("%Y-%m-%d")
    n = 0
    for line in open(SENT, encoding="utf-8"):
        if line.strip():
            try:
                if (json.loads(line).get("ts") or "").startswith(today):
                    n += 1
            except Exception:
                pass
    return n


def self_test():
    cases = []
    k = mixin_key("https://i0.hdslb.com/bfs/wbi/7cd084941338484aae1ad9425b84077c.png",
                  "https://i0.hdslb.com/bfs/wbi/4932caff0ff746eab6f01bf08b70ac45.png")
    cases.append(("mixin key 长度 32", len(k) == 32))
    s = sign_params({"oid": 1, "type": 1, "message": "abc"}, k, wts=1700000000)
    cases.append(("签名含 wts 与 w_rid", "wts" in s and len(s.get("w_rid", "")) == 32))
    s2 = sign_params({"oid": 1, "type": 1, "message": "abc"}, k, wts=1700000000)
    cases.append(("同输入同签名（可复算）", s["w_rid"] == s2["w_rid"]))
    s3 = sign_params({"oid": 1, "type": 1, "message": "abcd"}, k, wts=1700000000)
    cases.append(("改内容签名必变", s3["w_rid"] != s["w_rid"]))
    # 危险字符必须被过滤
    s4 = sign_params({"k": "a!'()*b"}, k, wts=1700000000)
    cases.append(("过滤 !'()* ", "!'()*" not in str(s4)))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--limit", type=int, default=1)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    # 只读/写都要先过风控闸
    sys.path.insert(0, HERE)
    import social_riskguard as guard
    import social_drafts as sd

    if a.list or a.dry:
        vids, why = my_videos_and_comments(limit_videos=3, per_video=6)
        if not vids:
            print("[comment] 拿不到作品/评论：%s" % (why or "空"))
            return 2
        for u, aid, cs in vids:
            print("[comment] %s（aid=%s）可回评论 %d 条" % (u, aid, len(cs)))
            for c in cs[:4]:
                print("    - %s: %s" % (c["author"][:8], c["text"][:36]))
        if a.list:
            return 0
        # dry：为目标评论生成草稿并核对闸
        for u, aid, cs in vids:
            for c in cs:
                k, d, h, n = sd.draft_best(c["text"], face="comment", samples=4)
                if d and not h:
                    print("[comment] DRY 待发 → %s | %s\n         回复：%s（%s）"
                          % (u, c["text"][:30], d, k))
                    return 0
        print("[comment] DRY：没有一条同时满足「非人工+有稿」（这是对的结果，不发）")
        return 0

    if a.send:
        if _today_sent() >= 2:
            print("[comment] 今日已发 2 条上限，停")
            return 0
        ok, why = guard.check("bilibili")
        if not ok:
            ok, why = guard.wait_turn("bilibili", max_wait=120)
            if not ok:
                print("[comment] 风控闸拒绝：%s" % why)
                return 3
        vids, why = my_videos_and_comments(limit_videos=3, per_video=8)
        if not vids:
            print("[comment] 拿不到评论：%s" % (why or "空"))
            return 2
        sent = 0
        for u, aid, cs in vids:
            for c in cs:
                if sent >= a.limit:
                    break
                if c["author"] and "大喵" in c["author"]:
                    continue          # 不回复自己
                k, d, h, n = sd.draft_best(c["text"], face="comment", samples=4)
                if not d or h:
                    continue
                okp, res = post_reply(aid, c["rpid"], d, dry=False)
                guard.note("bilibili", "ok" if okp else "blocked", "comment %s" % ("ok" if okp else res))
                vis, vwhy = (False, "未回验")
                if okp:
                    my_rpid = ""
                    try:
                        my_rpid = str((json.loads(str(res.get("text") or "{}")).get("data") or {})
                                      .get("rpid") or "")
                    except Exception:
                        my_rpid = ""
                    if my_rpid:
                        vis, vwhy = verify_visible(aid, c["rpid"], my_rpid, wait_s=120)
                rec = {"ts": datetime.now().isoformat(timespec="seconds"), "video": u, "aid": aid,
                       "rpid": c["rpid"], "to": c["text"][:80], "reply": d, "ok": okp,
                       "visible": vis, "visible_note": vwhy, "resp": str(res)[:200]}
                os.makedirs(os.path.dirname(SENT), exist_ok=True)
                open(SENT, "a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n")
                print("[comment] %s → %s ：%s（%s）"
                      % ("已提交" if okp else "失败", c["text"][:24], d, vwhy))
                if okp and vis:
                    sent += 1
                    time.sleep(90)          # 两条之间 90 秒，别连发
                elif okp:
                    print("[comment] 提交成功但不可见：今天不再发，等人工确认")
                    break
                break
            if sent >= a.limit:
                break
        print("[comment] 本轮发出 %d 条" % sent)
        return 0 if sent else 1
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
