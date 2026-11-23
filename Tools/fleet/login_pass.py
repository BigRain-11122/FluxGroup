#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""login_pass.py — 一次过登录通道：按平台依次弹窗口，登完自动存会话。

CEO 2026-11-23：「我都登陆一次，之后记住别来烦我了」。
所以这里做两件事：
1) `check`  —— 不弹窗，实测各平台现在到底登没登（cookie 判据，不靠猜）；
2) `login`  —— 有头窗口按顺序弹出来，人登一次；一检测到登录 cookie 就
   自动导出 storage_state（0600、仓库外）并写回凭据库，下次直接用。

判据一律用 **平台自己的登录 cookie**（存在即视为已登录）：
  bilibili → SESSDATA + bili_jct      xiaohongshu → web_session
  zhihu    → z_c0                     gzh(公众号)  → slave_sid 或 bizuin
  douyin   → sessionid 或 sessionid_ss  weibo      → SUB

用法：
  login_pass.py check                       # 只体检，不弹窗
  login_pass.py login --platform zhihu      # 单个
  login_pass.py login --all                 # 按 NEED_ORDER 依次（推荐）
Exit: 0 全部就绪；1 仍有未登录；2 环境问题
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import stat
import subprocess
import sys
import time

HOME = os.path.expanduser("~")
CHROME = os.path.join(HOME, ".fluxgroup/chrome/chrome-mac-arm64/"
                            "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing")
VAULT = os.path.join(HOME, ".fluxgroup", "credentials", "vault.json")

# 平台 → (profile 目录名, 登录页, 判据 cookie 组, 显示名)
PLATFORMS = {
    "bilibili":    ("browser-bilibili",    "https://passport.bilibili.com/login",
                    ("SESSDATA", "bili_jct"), "B站"),
    "xiaohongshu": ("browser-xiaohongshu", "https://www.xiaohongshu.com/explore",
                    ("web_session",), "小红书"),
    "zhihu":       ("browser-zhihu",       "https://www.zhihu.com/signin",
                    ("z_c0",), "知乎"),
    "gzh":         ("browser-gzh",         "https://mp.weixin.qq.com/",
                    ("slave_sid", "bizuin"), "微信公众号"),
    "douyin":      ("browser-douyin",      "https://www.douyin.com/",
                    ("sessionid", "sessionid_ss"), "抖音"),
    "weibo":       ("browser-weibo",       "https://weibo.com/login.php",
                    ("SUB",), "微博"),
}
# 先登"正在用"的，再登"缺的"；本机没有 profile 的排后（首次要建）
NEED_ORDER = ["zhihu", "gzh", "douyin", "xiaohongshu", "bilibili", "weibo"]


def state_path(p):
    return os.path.join(HOME, ".fluxgroup", "%s-state.json" % p)


def chrome_exe():
    if os.path.exists(CHROME):
        return CHROME
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return None      # 交给 playwright 自带浏览器
    except Exception:
        return None


async def _open(pw, key):
    prof, url, want, name = PLATFORMS[key]
    d = os.path.join(HOME, ".fluxgroup", prof)
    os.makedirs(d, exist_ok=True)
    return await pw.chromium.launch_persistent_context(
        d, headless=False, executable_path=chrome_exe(),
        args=["--no-sandbox", "--use-mock-keychain", "--password-store=basic",
              "--no-first-run", "--start-maximized"])


async def _has_login(ctx, want):
    names = {c["name"] for c in await ctx.cookies()}
    return all(w in names for w in want), sorted(names & set(want))


async def cmd_check(pw, a):
    rows = []
    for key in NEED_ORDER:
        if key not in PLATFORMS:
            continue
        prof, url, want, name = PLATFORMS[key]
        d = os.path.join(HOME, ".fluxgroup", prof)
        if not os.path.isdir(d):
            rows.append((name, "无 profile", ""))
            continue
        try:
            ctx = await pw.chromium.launch_persistent_context(
                d, headless=True, executable_path=chrome_exe(),
                args=["--no-sandbox", "--use-mock-keychain", "--password-store=basic"])
        except Exception as e:
            why = "在跑（机队占着，不重复打开）" if "Failed to" in str(e) else "启动失败"
            rows.append((name, why, str(e)[:40]))
            continue
        try:
            ok, got = await _has_login(ctx, want)
            rows.append((name, "已登录" if ok else "未登录", ",".join(got)))
        finally:
            await ctx.close()
    print("%-12s %-18s %s" % ("平台", "状态", "命中的登录 cookie"))
    for name, st, got in rows:
        print("%-12s %-18s %s" % (name, st, got))
    missing = [r[0] for r in rows if r[1] != "已登录"]
    print("\n待登录：%s" % ("、".join(missing) if missing else "无（全部就绪）"))
    return 0 if not missing else 1


async def cmd_login(pw, a):
    keys = NEED_ORDER if a.all else [a.platform]
    if a.all:
        print("将依次打开：%s" % "、".join(PLATFORMS[k][3] for k in keys))
        print("每登完一个会自动收起、接着开下一个；不在这个列表里的不用管。\n")
    done = []
    for key in keys:
        prof, url, want, name = PLATFORMS[key]
        d = os.path.join(HOME, ".fluxgroup", prof)
        print("→ 打开 %s 登录页（窗口等你操作，最多 %ds）" % (name, a.timeout), flush=True)
        ctx = await _open(pw, key)
        try:
            pg = ctx.pages[0] if ctx.pages else await ctx.new_page()
            try:
                await pg.goto(url, wait_until="domcontentloaded", timeout=30000)
            except Exception:
                pass
            t0 = time.time()
            ok = False
            while time.time() - t0 < a.timeout:
                ok, _ = await _has_login(ctx, want)
                if ok:
                    break
                await asyncio.sleep(2.5)
            if ok:
                sp = state_path(key)
                await ctx.storage_state(path=sp)
                os.chmod(sp, 0o600)
                _mark_vault(key, "ok")
                done.append(name)
                print("   ✓ %s 登录成功，会话已存 %s（0600）" % (name, sp), flush=True)
            else:
                print("   ✗ %s 超时未检测到登录态" % name, flush=True)
        finally:
            await ctx.close()
    print("\n本次完成：%s" % ("、".join(done) if done else "无"))
    return 0 if done else 1


def _mark_vault(platform, state):
    if not os.path.exists(VAULT):
        return
    keys = [k for k in ("%s/acct1" % platform, "%s/device" % platform, platform) ]
    d = json.load(open(VAULT, encoding="utf-8"))
    acc = d.get("accounts") or {}
    key = next((k for k in keys if k in acc), None) or ("%s/main" % platform)
    e = acc.setdefault(key, {"platform": platform, "alias": key.split("/")[-1]})
    e.setdefault("web_session", {})["state"] = state
    e["web_session"]["checked_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    e["web_session"]["evidence"] = "login_pass 实测 cookie 判据通过"
    d["accounts"] = acc
    with open(VAULT, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.chmod(VAULT, 0o600)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("check"); s.set_defaults(fn=cmd_check)
    s = sub.add_parser("login")
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--platform", choices=sorted(PLATFORMS))
    g.add_argument("--all", action="store_true")
    s.add_argument("--timeout", type=int, default=300)
    s.set_defaults(fn=cmd_login)
    a = ap.parse_args()

    from playwright.async_api import async_playwright
    async def run():
        async with async_playwright() as pw:
            return await a.fn(pw, a)
    return asyncio.run(run())


if __name__ == "__main__":
    sys.exit(main())
