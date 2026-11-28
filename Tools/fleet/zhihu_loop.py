#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""zhihu_loop.py — 知乎线（2026-11-28 CEO：「你开个知乎的线自己管」）。

这条线与 B 站线、公众号线**完全隔离**，靠三件物理隔离：
  独立 profile（~/.fluxgroup/browser-zhihu）、独立数据目录、独立 launchd 作业。
所以它不经过 browserd（那条单线程被养号线占着），也不和 gzh 抢同一份料。

一、维护设计（为什么这么设计，别只照着写）

1. **通道只用真浏览器**。知乎 API 要 `x-zse-96` 签名，自己 fetch 必回
   40362「您当前请求存在异常」（2026-11-28 实测，登录态下也一样）。
   浏览器页面自己会算签名，所以读也只能读渲染后的 DOM——这是唯一稳的路。
2. **风控按"整拍退避"处理，不按"重试"处理**。403/40362 是账号或 IP 被判异常，
   重试只会把封禁窗口拉长。规则：一次 403 → 冷却 30 分钟；连续两次 → 停线报 CEO。
3. **节奏比内容重要**。知乎一个号一天的有效动作上限远低于 B 站：
   每批 ≤2 个问题页、每页 ≥8 秒、每天回复 ≤5 条且间隔 ≥15 分钟。刷量＝封号。
4. **判据只认真实结果**。回复/回答发出后，用**未登录的干净上下文**核可见性，
   而不是拿自己的台账自证。判不出（403/超时）一律记 unknown，不许当不可见。
5. **与另两条线不交叉选题**。同一篇内容在三个平台搬运会被判搬运号；
   本线只做"回答别人的具体问题"，不做公众号那种长文转载。

二、四段流水（一拍只做一件，顺序按"现在真能推进"排）
  collect  采问题与高赞答案（渲染后 DOM）→ 学风格、找选题
  learn    从高赞答案提结构特征（段落长度/开头方式/数字密度/结尾方式）
  reply    在相关问题下写回复（本地模型 + 闸），前 3 条人工确认后才发
  verify   发后 4h/24h 各核一次可见性（干净上下文），落真实结果

用法：
  zhihu_loop.py --once            # 一拍
  zhihu_loop.py --probe           # 只探活（能否读/能否写）
  zhihu_loop.py --status          # 看上一拍与冷却
  zhihu_loop.py --self-test
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
DATA = os.path.join(SOCIAL, "zhihu")
STATE = os.path.join(DATA, "state.json")
LEDGER = os.path.join(DATA, "LOOP-LEDGER.jsonl")
QUESTIONS = os.path.join(DATA, "QUESTIONS.jsonl")
ANSWERS = os.path.join(DATA, "ANSWERS.jsonl")
OUTCOMES = os.path.join(DATA, "OUTCOMES.jsonl")

PROFILE = os.path.expanduser("~/.fluxgroup/browser-zhihu")
CHROME = os.path.expanduser(
    "~/.fluxgroup/chrome/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing")
VENV_PY = os.path.join(ROOT, ".venv-housing", "bin", "python")


def _ensure_pw():
    """playwright 只装在 .venv-housing。系统 python 直接跑会在 import 时失败，
    而失败会被记成「采集 0 条」——环境问题冒充产出问题，是这套系统最常见的假象。
    这里直接换解释器重跑一次（带哨兵防递归），而不是让调用方去猜。
    """
    try:
        import playwright  # noqa: F401
        return
    except Exception:
        pass
    if os.environ.get("ZHIHU_REEXEC") == "1" or not os.path.exists(VENV_PY):
        raise SystemExit("playwright 不可用，且无法换解释器（%s）" % VENV_PY)
    os.environ["ZHIHU_REEXEC"] = "1"
    os.execv(VENV_PY, [VENV_PY, os.path.abspath(__file__)] + sys.argv[1:])

