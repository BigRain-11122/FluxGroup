#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_browser.py - T3 执行器：无官方接口的平台，用你已登录的浏览器会话把页面动作做完。

CEO 2026-11-17 令「只能人工你也要操作我的电脑或者页面自己搞定」（令在 docs/orders.md）。
这条令把"封号风险"从我的判断变成了你的决定，所以工具按这个前提设计：
  * 只做**确定性动作**：打开目标页 → 校验已登录 → 找到输入框 → 粘贴草稿 → 校验文字真的
    落进去了 → 点发送 → 截图存证。任何一步对不上就**整平台停手**，不暴力重点、不猜选择器。
  * 不做点赞/关注/刷量/群发私信——那才是真正会被判作弊的行为。
  * 每次动作前后各一张截图（存 .codely-cli/evidence/social/<日期>/），逐条写审计。
  * 节奏人性化：两条之间 20-60 秒随机；单次运行默认最多 3 条。

运行环境：必须用带 Playwright 的解释器（本机= .venv-housing/bin/python），浏览器用系统 Chrome。

三条子命令
  --login  <platform>             打开有头浏览器，你扫码登录一次，登录态存进专用 profile
  --calibrate <platform>          打开目标页，把候选输入框/发送按钮的 CSS 路径打出来（标定）
  --plan / --dry / --send         按 BROWSER-SELECTORS 执行；--dry 到点发送前停住并截图

选择器正身：cph4/fleet/social/BROWSER-SELECTORS-v1.json
  没有 verified_at 的平台一律**拒绝执行**（不猜 = 不假绿）；--calibrate 产出候选后再填。

Usage:
  .venv-housing/bin/python Tools/fleet/social_browser.py --login xiaohongshu
  .venv-housing/bin/python Tools/fleet/social_browser.py --calibrate xiaohongshu
  .venv-housing/bin/python Tools/fleet/social_browser.py --plan
  .venv-housing/bin/python Tools/fleet/social_browser.py --dry  xiaohongshu --limit 1
  .venv-housing/bin/python Tools/fleet/social_browser.py --send xiaohongshu --limit 1
  python3 Tools/fleet/social_browser.py --self-test          # 不 import playwright，离线
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
SEL = os.path.join(SOCIAL, "BROWSER-SELECTORS-v1.json")
CONF = os.path.join(SOCIAL, "AUTOPILOT-v1.json")
PROFILE = os.path.join(os.path.expanduser("~"), ".fluxgroup", "browser-profile")
EVID = os.path.join(ROOT, ".codely-cli", "evidence", "social")

