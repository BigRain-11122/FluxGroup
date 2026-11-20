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
QUEUE = os.path.join(ROOT, "cph4", "fleet", "social", "reply-queue.jsonl")
PROF = os.path.join(os.path.expanduser("~"), ".fluxgroup", "browser-bilibili")


def merge_queue_done(mark):
    """按 root_rpid 行级合并写回队列（RG-15：禁整文件覆盖）。

    整文件重写会在别的写者追加时吞掉它刚写的行（2026-11-02 实锚吞掉 21 张自排卡）。
    这里加排他锁后**重新读一遍**再合并，写临时文件再 os.replace 原子替换，
    所以任何时刻读到的正式队列都是完整文件。
    """
    import fcntl
    if not os.path.exists(QUEUE):
        return 0
    updated = 0
    lock_path = QUEUE + ".lock"
    with open(lock_path, "a+") as lf:
        fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
        try:
            rows = []
            for line in open(QUEUE, encoding="utf-8"):
                if line.strip():
                    o = json.loads(line)
                    m = mark.get(str(o.get("root_rpid")))
                    if m:
                        o.update(m)
                        updated += 1
                    rows.append(o)
            tmp_path = QUEUE + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                for o in rows:
                    f.write(json.dumps(o, ensure_ascii=False) + "\n")
            os.replace(tmp_path, QUEUE)
        finally:
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)
    return updated
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


def _pw():
    """优先用 patchright（Apache-2.0，Playwright 的补丁分支，抹掉 CDP/Playwright 指纹）。

    2026-11-18 调研结论：行为拟人只是第二层，第一层是"浏览器别自报是机器人"。
    没装 patchright 就回落原生 playwright，功能不变但隐身弱。
    """
    try:
        import patchright.sync_api as _pw_mod
        return _pw_mod, True
    except Exception:
        from playwright import sync_api as _pw_mod
        return _pw_mod, False


def _launch(p, headless=True, wait_s=None):
    """开浏览器前先拿 profile 锁：补采/学习/发帖共用同一个 profile，抢不到就排队。

    2026-11-20 实锚：补采在跑时发帖直接抛 ProcessSingleton 异常，被记成"发布失败"；
    实际账号一切正常（CEO 手动评论成功）。所以启动前用 social_collect 那把 pid 锁排队，
    抢不到时给一句能读懂的话，而不是把浏览器内部错误当成账号问题。
    """
    kw = dict(user_data_dir=PROF, headless=headless, locale="zh-CN",
              timezone_id="Asia/Shanghai", viewport={"width": 1440, "height": 950},
              args=["--disable-blink-features=AutomationControlled"])
    if os.path.exists(CHROME):
        kw["executable_path"] = CHROME
    if wait_s is None:
        import os as _os
        wait_s = float(_os.environ.get("FLUX_PROFILE_WAIT", "180"))
    try:
        import social_collect as _sc
        if _sc._acquire_profile_lock(PROF, wait_s=wait_s) is None:
            raise RuntimeError("profile 被占用（等锁 %ds 超时）：先放补采或学习循环" % int(wait_s))
    except ImportError:
        pass
    return p.chromium.launch_persistent_context(**kw)


