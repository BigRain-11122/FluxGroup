#!/usr/bin/env python3
"""苏州/上海 二手房数据抓取（贝壳 + 我爱我家）

子命令:
    login     有头浏览器，等人工完成两平台登录并保存会话
    discover  抓 城市→区域→板块 拓扑与在售套数
    scrape    按板块抓挂牌与成交列表
    csv       汇总成 CSV
    dump      保存原始 HTML 供结构核对

设计要点:
    * 登录成功与否按"真实行为"判定（区域页是否还 302 到登录/验证码），不认 cookie 名。
    * 每条列表项同时保存字段解析结果与整块纯文本，结构变动时可回看。
    * 命中登录墙/验证码立即停该板块并记录原因，不硬刷。
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
STATE_DIR = HERE / ".state"
STORAGE = STATE_DIR / "storage_state.json"
OUT_ROOT = ROOT / "data" / "housing"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

CITIES = {"su": "苏州", "sh": "上海"}
PLATFORM_HOST = {"ke": "ke.com", "5i5j": "5i5j.com"}

# 贝壳区域选择器里混着的非区域链接
NON_DISTRICT = re.compile(r"^(co\d+|pg\d+|ershoufang|xiaoqu|chengjiao|zufang|login|register)$")
NON_DISTRICT_TEXT = ("二手房", "最新发布", "总价", "房屋单价", "面积", "登录", "注册",
                     "地图找房", "更多", "不限", "全部")


def clean(t: str | None) -> str:
    return re.sub(r"\s+", " ", t or "").strip()


def sleep_a_bit(lo: float = 1.5, hi: float = 3.5) -> None:
    time.sleep(random.uniform(lo, hi))


# ---------------------------------------------------------------- 浏览器

CHROME_CANDIDATES = [
    ROOT / ".venv-housing/browsers/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
]


def _chrome_path() -> str | None:
    for c in CHROME_CANDIDATES:
        if c.exists():
            return str(c)
    return None


def _launch(p, headless: bool):
    kw = dict(args=["--disable-blink-features=AutomationControlled"])
    exe = _chrome_path()
    if exe:
        kw["executable_path"] = exe
    try:
        browser = p.chromium.launch(headless=headless, **kw)
    except Exception as e:
        raise SystemExit(f"启动浏览器失败（{exe or '内置 chromium 未安装'}）：{e}")
    ctx_kwargs = dict(
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
        viewport={"width": 1440, "height": 900},
        user_agent=UA,
    )
    if STORAGE.exists():
        ctx_kwargs["storage_state"] = str(STORAGE)
    ctx = browser.new_context(**ctx_kwargs)
    ctx.add_init_script(
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
    return browser, ctx


def _landed_ok(ctx, url: str, min_len: int = 50000) -> bool:
    """真开一个页面看落点：被拦会跳到 clogin/captcha/user-login。"""
    page = ctx.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        final = page.url
        html = page.content()
        bad = ("clogin" in final or "captcha" in final or "/user/login" in final)
        return (not bad) and len(html) >= min_len
    except Exception:
        return False
    finally:
        page.close()


def _ke_logged_in(ctx) -> bool:
    """贝壳：区域页未登录必然跳 clogin。"""
    return _landed_ok(ctx, "https://su.ke.com/ershoufang/gongyeyuan/")


def _5i5j_logged_in(ctx) -> bool:
    """我爱我家：列表页未登录跳 /user/login/。"""
    return _landed_ok(ctx, "https://sz.5i5j.com/ershoufang/", min_len=40000)


def cmd_login(args) -> int:
    """同一窗口开两个标签页，任意顺序登录，检测到即算通过。"""
    from playwright.sync_api import sync_playwright

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, ctx = _launch(p, headless=False)

        sites = {
            "我爱我家·苏州": {"url": "https://sz.5i5j.com/", "check": _5i5j_logged_in, "ok": False},
            "贝壳·苏州": {"url": "https://su.ke.com/", "check": _ke_logged_in, "ok": False},
        }
        for name, s in sites.items():
            pg = ctx.new_page()
            try:
                pg.goto(s["url"], wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                print(f"[warn] {name} 打开异常（不影响手动操作）：{e}")
            s["page"] = pg

        print("\n" + "=" * 62)
        print("浏览器已打开两个标签页，请依次（顺序不限）：")
        print("  1) 我爱我家·苏州 —— 点右上角「登录」，账号登录 + 验证码")
        print("  2) 贝壳·苏州   —— 点右上角「登录」，账号登录 + 验证码")
        print("登录完成后**不要关窗口**，脚本会自动检测并保存会话。")
        print("=" * 62 + "\n")

        t0 = time.time()
        last_save = 0.0
        while time.time() - t0 < args.wait:
            for name, s in sites.items():
                if s["ok"]:
                    continue
                if s["check"](ctx):
                    s["ok"] = True
                    print(f"  ✅ {name} 登录已确认", flush=True)
            # 增量落盘：进程被杀也不丢已登录的 cookie
            if time.time() - last_save > 20:
                ctx.storage_state(path=str(STORAGE))
                last_save = time.time()
            if all(s["ok"] for s in sites.values()):
                break
            done = [n for n, s in sites.items() if s["ok"]]
            left = [n for n, s in sites.items() if not s["ok"]]
            print(f"  … 已登录 {done or '无'} | 待登录 {left} | 剩余 "
                  f"{int(args.wait-(time.time()-t0))}s", flush=True)
            time.sleep(6)

        ctx.storage_state(path=str(STORAGE))
        browser.close()

    print("\n")
    print(f"会话已保存: {STORAGE}")
    allok = all(s["ok"] for s in sites.values())
    for name, s in sites.items():
        print(f"  {name}: {'OK' if s['ok'] else 'FAILED'}")
    if not allok:
        print("\n有站点未登录成功。可重跑 `login` 继续；已登录站点的 cookie 会保留在会话里。")
    return 0 if allok else 1


def _wait_for(fn, timeout_s: int, poll: int = 4) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if fn():
            return True
        left = int(timeout_s - (time.time() - t0))
        print(f"    等待登录中… 剩余 {left}s", end="\r", flush=True)
        time.sleep(poll)
    print()
    return False


# ---------------------------------------------------------------- 解析

def _links(page, pattern: str) -> list[tuple[str, str]]:
    out = []
    for a in page.query_selector_all("a[href]"):
        try:
            href = a.get_attribute("href") or ""
            text = clean(a.inner_text())
        except Exception:
            continue
        if not text or not re.search(pattern, href):
            continue
        out.append((text, href))
    return out


def _block_links(page, idx: int = 0) -> list[tuple[str, str]]:
    """取第 idx 个 data-role=ershoufang 筛选块内的区域/板块链接。

    贝壳的区域块里同时混着地铁线（/ditiefang/…），用 href 严格形态过滤掉。
    """
    blocks = page.query_selector_all('div[data-role="ershoufang"]')
    if not blocks:
        return []
    blk = blocks[idx] if idx < len(blocks) else blocks[0]
    out, seen = [], set()
    for a in blk.query_selector_all("a[href]"):
        try:
            href = a.get_attribute("href") or ""
            text = clean(a.inner_text())
        except Exception:
            continue
        if not re.fullmatch(r"/ershoufang/[a-z0-9]+/?", href):
            continue
        slug = re.search(r"/ershoufang/([a-z0-9]+)", href).group(1)
        if slug in seen or NON_DISTRICT.match(slug) or not text or len(text) > 8:
            continue
        seen.add(slug)
        out.append((text, href))
    return out


def parse_districts(page, city: str) -> list[dict]:
    """从城市二手房首页取区域清单（只认区域块内的 /ershoufang/<slug>/）。"""
    return [{"slug": re.search(r"/ershoufang/([a-z0-9]+)", href).group(1),
             "name": text,
             "url": f"https://{city}.ke.com{href}"}
            for text, href in _block_links(page, 0)]


def _page_stats(page) -> tuple[int | None, int | None]:
    """返回 (在售套数, 总页数)。

    苏州类页面有「共找到 X 套」；上海类页面没有该文案，只有
    .house-lst-page-box 的 page-data={"totalPage":N,...}（贝壳上限 100 页）。
    """
    total = None
    try:
        for sel in ("h2.total", ".resultDes", ".total"):
            el = page.query_selector(sel)
            if not el:
                continue
            m = re.search(r"([\d,]+)\s*套", el.inner_text())
            if m:
                total = int(m.group(1).replace(",", ""))
                break
    except Exception:
        pass
    pages = None
    try:
        el = page.query_selector(".house-lst-page-box")
        if el:
            raw = el.get_attribute("page-data") or ""
            m = re.search(r'"totalPage"\s*:\s*(\d+)', raw)
            if m:
                pages = int(m.group(1))
    except Exception:
        pass
    return total, pages


def _on_sale_total(page) -> int | None:
    return _page_stats(page)[0]


def parse_bizcircles(page, city: str, exclude_slugs: set[str]):
    """区域页里除区域本身以外的 /ershoufang/<slug>/ 就是板块。"""
    rows = []
    for text, href in _block_links(page, 0):
        slug = re.search(r"/ershoufang/([a-z0-9]+)", href).group(1)
        if slug in exclude_slugs:
            continue
        rows.append({"slug": slug, "name": text,
                     "url": f"https://{city}.ke.com/ershoufang/{slug}/"})
    return rows, _page_stats(page)


def _txt(item, sel: str) -> str:
    try:
        el = item.query_selector(sel)
        return clean(el.inner_text()) if el else ""
    except Exception:
        return ""


def parse_house_info(info: str) -> dict:
    """'2室1厅 | 96.47平米 | 南 北 | 精装 | 高楼层(共18层) | 2008年建/板楼'"""
    d = {"house_type": "", "area_sqm": None, "orientation": "", "decoration": "",
         "floor": "", "total_floors": None, "build_year": None, "building_type": ""}
    parts = [clean(x) for x in info.split("|")]
    for part in parts:
        if not part:
            continue
        if re.match(r"^\d+室", part) and not d["house_type"]:
            d["house_type"] = part
        elif "平米" in part and d["area_sqm"] is None:
            m = re.search(r"([\d.]+)平米", part)
            if m:
                d["area_sqm"] = float(m.group(1))
        elif re.search(r"[东南西北]", part) and not d["orientation"] and len(part) <= 5:
            d["orientation"] = part
        elif part in ("精装", "简装", "毛坯", "其他", "豪华装修", "精装修"):
            d["decoration"] = part
        elif "楼层" in part or "地下室" in part or "顶层" in part or "底层" in part:
            d["floor"] = part
            m = re.search(r"共\s*(\d+)\s*层", part)
            if m:
                d["total_floors"] = int(m.group(1))
        elif "年建" in part or re.fullmatch(r"\d{4}年", part):
            m = re.search(r"(\d{4})年", part)
            if m:
                d["build_year"] = int(m.group(1))
            if "/" in part:
                d["building_type"] = clean(part.split("/", 1)[1])
    return d


def parse_price_wan(text: str):
    m = re.search(r"([\d.]+)", text.replace(",", ""))
    return float(m.group(1)) if m else None


def parse_unit_price(text: str):
    m = re.search(r"([\d,]+)\s*元", text.replace(" ", ""))
    return int(m.group(1).replace(",", "")) if m else None


def parse_list_items(page) -> tuple[list[dict], str]:
    """贝壳列表项。返回 (items, 命中选择器)。"""
    for sel in ("ul.sellListContent > li", "ul.listContent > li", "div.listContent"):
        nodes = page.query_selector_all(sel)
        if not nodes:
            continue
        items = []
        for node in nodes:
            try:
                a = node.query_selector("a[href*='/ershoufang/'], a[href*='/chengjiao/']")
                href = a.get_attribute("href") if a else ""
                hid = None
                if href:
                    m = re.search(r"/(\d+)\.html", href)
                    hid = m.group(1) if m else None
                info = _txt(node, ".houseInfo")
                rec = {
                    "house_id": hid,
                    "url": (href if href.startswith("http") else "https://su.ke.com" + href) if href else "",
                    "title": _txt(node, ".title a") or _txt(node, ".title"),
                    "community": _txt(node, ".positionInfo a") or _txt(node, ".positionInfo"),
                    "position": _txt(node, ".positionInfo"),
                    "total_price_wan": parse_price_wan(_txt(node, ".totalPrice")),
                    "unit_price_yuan": parse_unit_price(_txt(node, ".unitPrice")),
                    "follow_info": _txt(node, ".followInfo"),
                    "tags": _txt(node, ".tag"),
                    "deal_date": _txt(node, ".dealDate"),
                    "raw_text": clean(node.inner_text()),
                }
                rec.update(parse_house_info(info))
                rec["house_info_raw"] = info
                items.append(rec)
            except Exception as e:
                items.append({"error": str(e), "raw_text": clean(node.inner_text())[:300]})
        return items, sel
    return [], ""


def parse_5i5j_items(page) -> tuple[list[dict], str]:
    for sel in ("ul.house-list-wrap > li", "div.listItem", "ul.pList > li", "li.listItem"):
        nodes = page.query_selector_all(sel)
        if not nodes:
            continue
        items = []
        for node in nodes:
            try:
                a = node.query_selector("a[href*='/ershoufang/']")
                href = a.get_attribute("href") if a else ""
                rec = {
                    "house_id": (re.search(r"/(\d+)\.html", href).group(1)
                                 if href and re.search(r"/(\d+)\.html", href) else None),
                    "url": href,
                    "title": _txt(node, "h3 a") or _txt(node, ".listTit a") or _txt(node, "h2 a"),
                    "community": _txt(node, ".listX .name") or _txt(node, ".infor .name"),
                    "total_price_wan": parse_price_wan(_txt(node, ".jia .red") or _txt(node, ".price")),
                    "unit_price_yuan": parse_unit_price(_txt(node, ".jia p") or _txt(node, ".unit")),
                    "house_info_raw": _txt(node, ".listX") or _txt(node, ".infor"),
                    "tags": _txt(node, ".tags"),
                    "raw_text": clean(node.inner_text()),
                }
                rec.update(parse_house_info(rec["house_info_raw"]))
                items.append(rec)
            except Exception as e:
                items.append({"error": str(e)})
        return items, sel
    return [], ""


# ---------------------------------------------------------------- 抓取

def _goto(ctx, url: str, tag: str = ""):
    page = ctx.new_page()
    resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
    status = resp.status if resp else None
    landed = page.url
    blocked = None
    if status in (301, 302, 303, 307, 308) or "clogin" in landed or "captcha" in landed \
            or "/user/login" in landed:
        blocked = landed
    else:
        # 部分城市（如上海）列表是 JS 渲染，等它出现再读
        try:
            page.wait_for_selector("ul.sellListContent, .house-lst-page-box",
                                   timeout=args_list_wait())
        except Exception:
            pass
    return page, status, blocked


def args_list_wait() -> int:
    return 15000


def cmd_discover(args) -> int:
    from playwright.sync_api import sync_playwright

    out_dir = OUT_ROOT / datetime.now().strftime("%Y%m%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    cities = [args.city] if args.city else list(CITIES)
    topology = {}

    with sync_playwright() as p:
        browser, ctx = _launch(p, headless=not args.headed)
        if not _ke_logged_in(ctx):
            print("提示：贝壳当前未登录，区域页可能被拦。建议先跑 login。")

        for city in cities:
            print(f"\n### {CITIES[city]} ({city}.ke.com)")
            page, status, blocked = _goto(ctx, f"https://{city}.ke.com/ershoufang/")
            if blocked:
                print(f"  城市首页被拦: {blocked}")
                page.close()
                continue
            districts = parse_districts(page, city)
            page.close()
            print(f"  区域 {len(districts)} 个: {[d['name'] for d in districts]}")
            district_slugs = {d["slug"] for d in districts}

            topology[city] = {"name": CITIES[city], "districts": []}
            for d in districts:
                sleep_a_bit(1.0, 2.0)
                dpage, dstatus, dblocked = _goto(ctx, d["url"])
                if dblocked:
                    print(f"    - {d['name']}: 被拦({dblocked[:60]})")
                    dpage.close()
                    topology[city]["districts"].append({**d, "blocked": True, "bizcircles": []})
                    continue
                bcs, (total, pages) = parse_bizcircles(dpage, city, district_slugs)
                dpage.close()
                print(f"    - {d['name']}: 在售 {total} 套 / {pages} 页, 板块 {len(bcs)} 个")
                topology[city]["districts"].append(
                    {**d, "on_sale_total": total, "total_pages": pages,
                     "bizcircles": bcs})

        browser.close()

    (out_dir / "topology.json").write_text(
        json.dumps(topology, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n拓扑已保存: {out_dir / 'topology.json'}")
    return 0


def cmd_scrape(args) -> int:
    from playwright.sync_api import sync_playwright

    out_dir = OUT_ROOT / datetime.now().strftime("%Y%m%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    topo_path = out_dir / "topology.json"
    if not topo_path.exists():
        print("缺少 topology.json，请先跑 discover")
        return 2
    topo = json.loads(topo_path.read_text(encoding="utf-8"))

    cities = [args.city] if args.city else list(topo)
    log = {"started": datetime.now().isoformat(timespec="seconds"), "cities": {}}

    with sync_playwright() as p:
        browser, ctx = _launch(p, headless=not args.headed)

        for city in cities:
            if city not in topo:
                continue
            cname = topo[city]["name"]
            picked = _pick_bizcircles(topo[city]["districts"], args.top)
            print(f"\n### {cname} 抓 {len(picked)} 个板块: {[b['name'] for b in picked]}")
            log["cities"][city] = {"name": cname, "bizcircles": []}

            for b in picked:
                rec = {"name": b["name"], "slug": b["slug"], "district": b["district"],
                       "listings": [], "deals": [], "notes": []}
                # 挂牌
                for kind, prefix in (("listings", "ershoufang"), ("deals", "chengjiao")):
                    if args.only and kind not in args.only:
                        continue
                    for pg in range(1, args.pages + 1):
                        url = (b["url"] if pg == 1
                               else f"https://{city}.ke.com/{prefix}/{b['slug']}/pg{pg}/")
                        page, status, blocked = _goto(ctx, url)
                        if blocked:
                            rec["notes"].append(f"{kind} p{pg} 被拦 -> {blocked[:80]}")
                            print(f"    {kind} p{pg}: 被拦")
                            page.close()
                            break
                        items, sel = parse_list_items(page)
                        raw = page.content()
                        page.close()
                        if not items:
                            rec["notes"].append(f"{kind} p{pg} 解析为 0 条 (可能到底)")
                            break
                        for it in items:
                            it["city"] = city
                            it["city_name"] = cname
                            it["bizcircle"] = b["name"]
                            it["bizcircle_slug"] = b["slug"]
                            it["district"] = b["district"]
                            it["page"] = pg
                            it["kind"] = kind
                        rec[kind].extend(items)
                        print(f"    {kind} p{pg}: {len(items)} 条 (selector {sel})")
                        sleep_a_bit()
                        if len(items) < args.min_page_items:
                            break
                log["cities"][city]["bizcircles"].append(rec)

            # 我爱我家
            if not args.skip_5i5j:
                log["cities"][city]["fivei5j"] = _scrape_5i5j(ctx, city, args)

        browser.close()

    log["finished"] = datetime.now().isoformat(timespec="seconds")
    (out_dir / f"data_{datetime.now().strftime('%H%M%S')}.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n数据已保存: {out_dir}")
    return 0


def cmd_probe(args) -> int:
    """逐个板块页读真实在售套数，用来定"热门板块"。"""
    from playwright.sync_api import sync_playwright

    out_dir = OUT_ROOT / datetime.now().strftime("%Y%m%d")
    topo_path = out_dir / "topology.json"
    if not topo_path.exists():
        print("缺少 topology.json，请先跑 discover")
        return 2
    topo = json.loads(topo_path.read_text(encoding="utf-8"))
    cities = [args.city] if args.city else list(topo)

    with sync_playwright() as p:
        browser, ctx = _launch(p, headless=not args.headed)
        for city in cities:
            districts = sorted(
                [d for d in topo[city]["districts"] if not d.get("blocked")],
                key=lambda d: -(d.get("on_sale_total") or 0))
            for d in districts[:args.districts]:
                print(f"\n### {topo[city]['name']} / {d['name']}（区域在售 {d.get('on_sale_total')}）")
                for bc in d.get("bizcircles", []):
                    page, status, blocked = _goto(ctx, bc["url"])
                    if blocked:
                        bc["blocked"] = True
                        print(f"    {bc['name']}: 被拦")
                        page.close()
                        continue
                    bc["on_sale_total"], bc["total_pages"] = _page_stats(page)
                    page.close()
                    shown = (f"{bc['on_sale_total']} 套" if bc["on_sale_total"]
                             else f"页数 {bc['total_pages']}")
                    print(f"    {bc['name']}: {shown}")
                    sleep_a_bit(1.2, 2.6)
        browser.close()

    topo_path.write_text(json.dumps(topo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已回写板块套数: {topo_path}")
    return 0


def _pick_bizcircles(districts: list[dict], top: int) -> list[dict]:
    """选热门板块：有实测套数就按套数排，否则按所属区域套数轮转。"""
    rows = []
    for d in districts:
        if d.get("blocked"):
            continue
        for b in d.get("bizcircles", []):
            if b.get("blocked"):
                continue
            rows.append({**b, "district": d["name"],
                         "_w": (b.get("on_sale_total")
                                or (b.get("total_pages") or 0) * 30),
                         "_dw": d.get("on_sale_total") or 0})
    if not rows:
        return []
    if any(r["_w"] for r in rows):
        rows.sort(key=lambda r: (-r["_w"], -r["_dw"]))
        return rows[:top]
    # 没有实测套数：按区域量级轮转，避免全挤在同一区
    rows.sort(key=lambda r: -r["_dw"])
    by_d: dict[str, list] = {}
    for r in rows:
        by_d.setdefault(r["district"], []).append(r)
    picked = []
    for i in range(max((len(v) for v in by_d.values()), default=0)):
        for lst in by_d.values():
            if i < len(lst) and len(picked) < top:
                picked.append(lst[i])
    return picked[:top]


def _scrape_5i5j(ctx, city: str, args) -> dict:
    dom = {"sz": "sz"}.get(city, city)  # 苏州 sz、上海 sh
    result = {"host": f"https://{dom}.5i5j.com", "pages": [], "notes": []}
    for pg in range(1, args.pages + 1):
        url = f"https://{dom}.5i5j.com/ershoufang/" + ("" if pg == 1 else f"pg{pg}/")
        page, status, blocked = _goto(ctx, url)
        if blocked:
            result["notes"].append(f"p{pg} 被拦 -> {blocked[:100]}")
            print(f"    5i5j p{pg}: 被拦 {blocked[:60]}")
            page.close()
            break
        items, sel = parse_5i5j_items(page)
        raw = page.content()
        page.close()
        result["pages"].append({"page": pg, "count": len(items), "selector": sel,
                                "items": items, "html_len": len(raw)})
        print(f"    5i5j p{pg}: {len(items)} 条 (selector {sel or '未命中'})")
        if not items:
            break
        sleep_a_bit()
    return result


def cmd_dump(args) -> int:
    """保存指定 URL 的原始 HTML，用于核对页面结构。"""
    from playwright.sync_api import sync_playwright

    out_dir = OUT_ROOT / datetime.now().strftime("%Y%m%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, ctx = _launch(p, headless=not args.headed)
        page, status, blocked = _goto(ctx, args.url)
        html = page.content()
        page.close()
        browser.close()
    name = args.name or re.sub(r"[^\w\u4e00-\u9fa5-]", "_", args.url)[-60:]
    path = out_dir / f"dump_{name}.html"
    path.write_text(html, encoding="utf-8")
    print(f"status={status} blocked={blocked} size={len(html)} -> {path}")
    return 0


# ---------------------------------------------------------------- CSV

def cmd_csv(args) -> int:
    import csv

    out_dir = OUT_ROOT / datetime.now().strftime("%Y%m%d")
    files = sorted(out_dir.glob("data_*.json"))
    if not files:
        print("没有 data_*.json")
        return 2
    latest = files[-1]
    data = json.loads(latest.read_text(encoding="utf-8"))

    rows_list, rows_deal, rows_5i5j = [], [], []
    for city, c in data.get("cities", {}).items():
        for bc in c.get("bizcircles", []):
            for kind, sink in (("listings", rows_list), ("deals", rows_deal)):
                for it in bc.get(kind, []):
                    sink.append(it)
        for pg in c.get("fivei5j", {}).get("pages", []):
            for it in pg.get("items", []):
                it["city"] = city
                it["city_name"] = c.get("name")
                it["platform"] = "5i5j"
                rows_5i5j.append(it)

    base = ["city_name", "bizcircle", "district", "house_id", "title", "community",
            "total_price_wan", "unit_price_yuan", "house_type", "area_sqm",
            "orientation", "decoration", "floor", "total_floors", "build_year",
            "building_type", "tags", "deal_date", "follow_info", "url"]
    written = []

    def write(name: str, rows: list[dict], fields: list[str]):
        path = out_dir / name
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k) for k in fields})
        written.append((path, len(rows)))
        print(f"  {path.name}: {len(rows)} 行")

    if rows_list:
        write("贝壳_挂牌.csv", rows_list, base)
    if rows_deal:
        write("贝壳_成交.csv", rows_deal, base + ["position"])
    if rows_5i5j:
        write("我爱我家_挂牌.csv", rows_5i5j, base)

    print(f"\nCSV 输出目录: {out_dir}")
    (out_dir / "csv_manifest.json").write_text(json.dumps(
        {"source": latest.name,
         "generated": datetime.now().isoformat(timespec="seconds"),
         "files": [{"file": p.name, "rows": n} for p, n in written]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


# ---------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="苏州/上海 二手房数据抓取")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_login = sub.add_parser("login", help="人工登录并保存会话")
    p_login.add_argument("--wait", type=int, default=600, help="每个站点最长等待秒数")
    p_login.set_defaults(func=cmd_login)

    p_dis = sub.add_parser("discover", help="抓区域/板块拓扑")
    p_dis.add_argument("--city", choices=list(CITIES), help="只抓一个城市")
    p_dis.add_argument("--headed", action="store_true")
    p_dis.set_defaults(func=cmd_discover)

    p_probe = sub.add_parser("probe", help="实测各板块在售套数")
    p_probe.add_argument("--city", choices=list(CITIES))
    p_probe.add_argument("--districts", type=int, default=3, help="每城探测前几个区域")
    p_probe.add_argument("--headed", action="store_true")
    p_probe.set_defaults(func=cmd_probe)

    p_scr = sub.add_parser("scrape", help="抓挂牌与成交")
    p_scr.add_argument("--city", choices=list(CITIES))
    p_scr.add_argument("--top", type=int, default=6, help="每城抓几个热门板块")
    p_scr.add_argument("--pages", type=int, default=3, help="每板块每类抓几页(30条/页)")
    p_scr.add_argument("--min-page-items", type=int, default=20)
    p_scr.add_argument("--only", nargs="*", choices=["listings", "deals"])
    p_scr.add_argument("--skip-5i5j", action="store_true")
    p_scr.add_argument("--headed", action="store_true")
    p_scr.set_defaults(func=cmd_scrape)

    p_dump = sub.add_parser("dump", help="保存某页原始 HTML")
    p_dump.add_argument("url")
    p_dump.add_argument("--name")
    p_dump.add_argument("--headed", action="store_true")
    p_dump.set_defaults(func=cmd_dump)

    p_csv = sub.add_parser("csv", help="汇总成 CSV")
    p_csv.set_defaults(func=cmd_csv)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
