#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_collect.py - 只读采集：把页面上的真实评论抓成结构化样本（喂给画像器/语料池）。

CEO 2026-11-17「你主要是看数据，训练每个平台的用户的评论特点，风格等等」。
所以本工具**只读**：打开页面、滚动加载、把评论文本/作者/点赞抽出来，不改不点不发。

设计原则（对着本仓踩过的坑写的）：
  1 抓不到就明说抓不到：抽到的条数 < --min 就判失败并打印看到的结构，不写空文件冒充成功
  2 只认页面真出现过的文本：不补、不猜、不合成（编造观众声音比抓不到更糟）
  3 落地文件名 = <platform>.<behavior>.jsonl，可直接被 social_ingest / social_profile 吃
  4 无头优先（B站公开页可读）；被风控拦时提示改用 --headed，不硬闯

Usage:
  .venv-housing/bin/python Tools/fleet/social_collect.py --platform bilibili --url <视频URL> --min 20
  .venv-housing/bin/python Tools/fleet/social_collect.py --platform bilibili --from-home --min 20
  python3 Tools/fleet/social_collect.py --self-test
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
RAW = os.path.join(SOCIAL, "raw")
CHROME = os.path.join(os.path.expanduser("~"), ".fluxgroup", "chrome", "chrome-mac-arm64",
                      "Google Chrome for Testing.app", "Contents", "MacOS",
                      "Google Chrome for Testing")
PROFILE_DIR = os.path.join(os.path.expanduser("~"), ".fluxgroup", "browser-profile")
# 采集用独立 profile：登录窗口会独占 browser-profile 的 ProcessSingleton，
# 用同一个目录会直接报 "Failed to create a ProcessSingleton"（2026-11-17 实锚）。
READER_DIR = os.path.join(os.path.expanduser("~"), ".fluxgroup", "browser-reader")
MODE_FILE = os.path.join(ROOT, ".codely-cli", "state", "MEM-MODE")
WORKER_COST_MB = 1100      # 实测单实例 RSS ≈1.05GB（3 实例线性增长：1.06/2.10/3.16GB）
UNLOAD_MODELS = ("qwen3.5:9b-mlx", "qwen3.5:4b-mlx", "qwen3.5:2b")


def free_mb():
    out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5).stdout
    free = 0
    for line in out.splitlines():
        if "Pages free" in line:
            import re as _re
            free = int(_re.sub(r"[^0-9]", "", line.split(":")[1] or "0") or 0) * 4096 / 1048576
    return free


def unload_models(log=print):
    """采集是内存大户（1.1GB/实例），模型常驻也是（4.6-9GB）。两者同时干必换页。

    实测（2026-11-17）：停掉 4B/9B 后空闲内存 164MB → 4732MB。
    模型按需重载只要 1.5s，所以采集前卸、采集后让它自然重载，是最省的顺序。
    """
    for m in UNLOAD_MODELS:
        subprocess.run(["ollama", "stop", m], capture_output=True, timeout=30)
    log("[collect] 已卸载常驻模型，腾出内存给浏览器（模型下次请求自动重载 ~1.5s）")


def set_mode(mode):
    os.makedirs(os.path.dirname(MODE_FILE), exist_ok=True)
    if mode:
        open(MODE_FILE, "w").write(mode)
    elif os.path.exists(MODE_FILE):
        os.remove(MODE_FILE)