COOLDOWN_S = 1800          # 一次 403 冷静 30 分钟
STOP_AFTER_403 = 2         # 连续两次 403 就停线报 CEO
PAGE_WAIT_S = 8.0          # 每页停留（别抢，抢就是送人头）
MAX_PAGES = 2              # 一拍最多问题页数

# 搜索页是唯一稳定可读的入口（2026-11-28 实测：主页 200、搜索 200、39 张卡片可读；
# question/* 与 zhuanlan/* 一律 403+40362）。所以采集从"按关键词搜"入手：
# 拿得到的是**标题 + 约 120 字摘要**，够建选题库、够学标题风格；拿不到完整答案正文。
SEARCH_QUERIES = [
    "车机屏界面设计",
    "车载HMI 交互设计",
    "智能座舱 中控屏 布局",
    "车机 UI 字体 对比度",
    "汽车内饰 人机工程",
    "车机系统 卡顿 体验",
    "车载 语音交互 设计",
    "HUD 抬头显示 设计",
    "中控屏 图标 设计",
    "车机 深色模式 显示",
    "车载系统 信息架构",
    "座舱 多屏 交互",
    "汽车 UI 视觉 一致性",
    "车机 语音 误唤醒",
    "仪表盘 信息 层级",
]
SEARCH_FMT = "https://www.zhihu.com/search?type=content&q=%s"
# 首页流与热榜同样可达（2026-11-28 实测 200），而且是"人正在讨论什么"的最快信号。
FEED_URLS = ["https://www.zhihu.com/hot", "https://www.zhihu.com/follow"]


def iso():
    return datetime.now().isoformat(timespec="seconds")


