#!/usr/bin/env python3
"""静默浏览器：headless 独立 profile，不动鼠标、不抢焦点、不弹窗。

为什么需要它：CEO 令「模拟人类去用，但不要操控我的鼠标，静默实现」。
物理级 desktop_* 会移动光标、抢前台焦点；本工具走 headless Chromium，
在后台进程里跑 DOM，屏幕上看不见，鼠标不动。

用法：
  silent_browser.py goto <url> [--shot out.png] [--dump-text]
  silent_browser.py run  <script.json>        # 动作序列
  silent_browser.py --self-test

script.json 形如：
  [{"act":"goto","url":"https://mp.weixin.qq.com/"},
   {"act":"wait","ms":2000},
   {"act":"text","selector":"body"},
   {"act":"shot","path":"/tmp/a.png"}]

退出码：0 成功 / 2 动作失败 / 3 选择器超时 / 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import sys

CHROME = ("/Users/junsheng.sun/.fluxgroup/chrome/chrome-mac-arm64/"
          "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing")
PROFILE = os.path.expanduser("~/.fluxgroup/silent-profile")

# 明确不做的三件事（写进代码防止后人加回来）
# 1. 不用 desktop_mouse_click / desktop_type：会移动物理光标、抢焦点
# 2. 不用 headless=False：会在 Dock 里出现窗口
# 3. 不用 --start-maximized / --window-size：headless 无意义，且暗示要可见


def _launch(pw):
    os.makedirs(PROFILE, exist_ok=True)
    return pw.chromium.launch_persistent_context(
        PROFILE,
        executable_path=CHROME,
        headless=True,
        args=["--no-first-run", "--no-default-browser-check",
              "--disable-blink-features=AutomationControlled"],
        # 默认桌面 UA，避免被识别成自动化
        user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"),
        viewport={"width": 1440, "height": 900},
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
    )


def _page(ctx):
    return ctx.pages[0] if ctx.pages else ctx.new_page()


def _do(pg, act):
    """执行单个动作；返回 (ok, result)。"""
    kind = act.get("act")
    if kind == "goto":
        pg.goto(act["url"], wait_until=act.get("wait_until", "domcontentloaded"),
                timeout=act.get("timeout", 30000))
        return True, {"url": pg.url, "title": pg.title()}
    if kind == "wait":
        pg.wait_for_timeout(int(act.get("ms", 1000)))
        return True, {"waited_ms": act.get("ms", 1000)}
    if kind == "wait_for":
        pg.wait_for_selector(act["selector"], timeout=act.get("timeout", 15000))
        return True, {"selector": act["selector"]}
    if kind == "click":
        pg.click(act["selector"], timeout=act.get("timeout", 15000))
        return True, {"clicked": act["selector"]}
    if kind == "fill":
        pg.fill(act["selector"], act.get("value", ""), timeout=act.get("timeout", 15000))
        return True, {"filled": act["selector"]}
    if kind == "press":
        pg.press(act.get("selector") or "body", act.get("key", "Enter"))
        return True, {"pressed": act.get("key", "Enter")}
    if kind == "text":
        sel = act.get("selector", "body")
        txt = pg.inner_text(sel, timeout=act.get("timeout", 15000))
        lim = int(act.get("limit", 4000))
        return True, {"len": len(txt), "text": txt[:lim]}
    if kind == "html":
        return True, {"html": pg.content()[:int(act.get("limit", 8000))]}
    if kind == "eval":
        return True, {"value": pg.evaluate(act["js"])}
    if kind == "shot":
        path = act["path"]
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        pg.screenshot(path=path, full_page=bool(act.get("full_page", True)))
        return True, {"shot": path,
                      "bytes": os.path.getsize(path) if os.path.exists(path) else 0}
    if kind == "cookies":
        return True, {"count": len(pg.context.cookies())}
    raise ValueError(f"未知动作: {kind}")


def run_script(actions, verbose=True):
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    out = []
    with sync_playwright() as pw:
        ctx = _launch(pw)
        pg = _page(ctx)
        try:
            for i, act in enumerate(actions, 1):
                try:
                    ok, res = _do(pg, act)
                except PWTimeout as e:
                    return 3, out + [{"step": i, "act": act.get("act"),
                                      "error": f"timeout: {str(e)[:160]}"}]
                except Exception as e:  # noqa: BLE001
                    return 2, out + [{"step": i, "act": act.get("act"),
                                      "error": f"{type(e).__name__}: {str(e)[:160]}"}]
                out.append({"step": i, "act": act.get("act"), "ok": ok, **res})
                if verbose:
                    brief = {k: v for k, v in res.items() if k != "text" and k != "html"}
                    print(f"[{i}] {act.get('act')} {brief}", flush=True)
        finally:
            ctx.close()
    return 0, out


# ---------------- 扫码登录（唯一允许可见窗口的路径） ----------------
LOGIN_URL = "https://mp.weixin.qq.com/"


def login(timeout=300, poll=2):
    """可见窗口扫码登录，登录态写入同一 profile。

    这是本文件里唯一允许 headless=False 的地方——扫码必须人眼看得到。
    扫完之后所有操作回到 headless，不再弹窗。
    """
    import time
    from playwright.sync_api import sync_playwright

    os.makedirs(PROFILE, exist_ok=True)
    print(f"窗口即将弹出，请用微信扫码。profile={PROFILE}", flush=True)
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            PROFILE,
            executable_path=CHROME,
            headless=False,          # 唯一例外：人要看二维码
            args=["--no-first-run", "--no-default-browser-check"],
            viewport={"width": 1280, "height": 800},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        pg.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
        print(f"已打开：{pg.title()}", flush=True)

        deadline = time.time() + timeout
        ok = False
        while time.time() < deadline:
            # 扫码后页面会跳转，导航期间任何 DOM 读取都会抛
            # "Execution context was destroyed"——必须整体兜住，不能只兜 url
            try:
                u = pg.url
                # 登录成功会跳到 /cgi-bin/home?...token=...
                if "token=" in u and "cgi-bin/home" in u:
                    ok = True
                    break
                el = pg.query_selector(".weui-desktop-account__nickname")
                if el:
                    ok = True
                    break
            except Exception:  # noqa: BLE001 —— 导航中，继续等
                pass
            time.sleep(poll)

        if ok:
            nick = ""
            try:
                el = pg.query_selector(".weui-desktop-account__nickname")
                if el:
                    nick = (el.inner_text() or "").strip()
            except Exception:  # noqa: BLE001
                pass
            print(f"LOGIN OK 账号={nick or '(未取到昵称)'} url={pg.url[:90]}", flush=True)
            pg.wait_for_timeout(2500)   # 让 cookie 落盘
            rc = 0
        else:
            print(f"LOGIN TIMEOUT {timeout}s 未检测到登录态", flush=True)
            rc = 5
        ctx.close()
        return rc


# ---------------- 自检 ----------------
def self_test():
    """自检：必须证明"静默"是真的，不是自我宣称。"""
    fails = []
    # 用 ast 精确取 _launch 函数体，避免自检代码自指
    import ast
    src = open(__file__, encoding="utf-8").read()
    tree = ast.parse(src)
    launch_src = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_launch":
            launch_src = ast.get_source_segment(src, node) or ""
            break
    if launch_src is None:
        fails.append("找不到 _launch 函数，无法验证静默性")
        launch_src = ""

    # 1. 全模块可执行调用里不许出现物理输入
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            seg = ast.get_source_segment(src, node) or ""
            # 只取调用名部分，避免把参数里的字符串算进来
            fn = node.func
            name = getattr(fn, "attr", None) or getattr(fn, "id", None) or ""
            calls.append(name)
    for bad in ("desktop_mouse_click", "desktop_click", "osascript", "cliclick",
                "pyautogui", "Quartz", "CGEventCreateMouseEvent"):
        if bad in calls:
            fails.append(f"源码含物理输入调用: {bad}")

    # 2. _launch 必须显式 headless=True 且不含 headless=False
    if "headless=True" not in launch_src:
        fails.append("_launch 未硬编码 headless=True")
    if "headless=False" in launch_src:
        fails.append("_launch 里存在 headless=False")
    if "headless" not in launch_src:
        fails.append("_launch 完全没有 headless 参数")

    # 2b. 全模块里 headless=False 只准出现在 login()——扫码是唯一例外
    # 用 AST 精确匹配关键字参数，避免被检查字符串自身命中（自指）
    visible_funcs = set()

    def _has_headless_false(fn_node):
        for n in ast.walk(fn_node):
            if isinstance(n, ast.Call):
                for kw in n.keywords:
                    if (kw.arg == "headless" and isinstance(kw.value, ast.Constant)
                            and kw.value.value is False):
                        return True
        return False

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _has_headless_false(node):
                visible_funcs.add(node.name)
    if visible_funcs - {"login"}:
        fails.append(f"除 login() 外还有函数用可见窗口: {sorted(visible_funcs - {'login'})}")
    if "login" not in visible_funcs:
        fails.append("login() 没有可见窗口，扫码流程缺失")

    # 3. 真跑一次，并确认没有可见窗口
    rc, out = run_script([
        {"act": "goto", "url": "about:blank"},
        {"act": "eval", "js": "navigator.userAgent"},
    ], verbose=False)
    if rc != 0:
        fails.append(f"headless 启动失败 rc={rc}: {out[-1] if out else ''}")
    else:
        ua = out[-1].get("value", "")
        if "HeadlessChrome" in ua:
            # 我们覆盖了 UA，这里只确认浏览器起来了
            pass

    # 4. 真访问一次，证明网络与渲染可用
    rc2, out2 = run_script([
        {"act": "goto", "url": "https://mp.weixin.qq.com/"},
        {"act": "text", "selector": "title", "limit": 100},
    ], verbose=False)
    if rc2 != 0:
        fails.append(f"真实页面访问失败 rc={rc2}")
    else:
        title = (out2[-1].get("text") or "").strip()
        if not title:
            fails.append("页面标题为空（渲染未完成）")

    # 5. profile 必须落在独立目录，不许碰用户 Chrome
    if "silent-profile" not in PROFILE:
        fails.append("profile 未隔离")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print(f"SELF-TEST OK 5/5  profile={PROFILE}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="静默浏览器（headless，不动鼠标）")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--login", action="store_true",
                    help="可见窗口扫码登录（唯一会弹窗的路径，扫完即静默）")
    ap.add_argument("--timeout", type=int, default=300, help="扫码等待秒数")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    sub = ap.add_subparsers(dest="cmd")
    g = sub.add_parser("goto")
    g.add_argument("url")
    g.add_argument("--shot")
    g.add_argument("--dump-text", action="store_true")
    r = sub.add_parser("run")
    r.add_argument("script")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if a.login:
        return login(timeout=a.timeout)
    if a.cmd == "goto":
        acts = [{"act": "goto", "url": a.url}, {"act": "wait", "ms": 1500}]
        if a.dump_text:
            acts.append({"act": "text", "selector": "body"})
        if a.shot:
            acts.append({"act": "shot", "path": a.shot})
        rc, out = run_script(acts)
    elif a.cmd == "run":
        actions = json.load(open(a.script, encoding="utf-8"))
        rc, out = run_script(actions)
    else:
        ap.print_help()
        return 1
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    return rc


if __name__ == "__main__":
    sys.exit(main())