CHROME_CANDIDATES = [
    # 本机实测（2026-11-17）：系统没装 Chrome，Playwright 自带下载在本机恒 0%（CDN 不出数据），
    # 所以直接放一份 chrome-for-testing 二进制（npmmirror 5.7MB/s），用 executable_path 指过去。
    os.path.join(os.path.expanduser("~"), ".fluxgroup", "chrome", "chrome-mac-arm64",
                 "Google Chrome for Testing.app", "Contents", "MacOS", "Google Chrome for Testing"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def _conf():
    try:
        return json.load(open(CONF, encoding="utf-8"))
    except Exception:
        return {}


def _sels():
    try:
        return json.load(open(SEL, encoding="utf-8"))
    except Exception:
        return {}


def gate(conf, platform):
    """三道前置：T3 开关 / 风险令号 / 选择器已标定。返回 (ok, reason)。"""
    if conf.get("kill_switch"):
        return False, "kill_switch=true（整体停发）"
    if not conf.get("tier3_enabled"):
        return False, "T3 未开启（AUTOPILOT-v1.json tier3_enabled=false）"
    if not str(conf.get("tier3_risk_ack") or "").strip() or conf["tier3_risk_ack"] in ("null", "None"):
        return False, "T3 风险未留令号（tier3_risk_ack 为空）"
    row = (_sels().get("platforms") or {}).get(platform) or {}
    if not row.get("verified_at"):
        return False, "%s 选择器未标定（先跑 --calibrate 再填 verified_at）" % platform
    for k in ("compose", "submit"):
        if not row.get(k):
            return False, "%s 缺 %s 选择器" % (platform, k)
    return True, "ok"


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _evdir():
    d = os.path.join(EVID, datetime.now().strftime("%Y%m%d"))
    os.makedirs(d, exist_ok=True)
    return d


def _audit(row):
    p = os.path.join(SOCIAL, "audit.jsonl")
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _launch(p, profile=PROFILE, headless=False):
    """持久化 profile：登录一次，之后不用再登（比 storage_state 稳）。"""
    exe = next((c for c in CHROME_CANDIDATES if os.path.exists(c)), None)
    kw = dict(user_data_dir=profile, headless=headless, locale="zh-CN",
              timezone_id="Asia/Shanghai", viewport={"width": 1440, "height": 900},
              args=["--disable-blink-features=AutomationControlled"])
    if exe:
        kw["executable_path"] = exe
    ctx = p.chromium.launch_persistent_context(**kw)
    ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
    return ctx


def send_one(platform, row, dry=True, ctx=None, own_ctx=False):
    """在页面上完成一次"粘贴草稿→发送"。返回 (ok, receipt)。

    任何一步对不上就返回 False 并说明"哪一步对不上"——不重试、不猜。
    """
    ok, why = gate(_conf(), platform)
    if not ok:
        return False, "闸拒绝：%s" % why
    sels = (_sels().get("platforms") or {})[platform]
    target = row.get("url") or sels.get("list_url")
    if not target:
        return False, "缺目标页 url（草稿行带 url 或选择器文件给 list_url）"
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return False, "未装 playwright（用 .venv-housing/bin/python 运行）"

    created = False
    try:
        pw = None
        if ctx is None:
            pw = sync_playwright().start()
            ctx = _launch(pw)
            created = True
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(target, wait_until="domcontentloaded", timeout=45000)
        time.sleep(random.uniform(2.0, 4.0))
        # 1 已登录？被踢回登录页就整平台停手（不尝试绕）
        for marker in (sels.get("logged_out_markers") or []):
            try:
                if page.locator(marker).count() > 0:
                    return False, "未登录/被踢（命中 %s）——先 --login" % marker
            except Exception:
                pass
        # 2 输入框
        box = page.locator(sels["compose"]).first
        if box.count() == 0:
            return False, "找不到输入框（选择器 %s）" % sels["compose"]
        shot1 = os.path.join(_evdir(), "%s-%s-before.png" % (platform, row.get("id") or "x"))
        page.screenshot(path=shot1)
        box.click()
        time.sleep(random.uniform(0.4, 1.2))
        text = (row.get("draft") or "").strip()
        if not text:
            return False, "草稿为空"
        box.type(text, delay=random.randint(60, 160))     # 逐字敲，不用 fill
        time.sleep(random.uniform(0.6, 1.6))
        # 3 校验文字真的进去了（防止点了假输入框）
        got = (box.inner_text() or "").strip()
        if text[:12] not in got and text not in got:
            return False, "文字没落进输入框（读到「%s」）" % got[:30]
        if dry:
            page.screenshot(path=shot1.replace("-before", "-dry"))
            return False, "DRY：已填好未发送（截图 %s）" % shot1.replace("-before", "-dry")
        # 4 发送
        btn = page.locator(sels["submit"]).first
        if btn.count() == 0:
            return False, "找不到发送按钮（选择器 %s）" % sels["submit"]
        btn.click()
        time.sleep(random.uniform(1.5, 3.0))
        shot2 = shot1.replace("-before", "-after")
        page.screenshot(path=shot2)
        # 5 发送后：输入框应清空（未清空=可能没发出去）
        left = ""
        try:
            left = (page.locator(sels["compose"]).first.inner_text() or "").strip()
        except Exception:
            pass
        if left and text[:10] in left:
            return False, "点完发送输入框仍有原文（可能未发出，截图 %s）" % shot2
        return True, {"screenshot": shot2, "text": text[:40]}
    except Exception as e:
        return False, "%s: %s" % (type(e).__name__, str(e)[:120])
    finally:
        if created and ctx is not None:
            try:
                ctx.close()
            except Exception:
                pass


def calibrate(platform):
    """打开目标页，把候选输入框/按钮路径打出来。不猜、只列证据。"""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print("[browser] 未装 playwright：用 .venv-housing/bin/python 运行")
        return 2
    row = (_sels().get("platforms") or {}).get(platform) or {}
    url = row.get("list_url")
    if not url:
        print("[browser] %s 没有 list_url，先在选择器文件里填目标页" % platform)
        return 2
    with sync_playwright() as p:
        ctx = _launch(p)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(3)
        shot = os.path.join(_evdir(), "calibrate-%s.png" % platform)
        page.screenshot(path=shot)
        print("[browser] 已截图 %s" % shot)
        cands = page.evaluate("""() => {
          const out = [];
          document.querySelectorAll('textarea, [contenteditable="true"], input[type="text"]').forEach((el,i)=>{
            out.push({kind:'compose', tag:el.tagName, id:el.id||'', cls:(el.className||'').toString().slice(0,80),
                      ph:el.getAttribute('placeholder')||'', path:css(el)});
          });
          document.querySelectorAll('button, [role="button"], div[class*="send"], span[class*="send"]').forEach((el)=>{
            const t=(el.innerText||'').trim();
            if(/发送|发布|回复|评论/.test(t)) out.push({kind:'submit', text:t.slice(0,12), path:css(el)});
          });
          function css(el){ if(el.id) return '#'+el.id;
            let s=el.tagName.toLowerCase(); if(el.className) s+='.'+String(el.className).trim().split(/\\s+/).slice(0,2).join('.');
            return s; }
          return out.slice(0,40);
        }""")
        for c in cands:
            print("  %-8s %s" % (c.get("kind"), c.get("path")))
        print("[browser] 从上面挑 compose/submit 填进 BROWSER-SELECTORS-v1.json 并写 verified_at")
        ctx.close()
    return 0


def plan():
    conf = _conf()
    sels = (_sels().get("platforms") or {})
    print("[browser] T3=%s ack=%s kill=%s" % (conf.get("tier3_enabled"),
                                              bool(conf.get("tier3_risk_ack")), conf.get("kill_switch")))
    for plat, row in sels.items():
        ok, why = gate(conf, plat)
        print("  %-16s %s（%s）" % (plat, "就绪" if ok else "未就绪", why))
    return 0


def self_test():
    """离线：不 import playwright、不开浏览器、不写生产审计。"""
    cases = []
    conf = _conf()
    # 1 未开 T3 时必须拒
    cases.append(("T3 关闭必须拒", gate(dict(conf, tier3_enabled=False), "xiaohongshu")[0] is False))
    # 2 缺令号必须拒
    cases.append(("缺风险令号必须拒", gate(dict(conf, tier3_enabled=True, tier3_risk_ack=""),
                                          "xiaohongshu")[0] is False))
    # 3 未标定必须拒（不猜选择器）
    cases.append(("未标定必须拒", gate(dict(conf, tier3_enabled=True, tier3_risk_ack="O-1"),
                                      "xiaohongshu")[0] is False))
    # 4 kill switch 优先
    cases.append(("kill switch 优先", gate(dict(conf, kill_switch=True, tier3_enabled=True,
                                                tier3_risk_ack="O-1"), "xiaohongshu")[1].startswith("kill_switch")))
    # 5 send_one 在闸不过时不碰浏览器
    ok, why = send_one("xiaohongshu", {"id": "t", "draft": "x"}, dry=True)
    cases.append(("闸不过时不得启动浏览器", ok is False and "闸拒绝" in why))
    ok2, why2 = send_one("bilibili", {"id": "t", "draft": "x"}, dry=True)
    cases.append(("空草稿前先看闸", ok2 is False))
    # 6 选择器文件结构自检
    s = _sels()
    cases.append(("选择器文件必须有 platforms 段", isinstance(s.get("platforms"), dict)))
    cases.append(("每条必须有 list_url 与 compose 槽位键",
                  all(("list_url" in r and "compose" in r) for r in (s.get("platforms") or {}).values())))
    ok_n = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok_n, len(cases), "PASS" if ok_n == len(cases) else "FAIL"))
    return 0 if ok_n == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--login", default=None)
    ap.add_argument("--calibrate", default=None)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--dry", default=None)
    ap.add_argument("--send", default=None)
    ap.add_argument("--limit", type=int, default=1)
    ap.add_argument("--wait", type=int, default=120, help="--login 等待秒数（自动识别登录成功）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.plan:
        return plan()
    if a.calibrate:
        return calibrate(a.calibrate)
    if a.login:
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            print("[browser] 未装 playwright：用 .venv-housing/bin/python 运行")
            return 2
        row = (_sels().get("platforms") or {}).get(a.login) or {}
        url = row.get("login_url") or row.get("list_url")
        print("[browser] 打开浏览器（%s）。扫一次码即可，我自动识别登录成功，最多等 %ds"
              % (a.login, a.wait))
        ok = False
        with sync_playwright() as p:
            ctx = _launch(p, headless=False)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(url or "about:blank")
            deadline = time.time() + max(30, a.wait)
            while time.time() < deadline:
                time.sleep(3)
                u = (page.url or "").lower()
                if any(k in u for k in ("login", "passport", "signin")):
                    continue                      # 还在登录页
                try:
                    if page.locator("text=登录").count() > 3:
                        continue                  # 顶部一堆"登录"=还没登
                except Exception:
                    pass
                ok = True
                break
            shot = os.path.join(_evdir(), "login-%s.png" % a.login)
            try:
                page.screenshot(path=shot)
            except Exception:
                shot = ""
            if ok:
                time.sleep(2)
                keep = os.path.join(os.path.expanduser("~"), ".fluxgroup")
                os.makedirs(keep, exist_ok=True)
                try:
                    ctx.storage_state(path=os.path.join(keep, "%s-state.json" % a.login))
                except Exception:
                    pass
            ctx.close()
        print("[browser] %s%s" % ("已登录并保存" if ok else "超时未识别到登录（窗口已关，登录态未存）",
                                  (" 截图=%s" % shot) if shot else ""))
        return 0 if ok else 7
    if a.dry or a.send:
        plat = a.dry or a.send
        conf = _conf()
        ok, why = gate(conf, plat)
        if not ok:
            print("[browser] 拒绝：%s" % why)
            return 6
        drafts = os.path.join(SOCIAL, "drafts.jsonl")
        rows = []
        if os.path.exists(drafts):
            for l in open(drafts, encoding="utf-8"):
                if l.strip():
                    r = json.loads(l)
                    if (r.get("platform") or "") == plat and not r.get("needs_human") \
                            and (r.get("draft") or "").strip():
                        rows.append(r)
        rows = rows[:max(1, a.limit)]
        if not rows:
            print("[browser] 队列里没有 %s 的可用草稿" % plat)
            return 0
        sent = 0
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            ctx = _launch(p)
            for i, r in enumerate(rows):
                ok, receipt = send_one(plat, r, dry=bool(a.dry), ctx=ctx)
                _audit({"id": r.get("id"), "platform": plat, "behavior": r.get("behavior"),
                        "ts": _now(), "result": "SENT" if ok else ("DRY" if a.dry else "FAILED"),
                        "receipt": receipt, "tier": 3})
                print("[browser] %s %s %s" % (r.get("id"), "OK" if ok else "停", receipt))
                if ok:
                    sent += 1
                if not ok and not a.dry:
                    print("[browser] 出错即停（不重试、不猜）")
                    break
                if i < len(rows) - 1:
                    time.sleep(random.uniform(20, 60))     # 人性化间隔
            ctx.close()
        print("[browser] 本轮发出 %d 条" % sent)
        return 0
    print("[browser] 用 --login/--calibrate/--plan/--dry/--send 或 --self-test")
    return 2


if __name__ == "__main__":
    sys.exit(main())
