#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""practice_tick.py - 实战循环的一拍：每 90 分钟被 launchd 叫一次，干一件，永不收工。

CEO 2026-11-18「你创建自动化定时任务，不断循环啊，为什么我不看就不跑了」。

之前的问题：我挂的是 `RunAtLoad + KeepAlive=false` 的一次性批，跑完就没了。
现在改成 **StartInterval=5400（90 分钟）** 的循环作业，每一拍做这些事：

  1 读 FREQ-POLICY（每日上限 + 最小间隔），不满足就记一条"本拍跳过"并退出——**循环不中断**
  2 满足则：挑一个未用过的同领域视频 → 按字数带生成 → 双闸 → 发 → 回验 → 落账
  3 每次刷新 cph4/fleet/social/PRACTICE-ROLLING.md（滚动清单，不是一次性报告）
  4 止损：最近 7 条全不可见 → 停止发帖，写 BLOCKED-ACCOUNT 说明，只记账不再刷
     （对静默扣留的账号继续刷＝纯风险，不是勤奋）

设计原则：**每一拍都必须有产出（发出 / 跳过原因 / 止损原因），没有"什么都没做"的拍。**
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
TITLES = os.path.join(SOCIAL, "VIDEO-TITLES.json")
LEDGER = os.path.join(SOCIAL, "practice-log.jsonl")
SCREEN = os.path.join(SOCIAL, "PRACTICE-ROLLING.md")
BLOCKED = os.path.join(ROOT, ".codely-cli", "state", "PRACTICE-BLOCKED.json")
PY = sys.executable

sys.path.insert(0, HERE)
NICHE = ("剪辑", "教程", "MV", "mv", "转场", "调色", "分镜", "短片", "拍摄", "剪映", "运镜")
ARMS = ("C", "A", "D", "C")          # 轮转：顶级短评 → 短回复 → 长回复 → 顶级短评
STOP_AFTER = 7                        # 连续不可见多少条就停


