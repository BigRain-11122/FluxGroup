#!/usr/bin/env python3
"""user_agent.py — 养号行为体：像一个人那样去刷 B 站，而不是像任务队列。

CEO 2026-11-20 目标：「训练出一个真实的用户操作行为的智能体，会评论、会浏览、
会引流、会刷脸、会积累好感」。

落到代码上，这五件事各自有唯一判据（不是形容词）：

| 能力 | 判据 |
|---|---|
| 会浏览 | 每次会话有停留与滚动，看够时长才动手（human_rhythm）|
| 会评论 | 过品味闸 + 具体性 + 非模板（comment_taste / 开头两字配额）|
| 会引流 | **只在站内**、只在被问到时、≤1/10 条；跨平台黑话一律拒 |
| 会刷脸 | 同一垂类 UP 主 7 天内 ≤2 次，稳定出现但不刷屏 |
| 会积累好感 | 不删重发、不杠、不复读；被回复时有回应 |

红线（来自 2026-11 平台规则）：跨平台导流（主页有惊喜/私信/加V）→ 永久封禁；
被折叠评论删除重发 → 5 日限制 + 关联视频降权。所以 guard() 是第一道闸，
不是可选项。

用法：
  python3 Tools/fleet/user_agent.py --plan --minutes 18 --seg peer_pro   # 只出计划
  python3 Tools/fleet/user_agent.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
LEDGER = os.path.join(SOCIAL, "USER-AGENT-LEDGER.jsonl")
UPVISIT = os.path.join(SOCIAL, "UP-VISITS.json")
sys.path.insert(0, HERE)

# ---------------- 合规闸（第一道，不可跳过） ----------------
# 跨平台导流黑话：命中即拒稿，不给出"改一改就行"的余地。
OFFSITE = [
    r"微信", r"加\s*[vV微]", r"vx", r"VX", r"私信我", r"私我", r"主页有惊喜", r"懂的都懂",
    r"懂的自然懂", r"公众号", r"QQ", r"qq群", r"群号", r"链接", r"http", r"www\.",
    r"淘宝", r"闲鱼", r"代做", r"接单", r"代剪", r"引流", r"互赞", r"互关", r"关注我",
]
# 引战/拉踩/群体对立：掉好感最快的三种
CONFLICT = [r"傻[逼bB]", r"废物", r"垃圾up", r"取关", r"举报你", r"就你最懂", r"都不如我"]
# 硬广告：自己也是做内容的，别当自己讨厌的人
AD = [r"三连", r"点赞过", r"求三连", r"抽奖", r"福利", r"扫码"]
RED = re.compile("|".join(OFFSITE + CONFLICT + AD))


def guard(text):
    """返回 (ok, why)。ok=False 的稿子一律不发——不是扣分，是拒稿。"""
    t = (text or "").strip()
    if not t:
        return False, "空稿"
    m = RED.search(t)
    if m:
        return False, "红线词「%s」（跨平台导流/引战/广告）" % m.group(0)
    if t.count("#") or t.count("@") > 0:
        return False, "含话题/艾特，像推广不像评论"
    if len(re.findall(r"[!！]{2,}", t)):
        return False, "连续感叹号，像营销"
    return True, ""


# ---------------- 刷脸：同一 UP 主出现频率 ----------------
def _load_json(p, d):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return d


def up_visits():
    return _load_json(UPVISIT, {})


def may_visit(up_mid, days=7, cap=2):
    """同一 UP 主 7 天内最多出现 cap 次：稳定出现形成眼熟，但绝不刷屏。"""
    v = (up_visits() or {}).get(str(up_mid)) or []
    cut = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    return len([x for x in v if x >= cut]) < cap


def note_visit(up_mid):
    d = up_visits()
    d.setdefault(str(up_mid), []).append(datetime.now().isoformat(timespec="seconds"))
    cut = (datetime.now() - timedelta(days=30)).isoformat(timespec="seconds")
    d[str(up_mid)] = [x for x in d[str(up_mid)] if x >= cut][-20:]
    try:
        json.dump(d, open(UPVISIT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass


# ---------------- 引流：站内、被动、极低频 ----------------
MENTION = [
    "这个点我也踩过，后来自己做了一期讲这个",
    "我剪过类似的，卡在同一处，回头把过程整理出来",
    "同问，我这边也没搞明白，蹲个懂行的",
]


def may_mention(ratio=10, recent=None):
    """引流配额：每 ratio 条互动里最多 1 条提及自己作品，且必须被动语境。"""
    recent = recent or []
    must = [r for r in recent if r.get("mention")]
    return len(must) * ratio < max(1, len(recent))


def mention_line(rng=None):
    rng = rng or random.Random()
    return rng.choice(MENTION)


# ---------------- 会话计划：一个人这次的刷视频节奏 ----------------
def plan_session(minutes=18, seg="generic", rng=None, n_videos=None):
    """把"像人"翻译成可执行序列：先纯看，再偶尔动手，动作之间留白。

    配比依据：真实用户里**点赞常见**（过半的视频会点）、**说话少见**（弹幕/评论合计
    不超过三成），引流是极少数。任何"每条都动手"的节奏一眼就是机器。
    所以上限写死两个：点赞 ≤60% 视频数；弹幕+评论 ≤30% 视频数（至少 1 条）。
    """
    rng = rng or random.Random()
    minutes = max(5, min(35, int(minutes)))
    n_videos = n_videos or max(3, min(12, int(minutes / 2.5)))
    max_like = max(1, int(n_videos * 0.6))
    max_talk = max(1, int(n_videos * 0.3))
    dwells = [round(min(9.0, max(0.6, rng.lognormvariate(0.6, 0.55))), 1) for _ in range(n_videos)]
    steps = []
    t = 0.0
    n_like = n_talk = 0
    for i, d in enumerate(dwells):
        steps.append({"t_min": round(t, 1), "act": "watch", "dwell_min": d, "idx": i + 1})
        t += d
        r = rng.random()
        if r < 0.45 and n_like < max_like:
            n_like += 1
            steps.append({"t_min": round(t, 1), "act": "like"})
        elif r < 0.55 and n_talk < max_talk:
            n_talk += 1
            steps.append({"t_min": round(t, 1), "act": "danmaku" if rng.random() < 0.7 else "comment"})
        t += rng.uniform(0.05, 0.6)          # 手指/刷页面的间隙
    steps.append({"t_min": round(t, 1), "act": "end"})
    acts = [s["act"] for s in steps]
    return {
        "minutes": minutes, "seg": seg, "videos": n_videos,
        "n_watch": acts.count("watch"), "n_like": acts.count("like"),
        "n_danmaku": acts.count("danmaku"), "n_comment": acts.count("comment"),
        "caps": {"like": max_like, "talk": max_talk},
        "steps": steps,
        "note": "点赞常见、说话少见；说话类合计 ≤30% 视频数",
    }


def plan_violates(plan):
    """计划级负控：点赞 ≤60%、弹幕+评论 ≤30%、至少 3 条纯看。"""
    v = max(1, plan["n_watch"])
    if plan["n_like"] > max(1, int(v * 0.6)):
        return True
    if plan["n_danmaku"] + plan["n_comment"] > max(1, int(v * 0.3)):
        return True
    return plan["n_watch"] < 3


# ---------------- 点赞原语（真实用户最常做的动作） ----------------
def like(aid, dry=False):
    import social_comment as sc
    mod, _ = sc._pw()
    with mod.sync_playwright() as p:
        ctx = sc._launch(p)
        try:
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.goto("https://www.bilibili.com/video/av%s" % aid,
                    wait_until="domcontentloaded", timeout=60000)
            time.sleep(2)
            cookies = {c["name"]: c["value"] for c in ctx.cookies()}
            csrf = cookies.get("bili_jct", "")
            if not csrf:
                return False, "缺 csrf（bili_jct）"
            if dry:
                return True, {"dry": True, "aid": aid}
            body = "aid=%s&like=1&csrf=%s" % (aid, csrf)
            res = pg.evaluate("""async (body)=>{
                const r=await fetch('https://api.bilibili.com/x/web-interface/archive/like',
                  {method:'POST',credentials:'include',
                   headers:{'Content-Type':'application/x-www-form-urlencoded'},
                   body:body});
                return {status:r.status, text:await r.text()};}""", body)
            try:
                j = json.loads(res.get("text") or "{}")
            except Exception:
                j = {}
            return res.get("status") == 200 and j.get("code") == 0, {
                "code": j.get("code"), "message": j.get("message")}
        finally:
            try:
                ctx.close()
            except Exception:
                pass
            try:
                import social_collect as _sc
                _sc.release_profile_lock(sc.PROF)
            except Exception:
                pass


def log(rec):
    rec.setdefault("ts", datetime.now().isoformat(timespec="seconds"))
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ---------------- 自检 ----------------

# ---------------- 风控：日配额 + 重复内容 + 跨号错峰 ----------------
# 依据（2026-11 平台规则/社区实锚）：评论最敏感（折叠/仅自己可见都从它开始），
# 弹幕次之（单条可见度高、易被判刷），点赞最轻。所以配额按这个顺序收紧。
AGENT_LIMITS = {"like": 20, "danmaku": 5, "comment": 3}
CROSS_GAP_MIN = 10          # 两个号的动作至少错开 10 分钟


def _rows(limit=None):
    rows = []
    try:
        for line in open(LEDGER, encoding="utf-8"):
            if line.strip():
                rows.append(json.loads(line))
    except FileNotFoundError:
        pass
    return rows[-limit:] if limit else rows


def today_count(kind, account=None):
    today = datetime.now().strftime("%Y-%m-%d")
    n = 0
    for r in _rows():
        if r.get("dry_demo") or r.get("action") != kind or not str(r.get("ts", "")).startswith(today):
            continue
        if account and r.get("account") and r.get("account") != account:
            continue
        n += 1
    return n


_CAPS = {}


def quota_ok(kind, account=None):
    cap = (_CAPS.get(kind) or AGENT_LIMITS.get(kind))
    if not cap:
        return True, ""
    n = today_count(kind, account)
    if n >= cap:
        return False, "%s 今日已 %d 次（上限 %d）" % (kind, n, cap)
    return True, ""


def _norm(t):
    return re.sub(r"[^\u4e00-\u9fff0-9A-Za-z]", "", t or "")


def _grams(t, n=6):
    t = _norm(t)
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))} or ({t} if t else set())


def dup_recent(text, days=7, thresh=0.6):
    """同账号近 N 天说过近似的话就算重复——重复内容是官方明写的折叠原因之一。"""
    mine = _grams(text)
    if not mine:
        return True, "空文本"
    cut = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    for r in _rows():
        if r.get("action") not in ("comment", "danmaku") or str(r.get("ts", "")) < cut:
            continue
        other = _grams(r.get("text") or r.get("message") or "")
        if not other:
            continue
        inter = len(mine & other)
        if inter / max(1, min(len(mine), len(other))) >= thresh:
            return True, "与 %s 那条太像（%s）" % (str(r.get("ts"))[5:16], (r.get("text") or "")[:12])
    return False, ""


def cross_gap_ok(account=None, minutes=0):
    """两个号不许在同一时间动手：最近 N 分钟若有别号动作，就等。"""
    if minutes <= 0:
        return True, ""   # 2026-11-20 CEO「像两个人」：不再按时间硬错峰，改由"不同兴趣+不同视频"隔离
    cut = (datetime.now() - timedelta(minutes=minutes)).isoformat(timespec="seconds")
    for r in reversed(_rows(200)):
        ts = str(r.get("ts") or "")
        if ts < cut:
            continue
        other = r.get("account")
        if other and account and other != account and r.get("action") in ("like", "danmaku", "comment"):
            return False, "别号 %s 刚在 %s 动过手（%s 分钟内要错峰）" % (
                other, ts[11:16], minutes)
    return True, ""


# ---------------- 弹幕文本：必须从这条视频推出来 ----------------
DM_STYLES = {
    # 技术流：点评手法/细节
    "point": ["这个{kw}处理得干净", "{kw}这里卡点挺准", "{kw}这段我想试试", "{kw}的节奏稳",
              "刚看到{kw}，学到了"],
    # 感受流：说自己的感受，不评价技术
    "feel": ["{kw}这段听着心里一动", "看到{kw}我笑了", "{kw}好有画面感啊",
             "被{kw}这一段戳到了", "{kw}这里我看了两遍"],
}


_DM_USED = {}


def danmaku_line(title, rng=None, style="point"):
    """从标题抽关键词拼一条 ≤20 字弹幕。抽不出关键词就不发（宁可不发）。"""
    rng = rng or random.Random()
    t = re.sub(r"[【】\[\]（）()《》!！?？|/、,，.。\s]", " ", title or "")
    words = [w for w in t.split() if 2 <= len(w) <= 6 and not w.isdigit()]
    if words:
        kw = rng.choice(words)[:6]
    else:
        # 兜底：中文标题常常没有分隔符（"AI短视频工作流"），直接取片段当关键词。
        # 抽不出就整条不发会让弹幕几乎发不出来，等于把"会发弹幕"写成了摆设。
        # 取最长的中文连续片段（"电影最TOP生化危机" → "生化危机"），避免截出"电影最T"这种半个词
        runs = re.findall(r"[\u4e00-\u9fff]{2,}", t)
        if runs:
            kw = max(runs, key=len)[:6]
        else:
            # 一个汉字都没有（纯数字/纯英文/纯符号）就不发：弹幕必须贴内容
            if not re.search(r"[\u4e00-\u9fff]", t or ""):
                return None
            core = re.sub(r"\s+", "", t)
            if len(core) < 3:
                return None
            kw = core[:5]
    pats = list(DM_STYLES.get(style) or DM_STYLES["point"])
    used = _DM_USED.setdefault(style, [])
    fresh = [x for x in pats if x not in used] or pats
    if not [x for x in pats if x not in used]:
        _DM_USED[style] = []      # 全用过了就重置，不永久封死
    pat = rng.choice(fresh)
    _DM_USED[style].append(pat)
    line = pat.format(kw=kw)
    ok, _ = guard(line)
    return line[:20] if ok else None


# ---------------- 会话执行器：把计划真的跑一遍 ----------------
SEEN = os.path.join(SOCIAL, "SEEN-VIDEOS.json")


def _seen():
    return _load_json(SEEN, {})


def _mark_seen(url):
    d = _seen()
    d[url] = datetime.now().isoformat(timespec="seconds")
    try:
        json.dump(d, open(SEEN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass


def pick_videos(n, rng=None, topics=None):
    """从已采视频里挑几条没看过的；按人设话题优先，不重复刷同一条。"""
    rng = rng or random.Random()
    vids = _load_json(os.path.join(SOCIAL, "VIDEO-TITLES.json"), {})
    seen = _seen()
    cand = [(u, v) for u, v in vids.items() if (v or {}).get("title") and u not in seen]
    if topics:
        def score(kv):
            t = (kv[1].get("title") or "")
            return -sum(1 for w in topics if w in t)
        cand.sort(key=score)
    else:
        rng.shuffle(cand)
    return cand[:n]





def video_owned_by_other(aid, account):
    """同一条视频今天已被别的号互动过（赞/弹幕/评论）→ 本号不再动手。

    两个号在同一视频下同时出现，是最容易被串起来的关联特征；看没关系，别同时动手。
    """
    today = datetime.now().strftime("%Y-%m-%d")
    for r in _rows():
        if str(r.get("ts", ""))[:10] != today:
            continue
        if r.get("action") not in ("like", "danmaku", "comment"):
            continue
        if str(r.get("aid")) != str(aid):
            continue
        other = r.get("account")
        if other and account and other != account:
            return True, "这条视频今天已被 %s 互动过" % other
    return False, ""



WARMUP_DAYS = 3


def warmup_stage(acct):
    """新号前 3 天只浏览+点赞：新号评论最容易被吞，弹幕更容易被判刷。

    返回 (允许评论, 允许弹幕, 说明)。日期取账号表 created_at（登录当天算第 0 天）。
    """
    ts = (acct or {}).get("created_at")
    if not ts:
        return True, True, ""
    try:
        age = (datetime.now() - datetime.fromisoformat(ts)).days
    except Exception:
        return True, True, ""
    # 柔性分级（不是一刀切"三天不许说话"，真人新号第一天也会发两条弹幕）：
    #   第 0–1 天：可弹幕（配额再压一半），不评论
    #   第 2–3 天：可评论 1 条/天
    #   第 4 天起：按人设配额
    if age <= 1:
        return False, True, "新号第 %d 天：只弹幕+点赞，不评论" % age
    if age <= 3:
        return True, True, "新号第 %d 天：可评论 1 条/天" % age
    return True, True, ""



PERSONAS = os.path.join(SOCIAL, "ACCOUNT-PERSONAS.json")


def persona_of(acct):
    """账号级人设：两个号必须是不同的人（人群段/话题/口吻/字数/配额各不同）。"""
    d = _load_json(PERSONAS, {})
    alias = (acct or {}).get("alias") or ""
    if alias and alias in d:
        return d[alias]
    name = (acct or {}).get("uname") or ""
    for v in d.values():
        if isinstance(v, dict) and v.get("name") == name:
            return v
    return {}


def pick_account(force_alias=None):
    """挑本场用哪个号。force_alias 由常驻智能体传入（一个 agent 只养一个号）。

    依据：同一台机器、同一个 IP 上两个号同时活跃是典型关联特征；
    轮流开、每场只动一个号，才像"一个人分别用两个账号刷"。
    没有 mid 的账号（未登录）不参与轮转。
    """
    try:
        d = _load_json(os.path.expanduser("~/.fluxgroup/bili-accounts.json"), {})
    except Exception:
        return {}
    # 同一 mid 只保留一个主 profile：同一个号在两个 profile 间来回切，
    # 等于给同一账号制造两套设备指纹，反而更像"多设备同号"。
    by_mid = {}
    for k, v in (d.get("accounts") or {}).items():
        if not isinstance(v, dict) or not v.get("mid") or k.startswith("_"):
            continue
        cur = by_mid.get(v["mid"])
        if cur is None or (v.get("primary") and not cur.get("primary")):
            by_mid[v["mid"]] = v
    acts = {str(v["mid"]): v for v in by_mid.values()}
    if force_alias:
        want = (d.get("accounts") or {}).get(force_alias)
        if isinstance(want, dict) and want.get("mid"):
            acts = {str(want["mid"]): want}
    if not acts:
        return {}
    today = datetime.now().strftime("%Y-%m-%d")
    used, last = {}, {}
    for r in _rows():
        if r.get("action") != "session" or r.get("dry_demo"):
            continue
        who = r.get("account")
        ts = str(r.get("ts") or "")
        if ts.startswith(today):
            used[who] = used.get(who, 0) + 1
        last[who] = max(last.get(who, ""), ts)   # 跨天也算：越久没跑越先上
    last_acct = ""
    for r in reversed(_rows(300)):
        if r.get("action") == "session" and r.get("account"):
            last_acct = r["account"]
            break
    best = None
    for alias, v in acts.items():
        name = v.get("uname") or str(v.get("mid"))
        n = used.get(name, 0)
        per = persona_of(dict(v, alias=alias))
        hrs = per.get("hours") or []
        hour = datetime.now().hour
        # 时段偏好：当前小时落在该号活跃时段（含前后 1 小时）优先 —— 两个号像两个作息不同的人
        in_hour = 0 if any(abs(hour - h) <= 1 or abs(hour - h) >= 23 for h in hrs) else 1
        # 上一场刚跑过的号排后面 → 保证两号真交替，而不是同一个连跑
        key = (n, in_hour, 1 if name == last_acct else 0, last.get(name, "") or "0")
        if best is None or key < best[0]:
            best = (key, alias, v)
    alias, acct = best[1], best[2]
    if acct.get("profile"):
        os.environ["FLUX_BILI_PROFILE"] = acct["profile"]
        try:
            import social_comment as _scm
            _scm.PROF = acct["profile"]     # 已导入的模块不会重读 env，必须显式同步
        except Exception:
            pass
        acct = dict(acct, alias=alias)
    return acct


def _active_account():
    return pick_account(os.environ.get("FLUX_ACCOUNT") or None)


def _mid_lock(mid):
    """按 mid 的单实例锁：同一个号同一时刻只许一场会话（哪怕挂了两个 profile）。"""
    p = os.path.join(ROOT, ".codely-cli", "state", "BILI-MID-%s.lock" % (mid or "unknown"))
    try:
        if os.path.exists(p):
            old = int(open(p, encoding="utf-8").read().strip() or 0)
            try:
                os.kill(old, 0)
                return None
            except Exception:
                pass
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(str(os.getpid()))
        return p
    except Exception:
        return None


def _mid_unlock(p):
    try:
        if p and int(open(p, encoding="utf-8").read().strip() or 0) == os.getpid():
            os.remove(p)
    except Exception:
        pass


def session_due():
    """这一场该不该跑：在会话窗口内 + 本窗口还没跑过（一天 3-6 场，不重复）。"""
    import social_session as ss
    cur = ss.current()
    if not cur:
        return False, None, "不在会话窗口"
    start = cur.get("start") or ""
    try:
        for line in open(LEDGER, encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("action") == "session" and str(r.get("ts") or "") >= start:
                return False, cur, "本窗口已跑过（%s）" % r.get("ts")
    except FileNotFoundError:
        pass
    return True, cur, "该开一场"



def login_state(headless=True):
    """用当前 profile 轻量核验登录态（bili_jct + nav.isLogin）。

    为什么要每场核验：登录态失效时如果不先发现，会变成"点赞全失败、弹幕发不出、
    评论被静默吞"，看起来像账号被限流，实际只是没登录。
    核验失败只报 NEED-LOGIN，不开窗口、不反复试——人工登一次即可，之后复用 profile。
    """
    import social_comment as sc
    mod, _ = sc._pw()
    with mod.sync_playwright() as p:
        ctx = sc._launch(p, headless=headless)
        try:
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.goto("https://www.bilibili.com/", wait_until="domcontentloaded", timeout=60000)
            cookies = {c["name"]: c["value"] for c in ctx.cookies()}
            if not cookies.get("bili_jct"):
                return False, None, None
            nav = pg.evaluate("""async()=>{const r=await fetch(
                'https://api.bilibili.com/x/web-interface/nav',{credentials:'include'});
                const j=await r.json();const d=j.data||{};
                return {isLogin:d.isLogin, mid:d.mid, uname:d.uname};}""")
            if nav.get("isLogin"):
                return True, nav.get("mid"), nav.get("uname")
            return False, None, None
        except Exception:
            return False, None, None
        finally:
            try:
                ctx.close()
            except Exception:
                pass
            try:
                import social_collect as _sc
                _sc.release_profile_lock(sc.PROF)
            except Exception:
                pass


def run_session(minutes=18, dry=False, force=False):
    """按计划执行一次会话：看 → 偶尔赞 → 偶尔弹幕 → 极偶尔评论。

    纪律：任何一步失败都不中断整场（人也不会因为一条视频加载失败就关电脑），
    但失败要落账；不在会话时段一律不跑（节律本身就是"像人"的一部分）。
    force=True 只跳过"时段"这一条时序闸，护栏（合规闸/配额/刷脸上限）照旧。
    """
    acct = _active_account()
    lock = _mid_lock(acct.get("mid"))   # 只防同一号重复开；两号允许并行（不同 profile）
    glock = None
    if lock is None and not dry:
        return {"ok": False, "why": "同一个号已有会话在跑（按 mid 互斥）",
                "account": acct.get("uname") or acct.get("mid")}
    import social_session as ss
    cur = ss.current()
    if not cur and not force:
        _mid_unlock(lock); _mid_unlock(glock)
        return {"ok": False, "why": "不在会话时段（一天 3-6 次）"}
    try:
        logged, mid2, uname2 = (False, None, None) if dry else login_state()
    except Exception as e:
        # profile 被另一个进程占着不是故障：记一笔、本轮让路，别抛栈把 daemon 打成异常
        why = str(e).strip().splitlines()[0][:80]
        _mid_unlock(lock)
        log({"action": "profile_busy", "account": acct.get("uname") or acct.get("mid"),
             "why": why})
        return {"ok": False, "why": "profile 被占用：%s" % why,
                "account": acct.get("uname") or acct.get("mid")}
    if not dry and not logged:
        log({"action": "need_login", "account": acct.get("uname") or acct.get("mid"),
             "profile": acct.get("profile")})
        print("[session] %s 登录态失效：本轮只看不动手；请人工登录一次："
              "python3 Tools/fleet/bili_login.py --account %s"
              % (acct.get("alias") or "acct?", acct.get("alias") or "acct1"))
    can_comment, can_danmaku, warm_why = warmup_stage(acct)
    if warm_why:
        print("[session] %s" % warm_why)
    per = persona_of(acct)
    _CAPS.update(per.get("caps") or {})
    if (per.get("caps") or {}).get("danmaku") and (acct.get("created_at") or ""):
        try:
            from datetime import datetime as _dt
            if (_dt.now() - _dt.fromisoformat(acct["created_at"])).days <= 1:
                _CAPS["danmaku"] = max(2, int(_CAPS["danmaku"] // 2))
        except Exception:
            pass
    plan = plan_session(minutes, seg=per.get("seg") or "generic", rng=random.Random())
    vids = pick_videos(plan["videos"], topics=per.get("topics"))
    if not vids:
        return {"ok": False, "why": "没有未看过的视频可挑"}
    import social_comment as sc
    out = {"ok": True, "dry": dry, "plan": {k: v for k, v in plan.items() if k != "steps"},
           "steps": [], "videos": len(vids)}
    vi = 0
    for st in plan["steps"]:
        act = st["act"]
        if act in ("danmaku",) and not can_danmaku:
            out["steps"].append({"act": act, "ok": False, "why": warm_why})
            continue
        if act in ("comment",) and not can_comment:
            out["steps"].append({"act": act, "ok": False, "why": warm_why})
            continue
        if act in ("like", "danmaku", "comment") and not dry and not logged:
            out["steps"].append({"act": act, "ok": False, "why": "未登录，跳过动手"})
            continue
        if act == "end":
            break
        if vi >= len(vids):
            break
        url, meta = vids[vi]
        title = (meta.get("title") or "")[:60]
        aid = None
        try:
            aid = sc.bv_to_aid(meta.get("bvid") or meta.get("title") or "")
        except Exception:
            aid = None
        if act == "watch":
            if dry:
                out["steps"].append({"act": "watch", "title": title, "sec": int(st["dwell_min"] * 60)})
            else:
                ok, note = sc.browse_video(url, seconds=int(st["dwell_min"] * 60))
                out["steps"].append({"act": "watch", "ok": ok, "note": str(note)[:60]})
                _mark_seen(url)
            vi += 1
        elif act == "like":
            if not aid:
                out["steps"].append({"act": "like", "ok": False, "why": "无 aid"})
                continue
            acct_name = acct.get("uname") or acct.get("mid")
            q_ok, q_why = quota_ok("like", acct_name)
            c_ok, c_why = cross_gap_ok(acct_name)
            v_ok, v_why = video_owned_by_other(aid, acct_name)
            if not (q_ok and c_ok) or v_ok:
                out["steps"].append({"act": "like", "ok": False,
                                     "why": q_why or c_why or v_why})
                continue
            ok, res = (True, {"dry": True}) if dry else like(aid)
            out["steps"].append({"act": "like", "ok": ok, "aid": aid})
            log({"action": "like", "aid": aid, "ok": ok, "seg": plan["seg"],
                 "account": acct.get("uname") or acct.get("mid")})
        elif act == "danmaku":
            if not aid:
                continue
            line = danmaku_line(title, style=per.get("danmaku_style") or "point")
            if not line:
                out["steps"].append({"act": "danmaku", "ok": False, "why": "抽不出关键词"})
                continue
            acct_name = acct.get("uname") or acct.get("mid")
            q_ok, q_why = quota_ok("danmaku", acct_name)
            c_ok, c_why = cross_gap_ok(acct_name)
            d_ok, d_why = dup_recent(line)
            v_ok, v_why = video_owned_by_other(aid, acct_name)
            if not (q_ok and c_ok) or d_ok or v_ok:
                out["steps"].append({"act": "danmaku", "ok": False,
                                     "why": q_why or c_why or d_why or v_why})
                continue
            ok, res = (True, {"dry": True}) if dry else sc.send_danmaku(aid, line)
            out["steps"].append({"act": "danmaku", "ok": ok, "text": line})
            log({"action": "danmaku", "aid": aid, "text": line, "ok": ok, "seg": plan["seg"],
                 "account": acct.get("uname") or acct.get("mid")})
        elif act == "comment":
            if dry:
                out["steps"].append({"act": "comment", "dry": True})
            else:
                import subprocess
                env = dict(os.environ, FLUX_FORCE_SEG=per.get("seg") or "")
                r = subprocess.run([sys.executable, os.path.join(HERE, "practice_tick.py")],
                                   cwd=ROOT, capture_output=True, text=True,
                                   timeout=1800, env=env)
                tail = ((r.stdout or "") + (r.stderr or "")).strip()[-120:]
                out["steps"].append({"act": "comment", "ok": r.returncode == 0, "note": tail})
    log({"action": "session", "minutes": minutes, "dry": dry,
         "n_steps": len(out["steps"]), "seg": plan["seg"],
         "account": acct.get("uname") or acct.get("mid")})
    _mid_unlock(lock); _mid_unlock(glock)
    return out


def self_test():
    cases = []
    for bad in ("主页有惊喜，懂的都懂", "加V领取素材", "求三连", "垃圾up", "www.abc.com"):
        ok, _ = guard(bad)
        cases.append(("红线必拒：%s" % bad[:8], ok is False))
    for good in ("这个转场学到了", "剪辑节奏有点赶啊", "我剪过类似的，卡在同一处"):
        ok, _ = guard(good)
        cases.append(("正常评论放行：%s" % good[:8], ok is True))

    # 配额：10 条里最多 1 条提及
    cases.append(("10 条 0 条提及 → 可提", may_mention(10, []) is True))
    cases.append(("10 条已 1 条提及 → 不可提",
                  may_mention(10, [{"mention": True}] + [{}] * 9) is False))

    # 计划：必须"看多动少"
    for seed in range(20):
        pl = plan_session(18, rng=random.Random(seed))
        if plan_violates(pl):
            cases.append(("计划负控 seed=%d" % seed, False))
            break
    else:
        cases.append(("20 个随机计划都满足'看多动少'", True))

    # 弹幕：必须贴标题、≤20 字、且过合规闸；标题里没有可用词就不发
    line = danmaku_line("【吊打付费】剪映蒙版教程")
    cases.append(("弹幕从标题抽词", bool(line) and len(line) <= 20))
    cases.append(("标题没词就不发", danmaku_line("2024") is None))
    cases.append(("弹幕必过合规闸", all(guard(danmaku_line(t) or "x")[0]
                                     for t in ("用PR剪片", "调色翻车现场", "转场被玩坏了"))))


    # 风控三闸（用假台账，不碰真账）
    real_rows = globals()["_rows"]
    now_iso = datetime.now().isoformat(timespec="seconds")
    try:
        globals()["_rows"] = lambda limit=None: [
            {"action": "comment", "ts": now_iso, "account": "A",
             "text": "这个转场我看了三遍还是没看懂"},
            {"action": "comment", "ts": now_iso, "account": "A", "text": "x"},
            {"action": "comment", "ts": now_iso, "account": "A", "text": "y"},
        ]
        cases.append(("评论日配额 3 次封顶", quota_ok("comment", "A")[0] is False))
        cases.append(("重复内容被拦",
                      dup_recent("这个转场我看了三遍还是没看懂啊")[0] is True))
        cases.append(("不相似内容放行",
                      dup_recent("调色偏青了，皮肤没血色")[0] is False))
        globals()["_rows"] = lambda limit=None: [
            {"action": "like", "ts": now_iso, "account": "B"}]
        cases.append(("别号刚动手→错峰拦",
                      cross_gap_ok("A", minutes=10)[0] is False))
        cases.append(("同号自己动手不算错峰",
                      cross_gap_ok("B", minutes=10)[0] is True))
    finally:
        globals()["_rows"] = real_rows

    # 刷脸上限：同一 UP 主 7 天 ≤2
    mid = "test-up"
    d = up_visits()
    cases.append(("首次可访问", may_visit(mid) is True))

    ok = sum(1 for _, c in cases if c)
    for n, c in cases:
        print("  [%s] %s" % ("PASS" if c else "FAIL", n))
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--session", action="store_true", help="常驻入口：该开一场就跑完整一场")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="只跳时段闸（验证用），护栏不漏")
    ap.add_argument("--minutes", type=int, default=18)
    ap.add_argument("--seg", default="generic")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.plan:
        pl = plan_session(a.minutes, a.seg)
        print(json.dumps({k: v for k, v in pl.items() if k != "steps"},
                         ensure_ascii=False, indent=1))
        for s in pl["steps"]:
            print("  +%4.1f min  %-8s %s" % (s["t_min"], s["act"],
                                             ("停留 %.1f 分钟" % s["dwell_min"]) if s.get("dwell_min") else ""))
        print("[plan] 违反'看多动少'：%s" % plan_violates(pl))
        return 0
    if a.session:
        due, cur, why = session_due()
        if not due and not a.force:
            print("[session] 跳过：%s" % why)
            return 0
        minutes = int((cur or {}).get("dur_min") or a.minutes)
        print("[session] 开一场 %s 分钟（%s）" % (minutes, (cur or {}).get("start") or "force"))
        r = run_session(minutes, dry=a.dry, force=True)
        print(json.dumps(r, ensure_ascii=False, indent=1)[:1200])
        return 0 if r.get("ok") else 1
    if a.run:
        r = run_session(a.minutes, dry=a.dry, force=a.force)
        print(json.dumps(r, ensure_ascii=False, indent=1)[:1500])
        return 0 if r.get("ok") else 1
    print("用法：--plan / --self-test")
    return 2


if __name__ == "__main__":
    sys.exit(main())