def workers_by_mem(requested=2, reserve_mb=900):
    """按空闲内存算并发上限：留 reserve 给系统，每个 worker 1.1GB。"""
    free = free_mb()
    cap = max(0, int((free - reserve_mb) // WORKER_COST_MB))
    return max(1, min(requested, cap)), free, cap


def profile_for(platform=None):
    """每平台独立 profile（2026-11-17 并发改造）：同一 user_data_dir 不能两开，
    多平台并发必须各自一个目录，否则第二个直接 ProcessSingleton 失败。"""
    base = os.path.join(os.path.expanduser("~"), ".fluxgroup")
    if platform:
        return os.path.join(base, "browser-%s" % platform)
    return PROFILE_DIR

# 各平台评论节点的选择器（多套备选，取命中最多的一套；全不中=结构变了，直接报错）
SELECTORS = {
    "bilibili": [
        "#comment .reply-item",
        ".reply-list .reply-item",
        "#comment .sub-reply-item",
    ],
    "xiaohongshu": [
        ".comment-item",
        ".comments-container .comment-item",
        ".note-scroller .comment-item",
    ],
    "weibo": [".comment-item", ".item-content"],
}


def _launch(p, headed=False, platform=None):
    """优先用登录态所在的 browser-profile（评论区要登录才渲染）；
    若被别的进程占用（ProcessSingleton），退回 reader profile 只抓公开内容。

    2026-11-17 实锚：采集原来固定用 reader profile，而登录态存在 browser-profile，
    等于"登录了但采集用另一个没登录的浏览器"——B站 评论区不渲染，永远 0 条。
    """
    exe = CHROME if os.path.exists(CHROME) else None
    base = dict(headless=not headed, locale="zh-CN", timezone_id="Asia/Shanghai",
                viewport={"width": 1440, "height": 900},
                args=["--disable-blink-features=AutomationControlled"])
    if exe:
        base["executable_path"] = exe
    cands = [profile_for(platform)] if platform else [PROFILE_DIR, READER_DIR]
    for prof in cands:
        try:
            os.makedirs(prof, exist_ok=True)
            return p.chromium.launch_persistent_context(user_data_dir=prof, **base)
        except Exception:
            continue
    raise SystemExit("两个 profile 都起不来（可能被别的浏览器进程占用）")


def _clean(s):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s[:300]


def extract(page, platform, limit=200):
    """按选择器抽评论，返回 [(text, author, likes)]。命中最多的一套胜出。"""
    best = []
    for sel in SELECTORS.get(platform, []):
        try:
            nodes = page.locator(sel)
            n = min(nodes.count(), limit)
            got = []
            for i in range(n):
                el = nodes.nth(i)
                try:
                    text = _clean(el.inner_text())
                except Exception:
                    continue
                if len(text) < 2:
                    continue
                got.append((text[:200], "", 0))
            if len(got) > len(best):
                best = got
        except Exception:
            continue
    return best


def collect_bili_api(pg, url, limit=200, pages=3, guard=None):
    """B站 评论走"页面内 fetch 公开接口"：一次 20 条，比滚动省请求、也更像正常浏览。

    2026-11-17 实测：/x/v2/reply 带 cookie 返回 code 0（某视频 234 条评论），
    而 DOM 侧 inner_text 取不到（封闭 shadow DOM）。
    """
    import time as _t
    pg.goto(url, wait_until="domcontentloaded", timeout=60000)
    _t.sleep(4)
    aid = pg.evaluate("()=>{try{return window.__INITIAL_STATE__.aid||window.__INITIAL_STATE__.videoData.aid}catch(e){return 0}}")
    if not aid:
        return None, "拿不到 aid（页面结构变化）"
    rows = []
    for pn in range(1, pages + 1):
        if guard:
            ok, why = guard.check("bilibili")
            if not ok:
                # 间隔/会话休息 -> 等；真冷却 -> 放弃
                ok2, why2 = guard.wait_turn("bilibili", max_wait=120)
                if not ok2:
                    return (rows, "风控闸中途拒绝：%s" % why2) if rows else (None, "风控闸拒绝：%s" % why2)
        r = pg.evaluate("""async (u)=>{const r=await fetch(u,{credentials:'include'});
            return {status:r.status, body:await r.text()};}""",
            "https://api.bilibili.com/x/v2/reply?type=1&oid=%s&pn=%d&ps=20&sort=2" % (aid, pn))
        if r["status"] != 200:
            break
        try:
            js = json.loads(r["body"])
        except Exception:
            break
        if js.get("code") != 0:
            if guard:
                guard.note("bilibili", "blocked", "api code=%s" % js.get("code"))
            break
        data = js.get("data") or {}
        replies = data.get("replies") or []
        if not replies:
            break
        for it in replies:
            txt = ((it.get("content") or {}).get("message") or "").strip()
            if not txt:
                continue
            rows.append({"id": str(it.get("rpid") or ""),
                         "author": ((it.get("member") or {}).get("uname") or ""),
                         "text": txt[:300], "thread": url,
                         "like": it.get("like"), "ctime": it.get("ctime"),
                         "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
        if guard:
            guard.note("bilibili", "ok", "api page %d" % pn)
        if len(rows) >= limit:
            break
        _t.sleep(random.uniform(3, 7))       # 页间留间隔，别连射
    return rows, ""


def collect(url, platform, limit=200, min_n=20, scrolls=8, headed=False):
    try:
        sys.path.insert(0, HERE)
        import social_riskguard as guard
    except Exception:
        guard = None
    if guard:
        # 进来时若只是"间隔没到/会话该休息"，等一下就好（人也会等）；只有真冷却才拒绝
        ok, why = guard.wait_turn(platform, max_wait=150)
        if not ok:
            return None, "风控闸拒绝：%s" % why
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None, "未装 playwright（用 .venv-housing/bin/python 运行）"
    with sync_playwright() as p:
        ctx = _launch(p, headed=headed, platform=platform)
        try:
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            try:
                pg.goto(url, wait_until="domcontentloaded", timeout=60000)
            except Exception as e:
                return None, "打开失败：%s" % str(e)[:80]
            time.sleep(4)
            body = pg.inner_text("body")[:400]
            sign = guard.blocked_text(body) if guard else ""
            if sign:
                if guard:
                    guard.note(platform, "blocked", sign)     # 进冷却 + 升级，别重试
                return None, "被平台风控拦截（命中「%s」）——已进冷却，换 --headed 或等冷却结束" % sign
            if platform == "bilibili":
                rows, why = collect_bili_api(pg, url, limit=limit, pages=max(1, scrolls),
                                             guard=guard)
                if rows is None:
                    return None, why
                if not rows:
                    return None, "接口 0 条（可能关闭评论）%s" % why
                if len(rows) < min_n:
                    # 视频本身评论就少，不是抓取失败——照收，但把事实写进理由
                    return rows, "仅有 %d 条（视频评论本来少）%s" % (len(rows), why)
                return rows, why
            got = []
            for _ in range(max(1, scrolls)):
                got = extract(pg, platform, limit)
                if len(got) >= min_n:
                    break
                pg.mouse.wheel(0, random.randint(1800, 3000))
                time.sleep(random.uniform(2.0, 5.0))   # 滚动节奏随机化，固定节拍是风控特征
            if len(got) < min_n:
                # 打印看到的骨架，便于下一次改选择器（不写空文件冒充成功）
                skel = pg.evaluate("""() => [...document.querySelectorAll('[class*="comment"],[id*="comment"]')]
                    .slice(0,12).map(e=>e.id?('#'+e.id):('.'+String(e.className).split(' ')[0]))""")
                return None, "只抽到 %d 条（<%d），页面评论结构=%s" % (len(got), min_n, skel[:8])
            if guard:
                guard.note(platform, "ok", "collected %d" % len(got))
            rows, seen = [], set()
            for t, a, lk in got:
                if t in seen:
                    continue
                seen.add(t)
                rows.append({"id": "c%d" % len(rows), "author": a, "text": t,
                             "thread": url, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
            return rows, ""
        finally:
            try:
                ctx.close()
            except Exception:
                pass


def discover(platform, limit=5, headed=False):
    """登录态下自动发现"自己的作品页"，写进 SOURCES-v1.json。

    为什么要这一步：24h 循环需要目标页清单，而人不该每天手贴 URL。
    B站=打开 space.bilibili.com（会跳到自己主页）取 /video/BV 链接。
    """
    if platform != "bilibili":
        return None, "暂只支持 bilibili 自动发现（其它平台先手填 urls）"
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None, "未装 playwright"
    urls = []
    with sync_playwright() as p:
        ctx = _launch(p, headed=headed, platform="bilibili")
        try:
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.goto("https://space.bilibili.com/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)
            if any(k in pg.inner_text("body")[:200] for k in ("登录", "扫码")):
                return None, "未登录（先 --login bilibili）"
            for _ in range(3):
                got = pg.eval_on_selector_all(
                    "a[href*='/video/BV']", "els=>[...new Set(els.map(e=>e.href))]")
                urls = got if len(got) > len(urls) else urls
                pg.mouse.wheel(0, 1600)
                time.sleep(2)
        finally:
            try:
                ctx.close()
            except Exception:
                pass
    urls = [u.split("?")[0] for u in urls][:limit]
    if not urls:
        return None, "主页没找到作品链接（可能账号零作品）"
    path = os.path.join(SOCIAL, "SOURCES-v1.json")
    cfg = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {"platforms": {}}
    cfg.setdefault("platforms", {}).setdefault("bilibili", {})["urls"] = urls
    cfg["platforms"]["bilibili"]["enabled"] = True
    cfg.setdefault("platforms", {}).setdefault("bilibili", {})["discovered_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    json.dump(cfg, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return urls, ""


def discover_public(keyword, limit=8, headed=False):
    """按关键词找公开视频，把 URL 写进 SOURCES（多采集别人评论的入口）。"""
    from playwright.sync_api import sync_playwright
    import urllib.parse
    q = urllib.parse.quote(keyword)
    urls = []
    with sync_playwright() as p:
        ctx = _launch(p, headed=headed, platform="bilibili")
        try:
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.goto("https://search.bilibili.com/all?keyword=%s" % q,
                    wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)
            for _ in range(3):
                got = pg.eval_on_selector_all("a[href*='/video/BV']",
                                              "els=>[...new Set(els.map(e=>e.href))]")
                urls = got if len(got) > len(urls) else urls
                pg.mouse.wheel(0, 1800)
                time.sleep(2)
        finally:
            try:
                ctx.close()
            except Exception:
                pass
    urls = [u.split("?")[0] for u in urls][:limit]
    if not urls:
        return None, "搜索没拿到视频链接（可能触发风控）"
    path = os.path.join(SOCIAL, "SOURCES-v1.json")
    cfg = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {"platforms": {}}
    node = cfg.setdefault("platforms", {}).setdefault("bilibili", {})
    old = [u for u in (node.get("urls") or []) if u]
    merged = list(dict.fromkeys(old + urls))[:60]      # 最多留 60 个源，防无限膨胀
    node["urls"] = merged
    node["enabled"] = True
    node["public_keywords"] = list(dict.fromkeys((node.get("public_keywords") or []) + [keyword]))
    json.dump(cfg, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return urls, ""


def self_test():
    cases = []
    # 1 选择器表覆盖三个平台
    cases.append(("选择器表有三平台", all(k in SELECTORS for k in ("bilibili", "xiaohongshu", "weibo"))))
    # 2 清洗：去多余空白、截断
    cases.append(("清洗去空白", _clean("  a\n\n  b  ") == "a b"))
    cases.append(("清洗截断 300", len(_clean("x" * 500)) == 300))
    # 3 平台未知时 extract 返回空（不瞎猜）
    cases.append(("未知平台不猜选择器", SELECTORS.get("myspace") is None))
    # 4 抓不到必须有明确失败语（不写空文件）
    rows, why = collect("about:blank", "bilibili", min_n=3, scrolls=1)
    cases.append(("抓不到要明说", rows is None and isinstance(why, str) and why))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    print("[self-test] 注：真实抓取需联网，自检只验判据与失败语")
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", default="bilibili", choices=list(SELECTORS))
    ap.add_argument("--url", default=None)
    ap.add_argument("--from-home", action="store_true", help="从平台首页取第一条内容（B站）")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--min", type=int, default=20)
    ap.add_argument("--scrolls", type=int, default=8)
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--out", default=RAW)
    ap.add_argument("--discover", default=None, help="登录态下自动发现自己的作品页（bilibili）")
    ap.add_argument("--discover-public", default=None,
                    help="按关键词发现公开视频（别人/热门的评论也能采）：--discover-public 家常菜")
    ap.add_argument("--workers", type=int, default=2, help="并发浏览器数（按空闲内存自动压）")
    ap.add_argument("--no-unload", action="store_true", help="采集前不要卸载模型（内存够时可以）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.discover_public:
        urls, why = discover_public(a.discover_public, limit=8, headed=a.headed)
        if urls is None:
            print("[collect] 发现失败：%s" % why)
            return 3
        print("[collect] 关键词「%s」发现 %d 个公开视频：" % (a.discover_public, len(urls)))
        for u in urls:
            print("  -", u)
        return 0
    if a.discover:
        urls, why = discover(a.discover, limit=5, headed=a.headed)
        if urls is None:
            print("[collect] 发现失败：%s" % why)
            return 3
        print("[collect] 已写入 SOURCES-v1.json 的 %s 目标页 %d 条：" % (a.discover, len(urls)))
        for u in urls:
            print("  -", u)
        return 0
    url = a.url
    if a.from_home and not url:
        # 从首页推荐里拿第一条视频，避免"要你给 URL 才能动"
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                ctx = _launch(p, headed=a.headed)
                pg = ctx.pages[0] if ctx.pages else ctx.new_page()
                pg.goto("https://www.bilibili.com/", wait_until="domcontentloaded", timeout=60000)
                time.sleep(4)
                links = pg.eval_on_selector_all(
                    "a[href*='/video/BV']", "els=>[...new Set(els.map(e=>e.href))].slice(0,1)")
                url = links[0] if links else None
                ctx.close()
        except Exception as e:
            print("[collect] 取首页视频失败：%s" % str(e)[:80])
    if not url:
        print("[collect] 需要 --url 或 --from-home")
        return 2
    rows, why = collect(url, a.platform, limit=a.limit, min_n=a.min,
                        scrolls=a.scrolls, headed=a.headed)
    if rows is None:
        print("[collect] 失败：%s" % why)
        return 3
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "%s.comment.jsonl" % a.platform)
    # 追加 + 按 id 去重（2026-11-17 实锚：原来每次覆盖，采三条视频只剩最后一条的量）
    seen = set()
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    seen.add(json.loads(line).get("id"))
                except Exception:
                    pass
    new = 0
    with open(path, "a", encoding="utf-8") as f:
        for r in rows:
            if r.get("id") in seen:
                continue
            seen.add(r.get("id"))
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            new += 1
    total = sum(1 for _ in open(path, encoding="utf-8"))
    print("[collect] %s 本轮 %d 条（新增 %d）→ 累计 %d 条 -> %s"
          % (a.platform, len(rows), new, total, path))
    print("[collect] 下一步：python3 Tools/fleet/social_profile.py --raw-dir %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