def rows_today():
    today = datetime.now().strftime("%Y-%m-%d")
    out = []
    try:
        for line in open(LEDGER, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                if str(r.get("ts", "")).startswith(today):
                    out.append(r)
    except FileNotFoundError:
        pass
    return out


def recent_visibility(n=STOP_AFTER):
    """最近 n 条**有确定结论**的回验（True/False）。用于止损判断。

    visible=None 表示"取数失败未判定"（412/风控/接口报错），**不能算不可见**——
    2026-11-19 实锚：旧判据把顶级评论用错接口 + 报错也判 False，于是 9 条里 6 条
    明明可见却被记成 20% 可见率，还触发了止损。取数失败必须与"确实看不见"分开。
    """
    v = []
    try:
        for line in open(LEDGER, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                if r.get("action") == "verify" and r.get("visible") is not None:
                    v.append(bool(r["visible"]))
    except FileNotFoundError:
        pass
    return v[-n:]


def used_videos():
    s = set()
    for line in (open(LEDGER, encoding="utf-8") if os.path.exists(LEDGER) else []):
        if line.strip():
            r = json.loads(line)
            if r.get("video"):
                s.add(r["video"])
    return s


def blocked():
    try:
        d = json.load(open(BLOCKED, encoding="utf-8"))
        return d if d.get("active") else None
    except Exception:
        return None


def set_blocked(why):
    os.makedirs(os.path.dirname(BLOCKED), exist_ok=True)
    json.dump({"active": True, "why": why, "since": datetime.now().isoformat(timespec="seconds")},
              open(BLOCKED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def clear_blocked(why):
    try:
        json.dump({"active": False, "why": why,
                   "since": datetime.now().isoformat(timespec="seconds")},
                  open(BLOCKED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass


def mature_verify(n=5, min_age_s=600, limit=3):
    """对"发帖后只验过一次就再没验"的投递补一次成熟回验。

    2026-11-20 实锚：回验在发帖后 ~40 秒就做，B 站评论过审/进列表常要几分钟，
    于是 40 秒时的 False 永久留在账上，止损据此停发——判据用的是"婴儿期"证据。
    现在补一条：投递满 min_age_s 且没有成熟结论的，重新验一次并落账。
    返回本轮补验的条数。
    """
    try:
        import social_comment as sc
    except Exception:
        return 0
    posts, mature = {}, {}
    try:
        for line in open(LEDGER, encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            rp = str(r.get("rpid") or "")
            if not rp:
                continue
            if r.get("action") == "post":
                posts[rp] = r
            elif r.get("action") == "verify" and r.get("mature"):
                mature[rp] = r.get("visible")
    except FileNotFoundError:
        return 0
    todo = [rp for rp in list(posts) if rp not in mature][-limit:]
    done = 0
    for rp in todo:
        p = posts[rp]
        try:
            age = (datetime.now() - datetime.fromisoformat(p.get("ts"))).total_seconds()
        except Exception:
            age = 0
        if age < min_age_s:
            continue
        aid = p.get("aid") or p.get("oid")
        try:
            v, why = sc.verify_comment_browser(aid, rp)
        except Exception as e:
            log({"action": "verify", "rpid": rp, "visible": None, "mature": True,
                 "why": "复核异常 %s" % type(e).__name__})
            continue
        log({"action": "verify", "rpid": rp, "visible": v, "mature": True,
             "age_min": int(age / 60), "why": why})
        done += 1
    return done


def log(rec):
    rec.setdefault("ts", datetime.now().isoformat(timespec="seconds"))
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def refresh_screen(note=""):
    posts, vis = {}, {}
    for r in rows_today():
        # 没有 rpid 的历史行也要进表，否则"今日已发 N 条"与表格行数对不上（11-18 实锚 10 vs 9）
        key = r.get("rpid") or ("norp-%s" % r.get("ts", ""))
        if r.get("action") == "post":
            posts[key] = r
        elif r.get("action") == "verify" and r.get("rpid"):
            vis[r["rpid"]] = bool(r.get("visible"))
    L = ["# 实战滚动清单 %s" % datetime.now().strftime("%m-%d %H:%M"), "",
         "- 今日已发 %d 条 ｜ 公开可见 %d 条 ｜ 最近 %d 条可见率 %s"
         % (len(posts), sum(vis.values()), len(recent_visibility()),
            "%.0f%%" % (100.0 * sum(recent_visibility()) / max(len(recent_visibility()), 1))),
         "- 本拍：%s" % (note or "-"), "",
         "| # | 时间 | 动作 | 文案 | rpid | 可见 |", "|---|---|---|---|---|---|"]
    for i, (rp, r) in enumerate(sorted(posts.items(), key=lambda kv: kv[1]["ts"]), 1):
        L.append("| %d | %s | post | %s | %s | %s |"
                 % (i, r["ts"][11:16], (r.get("text") or "")[:28].replace("|", "/"), rp,
                    "✅" if vis.get(rp) else ("❌" if rp in vis else "…")))
    b = blocked()
    if b:
        L += ["", "> ⛔ 已止损：%s（自 %s）" % (b["why"], b["since"])]
    open(SCREEN, "w", encoding="utf-8").write("\n".join(L) + "\n")


LANE_ORDER = ("lora", "4b")     # 训好的本地适配器优先，基座兜底；模型名一源在 social_comment_gen.LANES


PERSONAS = os.path.join(ROOT, "cph4", "fleet", "social", "SEGMENT-PERSONAS-v1.json")


def persona_line(sid):
    """把"这群人怎么说话"压成一行提示词（来自实测画像 + 规格的语义约束）。

    只给可执行的硬约束与禁忌，不写形容词堆砌：实测告诉我们长度和 emoji 密度，
    规格告诉我们称呼与雷区，两边各取所长。
    """
    if not sid:
        return ""
    try:
        doc = json.load(open(PERSONAS, encoding="utf-8"))
        p = (doc.get("segments") or {}).get(sid) or {}
        g = p.get("gen") or {}
        bits = []
        if g.get("tone"):
            bits.append("语气：%s" % g.get("tone"))
        if g.get("address"):
            bits.append("称呼：%s" % g.get("address"))
        if int(g.get("emoji_max") or 0) == 0:
            bits.append("不要 emoji")
        if p.get("dont"):
            bits.append("别做：%s" % "、".join(p["dont"][:2]))
        return ("（你是%s：%s）" % (p.get("name") or sid, "；".join(bits))) if bits else ""
    except Exception:
        return ""


def pick_persona(title, desc="", k=0):
    """选"这条评论是谁说的"，返回 (段id, 字数带)。段必须 n>=60（不足就是拿噪声当习惯）。

    选择顺序：① 视频标题/简介命中的段（谁在这条视频下说话最可能）→
              ② 轮转其他够料的段（避免每条都用同一副面孔）。
    带子取实测 P10-P90 并夹到 [8, 90]：太窄模型永远不过、太宽等于没约束。
    """
    try:
        doc = json.load(open(PERSONAS, encoding="utf-8"))
    except Exception:
        return "", (10, 20)
    segs = {k: v for k, v in (doc.get("segments") or {}).items()
            if v and not v.get("insufficient") and (v.get("n") or 0) >= 60}
    if not segs:
        return "", (10, 20)
    hit = ""
    try:
        import segments as sg
        r = sg.classify((title or "") + " " + (desc or ""), sg.load_spec())
        for cand in [r.get("primary")] + list(r.get("secondary") or []):
            if cand in segs:
                hit = cand
                break
    except Exception:
        pass
    sid = hit or sorted(segs, key=lambda x: -(segs[x].get("n") or 0))[k % max(1, len(segs))]
    g = (segs[sid].get("gen") or {}).get("len") or [10, 20]
    lo, hi = max(8, int(g[0] or 10)), min(90, int(g[1] or 20))
    if hi <= lo:
        lo, hi = 10, 20
    return sid, (lo, hi)


def serving_adapter():
    """8788 当前声明在跑什么：适配器路径，或 "base"（ACTIVE mode=base）。

    lane 只说明"走的哪条车道"，不说"这条车道里挂的是适配器还是基座"。
    2026-11-19 实锚——ACTIVE 指向的目录变空、服务器静默挂上未验收候选，
    而落账只写 lane=lora，事后无法分辨那句话是适配器说的还是基座说的。
    """
    try:
        a = json.load(open(os.path.join(ROOT, "cph4", "fleet", "social", "train",
                                        "ACTIVE.json"), encoding="utf-8"))
        if (a.get("mode") or "").lower() == "base":
            return "base"
        return a.get("adapter") or "base"
    except Exception:
        return "unknown"


def make_text(prompt):
    """按车道阶梯出稿，返回 (text, lane)。两条都不通返回 ("", "")。

    CEO 2026-11-18「使用的是本地大模型能力训练和养号实践」：训练产出的适配器必须
    真的进实战出稿，否则训完还在用基座＝训练白做。实测同一提示词两条车道文案不同
    （lora=「转场特效确实能瞬间提升视频质感…」，4b=「三分钟就教会我高效剪片…」），
    所以落账必须记 lane，才能事后归因"这话是谁说的"。
    """
    import social_comment_gen as cg
    for lane in LANE_ORDER:
        fn = cg.LANES.get(lane)
        if not fn:
            continue
        try:
            r = fn(prompt)
        except Exception:
            continue
        t = (r.get("text") or "").strip().strip("“”\"'").split("\n")[0].strip()
        if t:
            return t, lane
    return "", ""


def recent_post_outcomes(n=5):
    """最近 n 条**已回验的投递**各自是否可见（每条投递只算一次）。

    2026-11-20 实锚：旧判据数的是"verify 行"，同一条评论 30/60 分钟各查一次会被算成两条，
    于是 1/6 可见这种明摆着的降权也能绕过熔断继续发。判据必须落在"投递"上，不是"检查次数"。
    """
    posts, ver = [], {}
    try:
        for line in open(LEDGER, encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            rp = str(r.get("rpid") or "")
            if not rp:
                continue
            if r.get("action") == "post":
                posts.append(rp)
            elif r.get("action") == "verify":
                ver.setdefault(rp, []).append(r.get("visible"))
    except FileNotFoundError:
        pass
    out = []
    for rp in posts:
        vs = [v for v in ver.get(rp, []) if v is not None]
        if vs:
            out.append(any(vs))
    return out[-n:]


def main():
    # 0 成熟回验：止损/发帖前先补"过了几分钟才准"的结论，别用婴儿期证据下判决
    try:
        n_fix = mature_verify()
        if n_fix:
            print("[tick] 补做成熟回验 %d 条" % n_fix)
    except Exception as e:
        print("[tick] 成熟回验失败：%s" % e)
    # 1 止损闸
    b = blocked()
    if b:
        # 有成熟证据翻转时可以自动解除：最近 5 条投递里 ≥2 条成熟可见，说明限流已缓解
        mv = []
        try:
            posts, mat = [], {}
            for line in open(LEDGER, encoding="utf-8"):
                if not line.strip():
                    continue
                r = json.loads(line)
                rp = str(r.get("rpid") or "")
                if not rp:
                    continue
                if r.get("action") == "post":
                    posts.append(rp)
                elif r.get("action") == "verify" and r.get("mature"):
                    mat[rp] = r.get("visible")
            mv = [mat[rp] for rp in posts[-5:] if rp in mat]
        except FileNotFoundError:
            pass
        if len(mv) >= 3 and sum(bool(x) for x in mv) >= 2:
            clear_blocked("成熟回验显示最近 %d 条中 %d 条可见，限流缓解，恢复发帖"
                          % (len(mv), sum(bool(x) for x in mv)))
            log({"action": "unblocked", "mature_visible": sum(bool(x) for x in mv),
                 "mature_n": len(mv)})
            b = None
        else:
            refresh_screen("止损中，不发帖")
            print("[tick] 已止损：%s" % b["why"])
            return 0
    # 2026-11-20 CEO「评论在不在显示不重要，按规则好好评论、像真实用户就行」：
    # 可见率只做记录与屏显，**不再作为停发依据**——B 站有 AI 复审（平均 7 分钟）与
    # 折叠机制（2025-03 起被折叠的挪到最末页），"前几页查不到"既可能是折叠也可能是
    # 仅自己可见，拿它当账号判决会误停。
    # 仍然保留一条硬闸：**真的发不出去**（发送失败连续出现）才停。
    # 只有"真发不出去"才停：节律拒绝（距上帖太近）、内容闸拒稿都不算账号问题。
    # 2026-11-20 实锚：把 fail 全算成发送失败，会把"距上帖仅 8 分钟"这种自家节律
    # 也算成账号被封，属误判——判据必须认原因，不能只认动作名。
    def _send_fail(rec):
        w = rec.get("why")
        w = json.dumps(w, ensure_ascii=False) if not isinstance(w, str) else w
        if "距上帖" in w or "下限" in w:
            return False
        if any(k in w for k in ("指控", "品味", "无关", "太长", "RISKY", "红线", "重复", "闸")):
            return False
        return any(k in w for k in ("code=", "风控", "-412", "12002", "发送失败", "reply/add"))

    recent = []
    try:
        rows = [json.loads(l) for l in open(LEDGER, encoding="utf-8") if l.strip()]
        recent = [r for r in rows if r.get("action") in ("post", "fail", "send_fail")][-10:]
    except Exception:
        pass
    bad_send = sum(1 for r in recent
                   if r.get("action") == "send_fail" or
                   (r.get("action") == "fail" and _send_fail(r)))
    if len(recent) >= 5 and bad_send >= 2:
        why = "最近 %d 次投递里 %d 次真发送失败（风控/接口拒绝）→ 停止发帖" % (
            len(recent), bad_send)
        set_blocked(why)
        log({"action": "blocked", "why": why})
        refresh_screen(why)
        print("[tick] 止损：%s" % why)
        return 0
    # 2 政策闸
    sys.path.insert(0, HERE)
    import freq_policy as fp
    import arm_probe as ap
    pol = fp.load_policy()
    mx, gap = int(pol.get("max_per_day", 2)), int(pol.get("min_gap_min", 90))
    n = len([r for r in rows_today() if r.get("action") == "post"])
    if n >= mx:
        refresh_screen("今日已达上限 %d 条，本拍跳过" % mx)
        log({"action": "skip", "why": "daily cap %d/%d" % (n, mx)})
        print("[tick] 跳过：今日 %d/%d" % (n, mx))
        return 0

    # 2.5 拟人节律：不在线时段不发（CEO「模拟人类操作习惯就好」——
    #     真风险不是次数多，而是机械均匀与零互动；夜里准点发帖比多发更假）。
    # 上一拍如果被杀在"段件在线"状态，这里兜底切回基座（最多滞后十分钟）
    try:
        import adapter_router as _ar0
        if _ar0.current():
            _hok, _hnote = _ar0.heal_stale(10)
            if _hok:
                log({"action": "heal", "note": _hnote})
                print("[tick] 兜底：段件留在线上，已切回基座（%s）" % _hnote)
    except Exception:
        pass

    # GPU 独占：训练在跑时出稿会拿到 2 tok/s 的烂产出（实测），不如等它训完
    sent = os.path.join(ROOT, ".codely-cli", "state", "TRAIN-EXCLUSIVE")
    if os.path.exists(sent) and os.environ.get("FLUX_PRACTICE_FORCE") != "1":
        log({"action": "skip", "why": "training-gpu"})
        print("[tick] 训练占用 GPU，本轮延后（会话时段会照常发）")
        return 0

    # 2.5 会话节律：一天 3-6 次"进来刷一会儿"，而不是每 20 分钟拍一次决定发不发。
    #     会话内按预算动手（多数会话只看不动手），没预算就做一次真实浏览。
    import social_session as sess
    rng = random.Random()
    forced = os.environ.get("FLUX_PRACTICE_FORCE") == "1"
    s_now = sess.current(rng=rng)
    # 2026-11-20：两个号改由 agent_daemon 驱动，不再走 social_session 的时间窗。
    # 哨兵在 = 此刻确实有一场"人"的会话在进行，出稿应当被允许；
    # 否则评论会永远被判 off-session，产出恒为 0（实锚：今晚 8 条全 skip）。
    try:
        sd = os.path.join(ROOT, ".codely-cli", "state")
        if not s_now and any(f.startswith("AGENT-SESSION-") for f in os.listdir(sd)):
            s_now = {"start": "agent", "dur_min": 20, "social": 2, "passive": 6,
                     "progress": {"posted": 0, "browsed": 0}}
    except Exception:
        pass
    if forced:
        log({"action": "skip", "why": "会话闸人工放行"})
    elif not s_now:
        log({"action": "skip", "why": "off-session"})
        print("[tick] 不在会话时段（一天 3-6 次，见 social_session --plan）")
        return 0
    if s_now:
        prog = s_now.get("progress") or {}
        budget = int(s_now.get("social", 0))
        used = int(prog.get("posted", 0))
        browsed = int(prog.get("browsed", 0))
        # 预算用完了（或这条会话本来就不动手）：浏览一条就收工，别硬凑评论
        if used >= budget:
            if browsed >= int(s_now.get("passive", 6)):
                print("[tick] 本次会话已刷满（看 %d 条、发 %d 条），离开" % (browsed, used))
                return 0
            row0 = pick()
            if row0:
                okb, info = sc.browse_video(row0["video"],
                                            seconds=rng.uniform(25, 110), rng=rng)
                tit, got = (info.rsplit("|", 1) + [""])[:2] if info else ("", "")
                try:
                    got = int(got)
                except Exception:
                    got = 0
                sess.bump(s_now["start"], "browsed")
                log({"action": "browse", "ok": okb, "video": row0.get("video"),
                     "note": tit if okb else info, "harvested": got})
                # 这一趟顺手采到的评论并入语料（每场会话只并一次，避免反复重算）
                if got and not (s_now.get("progress") or {}).get("ingested"):
                    n_new, note = sc.ingest_harvest()
                    sess.bump(s_now["start"], "ingested")
                    log({"action": "ingest", "added": n_new, "note": note})
                    print("[tick] 顺手采到 %d 条评论 → 入库新增 %d 行（%s）" % (got, n_new, note))
                print("[tick] 刷到《%s》→ %s" % ((tit or "")[:24],
                                               "看了" if okb else "打开失败"))
            return 0

    # 3 挑目标（同领域优先、未用过）
    try:
        vids = json.load(open(TITLES, encoding="utf-8"))
    except Exception:
        refresh_screen("无视频清单")
        return 2
    used = used_videos()
    cand = [(k, v) for k, v in vids.items()
            if (v or {}).get("title") and k not in used]
    cand.sort(key=lambda kv: -sum(1 for w in NICHE if w in (kv[1]["title"] or "")))
    if not cand:
        refresh_screen("没有未用过的视频")
        log({"action": "skip", "why": "no target"})
        return 0
    url, meta = cand[0]
    title = meta["title"]
    # 4 生成：先定"这条评论是谁说的"（人群画像），再按那群的实测习惯出稿。
    #   2026-11-19 CEO「分足够多的人群画像和习惯，能应对自如」：全局统一字数带
    #   等于对所有人说同一种话；而规格里的带子本身也失真（玩梗党实测中位 33 字、
    #   规格只写 6-18，覆盖率 17%），所以参数一律取 SEGMENT-PERSONAS 的实测值。
    seg, band = pick_persona(title, meta.get("desc") or "", n)
    # 账号级人设：由 user_agent 传入，保证"这两个号是不同的人"
    force = (os.environ.get("FLUX_FORCE_SEG") or "").strip()
    if force:
        seg = force
    arm = ARMS[n % len(ARMS)]
    # 人群带子与臂带子取交集：人群说这类人写 9-63 字，而 C 臂形态上限是 20 字，
    # 直接用人群体会把文案发到 32 字被 arm_probe 判"不在 10-20"（2026-11-19 实锚）。
    try:
        a_spec = ap.ARMS.get(arm) or {}
        lo = max(int(band[0]), int(a_spec.get("min_len") or 0))
        hi = min(int(band[1]), int(a_spec.get("max_len") or 999))
    except Exception:
        lo, hi = band
    if hi <= lo:
        lo, hi = band
    import llm_client as lc
    # 2026-11-21：有亲笔语料的号（老号）不再统一写 10-20 字——他真人 2-63 字，
    # 全挤进一个区间本身就是模板。改成按实测分布取目标，允许 ±3 浮动。
    _tlen = lc.human_len_target(n)
    if _tlen:
        lo = max(4, _tlen - 2)
        hi = min(30, _tlen + 3)
    import comment_taste as ct
    import social_practice as sp
    # 2026-11-20：原来是"第一条过闸就发"，于是发出去的都是第一版平淡句。
    # 改成 best-of-8：语感+人味优先，总分次之；并且生硬的语气词（塞在词中间）直接拒稿——
    # 那是为了刷分硬塞的，发出去比不发更伤账号。
    # 按人设切到该段的适配器（训好的件不用=白训）；进程退出时自动切回基座。
    # 切换要重启 8788（约 20–30 秒），正好被"发前先读一会儿"的停留吸收。
    try:
        import adapter_router as ar
        import atexit
        rok, rnote, rsecs = ar.ensure(seg)
        log({"action": "route", "seg": seg, "ok": rok, "secs": rsecs, "note": rnote})
        if rok:
            atexit.register(ar.restore)
    except Exception as e:
        log({"action": "route", "seg": seg, "ok": False, "note": str(e)[:80]})

    # 连发同款开头的检查：读最近 20 条投出去的文案，开头两个字重复的扣优先级。
    # 单条看不出问题，连着发就是模板（2026-11-20 实测 12 条里 9 条是"那个/那"）。
    recent_ops = {}
    try:
        for r in rows_today()[-40:] + []:
            if r.get("action") == "post" and r.get("text"):
                op = ct.opening_key(r["text"])
                recent_ops[op] = recent_ops.get(op, 0) + 1
    except Exception:
        pass

    # 视频内容简报：从这条视频的真实评论里抽"观众在聊什么"，让稿子指着具体内容说
    try:
        import video_brief as vb
        _brief = vb.block(url)
    except Exception:
        _brief = ""
    best = None
    for k in range(8):
        p = lc.lora_comment_prompt(title, meta.get("desc") or "", i=k, brief=_brief)
        p += persona_line(seg)
        p += "只写 %d-%d 字，一句话。" % (lo, hi)
        # 温度在车道函数内部固定，这里不改签名（改了要动 social_comment_gen）；
        # 多样性靠上面的随机角度 + 不同的目标字数，不靠温度。
        t, lane = make_text(p)
        if not t or not (lo <= len(t) <= hi):
            continue
        ok, why = ct.gen_gate(t, ctx=(title or "") + (meta.get("desc") or ""))
        if not ok:
            log({"action": "skip", "why": "gen-gate:" + why, "arm": arm})
            continue
        if ct.awkward_particles(t):
            continue
        # 品味分只用来排序（下面 best-of-8），不再一票否决——2026-11-21 回归实测：
        # 拿它当及格线会把亲笔句毙掉 88%（「太喜欢这首歌了，没有之一。」被判"逻辑不够"）。
        s = ct.score(t, seg=seg or None)
        if not sp.safe_to_send(t, title)[0]:
            continue
        key = (s["voice"] + s["human"], s["total"])
        if recent_ops.get(ct.opening_key(t)):
            key = (key[0] - 3, key[1])   # 开头撞车：让位给别的候选
        if best is None or key > best[0]:
            best = (key, t, lane)
    text, lane_used = "", ""
    if best:
        text, lane_used = best[1], best[2]
    if not text:
        refresh_screen("本拍无文案过闸（不硬发）")
        log({"action": "skip", "why": "no text passed gates", "arm": arm, "video": url})
        print("[tick] 跳过：无文案过闸")
        return 0

    # 5 发 + 回验：发前先"读一会儿"（拟人停留），再发
    try:
        dwell = min(60, int(hr.dwell_before_post_s(rng=rng)))
        time.sleep(max(0, dwell))
    except Exception:
        pass
    # profile 互斥：采集与发布用的是同一个登录 profile，同时开会 ProcessSingleton 崩溃
    # （2026-11-19 实锚：补采脚本在跑时 practice-tick 直接 rc=1）。忙就本轮跳过，
    # 记事由、返回 0——"环境被占用"不是故障，不该把作业打成红。
    res = None
    for attempt in range(3):
        try:
            res = ap.run(arm, url, text, dry=False, wait_s=25, ctx=title)
            break
        except Exception as e:
            msg = str(e)
            if "ProcessSingleton" in msg or "profile directory" in msg:
                if attempt < 2:
                    time.sleep(20)
                    continue
                refresh_screen("浏览器 profile 被占用（采集在跑），本拍跳过")
                log({"action": "skip", "why": "profile busy", "arm": arm})
                print("[tick] 跳过：profile 被占用")
                return 0
            raise
    if res.get("stage") != "posted":
        refresh_screen("发帖未成：%s" % str(res.get("why"))[:60])
        log({"action": "fail", "why": str(res.get("why"))[:120], "arm": arm, "lane": lane_used})
        print("[tick] 未成：%s" % str(res.get("why"))[:80])
        return 0
    # 车道落这一行：事后要能回答"这条评论是适配器说的还是基座说的"
    log({"action": "lane", "lane": lane_used, "serving": serving_adapter(),
         "rpid": res.get("rpid"), "arm": arm, "persona": seg})
    if s_now:
        try:
            sess.bump(s_now["start"], "posted")   # 只有真发出去才消耗预算
        except Exception:
            pass
    refresh_screen("本轮 %s 臂已发（%s 车道）：%s" % (arm, lane_used, text[:20]))
    print("[tick] 发出 rpid=%s 可见=%s 车道=%s"
          % (res.get("rpid"), res.get("visible"), lane_used))
    return 0


def unblock():
    """解除止损。人工确认账号已恢复（实名/手机号/可见率回升）后才可调用。"""
    if os.path.exists(BLOCKED):
        os.remove(BLOCKED)
        log({"action": "unblock"})
    refresh_screen("已人工解除止损")
    return 0


def status():
    b = blocked()
    rv = recent_visibility()
    n = len([r for r in rows_today() if r.get("action") == "post"])
    print("[tick] 今日已发 %d 条 ｜ 最近 %d 条可见 %d ｜ 止损 %s"
          % (n, len(rv), sum(rv), ("中(%s)" % b["why"]) if b else "未触发"))
    return 0


def self_test():
    """负控自检：三个闸都必须能拦住，且**任何路径都不许真发帖**。

    2026-11-18 教训：llm_client.lora_comment_prompt 被别的机器提交整段覆盖，
    4 个工具同时失效却没人发现——所以自检里必须包含"依赖完整性"这一项。
    """
    import tempfile
    global LEDGER, SCREEN, BLOCKED, STOP_AFTER
    saved = (LEDGER, SCREEN, BLOCKED, STOP_AFTER)
    d = tempfile.mkdtemp(prefix="ptick-")
    LEDGER, SCREEN, BLOCKED = (os.path.join(d, n) for n in
                               ("log.jsonl", "screen.md", "blocked.json"))
    now = datetime.now().isoformat(timespec="seconds")
    ok, bad = [], []

    def check(name, cond):
        (ok if cond else bad).append(name)
        print("  %s %s" % ("PASS" if cond else "FAIL", name))

    def write(rows):
        with open(LEDGER, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def posts():
        try:
            return sum(1 for l in open(LEDGER, encoding="utf-8")
                       if l.strip() and json.loads(l).get("action") == "post")
        except FileNotFoundError:
            return 0

    try:
        # A 2026-11-20 新口径：七连不可见**不再停发**（可见性只记录，不判决）。
        #   为了不触发真发帖，这里把日限占满，走政策闸跳过。
        import freq_policy as fp
        mxA = int(fp.load_policy().get("max_per_day", 2))
        write([{"action": "verify", "rpid": str(i), "visible": False, "ts": now}
               for i in range(STOP_AFTER)]
              + [{"action": "post", "rpid": "x%d" % i, "ts": now} for i in range(mxA)])
        rc = main()
        check("A 七连不可见→不再止损（只记录）", rc == 0 and blocked() is None)

        # A2 真发不出去（连续 fail）→ 必须止损
        write([{"action": "fail", "why": "code=-412", "ts": now} for _ in range(3)]
              + [{"action": "post", "rpid": "y%d" % i, "ts": now} for i in range(3)])
        p_before = posts()
        rc = main()
        check("A2 连续发送失败→止损且不再发帖",
              rc == 0 and blocked() and posts() == p_before)

        # B 已止损 → 再跑也不发帖（幂等）
        p_before = posts()
        rc = main()
        check("B 止损后静默不重复发", rc == 0 and posts() == p_before)

        # C 解除止损 → 状态回到未触发
        unblock()
        check("C --unblock 可解除", blocked() is None)

        # D 负控：阈值未到（STOP_AFTER+1）就**不许**止损。
        #    必须同时把日限占满，否则会走到真生成路径（自检绝不许触发真发帖）。
        import freq_policy as fp
        mx = int(fp.load_policy().get("max_per_day", 2))
        STOP_AFTER = 8
        write([{"action": "verify", "rpid": str(i), "visible": False, "ts": now}
               for i in range(7)]
              + [{"action": "post", "rpid": "d%d" % i, "ts": now} for i in range(mx)])
        main()
        check("D 负控：未到阈值不误判止损", blocked() is None)
        STOP_AFTER = 7

        # E 已达日限 → 走政策闸跳过，不发帖
        write([{"action": "post", "rpid": "p%d" % i, "ts": now} for i in range(mx)])
        rc = main()
        check("E 日限已满→跳过零发帖", rc == 0 and posts() == mx)

            # J 取数失败（visible=None）不得计入可见率——这是 11-19 假止损的直接原因
        with open(LEDGER, "w", encoding="utf-8") as f:
            for row in ({"action": "verify", "visible": None},
                        {"action": "verify", "visible": True}):
                f.write(json.dumps(row) + "\n")
        check("J visible=None 不计入可见率", recent_visibility() == [True])

    # F 依赖完整性（本次事故的回归位）
        import llm_client as lc
        check("F llm_client 三件与训练哨兵齐备",
              all(hasattr(lc, n) for n in
                  ("lora_comment_prompt", "generate_lora", "TRAIN_SENTINEL")))
        import social_collect as sc
        check("G social_collect 内存闸齐备",
              all(hasattr(sc, n) for n in ("workers_by_mem", "unload_models", "set_mode")))
        # H 出稿车道：必须是"训好的本地适配器优先"，否则训练成果进不了实战
        import social_comment_gen as cg
        check("H 出稿车道 lora 优先且存在",
              LANE_ORDER[0] == "lora" and "lora" in cg.LANES and "4b" in cg.LANES)
        # I 行为级：车道函数真的能出话（不联网失败时至少返回空串而不是抛）
        t, lane = make_text("只写一句话：收到。")
        check("I 车道可出稿（text 非空且记到 lane）", bool(t) and lane in LANE_ORDER)
    finally:
        LEDGER, SCREEN, BLOCKED, STOP_AFTER = saved
        import shutil
        shutil.rmtree(d, ignore_errors=True)

    print("[tick] self-test %d/%d" % (len(ok), len(ok) + len(bad)))
    if bad:
        print("[tick] 失败项：" + "；".join(bad))
        return 1
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--unblock", action="store_true", help="人工解除止损")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    if a.unblock:
        sys.exit(unblock())
    if a.status:
        sys.exit(status())
    sys.exit(main())