def _rows(p):
    out = []
    try:
        for ln in open(p, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


def _append(p, rec):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def load_state():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:
        return {}


def save_state(d):
    os.makedirs(DATA, exist_ok=True)
    d = dict(d, ts=iso())
    tmp = STATE + ".tmp"
    json.dump(d, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, STATE)


def cooling(state=None, now=None):
    """现在是否在冷却窗口内。返回剩余秒数（0=可以干）。"""
    st = state if state is not None else load_state()
    now = now if now is not None else time.time()
    last = float(st.get("blocked_ts") or 0)
    left = COOLDOWN_S - (now - last)
    return int(left) if left > 0 else 0


def classify(reachable, http, body_head, me_name=None):
    """把一次探测归成三态 + 是否该停线。纯函数，便于自检。

    为什么单独抽出来：这是整条线的判据核心——把「被风控」误判成「采到 0 条」
    会让循环整夜空转并写出一堆假 FAIL，正是别的线上踩过的坑。
    """
    b = str(body_head or "")
    if "40362" in b or "请求存在异常" in b:
        return {"status": "BLOCKED-RISK", "why": "知乎风控 40362：整拍退避，不重试"}
    if http == 403:
        return {"status": "BLOCKED-403", "why": "403 但未见风控文案：按限流处理，退避"}
    if http == 401 or "请登录" in b or "signin" in str(b):
        return {"status": "NEED-LOGIN", "why": "登录态失效：需要 CEO 重新登录"}
    if not reachable:
        return {"status": "DOWN", "why": "打不开（超时/网络）"}
    if not me_name:
        return {"status": "NEED-LOGIN", "why": "能打开但取不到身份：多半未登录"}
    return {"status": "OK", "why": "可达且已登录：%s" % me_name}


def probe(timeout_s=40):
    """探活：能不能读、以谁的身份。返回 classify() 的结果。"""
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        return {"status": "DOWN", "why": "playwright 不可用：%s" % str(e)[:50]}
    if not os.path.isdir(PROFILE):
        return {"status": "NEED-LOGIN", "why": "profile 目录不存在：%s" % PROFILE}
    kw = dict(user_data_dir=PROFILE, headless=True, locale="zh-CN",
              timezone_id="Asia/Shanghai", viewport={"width": 1440, "height": 950},
              args=["--disable-blink-features=AutomationControlled"])
    if os.path.exists(CHROME):
        kw["executable_path"] = CHROME
    http, head, name = None, "", None
    try:
        with sync_playwright() as p:
            c = p.chromium.launch_persistent_context(**kw)
            try:
                pg = c.pages[0] if c.pages else c.new_page()
                r = pg.goto("https://www.zhihu.com/question/19550693",
                            wait_until="domcontentloaded", timeout=timeout_s * 1000)
                http = r.status if r else None
                time.sleep(2)
                head = pg.evaluate("()=>document.body?document.body.innerText.slice(0,200):''")
                # 身份：从首页拿（问题页被拦时首页通常还能开）
                try:
                    r2 = pg.goto("https://www.zhihu.com/", wait_until="domcontentloaded",
                                 timeout=timeout_s * 1000)
                    if (r2.status if r2 else 0) == 200:
                        name = pg.evaluate(
                            "()=>{const m=document.querySelector('.AppHeader-profile');"
                            "return m?m.innerText.trim().slice(0,20):'';}") or None
                except Exception:
                    pass
            finally:
                c.close()
    except Exception as e:
        return {"status": "DOWN", "why": "浏览器异常：%s" % str(e)[:60]}
    return classify(True, http, head, name)


def collect_search(queries=None, log=print):
    """从搜索页采集（唯一稳定入口）：标题 + 摘要 + 链接。

    为什么不用问题页：question/* 与 zhuanlan/* 在 2026-11-28 实测一律 403+40362，
    而 /search?type=content 返回 200、一页 39 张卡片、每张 110-130 字。

    **查询必须轮换**：2026-11-28 实测连采两批后，卡片从 136 涨到 232，但去重后的
    相关选题一直卡在 34 条——因为每拍都搜同样两个词，返回的还是同一批。
    所以按 state 里的 cursor 逐个往前走，一轮走完 8 个查询再看总数。
    """
    st = load_state()
    cur = int(st.get("q_cursor") or 0)
    all_q = queries or SEARCH_QUERIES
    picked = [all_q[(cur + i) % len(all_q)] for i in range(2)]
    st["q_cursor"] = (cur + 2) % len(all_q)
    save_state(st)
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        return 1, "playwright 不可用：%s" % str(e)[:50], 0
    kw = dict(user_data_dir=PROFILE, headless=True, locale="zh-CN",
              timezone_id="Asia/Shanghai", viewport={"width": 1440, "height": 950},
              args=["--disable-blink-features=AutomationControlled"])
    if os.path.exists(CHROME):
        kw["executable_path"] = CHROME
    got = 0
    seen_titles = {(parse_card(r.get("text"))["title"] or "").strip() for r in _rows(ANSWERS)}
    try:
        with sync_playwright() as p:
            c = p.chromium.launch_persistent_context(**kw)
            try:
                pg = c.pages[0] if c.pages else c.new_page()
                # 先刷两类"可达入口"：热榜/关注流（人正在讨论什么）+ 轮换后的关键词搜索
                targets = [(u, "feed") for u in FEED_URLS] + \
                          [(SEARCH_FMT % __import__("urllib.parse", fromlist=["quote"]).quote(q), q)
                           for q in picked]
                for u, q in targets:
                    r = pg.goto(u, wait_until="domcontentloaded", timeout=40000)
                    http = r.status if r else None
                    time.sleep(4)
                    head = pg.evaluate("()=>document.body?document.body.innerText.slice(0,200):''")
                    cls = classify(True, http, head, me_name="probe")
                    if cls["status"].startswith("BLOCKED") or cls["status"] in ("NEED-LOGIN", "DOWN"):
                        return 2, cls["why"] + "（入口=%s）" % q, got
                    for _ in range(2):
                        pg.mouse.wheel(0, 2200)
                        time.sleep(1.5)
                    cards = pg.evaluate("""()=>{const out=[];
                        const sel='.SearchResult-Card,.HotItem,.ContentItem';
                        document.querySelectorAll(sel).forEach(c=>{
                          const t=(c.innerText||'').trim();
                          if(t.length<40) return;
                          const a=c.querySelector('a[href*="/question/"],a[href*="/p/"]');
                          out.push({text:t.slice(0,400), url:a?a.href:''});});
                        return out.slice(0,25);}""") or []
                    _append(QUESTIONS, {"ts": iso(), "q": q, "http": http, "cards": len(cards)})
                    new = 0
                    for cd in cards:
                        ttl = (parse_card(cd.get("text"))["title"] or "").strip()
                        if ttl and ttl in seen_titles:      # 同题不重复入库，省得台账虚胖
                            continue
                        if ttl:
                            seen_titles.add(ttl)
                        _append(ANSWERS, {"ts": iso(), "q": q, "url": cd.get("url"),
                                          "chars": len(cd.get("text") or ""),
                                          "text": cd.get("text")})
                        got += 1
                        new += 1
                    log("[zhihu] %s → %d 张（新增 %d）" % (q, len(cards), new))
            finally:
                c.close()
    except Exception as e:
        return 1, "采集异常：%s" % str(e)[:60], got
    return 0, "搜索采集完成", got


def collect(limit_pages=MAX_PAGES, log=print):
    """采问题与高赞答案（渲染后 DOM）。被风控直接返回 BLOCKED，不重试。"""
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        return 1, "playwright 不可用：%s" % str(e)[:50], 0
    kw = dict(user_data_dir=PROFILE, headless=True, locale="zh-CN",
              timezone_id="Asia/Shanghai", viewport={"width": 1440, "height": 950},
              args=["--disable-blink-features=AutomationControlled"])
    if os.path.exists(CHROME):
        kw["executable_path"] = CHROME
    got = 0
    try:
        with sync_playwright() as p:
            c = p.chromium.launch_persistent_context(**kw)
            try:
                pg = c.pages[0] if c.pages else c.new_page()
                seeds = [r.get("url") for r in _rows(QUESTIONS) if r.get("url")][:limit_pages]
                if not seeds:
                    seeds = ["https://www.zhihu.com/question/19550693"]
                for u in seeds:
                    r = pg.goto(u, wait_until="domcontentloaded", timeout=40000)
                    http = r.status if r else None
                    time.sleep(PAGE_WAIT_S)
                    head = pg.evaluate("()=>document.body?document.body.innerText.slice(0,200):''")
                    cls = classify(True, http, head, me_name="probe")
                    if cls["status"].startswith("BLOCKED") or cls["status"] in ("NEED-LOGIN", "DOWN"):
                        return 2, cls["why"], got
                    for i in range(2):
                        pg.mouse.wheel(0, 2200)
                        time.sleep(1.2)
                    rows = pg.evaluate("""()=>{
                        const out=[];
                        document.querySelectorAll('.AnswerItem,.ContentItem').forEach(a=>{
                          const body=a.querySelector('.RichContent-inner');
                          const who=a.querySelector('.AuthorInfo-name');
                          const vote=a.querySelector('.VoteButton--up');
                          const txt=body?body.innerText:'';
                          if(txt.length<80) return;
                          out.push({author: who?who.innerText.trim():'', vote: vote?vote.innerText.trim():'',
                                    text: txt.slice(0,4000)});
                        });
                        return out.slice(0,10);}""") or []
                    title = pg.title()
                    _append(QUESTIONS, {"ts": iso(), "url": u, "title": title, "answers": len(rows)})
                    for a in rows:
                        _append(ANSWERS, {"ts": iso(), "q_url": u, "q_title": title,
                                          "author": a.get("author"), "vote": a.get("vote"),
                                          "chars": len(a.get("text") or ""),
                                          "text": a.get("text")})
                        got += 1
                    log("[zhihu] %s → %d 条答案" % (u[-24:], len(rows)))
            finally:
                c.close()
    except Exception as e:
        return 1, "采集异常：%s" % str(e)[:60], got
    return 0, "采集完成", got


def parse_card(text):
    """把搜索卡片拆成 题目/作者/正文。格式实测：「标题\\n作者：正文…」。"""
    t = (text or "").strip()
    lines = [x.strip() for x in t.split("\n") if x.strip()]
    if not lines:
        return {"title": "", "author": "", "body": ""}
    title = lines[0]
    rest = " ".join(lines[1:])
    author, body = "", rest
    if "：" in rest[:20]:
        author, body = rest.split("：", 1)
    return {"title": title, "author": author.strip(), "body": body.strip()}


def learn(log=print):
    """从已采卡片提可量化的选题/标题特征。

    只说数据能说的：现在拿到的是**搜索卡片（标题+摘要约 123 字）**，
    不是完整答案，所以只统计标题与摘要层面的特征，不假装能分析答案结构。
    """
    rows = _rows(ANSWERS)
    if len(rows) < 5:
        return 1, "样本不足（%d 条，至少 5）" % len(rows), {}
    import re
    import statistics as st
    cards = [parse_card(r.get("text")) for r in rows]
    titles = [c["title"] for c in cards if c["title"]]
    bodies = [c["body"] for c in cards if c["body"]]
    tl = [len(x) for x in titles]
    with_num = sum(1 for x in titles if re.search(r"\d", x))
    ask = sum(1 for x in titles if re.search(r"[？?]\s*$", x))
    heads = {}
    for b in bodies:
        k = b[:2]
        heads[k] = heads.get(k, 0) + 1
    d = {"basis": "search-card（标题+摘要）", "n": len(rows),
         "title_median": round(st.median(tl), 1) if tl else 0,
         "title_with_num_pct": round(100.0 * with_num / max(1, len(titles))),
         "title_question_pct": round(100.0 * ask / max(1, len(titles))),
         "body_median": round(st.median([len(b) for b in bodies]), 1) if bodies else 0,
         "top_openers": sorted(heads.items(), key=lambda kv: -kv[1])[:5]}
    log("[zhihu] 学习：%d 张卡片 / 标题中位 %s 字 / 含数字 %s%% / 摘要中位 %s 字"
        % (d["n"], d["title_median"], d["title_with_num_pct"], d["body_median"]))
    return 0, "已学习", d


TOPIC_TARGET = 80          # 选题库目标。2026-11-28 标定：8 个查询轮一遍能到 ~75
                           # （实测 34→53→73），所以目标定 80 而不是拍 120；
                           # 想再高必须加查询词，不是延长采集时间。
DRAFT_DIR = os.path.join(DATA, "drafts")


def unique_topics():
    """去重后与车/座舱相关的选题数。判据是这条线"推进到哪了"的唯一刻度。"""
    kw = ("车机", "座舱", "HMI", "中控", "仪表", "内饰", "屏幕", "界面",
          "交互", "语音", "HUD", "车载", "驾驶")
    junk = ("相关搜索", "大家都在搜", "热门推荐", "广告")
    seen = set()
    for r in _rows(ANSWERS):
        c = parse_card(r.get("text"))
        t = (c["title"] or "").strip()
        if not t or any(j in t for j in junk):
            continue
        if not any(k in (t + c["body"]) for k in kw):
            continue
        seen.add(t)
    return len(seen)


def draft_today():
    p = os.path.join(DRAFT_DIR, datetime.now().strftime("%Y-%m-%d") + ".md")
    try:
        return os.path.getsize(p) > 600
    except Exception:
        return False


def pick_topic():
    """从已采卡片里挑一个最贴专业面的选题（优先含 中控/车机/字体/布局 的标题）。"""
    pref = ("中控", "车机", "字体", "布局", "对比度", "层级", "图标", "HUD", "交互")
    cands = []
    for r in _rows(ANSWERS):
        c = parse_card(r.get("text"))
        t = (c["title"] or "").strip()
        if len(t) < 8 or t in [x[0] for x in cands]:
            continue
        if not any(k in (t + c["body"]) for k in ("车机", "座舱", "中控", "HMI", "界面")):
            continue
        score = sum(1 for k in pref if k in t)
        cands.append((score, t, c["body"][:120]))
    cands.sort(key=lambda x: -x[0])
    return cands[0] if cands else None


def write_draft(log=print):
    """写一篇答案草稿：本地 4B 生成 → 严谨闸 + 权威闸 → 落盘进人审。

    为什么只用两闸：结构闸是按公众号长文标定的（段落中位 78 字/8-10 张图），
    拿它判知乎答案会把正常答案判死。知乎侧的结构判据还没标定，所以**先不假装有**。
    """
    topic = pick_topic()
    if not topic:
        return 1, "没有可用选题（先采）"
    _, title, excerpt = topic
    try:
        import llm_client as L
    except Exception as e:
        return 1, "llm_client 不可用：%s" % str(e)[:40]
    prompt = (
        "你在知乎回答一个具体问题。问题/参考标题：%s\n参考摘要：%s\n\n"
        "要求：\n"
        "1. 第一句直接给判断，不铺垫、不写「这个问题很好」。\n"
        "2. 3 段以内，每段不超过 120 字；用具体物和具体数字说话（比例/尺寸/色值/交互步数）。\n"
        "3. 只写你能负责的内容：不编标准编号、不编实测里程、不编「我曾参与某项目」。\n"
        "4. 至少一句承认自己可能错在哪。\n"
        "5. 结尾给明确取舍：什么情况下别听我的。\n"
        "只输出正文，不要标题以外的解释。\n" % (title, excerpt))
    r = L.generate(prompt, cls="resident", keep_alive="10m", num_predict=700,
                   timeout=300, think=False)
    if not r.get("ok"):
        return 1, "模型失败：%s" % str(r.get("why"))[:60]
    text = (r.get("text") or "").strip()
    if len(text) < 150:
        return 1, "稿子过短（%d 字）" % len(text)
    os.makedirs(DRAFT_DIR, exist_ok=True)
    day = datetime.now().strftime("%Y-%m-%d")
    p = os.path.join(DRAFT_DIR, day + ".md")
    with open(p, "w", encoding="utf-8") as f:
        f.write("<!-- 选题：%s\n     参考：%s\n     席位：resident/4B；状态 NEEDS-HUMAN -->\n\n"
                % (title, excerpt))
        f.write(text + "\n")
    man = {"date": day, "topic": title, "chars": len(text), "seat": "resident",
           "status": "NEEDS-HUMAN", "gates": {}}
    # 两闸：严谨（AI 指纹）+ 权威（编造标准/履历）。任一红都记下，但不改稿。
    import subprocess
    for name, script in (("rigor", "gzh_rigor_check.py"), ("authority", "gzh_authority_check.py")):
        try:
            q = subprocess.run([sys.executable, os.path.join(HERE, script), "--in", p],
                               capture_output=True, text=True, timeout=120)
            man["gates"][name] = q.returncode
            if q.returncode != 0:
                man.setdefault("gate_tail", {})[name] = (q.stdout or "")[:200]
        except Exception as e:
            man["gates"][name] = 9
            man.setdefault("gate_tail", {})[name] = str(e)[:80]
    json.dump(man, open(os.path.join(DRAFT_DIR, day + ".json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    log("[zhihu] 草稿 %d 字 → %s（闸 %s）" % (len(text), p, man["gates"]))
    return 0, "草稿已出（NEEDS-HUMAN）"


def decide(st=None, now=None):
    """一拍做一件。顺序＝现在真能推进的那件。

    推进顺序刻意做成"池子没攒够就先攒"：选题库 < 目标时，出稿再多也是瞎写；
    攒够才出稿；出完稿才轮到回复（而回复还卡在问题页 403）。
    """
    st = st if st is not None else load_state()
    now = now if now is not None else time.time()
    # 冷却必须按**通道**算：问题页被拦不代表搜索页被拦（2026-11-28 实测正是如此：
    # question/* 403，而 /search 200）。拿问题页的冷却去挡搜索采集，就是自己把活停掉。
    scope = st.get("block_scope") or "question"
    left = cooling(st, now) if scope == "search" else 0
    if left:
        return {"phase": "cool", "why": "搜索通道风控冷却中，剩 %d 分钟（不重试）" % (left // 60 + 1)}
    if int(st.get("consecutive_403") or 0) >= STOP_AFTER_403:
        return {"phase": "stop", "why": "连续 %d 次 403：停线报 CEO，等人处理登录/风控"
                                       % int(st.get("consecutive_403"))}
    n_topics = unique_topics()
    if n_topics < TOPIC_TARGET:
        return {"phase": "collect", "why": "选题库 %d/%d：先攒够再谈出稿" % (n_topics, TOPIC_TARGET)}
    if not st.get("learned_n") or st.get("learned_n") != len(_rows(ANSWERS)):
        return {"phase": "learn", "why": "样本变了（%d 条）：重学标题基线" % len(_rows(ANSWERS))}
    if not draft_today():
        return {"phase": "write", "why": "今天还没有答案草稿：按选题写一篇（进人审）"}
    if int(st.get("consecutive_403") or 0) == 0 and st.get("answer_ok"):
        return {"phase": "reply", "why": "问题页可用：写回复并送人审"}
    return {"phase": "idle", "why": "池子与草稿都就绪，回复待问题页解封（40362）"}


def once(dry=False, log=print):
    st = load_state()
    d = decide(st)
    if dry:
        log("[zhihu] 决策：%s（%s）" % (d["phase"], d["why"]))
        return 0
    if d["phase"] == "cool":
        save_state(st)
        _append(LEDGER, {"ts": iso(), "phase": "cool", "status": "SKIP", "why": d["why"]})
        log("[zhihu] SKIP：%s" % d["why"])
        return 0
    if d["phase"] == "stop":
        _append(LEDGER, {"ts": iso(), "phase": "stop", "status": "BLOCKED", "why": d["why"]})
        log("[zhihu] BLOCKED：%s" % d["why"])
        return 2
    if d["phase"] == "collect":
        # 优先搜索采集：问题页当前一律 403，硬试只会把风控窗口拉长。
        rc, why, got = collect_search(log=log)
        if rc == 2:      # 被风控/未登录（搜索通道）
            st["blocked_ts"] = time.time()
            st["block_scope"] = "search"
            st["consecutive_403"] = int(st.get("consecutive_403") or 0) + 1
            st["last_why"] = why
            save_state(st)
            _append(LEDGER, {"ts": iso(), "phase": "collect", "status": "BLOCKED", "why": why})
            log("[zhihu] BLOCKED：%s（冷却 %d 分钟）" % (why, COOLDOWN_S // 60))
            return 2
        st["consecutive_403"] = 0
        save_state(st)
        # rc==1 是环境/程序故障，不是"采到 0 条"。两者必须分开记，
        # 否则"playwright 没装"会在面板上长期伪装成"今天没有新内容"。
        status = "OK" if rc == 0 and got else ("FAIL" if rc == 1 else "EMPTY")
        _append(LEDGER, {"ts": iso(), "phase": "collect", "status": status,
                         "why": why, "got": got})
        log("[zhihu] %s：%d 条" % (why, got))
        return 0 if rc == 0 and got else (1 if rc == 1 else 3)
    if d["phase"] == "learn":
        rc, why, info = learn(log=log)
        st["learned_n"] = len(_rows(ANSWERS))
        st["learned"] = info
        save_state(st)
        _append(LEDGER, {"ts": iso(), "phase": "learn", "status": "OK" if rc == 0 else "FAIL",
                         "why": why, "info": info})
        return rc
    if d["phase"] == "write":
        rc, why = write_draft(log=log)
        save_state(st)
        _append(LEDGER, {"ts": iso(), "phase": "write",
                         "status": "OK" if rc == 0 else "FAIL", "why": why})
        log("[zhihu] %s" % why)
        return rc
    if d["phase"] == "idle":
        save_state(st)
        _append(LEDGER, {"ts": iso(), "phase": "idle", "status": "DEFER", "why": d["why"]})
        log("[zhihu] DEFER：%s" % d["why"])
        return 0
    _append(LEDGER, {"ts": iso(), "phase": "reply", "status": "DEFER",
                     "why": "回复默认进人审队列，不自动发"})
    log("[zhihu] 回复进人审队列（不自动发）")
    return 0


def self_test():
    cases = []
    # 1 风控：40362 必须判 BLOCKED-RISK，不能当"采到 0 条"
    c = classify(True, 403, '{"error":{"message":"您当前请求存在异常...","code":40362}}', "x")
    cases.append(("40362 → BLOCKED-RISK", c["status"] == "BLOCKED-RISK"))
    # 2 光 403 没有风控文案 → BLOCKED-403（也不能当正常）
    c = classify(True, 403, "Forbidden", "x")
    cases.append(("403 无文案 → BLOCKED-403", c["status"] == "BLOCKED-403"))
    # 3 401/请登录 → NEED-LOGIN
    c = classify(True, 401, "请登录后查看", None)
    cases.append(("401 → NEED-LOGIN", c["status"] == "NEED-LOGIN"))
    # 4 能开但取不到身份 → NEED-LOGIN（不许当 OK）
    c = classify(True, 200, "首页", "")
    cases.append(("可达但无身份 → NEED-LOGIN", c["status"] == "NEED-LOGIN"))
    # 5 正常 → OK
    c = classify(True, 200, "首页", "大喵你不懂")
    cases.append(("可达且已登录 → OK", c["status"] == "OK"))
    # 6 冷却只对**被拦的那个通道**生效：搜索通道被拦 → 冷却
    d = decide({"blocked_ts": time.time() - 60, "block_scope": "search",
                "consecutive_403": 1}, now=time.time())
    cases.append(("搜索通道被拦 → 冷却中", d["phase"] == "cool"))
    # 6b 负控：问题页被拦**不许**挡住搜索采集（实测正是 question 403 / search 200）
    d = decide({"blocked_ts": time.time() - 60, "block_scope": "question",
                "consecutive_403": 1}, now=time.time())
    cases.append(("问题页被拦 → 不挡搜索采集", d["phase"] != "cool"))
    # 7 冷却过期 → 不在冷却
    d = decide({"blocked_ts": time.time() - COOLDOWN_S - 10, "block_scope": "search",
                "consecutive_403": 1}, now=time.time())
    cases.append(("冷却过期 → 不在冷却", d["phase"] != "cool"))
    # 8 连续两次 403 → 停线
    d = decide({"blocked_ts": 0, "consecutive_403": STOP_AFTER_403}, now=time.time())
    cases.append(("连续两次 403 → 停线", d["phase"] == "stop"))
    # 9 样本少 → 先采
    d = decide({"blocked_ts": 0, "consecutive_403": 0}, now=time.time())
    cases.append(("答案不足 20 → 先采", d["phase"] == "collect" or d["phase"] == "learn"))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  [%s] %s" % ("PASS" if v else "FAIL", n))
    print("[zhihu] self-test %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--collect", action="store_true", help="强制跑一批采集（跳过 decide 顺序）")
    a = ap.parse_args()
    if a.self_test:          # 纯逻辑自检，不需要 playwright
        return self_test()
    _ensure_pw()
    if a.collect:
        rc, why, got = collect_search(log=print)
        print("[zhihu] %s：%d 条（rc=%d）" % (why, got, rc))
        return 0 if rc == 0 else rc
    if a.probe:
        r = probe()
        print(json.dumps(r, ensure_ascii=False))
        return 0 if r["status"] == "OK" else 2
    if a.status:
        st = load_state()
        left = cooling(st)
        print(json.dumps({"state": st, "cooling_s": left,
                          "answers": len(_rows(ANSWERS)),
                          "questions": len(_rows(QUESTIONS)),
                          "last": (_rows(LEDGER) or [{}])[-1]}, ensure_ascii=False, indent=1))
        return 0
    return once(dry=a.dry)


if __name__ == "__main__":
    sys.exit(main())
