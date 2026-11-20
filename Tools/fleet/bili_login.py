#!/usr/bin/env python3
"""bili_login.py — 按号登录：开一个有头浏览器，等人手动点完，再核验登录态。

为什么不用脚本自动填账号密码（2026-11-20 CEO 选「我来点，你等我」）：
B 站登录有滑块/验证码，脚本硬填既成功率低、又容易触发风控；真人点一次最干净。
脚本只做三件事：开窗口 → 等 bili_jct 出现 → 记录 mid/昵称并落盘。

账号密码只存在 ~/.fluxgroup/bili-accounts.json（0600，仓库外），
**绝不进代码/日志/git**；这里也不打印密码。

用法：
  python3 Tools/fleet/bili_login.py --account acct2          # 登录/复验
  python3 Tools/fleet/bili_login.py --account acct2 --check   # 只核验，不开窗口
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ACC = os.path.expanduser("~/.fluxgroup/bili-accounts.json")
sys.path.insert(0, HERE)


def load_accounts():
    try:
        return json.load(open(ACC, encoding="utf-8"))
    except Exception:
        return {"accounts": {}}


def save_accounts(d):
    import stat as _st
    os.makedirs(os.path.dirname(ACC), exist_ok=True)
    json.dump(d, open(ACC, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.chmod(ACC, 0o600)


def verify(ctx, pg):
    """返回 (ok, mid, uname)。bili_jct 在 + nav.isLogin 才算真登录。"""
    cookies = {c["name"]: c["value"] for c in ctx.cookies()}
    if not cookies.get("bili_jct"):
        return False, None, None
    try:
        nav = pg.evaluate("""async()=>{const r=await fetch(
            'https://api.bilibili.com/x/web-interface/nav',{credentials:'include'});
            const j=await r.json();const d=j.data||{};
            return {isLogin:d.isLogin, mid:d.mid, uname:d.uname};}""")
    except Exception:
        return False, None, None
    if nav.get("isLogin"):
        return True, nav.get("mid"), nav.get("uname")
    return False, None, None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", default="acct1")
    ap.add_argument("--check", action="store_true", help="只核验已有登录，不开登录页")
    ap.add_argument("--wait", type=int, default=600, help="等手动登录的秒数")
    a = ap.parse_args(argv)

    d = load_accounts()
    acct = (d.get("accounts") or {}).get(a.account)
    if not acct:
        print("未登记该账号：%s（先写进 %s）" % (a.account, ACC))
        return 2
    prof = acct.get("profile") or os.path.expanduser("~/.fluxgroup/browser-bilibili")
    os.environ["FLUX_BILI_PROFILE"] = prof
    import social_comment as sc

    mod, _ = sc._pw()
    with mod.sync_playwright() as p:
        ctx = sc._launch(p, headless=bool(a.check))
        try:
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.goto("https://www.bilibili.com/", wait_until="domcontentloaded", timeout=60000)
            ok, mid, uname = verify(ctx, pg)
            if ok:
                print("[login] %s 已登录：mid=%s 昵称=%s（profile=%s）" % (a.account, mid, uname, prof))
                acct.update({"mid": mid, "uname": uname,
                             "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S")})
                save_accounts(d)
                return 0
            if a.check:
                print("[login] %s 未登录（profile=%s）" % (a.account, prof))
                return 1
            print("[login] 请在打开的窗口里手动登录 %s（最多等 %d 秒）" % (a.account, a.wait))
            try:
                pg.goto("https://passport.bilibili.com/login", wait_until="domcontentloaded",
                        timeout=60000)
            except Exception:
                pass
            t0 = time.time()
            while time.time() - t0 < a.wait:
                time.sleep(5)
                ok, mid, uname = verify(ctx, pg)
                if ok:
                    print("[login] 登录成功：mid=%s 昵称=%s" % (mid, uname))
                    acct.update({"mid": mid, "uname": uname,
                                 "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S")})
                    save_accounts(d)
                    return 0
            print("[login] 超时未检测到登录态")
            return 1
        finally:
            try:
                ctx.close()
            except Exception:
                pass
            try:
                import social_collect as _sc
                _sc.release_profile_lock(prof)
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())