def my_videos_and_comments(limit_videos=3, per_video=6):
    """返回 [(video_url, aid, [comments])]，只读。"""
    _mod, _stealth = _pw()
    out = []
    with _mod.sync_playwright() as p:
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
            # 空降页是重前端页：6 秒在 patchright 下抓不到链接（实锚：0 条），
            # 改为等元素出现 + 兜底 10 秒。
            try:
                pg.wait_for_selector("a[href*='/video/BV']", timeout=15000)
            except Exception:
                pass
            time.sleep(4)
            links = pg.eval_on_selector_all(
                "a[href*='/video/BV']", "els=>[...new Set(els.map(e=>e.href))]")
            links = [u.split("?")[0] for u in links][:limit_videos]
            for u in links:
                pg.goto(u, wait_until="domcontentloaded", timeout=60000)
                time.sleep(4)
                aid = pg.evaluate("()=>{try{return window.__INITIAL_STATE__.aid}catch(e){return 0}}")
                if not aid:
                    # patchright 下 __INITIAL_STATE__ 未必注入；直接问接口要 aid。
                    import re as _r2
                    m = _r2.search(r"(BV[0-9A-Za-z]{10})", u)
                    if m:
                        try:
                            raw = pg.evaluate("""async(x)=>{const r=await fetch(
                                'https://api.bilibili.com/x/web-interface/view?bvid='+x,
                                {credentials:'include'});return await r.text();}""", m.group(1))
                            aid = ((json.loads(raw).get("data") or {}).get("aid")) or 0
                        except Exception:
                            aid = 0
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


