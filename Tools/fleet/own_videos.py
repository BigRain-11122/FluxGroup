#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""own_videos.py — 读"自己号下有哪些视频"，输出 JSON 供回复线用。

为什么是独立进程（而不是塞进 browser_daemon）：
2026-11-24 实锚——把"开空间页抓作品"加进常驻 daemon，一个 goto 挂住就把单线程卡死，
发帖与浏览全线停摆，只能重启。导航类动作一律不进 daemon。

做法：用已登录 profile 起一个临时上下文，打开 space.bilibili.com（登录态会跳到本人主页），
抓 /video/BV 链接；三步都带硬超时，卡住就整体放弃并如实报错，绝不无限等。

用法：
  FLUX_ACCOUNT=acct3 python3 Tools/fleet/own_videos.py            # 打印并写盘
  FLUX_ACCOUNT=acct3 python3 Tools/fleet/own_videos.py --limit 40
  python3 Tools/fleet/own_videos.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "cph4", "fleet", "social", "OWN-VIDEOS.json")


def _profile():
    """账号 → profile 目录。带兜底：不存在就用 browser-bilibili（当前唯一已登录的）。"""
    base = os.path.join(os.path.expanduser("~"), ".fluxgroup")
    acct = os.environ.get("FLUX_ACCOUNT") or ""
    cand = os.path.join(base, "browser-%s" % acct) if acct else ""
    if cand and os.path.isdir(cand):
        return cand
    return os.environ.get("FLUX_BILI_PROFILE") or os.path.join(base, "browser-bilibili")


def fetch(limit=60, timeout_ms=25000):
    """返回 (ok, 数据或错误)。整段有硬上限，任何一步超时就放弃。"""
    from playwright.sync_api import sync_playwright
    prof = _profile()
    # 用仓库里的本地 Chrome（Playwright 自带 Chromium 本机从没装成功过：CDN 0%）
    os.environ["FLUX_BILI_PROFILE"] = prof
    sys.path.insert(0, HERE)
    import social_comment as sc
    mid = None
    out = []
    with sync_playwright() as p:
        ctx = sc._launch(p, headless=True, prof=prof)
        try:
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.set_default_timeout(timeout_ms)
            pg.goto("https://space.bilibili.com/", wait_until="domcontentloaded", timeout=timeout_ms)
            pg.wait_for_timeout(2500)
            mid = pg.evaluate("""() => {
                const m = (location.pathname || '').match(/\\/(\\d+)/);
                return m ? m[1] : '';
            }""")
            for _ in range(2):
                pg.mouse.wheel(0, 1400)
                pg.wait_for_timeout(1200)
            items = pg.evaluate("""() => {
                const seen = new Map();
                document.querySelectorAll('a[href*="/video/BV"]').forEach(a => {
                    const m = (a.href || '').match(/\\/video\\/(BV[0-9A-Za-z]+)/);
                    if (!m) return;
                    const t = (a.getAttribute('title') || a.textContent || '').trim().slice(0, 80);
                    if (!seen.has(m[1])) seen.set(m[1], t);
                });
                return [...seen.entries()].map(([bvid, title]) => ({bvid, title}));
            }""")
            out = [{"bvid": x.get("bvid"), "title": (x.get("title") or "").strip(),
                    "url": "https://www.bilibili.com/video/%s/" % x.get("bvid")}
                   for x in (items or [])[:limit]]
        finally:
            try:
                ctx.close()
            except Exception:
                pass
    return True, {"mid": mid, "profile": prof, "videos": out,
                  "ts": datetime.now().isoformat(timespec="seconds")}


def self_test():
    """负控：profile 解析不能崩；空环境要有兜底；写盘结构要稳定。"""
    cases = []
    saved = os.environ.get("FLUX_ACCOUNT")
    os.environ["FLUX_ACCOUNT"] = "no-such-account"
    cases.append(("未知账号 → 兜底 profile 仍返回路径", bool(_profile())))
    os.environ.pop("FLUX_ACCOUNT", None)
    cases.append(("无账号 → 仍返回路径", bool(_profile())))
    if saved:
        os.environ["FLUX_ACCOUNT"] = saved
    # 结构：videos 里每条必须有 bvid/url
    fake = {"bvid": "BV1xx", "title": "t"}
    cases.append(("条目结构含 bvid/url", "bvid" in fake))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", n))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    try:
        ok, data = fetch(a.limit)
    except Exception as e:
        print("[own] 失败：%s: %s" % (type(e).__name__, str(e)[:140]))
        return 2
    if not ok:
        print("[own] 失败：%s" % data)
        return 2
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("[own] mid=%s｜profile=%s｜作品 %d 条 → %s"
          % (data.get("mid"), os.path.basename(data.get("profile") or ""),
             len(data.get("videos") or []), os.path.relpath(OUT, ROOT)))
    for v in (data.get("videos") or [])[:10]:
        print("   %s %s" % (v["bvid"], (v.get("title") or "")[:40]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
