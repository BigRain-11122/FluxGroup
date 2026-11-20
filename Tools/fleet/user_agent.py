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
# ---------------- 弹幕文本：必须从这条视频推出来 ----------------
DM_PATTERNS = ["这个{kw}绝了", "{kw}这段我回看了三遍", "刚看到{kw}这里", "被{kw}戳到了啊",
               "{kw}这操作学到了", "看到{kw}我笑了"]


def danmaku_line(title, rng=None):
    """从标题抽关键词拼一条 ≤20 字弹幕。抽不出关键词就不发（宁可不发）。"""
    rng = rng or random.Random()
    t = re.sub(r"[【】\[\]（）()《》!！?？|/、,，.。\s]", " ", title or "")
    words = [w for w in t.split() if 2 <= len(w) <= 6 and not w.isdigit()]
    if not words:
        return None
    kw = rng.choice(words)[:6]
    line = rng.choice(DM_PATTERNS).format(kw=kw)
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


def pick_videos(n, rng=None):
    """从已采视频里挑几条没看过的；不重复刷同一条。"""
    rng = rng or random.Random()
    vids = _load_json(os.path.join(SOCIAL, "VIDEO-TITLES.json"), {})
    seen = _seen()
    cand = [(u, v) for u, v in vids.items() if (v or {}).get("title") and u not in seen]
    rng.shuffle(cand)
    return cand[:n]



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


def run_session(minutes=18, dry=False, force=False):
    """按计划执行一次会话：看 → 偶尔赞 → 偶尔弹幕 → 极偶尔评论。

    纪律：任何一步失败都不中断整场（人也不会因为一条视频加载失败就关电脑），
    但失败要落账；不在会话时段一律不跑（节律本身就是"像人"的一部分）。
    force=True 只跳过"时段"这一条时序闸，护栏（合规闸/配额/刷脸上限）照旧。
    """
    import social_session as ss
    cur = ss.current()
    if not cur and not force:
        return {"ok": False, "why": "不在会话时段（一天 3-6 次）"}
    plan = plan_session(minutes, rng=random.Random())
    vids = pick_videos(plan["videos"])
    if not vids:
        return {"ok": False, "why": "没有未看过的视频可挑"}
    import social_comment as sc
    out = {"ok": True, "dry": dry, "plan": {k: v for k, v in plan.items() if k != "steps"},
           "steps": [], "videos": len(vids)}
    vi = 0
    for st in plan["steps"]:
        act = st["act"]
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
            ok, res = (True, {"dry": True}) if dry else like(aid)
            out["steps"].append({"act": "like", "ok": ok, "aid": aid})
            log({"action": "like", "aid": aid, "ok": ok, "seg": plan["seg"]})
        elif act == "danmaku":
            if not aid:
                continue
            line = danmaku_line(title)
            if not line:
                out["steps"].append({"act": "danmaku", "ok": False, "why": "抽不出关键词"})
                continue
            ok, res = (True, {"dry": True}) if dry else sc.send_danmaku(aid, line)
            out["steps"].append({"act": "danmaku", "ok": ok, "text": line})
            log({"action": "danmaku", "aid": aid, "text": line, "ok": ok, "seg": plan["seg"]})
        elif act == "comment":
            if dry:
                out["steps"].append({"act": "comment", "dry": True})
            else:
                import subprocess
                r = subprocess.run([sys.executable, os.path.join(HERE, "practice_tick.py")],
                                   cwd=ROOT, capture_output=True, text=True, timeout=1800)
                tail = ((r.stdout or "") + (r.stderr or "")).strip()[-120:]
                out["steps"].append({"act": "comment", "ok": r.returncode == 0, "note": tail})
    log({"action": "session", "minutes": minutes, "dry": dry,
         "n_steps": len(out["steps"]), "seg": plan["seg"]})
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