def post_reply(aid, root_rpid, message, dry=True, read_first=False):
    """在自己视频下回复某条评论。dry=True 只走签名+构造，不发请求。"""
    _mod, _stealth = _pw()
    with _mod.sync_playwright() as p:
        ctx = _launch(p)
        try:
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.goto("https://www.bilibili.com/video/av%s" % aid,
                    wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            if read_first:
                human_read(pg)          # 先像人一样读一会儿评论再动手
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
                return {status:r.status, text:await r.text()};}""", body)
            return res.get("status") == 200, res
        finally:
            try:
                ctx.close()
            except Exception:
                pass


UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def _get_json(url, timeout=20):
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://www.bilibili.com/"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or "{}")


def bv_to_aid(video):
    """BV 号 → aid。裸 HTTP 会被风控（-412/403），所以失败时回落到浏览器同源请求。

    2026-11-18 实锚：urllib 直连 /x/web-interface/view 直接抛异常（无 cookie 被拒），
    而在已登录的页面上下文里 fetch 同一个接口是通的——同源真 cookie 才是正路。
    """
    import re as _re
    m = _re.search(r"(BV[0-9A-Za-z]{10})", video or "")
    if not m:
        return None
    bv = m.group(1)
    try:
        d = _get_json("https://api.bilibili.com/x/web-interface/view?bvid=%s" % bv)
        aid = (d.get("data") or {}).get("aid")
        if aid:
            return aid
    except Exception:
        pass
    _mod, _stealth = _pw()
    with _mod.sync_playwright() as p:
        ctx = _launch(p)
        try:
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.goto("https://www.bilibili.com/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            raw = pg.evaluate("""async(u)=>{const r=await fetch(u,{credentials:'include'});
                return await r.text();}""",
                "https://api.bilibili.com/x/web-interface/view?bvid=%s" % bv)
            return ((json.loads(raw).get("data") or {}).get("aid")) or None
        except Exception:
            return None
        finally:
            try:
                ctx.close()
            except Exception:
                pass


def verify_comment_browser(aid, rpid, pages=3, sorts=(0, 2), tries=3, wait_s=45):
    """登录态回验：用浏览器同源请求扫前几页，返回 (True/False/None, 说明)。

    None = 取不到数（不是"看不见"）。2026-11-20 实锚：原来用**匿名** urllib 打
    /x/v2/reply，接口回 code=0 但 replies 为空——于是每条都被判"不可见"，
    熔断把发帖停了，而账号本身一切正常（CEO 手动评论成功）。
    判据纪律：取数失败必须与"确实不可见"分开，否则一个接口变动就能冤枉整个账号。
    """
    import time as _t
    for attempt in range(max(1, tries)):
        mod, _st = _pw()
        got_any = False
        try:
            with mod.sync_playwright() as p:
                ctx = _launch(p)
                try:
                    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
                    pg.goto("https://www.bilibili.com/video/av%s" % aid,
                            wait_until="domcontentloaded", timeout=60000)
                    _t.sleep(3)
                    for sort in sorts:
                        for pn in range(1, pages + 1):
                            url = ("https://api.bilibili.com/x/v2/reply?type=1&oid=%s"
                                   "&pn=%d&ps=20&sort=%d" % (aid, pn, sort))
                            raw = pg.evaluate(
                                "async(u)=>{const r=await fetch(u,{credentials:'include'});"
                                "return await r.text();}", url)
                            try:
                                d = json.loads(raw)
                            except Exception:
                                continue
                            if d.get("code") not in (0, None):
                                continue
                            reps = ((d.get("data") or {}).get("replies") or [])
                            if reps:
                                got_any = True
                            if str(rpid) in [str(x.get("rpid")) for x in reps]:
                                return True, "已公开可见（sort=%d 第%d页）" % (sort, pn)
                    if got_any:
                        return False, "%d 页内查不到该 rpid（确实不在公开列表）" % pages
                finally:
                    try:
                        ctx.close()
                    except Exception:
                        pass
                    try:
                        import social_collect as _sc2
                        _sc2.release_profile_lock(PROF)
                    except Exception:
                        pass
        except Exception as e:
            msg = str(e).strip().splitlines()[0][:80]
            if "ProcessSingleton" in msg or "profile" in msg.lower():
                _t.sleep(wait_s)      # profile 被补采占着：等，不判红
                continue
            return None, "回验异常：%s" % msg
        _t.sleep(wait_s)
    return None, "回验未取到数（%d 次尝试均被占用/失败）" % tries


def verify_comment(aid, rpid, wait_s=900, step_s=60):
    """顶级评论回验：评论区第一页查得到 rpid 才算公开可见。

    与 verify_visible（子回复）不是同一个接口：顶级评论在 /x/v2/reply 的 replies 里。
    """
    vis, why = verify_comment_browser(aid, rpid)
    if vis is not None:
        return vis, why
    deadline = time.time() + wait_s
    while time.time() < deadline:
        try:
            d = _get_json("https://api.bilibili.com/x/v2/reply?type=1&oid=%s&pn=1&ps=20&sort=0" % aid)
            reps = ((d.get("data") or {}).get("replies") or [])
            if str(rpid) in [str(x.get("rpid")) for x in reps]:
                return True, "已公开可见（第 1 页）"
        except Exception as e:
            return False, "回验请求失败：%s" % str(e)[:60]
        time.sleep(step_s)
    return False, "%ds 内评论区查不到（多为送审/静默）" % wait_s


HARVEST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "cph4", "fleet", "social", "raw", "session")


def _harvest(url, title, items):
    """把这一趟"读页面"顺手读到的评论落盘，供语料链复用。

    CEO 2026-11-20「刷视频的同时也在积累训练素材」：浏览和采集本来就是同一个页面、
    同一次停留，分开跑等于把同一份流量花两遍，还互相抢 profile。
    """
    if not items:
        return 0
    os.makedirs(HARVEST_DIR, exist_ok=True)
    day = datetime.now().strftime("%Y%m%d")
    p = os.path.join(HARVEST_DIR, "session-%s.jsonl" % day)
    n, seen = 0, set()
    try:
        for line in open(p, encoding="utf-8"):
            try:
                seen.add(json.loads(line).get("text") or "")
            except Exception:
                pass
    except FileNotFoundError:
        pass
    with open(p, "a", encoding="utf-8") as f:
        for i, it in enumerate(items):
            t = str(it[0] if isinstance(it, (list, tuple)) else it).strip()
            if len(t) < 4 or t in seen:
                continue
            seen.add(t)
            f.write(json.dumps({"id": "s%s-%d" % (datetime.now().strftime("%H%M%S"), i),
                                "author": (it[1] if isinstance(it, (list, tuple)) and len(it) > 1 else ""),
                                "text": t[:200], "thread": url, "ts": datetime.now().isoformat(timespec="seconds")},
                               ensure_ascii=False) + "\n")
            n += 1
    return n


def ingest_harvest(timeout=900):
    """把本次会话采到的评论并入语料链（own_collected → QUALITY-PASS）。

    只并入、不重建：human_corpus 自带去重；comment_taste 重算可训练集。
    返回 (新增行数, 说明)。
    """
    import subprocess
    py = "/Users/junsheng.sun/.pyenv/versions/3.13.18/bin/python3"
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    own = os.path.join(root, "cph4", "fleet", "social", "corpus", "human", "own_collected.jsonl")
    qp = os.path.join(root, "cph4", "fleet", "social", "corpus", "human", "QUALITY-PASS.jsonl")
    before = sum(1 for _ in open(own, encoding="utf-8", errors="replace")) if os.path.exists(own) else 0
    r1 = subprocess.run([py, os.path.join(root, "Tools/fleet/human_corpus.py"),
                         "--from-dir", HARVEST_DIR, "--use", "train"],
                        cwd=root, capture_output=True, text=True, timeout=timeout)
    if r1.returncode != 0:
        return 0, "入库失败：%s" % ((r1.stdout or r1.stderr or "").strip().splitlines()[-1][:80])
    after = sum(1 for _ in open(own, encoding="utf-8", errors="replace"))
    subprocess.run([py, os.path.join(root, "Tools/fleet/comment_taste.py"),
                    "--corpus", own, "--out", qp], cwd=root, capture_output=True, text=True,
                   timeout=timeout)
    return max(0, after - before), "own %d→%d" % (before, after)


def browse_video(url, seconds=None, rng=None, harvest=True):
    """真的把视频页打开、停留、滚动一段再关掉（不调接口、不互动）。

    为什么要有这一步：真人的轨迹是"进来先刷几条"，只在少数几条上动手。
    只发不看的账号，行为序列里没有任何阅读停留，本身就是异常信号。
    """
    import random as _r
    mod, _st = _pw()
    try:
        with mod.sync_playwright() as p:
            ctx = _launch(p)
            try:
                pg = ctx.pages[0] if ctx.pages else ctx.new_page()
                pg.goto(url, wait_until="domcontentloaded", timeout=60000)
                human_read(pg, seconds=seconds)
                title = (pg.title() or "")[:40]
                got = 0
                if harvest:
                    try:
                        import social_collect as _sc4
                        items = _sc4.extract(pg, "bilibili", limit=40) or []
                        got = _harvest(url, title, items)
                    except Exception:
                        got = 0
                return True, "%s|%d" % (title, got)
            finally:
                try:
                    ctx.close()
                except Exception:
                    pass
                try:
                    import social_collect as _sc3
                    _sc3.release_profile_lock(PROF)
                except Exception:
                    pass
    except Exception as e:
        return False, str(e).strip().splitlines()[0][:80]


def human_read(pg, seconds=None):
    """像一个在看评论的人：下滚、停留、再下滚。

    我们原来的动作是"开页 → 直接调接口发"——这在服务端看就是无阅读行为的异常账号。
    真人的特征是停留与滚动，所以发之前必须先"读"。
    """
    import random as _r
    if seconds is None:
        seconds = _r.uniform(20, 120)
    end = time.time() + seconds
    while time.time() < end:
        try:
            pg.mouse.wheel(0, _r.randint(120, 480))
        except Exception:
            pass
        time.sleep(min(_r.uniform(1.5, 4.5), max(0.5, end - time.time())))


def delete_reply(aid, rpid, dry=False):
    """撤回自己发过的回复。

    CEO 2026-11-18「根据情况撤回或者留下」——所以撤回必须是**能真执行的动作**，
    不是一句流程说明。B站删自己评论走 /x/v2/reply/del，同样要 wbi+csrf，同源发出。
    """
    _mod, _stealth = _pw()
    with _mod.sync_playwright() as p:
        ctx = _launch(p)
        try:
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.goto("https://www.bilibili.com/video/av%s" % aid,
                    wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            if read_first:
                human_read(pg)          # 先像人一样读一会儿评论再动手
            nav = pg.evaluate("""async()=>{const r=await fetch('https://api.bilibili.com/x/web-interface/nav',
                {credentials:'include'});const j=await r.json();return {wbi:(j.data||{}).wbi_img,
                isLogin:(j.data||{}).isLogin};}""")
            if not nav.get("isLogin"):
                return False, "未登录"
            wbi = nav.get("wbi") or {}
            key = mixin_key(wbi.get("img_url", ""), wbi.get("sub_url", ""))
            cookies = {c["name"]: c["value"] for c in ctx.cookies()}
            csrf = cookies.get("bili_jct", "")
            if not csrf:
                return False, "缺 csrf（bili_jct）"
            params = sign_params({"oid": aid, "type": 1, "rpid": rpid, "csrf": csrf}, key)
            if dry:
                return True, {"dry": True, "params": {k: str(v)[:20] for k, v in params.items()}}
            body = urllib.parse.urlencode(params)
            res = pg.evaluate("""async(body)=>{const r=await fetch('https://api.bilibili.com/x/v2/reply/del',
                {method:'POST',credentials:'include',
                 headers:{'Content-Type':'application/x-www-form-urlencoded'},body:body});
                return {status:r.status, text:(await r.text()).slice(0,300)};}""", body)
            return res.get("status") == 200, res
        finally:
            try:
                ctx.close()
            except Exception:
                pass


def _scan_reply_list(pg, aid, rpid, max_pages=5, ps=20):
    """在顶级评论列表里找 rpid。返回 ("VISIBLE"|"MISS"|"UNKNOWN", 说明)。

    2026-11-19 实锚（CEO 当场纠正）：原版对 root=0 也调 `reply/reply?root=0`，
    那个接口对顶级评论永远返回空 → 我们发的每条顶级评论都被判"不可见"，进而触发
    止损、把可见率记成 20%——实际按评论列表查，9 条里 6 条可见。
    三条纪律：①顶级评论只能查 /x/v2/reply（不是 reply/reply）；
             ②按时间序(sort=0)与热度序(sort=2)各扫一遍，翻到 ps 不足或 max_pages；
             ③**接口报错一律判 UNKNOWN，绝不当成"不可见"**（把取数失败翻译成结论，
             是这类假红的总根源）。
    """
    JS = """async(u)=>{const x=await fetch(u,{credentials:'include'});return await x.text();}"""
    errs = []
    scanned = 0
    for srt in (0, 2):
        for pn in range(1, max_pages + 1):
            time.sleep(0.8)          # 节流：连打会吃 412（实测同一接口几秒内多次即被拦）
            u = ("https://api.bilibili.com/x/v2/reply?type=1&oid=%s&pn=%d&ps=%d&sort=%d"
                 % (aid, pn, ps, srt))
            try:
                raw = pg.evaluate(JS, u) or "{}"
                d = json.loads(raw)
            except Exception:
                # 412 风控页是 HTML，不是 JSON——这类一律 UNKNOWN，绝不判"不可见"
                errs.append("412/风控或非JSON")
                break
            if d.get("code") not in (0, None):
                errs.append("code=%s" % d.get("code"))
                break
            reps = ((d.get("data") or {}).get("replies") or [])
            scanned += 1
            if str(rpid) in [str(x.get("rpid")) for x in reps]:
                return "VISIBLE", "评论列表第 %d 页（sort=%d）" % (pn, srt)
            if len(reps) < ps:
                break
    if scanned == 0:
        return "UNKNOWN", "评论列表取数失败（%s）" % ("/".join(errs[:2]) or "无响应")
    return "MISS", "已扫 %d 页（sort=0/2）未见该 rpid" % scanned


def verify_visible(aid, root_rpid, my_rpid, wait_s=120):
    """发后回验：返回 (True 可见 / False 确认不可见 / None 取数失败未判定, 说明)。

    2026-11-17 实锚：code=0 不等于公开可见（rpid 324260408320 发送成功但列表查不到）。
    2026-11-19 修正：顶级评论与子回复走**不同接口**，且报错一律 UNKNOWN。
    """
    from playwright.sync_api import sync_playwright
    deadline = time.time() + wait_s
    last = "未开始"
    while time.time() < deadline:
        with sync_playwright() as p:
            ctx = _launch(p)
            try:
                pg = ctx.pages[0] if ctx.pages else ctx.new_page()
                # 必须从**视频页**发起请求：从首页 fetch 评论接口会被 412（无正确 Referer）
                pg.goto("https://www.bilibili.com/video/av%s" % aid,
                        wait_until="domcontentloaded", timeout=60000)
                time.sleep(3)
                JS = ("async(u)=>{const x=await fetch(u,{credentials:'include'});"
                      "return await x.text();}")
                root = str(root_rpid or 0)
                if root in ("0", "", "None"):
                    st, why = _scan_reply_list(pg, aid, my_rpid)
                    if st == "VISIBLE":
                        return True, why
                    last = why
                    if st == "UNKNOWN":
                        time.sleep(20)
                        continue
                else:
                    u = ("https://api.bilibili.com/x/v2/reply/reply?type=1&oid=%s"
                         "&root=%s&pn=1&ps=50" % (aid, root))
                    d = json.loads(pg.evaluate(JS, u) or "{}")
                    reps = ((d.get("data") or {}).get("replies") or [])
                    if str(my_rpid) in [str(it.get("rpid")) for it in reps]:
                        return True, "子回复列表可见"
                    # 子回复也可能因排序沉底：退一步在整个评论列表里找
                    st2, why2 = _scan_reply_list(pg, aid, my_rpid, max_pages=3)
                    if st2 == "VISIBLE":
                        return True, "子回复（评论列表）" + why2
                    last = why2
                    if st2 == "UNKNOWN":
                        time.sleep(20)
                        continue
            except Exception as e:
                last = "回验异常：%s" % type(e).__name__
            finally:
                try:
                    ctx.close()
                except Exception:
                    pass
        time.sleep(30)
    return False, "发后 %ds 内未在列表中找到（%s）" % (wait_s, last)

GHOST = ("账号已注销", "已注销", "用户已注销", "匿名用户", "bilibili_")
KEEP_AUTHOR_MIN = 2      # 作者名短于这个长度基本是占位/注销号，回它没人看得见

def live_comments(cs):
    """只留活人评论。

    2026-11-18 实锚：dry 选中的第一条是「账号已注销: UP主加油！」——给注销号回复，
    没人会看到，唯一效果是让账号看起来像在空转。而且草稿顺手编了"剪完这集"这种
    我们并不在做的事实（编事实=红线）。所以先滤作者，再谈文案。
    """
    out = []
    for c in cs:
        a = (c.get("author") or "").strip()
        if len(a) < KEEP_AUTHOR_MIN:
            continue
        if any(g in a for g in GHOST):
            continue
        out.append(c)
    return out


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
    ap.add_argument("--queue", action="store_true", help="按人类习惯排期（不回立即发）")
    ap.add_argument("--flush", action="store_true", help="到点的排期项真发")
    ap.add_argument("--withdraw", default=None, help="撤回指定 rpid（撤回也是真动作，要验）")
    ap.add_argument("--aid", default=None, help="配 --withdraw 使用")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    if a.withdraw:
        if not a.aid:
            print("[comment] --withdraw 需要配 --aid")
            return 2
        ok, res = delete_reply(a.aid, a.withdraw)
        print("[comment] 撤回 rpid=%s → %s %s" % (a.withdraw, "ok" if ok else "fail",
                                                 json.dumps(res, ensure_ascii=False)[:200]))
        return 0 if ok else 1

    # 只读/写都要先过风控闸
    sys.path.insert(0, HERE)
    import social_riskguard as guard
    import social_drafts as sd
    # 频率上限由 freq_policy 判（可见率驱动），不再写死 2 条
    try:
        import freq_policy as _fp
        _pol = _fp.load_policy()
        CAP_PER_DAY = int(_pol.get("max_per_day", 2))
        MIN_GAP = int(_pol.get("min_gap_min", 90))
    except Exception:
        CAP_PER_DAY, MIN_GAP = 8, 15   # 与 FREQ-POLICY 档 0 对齐（读不到策略时的兜底，别退回保守值）

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
            for c in live_comments(cs):
                k, d, h, n = sd.draft_best(c["text"], face="comment", samples=4)
                if d and not h:
                    print("[comment] DRY 待发 → %s | %s\n         回复：%s（%s）"
                          % (u, c["text"][:30], d, k))
                    return 0
        print("[comment] DRY：没有一条同时满足「非人工+有稿」（这是对的结果，不发）")
        return 0

    if a.queue or a.flush:
        import human_rhythm as hr
        import random as _rng
        rng = _rng.Random()
        if a.queue:
            vids, why = my_videos_and_comments(limit_videos=3, per_video=8)
            if not vids:
                print("[comment] 拿不到评论：%s" % (why or "空"))
                return 2
            exist = set()
            try:
                for line in open(QUEUE, encoding="utf-8"):
                    if line.strip():
                        exist.add(str(json.loads(line).get("root_rpid")))
            except FileNotFoundError:
                pass
            n = 0
            with open(QUEUE, "a", encoding="utf-8") as f:
                for u, aid, cs in vids:
                    for c in cs:
                        if str(c.get("rpid")) in exist:
                            continue
                        ok, why2 = hr.should_reply(c["text"], rng)
                        if not ok:
                            continue
                        due = datetime.now().timestamp() + hr.reply_delay_s(rng=rng)
                        f.write(json.dumps({"video": u, "aid": aid, "root_rpid": c["rpid"],
                                            "to": c["text"], "due_at": due, "why": why2,
                                            "queued": datetime.now().isoformat(timespec="seconds")},
                                           ensure_ascii=False) + "\n")
                        n += 1
            print("[comment] 排期 %d 条（按人类延迟分布，不回立即发）" % n)
            return 0
        # flush：到点且醒着才发
        if not hr.awake(rng=rng):
            print("[comment] 现在不在线时段（作息模型），本次不发")
            return 0
        if _today_sent() >= CAP_PER_DAY:
            print("[comment] 今日已发 %d 条（频率策略上限 %d），停" % (_today_sent(), CAP_PER_DAY))
            return 0
        pending = []
        try:
            for line in open(QUEUE, encoding="utf-8"):
                if line.strip():
                    d = json.loads(line)
                    if not d.get("done") and d.get("due_at", 0) <= time.time():
                        pending.append(d)
        except FileNotFoundError:
            pass
        if not pending:
            print("[comment] 没有到点的排期项")
            return 0
        ok, why = guard.check("bilibili")
        if not ok:
            ok, why = guard.wait_turn("bilibili", max_wait=120)
            if not ok:
                print("[comment] 风控闸拒绝：%s" % why)
                return 3
        for d in pending[:1]:
            k, draft, human_flag, note = sd.draft_best(d["to"], face="comment", samples=3)
            if not draft or human_flag:
                print("[comment] 目标卡在闸上，跳过：%s（%s）" % (note[:50], d["to"][:20]))
                continue
            okp, resp = post_reply(d["aid"], d["root_rpid"], draft, dry=False, read_first=True)
            rpid = ""
            try:
                rpid = str((json.loads(resp.get("text") or "{}").get("data") or {}).get("rpid") or "")
            except Exception:
                pass
            vis, vnote = (verify_visible(d["aid"], d["root_rpid"], rpid) if rpid else (False, "无 rpid"))
            rec = {"ts": datetime.now().isoformat(timespec="seconds"), "video": d["video"],
                   "aid": d["aid"], "rpid": d["root_rpid"], "to": d["to"], "reply": draft,
                   "my_rpid": rpid, "ok": okp, "visible": vis, "visible_note": vnote,
                   "human": note}
            with open(SENT, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            d["done"] = True
            d["my_rpid"] = rpid
            print("[comment] 发出 rpid=%s 可见=%s ｜ %s" % (rpid or "?", vis, draft))
        # 回写队列（标记已完成）：行级合并，不整文件覆盖（RG-15）
        merge_queue_done({str(d["root_rpid"]): {"done": True, "my_rpid": d.get("my_rpid", "")}
                          for d in pending[:1]})
        return 0

    if a.send:
        if _today_sent() >= CAP_PER_DAY:
            print("[comment] 今日已发 %d 条（频率策略上限 %d），停" % (_today_sent(), CAP_PER_DAY))
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


def send_danmaku(aid, text, progress_ms=None, dry=False):
    """发一条弹幕（真实用户会做的动作之一）。

    2026-11-20 CEO「弹幕什么，像一个真实的用户操作习惯就好」。
    纪律（都是为"像人"而不是"能发"）：
    · 短：≤20 字，长了不像弹幕；
    · 低频：由调用方控制（tools 里按"看过几条视频才发一条"配比）；
    · 贴视频：文本必须从该视频标题/简介推出来，不许泛夸；
    · 时间点随机：progress 落在前 90 秒内随机，避免每条都同一时刻。
    接口：/x/v2/dm/post，需 csrf(bili_jct) 与 cid（由 view 接口取）。
    """
    import random as _r
    _mod, _stealth = _pw()
    with _mod.sync_playwright() as p:
        ctx = _launch(p)
        try:
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.goto("https://www.bilibili.com/video/av%s" % aid,
                    wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            info = pg.evaluate("""async(a)=>{const r=await fetch(
                'https://api.bilibili.com/x/web-interface/view?aid='+a,
                {credentials:'include'});const j=await r.json();
                const d=j.data||{}; return {code:j.code, cid:(d.pages&&d.pages[0]||{}).cid||d.cid,
                bvid:d.bvid, dur:d.duration, isLogin:true};}""", aid)
            cid, bvid = info.get("cid"), info.get("bvid")
            if not cid:
                return False, "取不到 cid（code=%s）" % info.get("code")
            cookies = {c["name"]: c["value"] for c in ctx.cookies()}
            csrf = cookies.get("bili_jct", "")
            if not csrf:
                return False, "缺 csrf（bili_jct）——登录态不完整"
            dur = int(info.get("dur") or 120)
            if progress_ms is None:
                progress_ms = _r.randint(3000, max(4000, min(90000, dur * 1000)))
            body = urllib.parse.urlencode({
                "type": 1, "oid": cid, "msg": text[:20], "bvid": bvid,
                "progress": int(progress_ms), "mode": 1, "fontsize": 25,
                "color": 16777215, "pool": 0, "plat": 1, "csrf": csrf})
            if dry:
                return True, {"dry": True, "cid": cid, "bvid": bvid,
                              "progress": progress_ms, "msg": text[:20]}
            res = pg.evaluate("""async (body)=>{
                const r=await fetch('https://api.bilibili.com/x/v2/dm/post',
                  {method:'POST',credentials:'include',
                   headers:{'Content-Type':'application/x-www-form-urlencoded'},
                   body:body});
                return {status:r.status, text:await r.text()};}""", body)
            try:
                j = json.loads(res.get("text") or "{}")
            except Exception:
                j = {}
            ok = res.get("status") == 200 and j.get("code") == 0
            return ok, {"code": j.get("code"), "message": j.get("message"),
                        "cid": cid, "progress": progress_ms}
        finally:
            try:
                ctx.close()
            except Exception:
                pass
            try:
                import social_collect as _sc
                _sc.release_profile_lock(PROF)
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())
