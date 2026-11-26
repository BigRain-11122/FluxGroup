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

# 2026-11-22：这两个模块级导入在一次机队同步里被冲掉了（文件里还留着调用），
# 表现为 NameError: sc / pick。补回来，并且只从一处导入。
sys.path.insert(0, HERE) if 'HERE' in globals() else None
import social_comment as sc          # noqa: E402
import social_practice as sp         # noqa: E402

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


def pick():
    """挑一条还没用过的视频来浏览（会话预算用完时的"只看不发"）。

    2026-11-22：这个函数在一次同步回滚里整段消失，留下裸调用 pick()，
    于是会话一旦走"预算用完"分支就 NameError（白天 swatch/浏览全停）。
    它的语义是"挑视频"，与 social_practice.pick（挑队列评论）不是一回事。
    """
    try:
        vids = json.load(open(TITLES, encoding="utf-8"))
    except Exception:
        return None
    used = used_videos()
    cand = [(k, v) for k, v in vids.items()
            if (v or {}).get("title") and k not in used]
    if not cand:
        return None
    u, meta = cand[0]
    return {"video": u, "title": (meta or {}).get("title") or ""}


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


def mature_verify(n=5, min_age_s=600, limit=3, quick=False):
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
            # quick：出稿前的补验只准试一次、等 5 秒。默认 3 次 × 45 秒会在
            # profile 被另一号占着时把出稿拖到两三分钟（2026-11-22 实测）。
            v, why = sc.verify_comment_browser(
                aid, rp, tries=1 if quick else 3, wait_s=5 if quick else 45)
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
    # 按号归因：agent_daemon 会设 FLUX_ACCOUNT。没有这一列，"今日 acct1 发了几条"
    # 只能靠猜，而配额判据必须能分号（2026-11-22 实测 HEALTH.comment 恒 0）。
    rec.setdefault("account", os.environ.get("FLUX_ACCOUNT") or None)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _seg_skip_no_base(lanes, used_lane):
    """退步段本该走基座却没走成时，本拍不发。纯函数，可被自检直接注入。

    条件：首选车道不是 lora（=策略认为该走基座），且实际用的不是首选。
    这样训练期间（基座不可用）退步段就不会继续产出比基座更差的话。
    """
    try:
        return bool(lanes) and lanes[0] != "lora" and used_lane != lanes[0]
    except Exception:
        return False


def _recent_openings(n=20):
    """跨天取最近 n 条已发文案的开头 2 字 → {开头: 次数}。读台账尾部，不分日期。"""
    out = {}
    try:
        lines = open(LEDGER, encoding="utf-8").read().splitlines()
    except FileNotFoundError:
        return out
    got = 0
    for line in reversed(lines):
        if got >= n:
            break
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("action") == "post" and r.get("text"):
            import comment_taste as _ct
            op = _ct.opening_key(r["text"])
            if op:
                out[op] = out.get(op, 0) + 1
                got += 1
    return out


COLLECT_EVERY_MIN = 25   # 采集（看视频）独立节拍：约半小时一条，仍是"人"的频率


def _collect_due():
    """离上次采集够久了吗？读 practice-log 的最后一条 ingest/browse 行，不用额外状态文件。"""
    last = None
    try:
        for line in open(LEDGER, encoding="utf-8"):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("action") in ("ingest", "browse"):
                last = r.get("ts")
    except FileNotFoundError:
        return True
    if not last:
        return True
    try:
        t = datetime.fromisoformat(str(last))
    except Exception:
        return True
    return (datetime.now() - t).total_seconds() >= COLLECT_EVERY_MIN * 60


def _independent_collect(rng):
    """不在会话里也看一眼视频并顺手采评论。纯读，走平台租约；成功即记 browse/ingest。

    返回 True 表示这一拍真做了采集（调用方不用再记 off-session）。
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import res_alloc
        rc, why = res_alloc.may("bilibili")
        if rc != 0:
            print("[tick] 采集让位：%s" % why)
            return False
    except Exception as e:
        print("[tick] 仲裁器不可用（%s），按放行处理" % type(e).__name__)
    row0 = pick()
    if not row0:
        return False
    import social_comment as sc
    ok, info = sc.browse_video(row0["video"], seconds=rng.uniform(25, 90), rng=rng)
    tit, got = (info.rsplit("|", 1) + [""])[:2] if info else ("", "")
    try:
        got = int(got)
    except Exception:
        got = 0
    log({"action": "browse", "ok": ok, "video": row0.get("video"),
         "note": tit if ok else info, "harvested": got, "why": "independent-collect"})
    if got:
        n_new, note = sc.ingest_harvest()
        log({"action": "ingest", "added": n_new, "note": note})
        print("[tick] 独立采到 %d 条评论 → 入库新增 %d 行（%s）" % (got, n_new, note))
    print("[tick] 独立采集：刷到《%s》→ %s" % ((tit or "")[:24], "看了" if ok else "打开失败"))
    return bool(ok)


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


def make_text(prompt, lanes=None):
    """按车道阶梯出稿。出稿链路默认**只用 lora**：4b 兜底要现加载模型（约 30 秒），
    一拍 3 条候选就会变成 90 秒——这正是"太慢"的一大块（2026-11-22 实测）。"""
    """按车道阶梯出稿，返回 (text, lane)。两条都不通返回 ("", "")。

    CEO 2026-11-18「使用的是本地大模型能力训练和养号实践」：训练产出的适配器必须
    真的进实战出稿，否则训完还在用基座＝训练白做。实测同一提示词两条车道文案不同
    （lora=「转场特效确实能瞬间提升视频质感…」，4b=「三分钟就教会我高效剪片…」），
    所以落账必须记 lane，才能事后归因"这话是谁说的"。
    """
    import social_comment_gen as cg
    for lane in (lanes or LANE_ORDER):
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


def _short_profile_wait(fn, *a, **kw):
    """把浏览器 profile 锁的等待压到 10 秒再执行 fn。

    2026-11-22 实锚：两个号各自开着会话时，profile 锁被占；出稿进程在
    social_collect._acquire_profile_lock 里每 5 秒轮询、最多等 180 秒，**且不打任何日志**，
    表现就是"点了没反应、五分钟没动静"，而 timing 行还显示 71 秒（等待不在计时里）。
    回验是锦上添花，不该挡住出稿：拿不到锁就退回 reader profile 或当轮跳过。
    """
    old = os.environ.get("FLUX_PROFILE_WAIT")
    os.environ["FLUX_PROFILE_WAIT"] = "10"
    try:
        return fn(*a, **kw)
    finally:
        if old is None:
            os.environ.pop("FLUX_PROFILE_WAIT", None)
        else:
            os.environ["FLUX_PROFILE_WAIT"] = old


def _lora_ready(timeout=4):
    """8788（LoRA 车道）是否在位——训练期允许共存的唯一前提。"""
    try:
        import urllib.request as _u
        with _u.urlopen("http://127.0.0.1:8788/v1/models", timeout=timeout) as r:
            return bool(json.loads(r.read().decode() or "{}").get("data"))
    except Exception:
        return False


def _coexist_gap_ok(gap_s=600):
    """两次"占用共存窗口"之间至少隔 10 分钟：训练拿绝对多数时间，出稿只取它够用的那一小段。

    2026-11-27 修（判据只看动作不看产出）：原来只认 `coexist-publish`，而那一行是在
    **获批窗口**时写的、当时还没出稿。实锚：00:18:10 那条 coexist-publish 既没有 text
    也没有 rpid——台账读起来像"发过一条"，实际那一拍后面是"无文案过闸"。
    现在窗口授权记 `coexist-grant`（它是资源配额，冷却仍按它算），
    真实发文另记 `post` 并带 rpid；两者都计入冷却，但读台账不会再混淆。
    """
    import time as _t
    try:
        rows = [json.loads(l) for l in open(LEDGER, encoding="utf-8") if l.strip()]
    except Exception:
        return True
    last = 0
    for r in rows[-80:]:
        if r.get("action") in ("coexist-grant", "coexist-publish", "post"):
            try:
                ts = __import__("datetime").datetime.fromisoformat(str(r.get("ts")))
                last = max(last, _t.mktime(ts.timetuple()))
            except Exception:
                continue
    return (time.time() - last) >= gap_s if last else True


def _lane(phase, **meta):
    """写本线状态件（lane-practice.json）。失败吞掉——旁证不许挡住发帖。"""
    try:
        import lane_state as ls
        ls.put("practice", phase, **meta)
    except Exception:
        pass


def main():
    t_boot0 = time.time()
    # 0 成熟回验：止损/发帖前先补"过了几分钟才准"的结论，别用婴儿期证据下判决
    try:
        n_fix = _short_profile_wait(mature_verify, limit=1, quick=True)
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

    # 2.4 间隔与额度的早判：放到生成之前，别把 3–5 秒生成白花在"还差 3 分钟"上
    try:
        import arm_probe as _ap0
        _okc, _wc = _ap0.cap_check()
        if not _okc:
            log({"action": "skip", "why": _wc})
            print("[tick] 跳过：%s" % _wc[:40])
            return 0
    except Exception:
        pass

    # 2.5 拟人节律：不在线时段不发（CEO「模拟人类操作习惯就好」——
    #     真风险不是次数多，而是机械均匀与零互动；夜里准点发帖比多发更假）。
    # 上一拍如果被杀在"段件在线"状态，这里兜底切回基座（最多滞后十分钟）
    try:
        import adapter_router as _ar0
        if _ar0.current() and os.environ.get("FLUX_IN_SESSION") != "1":
            _hok, _hnote = _ar0.heal_stale(30)
            if _hok:
                log({"action": "heal", "note": _hnote})
                print("[tick] 兜底：段件留在线上，已切回基座（%s）" % _hnote)
    except Exception:
        pass

    # GPU 独占：训练在跑时出稿会拿到 2 tok/s 的烂产出（实测），不如等它训完
    sent = os.path.join(ROOT, ".codely-cli", "state", "TRAIN-EXCLUSIVE")
    if os.path.exists(sent) and os.environ.get("FLUX_PRACTICE_FORCE") != "1":
        # 2026-11-22 实锚：这条"见哨兵就跳过"让出稿停了 8 小时（13:25→21:42），
        # 而 train_run.sh 里自己记着：训练 + 8788 出稿 + 采集同时跑实测 swap 零增长、
        # 出稿 10/10 成功。规则没跟上事实，是规则的问题。
        # 正法：训练期间只许走 8788（LoRA 车道，已在训练白名单里），探一下活着就照常发；
        # ollama 车道（4b 兜底）才必须跳过——那才是真要额外装模型、会挤训练的那条。
        _lora_ok = False
        try:
            import urllib.request as _u
            with _u.urlopen("http://127.0.0.1:8788/v1/models", timeout=4) as _r:
                _lora_ok = bool(json.loads(_r.read().decode() or "{}").get("data"))
        except Exception:
            _lora_ok = False
        if not _lora_ok:
            log({"action": "skip", "why": "training-gpu（8788 不在位）"})
            print("[tick] 训练独占且 8788 不在位，本轮延后")
            return 0
        os.environ["FLUX_ALLOW_DURING_TRAIN"] = "1"
        os.environ["FLUX_LANE_FORCE"] = "lora"
        log({"action": "coexist", "why": "训练中，仅走 8788 LoRA 车道"})
        print("[tick] 训练中：仅走 8788 LoRA 车道（训练+出稿共存已验证）")

    try:
        if os.environ.get("FLUX_SKIP_VERIFY") != "1":
            import practice_due as _pd0
            _owed0, _ = _pd0.due(within_s=0)
            if not _owed0:
                # 原调用 verify_pending(1) 在这个文件里从未定义过，被 except 静默吞掉，
                # 等于这一步一直是空的（2026-11-22 实锚）。补验统一走 mature_verify，
                # 且同样限时拿锁，不许挡住出稿。
                _short_profile_wait(mature_verify, limit=1, quick=True)
    except Exception:
        pass

    # 2.5 会话节律：一天 3-6 次"进来刷一会儿"，而不是每 20 分钟拍一次决定发不发。    #     会话内按预算动手（多数会话只看不动手），没预算就做一次真实浏览。
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
        # 采集与出稿解耦：评论出稿必须等"人"的会话，看视频不需要。
        # 2026-11-23 实锚：采集被焊在会话里，今天 off-session 18 次 = 整天 0 条采集，
        # 而会话一天只有 3-6 次。看视频是纯读动作，按自己的节拍走（冷却 + 平台租约）。
        if _collect_due():
            if _independent_collect(rng):
                return 0
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
    # 进程起点：真实总节拍必须含 0–2.5 段的等待（回验/拿锁/会话判定）。
    # 起点原来放在"挑定视频之后"，于是五分钟没发出去也能记成 71 秒。
    t_tick0 = t_boot0
    # 4 生成：先定"这条评论是谁说的"（人群画像），再按那群的实测习惯出稿。
    #   2026-11-19 CEO「分足够多的人群画像和习惯，能应对自如」：全局统一字数带
    #   等于对所有人说同一种话；而规格里的带子本身也失真（玩梗党实测中位 33 字、
    #   规格只写 6-18，覆盖率 17%），所以参数一律取 SEGMENT-PERSONAS 的实测值。
    seg, band = pick_persona(title, meta.get("desc") or "", n)
    # 账号级人设：由 user_agent 传入，保证"这两个号是不同的人"
    force = (os.environ.get("FLUX_FORCE_SEG") or "").strip()
    if force:
        seg = force
    # 2026-11-22：臂不再按 n 轮转——轮转会让"提示词要 10–20 字"与"臂是 D(21–90)"打架，
    # 候选全部落空且不落日志（实锚：一拍连跑 6 条全被长度筛掉，只留一句"无文案过闸"）。
    # 现在统一由最终字数带决定臂：≤20 用 C，>20 用 D。
    _arm_by_band = None
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
    # 出稿要 60 秒 GPU：训练正占着（TTL 4h）就本轮让路，不硬抢。
    # 与 train_forever 的"出稿到期让路"配成一对：训练让出窗口，出稿在窗口里拿锁。
    try:
        import gpu_lease as _gl
        # TTL 600→120：出稿正常 5 秒完成，10 分钟只够让卡死的进程白占租约。
        # 卡住时（浏览器无响应，CPU 0%）120 秒后过期，gpu_lease 的僵尸回收能接手。
        _got, _why = _gl.acquire("publish", ttl_s=120, wait_s=20)
    except Exception:
        _got, _why = True, ""
    if (not _got and "train" in str(_why)
            and os.path.exists(os.path.join(ROOT, ".codely-cli", "state", "TRAIN-EXCLUSIVE"))
            and _lora_ready() and _coexist_gap_ok()):
        # 训练正在跑且 8788 在位：抬手等待没意义（训练侧本轮代码不响应），
        # 直接进受限共存，省掉最多 90 秒空等（实测 total 188.7→117.1 就是这 90 秒的差）
        _got, _exclusive = True, False
        _why = "coexist（训练持锁，8788 在位，跳过举手等待）"
        log({"action": "coexist-grant", "why": _why})
    if not _got and "train" in str(_why):
        # 2026-11-22 握手：训练只在"出稿到期"时让路，可手动/会话触发的这一拍可能还没到期，
        # 于是干等。出稿这里举一次手（PUBLISH-REQUEST），训练侧看到就 SIGSTOP 让路，
        # 最多等 90 秒；等不到才认让路。
        req = os.path.join(ROOT, ".codely-cli", "state", "PUBLISH-REQUEST")
        try:
            os.makedirs(os.path.dirname(req), exist_ok=True)
            json.dump({"ts": time.time(), "pid": os.getpid()}, open(req, "w"))
        except Exception:
            pass
        t_w = time.time()
        while time.time() - t_w < 90:
            time.sleep(5)
            _got, _why = _gl.acquire("publish", ttl_s=120, wait_s=5)
            if _got:
                log({"action": "yield-wait", "secs": round(time.time() - t_w, 1)})
                break
        try:
            os.remove(req)
        except Exception:
            pass
    _exclusive = bool(_got)
    if not _got and "train" in str(_why):
        # 训练持锁是 4 小时 TTL：它一占，出稿就被饿死（2026-11-22 实锚：13:25→21:42 零产出）。
        # 而 train_run.sh 自己的探针已证明"训练 + 8788 出稿 + 采集"可同时跑
        # （swap 零增长、训练 3.0–3.5s/步、出稿 10/10 成功）。所以允许**受限共存**：
        # ①只在 8788 在位时 ②两次共存窗口间隔 ≥10 分钟 ③窗口授权落成 coexist-grant
        # （不是 coexist-publish——那一刻还没出稿，记成"已发"就是假绿）。
        if _lora_ready() and _coexist_gap_ok():
            _got, _why, _exclusive = True, "coexist（训练持锁，8788 在位）", False
            log({"action": "coexist-grant", "why": _why})
        else:
            _why = _why + "； coexist 不可用（8788 不在位或间隔未到）"
    if not _got:
        log({"action": "skip", "why": "gpu-busy:" + _why, "waited_s": 15})
        print("[tick] 让路：%s" % _why)
        return 0
    if _exclusive:
        try:
            import atexit as _atexit
            _atexit.register(lambda: _gl.release("publish"))
        except Exception:
            pass
    # 2026-11-21：有亲笔语料的账号（老号）不再统一写 10-20 字——他真人 2-63 字，
    # 全挤进一个区间本身就是模板。改成按实测分布取目标，允许 ±3 浮动。
    _tlen = lc.human_len_target(n)
    if _tlen:
        lo = max(4, _tlen - 2)
        hi = min(30, _tlen + 3)
    arm = "C" if hi <= 20 else ("D" if hi >= 21 else "C")
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
        # 2026-11-22「快点弄好」：每拍换一次段件要 15–20 秒（重启 8788 再加载）。
        # 段件之间都是同一套语料风格，差异远小于"每条多花 20 秒"；
        # 已经在任一 LoRA 上就沿用，只有还在基座时才切。
        if ar.current():
            rok, rnote, rsecs = True, "沿用已加载段件（%s）" % os.path.basename(
                str(ar.current())), 0.0
        else:
            rok, rnote, rsecs = ar.ensure(seg)
        log({"action": "route", "seg": seg, "ok": rok, "secs": rsecs, "note": rnote})
        if rok:
            # 2026-11-22「太慢了」：/v1/models 能应答 ≠ 权重已加载完，切换后第一枪要
            # 20 秒（实测一拍 85 秒里有 65 秒花在这）。这里先打一枪暖机（max_tokens=1），
            # 再进候选循环；会话内也不切回基座，否则下一拍又要重付一次切换+暖机。
            if rsecs and rsecs > 1:      # 只有真的切过才需要暖机；已在位还暖就是白等
                try:
                    _t0 = time.time()
                    lc.generate_lora("暖机", max_tokens=1)
                    log({"action": "warmup", "secs": round(time.time() - _t0, 1), "seg": seg})
                except Exception:
                    pass
            if os.environ.get("FLUX_IN_SESSION") != "1":
                atexit.register(ar.restore)
    except Exception as e:
        log({"action": "route", "seg": seg, "ok": False, "note": str(e)[:80]})

    # 连发同款开头的检查：读**跨天**的最近 20 条已发文案。
    # 原来只读 rows_today()，每天重置——于是"你那…"一天冒一个、天天不断
    # （2026-11-24 实测 36 条里 5 条以"你那"开头，而当天内是判重了的）。
    recent_ops = _recent_openings(20)

    # 视频内容简报：从这条视频的真实评论里抽"观众在聊什么"，让稿子指着具体内容说
    try:
        import video_brief as vb
        _brief = vb.block(url)
        _topics = (vb.get(url) or {}).get("topics") or []
    except Exception:
        _brief, _topics = "", []
    t_gen0 = time.time()
    best = None
    # 候选数 8→12：2026-11-21 实测单条候选过闸率 30–47%，8 条里"一条都没过"的概率有 2–6%，
    # 而那意味着这一轮白跑（不发也不记产出）。12 条把"全部被拒"压到 <1%，
    # 代价是单次出稿多花约 50% 生成时间（约 5 秒），可接受。
    # 自适应候选数（2026-11-22「太慢了」）：单条生成 ~4s，12 条 = 48s。
    # 单条过闸率 30–47%，先跑 3 条（约 12s、七成概率已有货），不够再追加 3 条，
    # 最多 9 条。典型一拍从 48s 降到 12–24s，而"全被拒"仍 <1%。
    # 前缀只拼一次（模板固定 i=0 + 视频上下文），候选之间只变末尾的角度/字数，
    # 这样 8788 的提示词缓存能命中：实测单条 5.1s → 0.6–1.2s。
    p_base = lc.lora_comment_prompt(title, meta.get("desc") or "", i=0, brief=_brief)
    n_first = int(os.environ.get("FLUX_CANDIDATES") or 3)
    n_batch = int(os.environ.get("FLUX_CANDIDATE_BATCH") or 3)
    n_max = max(n_first, int(os.environ.get("FLUX_CANDIDATE_MAX") or 9))
    n_cand = n_first
    for k in range(n_max):
        p = lc.lora_comment_prompt(title, meta.get("desc") or "", i=k, brief=_brief)
        p += persona_line(seg)
        # 字数带只许有一处：原型带（真人实测）优先，否则人设带。两处都给会互相打架，
        # 模型挑一个执行，长度带命中率掉到 67%（2026-11-22 实测）。
        _vb = lc.voice_band(k, title)
        # 原型带与闸带取**交集**，不许整条覆盖。
        # 2026-11-24 实锚：acct1 的形态臂闸是 8-13 字，而原型带是 16-38，覆盖之后
        # 提示词要 16-38、闸只要 8-13，模型怎么写都被拒——今天 acct1 一条没发就死在这。
        if _vb:
            _lo, _hi = max(int(_vb[0]), int(lo)), min(int(_vb[1]), int(hi))
            if _lo > _hi:                     # 交集为空说明两套标定互相矛盾，退回闸带并留痕
                _lo, _hi = int(lo), int(hi)
                log({"action": "skip", "why": "band-conflict:%s-%s vs %s-%s" % (_vb[0], _vb[1], lo, hi)})
        else:
            _lo, _hi = int(lo), int(hi)
        p += "只写 %d-%d 字，一句话。" % (_lo, _hi)
        if arm == "D":
            # D 臂要求含具体对象，提示词不要求就会被形态闸整批拒（2026-11-22 实锚：
            # 连拒 5 条、日志只写 gate:[True,'']，看不出是形态闸）
            p += "提到一个具体的东西（画面/剪辑/镜头/转场/配乐）。"
        # 贴题：2026-11-26 统计今日拒稿，"与本视频无关"56 条是最大单项——模型写的是
        # 泛泛夸赞（"这个真的太好了"），既不落标题也不落领域词，于是被判无关。
        # 这不是闸太严（闸接受"标题里任意 2-6 字词"），而是提示词没要求贴题。
        # 所以补一句要求，不动判据。
        p += "这句话要能看出是在说这条视频，可以把标题里的词直接用在句子里。"
        # 温度在车道函数内部固定，这里不改签名（改了要动 social_comment_gen）；
        # 多样性靠上面的随机角度 + 不同的目标字数，不靠温度。
        # 车道按人群段定（2026-11-24）：实测有 3 个段 adapter 比基座差，
        # 硬走 lora 等于在这些人群上写得更差。策略文件由 eval_trend 的事实生成。
        try:
            import seg_policy as _sp
            _lanes = tuple(_sp.lanes_for(seg))
        except Exception:
            _lanes = ("lora", "4b")
        t, lane = make_text(p, lanes=_lanes)
        # 退步段本该走基座；但训练期间 8788 里烧的是带 adapter 的模型、ollama 基座又被
        # TRAIN-EXCLUSIVE 挡住，于是会静默回落 lora——退步段照旧发比基座更差的话。
        # 判断：宁可不发。等基座车道可用（或训练追上）再恢复，策略文件已经是基座优先。
        if _seg_skip_no_base(_lanes, lane):
            log({"action": "skip", "why": "seg-regressing-no-base:%s" % seg,
                 "arm": arm, "text": (t or "")[:20]})
            print("[tick] %s 段 adapter 弱于基座且基座车道不可用，本拍不发" % seg)
            continue
        t = lc.fix_emoji(t)          # [打 call] → [打call]：写法瑕疵不该整条作废
        if not t or not (lo <= len(t) <= hi):
            log({"action": "skip", "why": "length:%d not in %d-%d" % (len(t or ""), lo, hi),
                 "arm": arm, "text": (t or "")[:20]})
            continue
        # 2026-11-22 实锚：生成时用 ct.gen_gate、发送前用 cg.gate，两套判据打架——
        # 候选过了第一套、best 出去被第二套拒（「太实用」这类词只在后者表里），
        # 一整天就这样白跑。正解=只用**发送前那一套**（ap.gates）做候选筛选，
        # 过不了的压根不参与排序，"过了却发不出去"这类白跑从结构上消失。
        okg, ginfo = ap.gates(t, title or "", topics=_topics)
        _rej = ""
        if okg:
            _fok, _fwhy = ap.form_check(arm, t, topics=_topics)
            if not _fok:
                okg, _rej = False, "form:" + str(_fwhy)[:50]
        if not okg:
            if not _rej:
                # 2026-11-22 实锚：原来只看 gen_gate，别的闸拒了也写成 "gate:form"，
                # 一整天 9 条候选全被记成同一个原因，真正的拒稿理由被这个标签藏起来。
                _fails = [(k, v[1]) for k, v in (ginfo or {}).items()
                          if isinstance(v, (list, tuple)) and v and v[0] is False]
                _rej = "; ".join("%s:%s" % (k, str(w)[:40]) for k, w in _fails) or "unknown"
            log({"action": "skip", "why": _rej, "arm": arm, "text": t[:24]})
            continue
        if ct.awkward_particles(t):
            continue
        # 品味分只用来排序，不再一票否决（2026-11-21 回归：当及格线会误杀亲笔句 88%）。
        s = ct.score(t, seg=seg or None)
        key = (s["voice"] + s["human"], s["total"])
        # 只禁"系统性重复"（近 20 条里出现 ≥2 次）。一律全禁会把 14/26 个常见开头
        # 全部封死，8 条候选可能全撞、一条都发不出——过度拦截和漏拦一样是坏闸。
        if recent_ops.get(ct.opening_key(t), 0) >= 2:
            # 撞开头是可判定的硬伤（2026-11-22 质量分实测：22% 已发稿撞开头），
            # 只扣分仍可能被选中，直接丢弃这条候选，让模型再写一条
            log({"action": "skip", "why": "opening-dup:%s" % ct.opening_key(t)[:4],
                 "arm": arm, "text": t[:20]})
            continue
        if best is None or key > best[0]:
            best = (key, t, lane, s, lc._pick_arch(k, title))
        if best and k + 1 >= n_cand:
            break                      # 已有货就不再追加
        if k + 1 >= n_cand and n_cand < n_max:
            n_cand = min(n_max, n_cand + n_batch)   # 不够就再给一批
    text, lane_used = "", ""
    if best:
        text, lane_used = best[1], best[2]
    if not text:
        refresh_screen("本拍无文案过闸（不硬发）")
        log({"action": "skip", "why": "no text passed gates", "arm": arm, "video": url})
        print("[tick] 跳过：无文案过闸")
        _lane("skip-notext", arm=arm, video=(url or "")[-24:])
        return 0

    # 生成段到此结束。此前 gen_s 是在 ap.run 之后才算的，把发帖往返也吞了进去，
    # 于是"生成慢"的结论一直无法证伪（2026-11-22 实测：候选单条 2.1s，一拍却记 71s）。
    t_gen1 = time.time()

    # 5 发 + 回验：发前先"读一会儿"（拟人停留），再发
    # 2026-11-22 CEO「太慢了，真人不会这样」：会话里已经看过这条视频，
    # 发前再等 20–60 秒是双份。会话内直接发；独立跑才做一次短停留（≤10s）。
    try:
        if os.environ.get("FLUX_IN_SESSION") == "1":
            dwell = 0
        else:
            dwell = min(10, int(hr.dwell_before_post_s(rng=rng)))
        if dwell:
            time.sleep(dwell)
    except Exception:
        dwell = 0
    # profile 互斥：采集与发布用的是同一个登录 profile，同时开会 ProcessSingleton 崩溃
    # （2026-11-19 实锚：补采脚本在跑时 practice-tick 直接 rc=1）。忙就本轮跳过，
    # 记事由、返回 0——"环境被占用"不是故障，不该把作业打成红。
    res = None
    # 发帖优先标记：让常驻浏览器把"浏览"这种可推迟的动作让开（单线程排队的根因）
    _pend = os.path.join(ROOT, ".codely-cli", "state", "POST-PENDING")
    try:
        os.makedirs(os.path.dirname(_pend), exist_ok=True)
        open(_pend, "w").write(str(os.getpid()))
    except Exception:
        pass
    t_post0 = time.time()
    for attempt in range(2):
        try:
            res = ap.run(arm, url, text, dry=False, wait_s=10, ctx=title, seg=seg,
                         topics=_topics, verify=False)
            break
        except Exception as e:
            msg = str(e)
            # 2026-11-22 实锚：原来 3 次 × 20 秒 sleep，一次抢锁失败就把 post 拉到 81 秒，
            # 看上去像"发帖很慢"，其实是自家重试把预算吃光（25+20+25+11=81s）。
            # 抢不到就让开下一拍：宁可记一次 skip，也不要产出一条假的慢样本。
            if "ProcessSingleton" in msg or "profile" in msg or "占用" in msg:
                if attempt < 1:
                    time.sleep(4)
                    continue
                refresh_screen("浏览器 profile 被占用（采集在跑），本拍跳过")
                log({"action": "skip", "why": "profile busy", "arm": arm})
                print("[tick] 跳过：profile 被占用")
                return 0
            raise
    t_post1 = time.time()
    try:
        if os.path.exists(_pend):
            os.remove(_pend)
    except Exception:
        pass
    if res.get("stage") != "posted":
        refresh_screen("发帖未成：%s" % str(res.get("why"))[:60])
        log({"action": "fail", "why": str(res.get("why"))[:120], "arm": arm, "lane": lane_used})
        print("[tick] 未成：%s" % str(res.get("why"))[:80])
        return 0
    # 车道落这一行：事后要能回答"这条评论是适配器说的还是基座说的"
    log({"action": "lane", "lane": lane_used, "serving": serving_adapter(),
         "rpid": res.get("rpid"), "arm": arm, "persona": seg})
    # 「合格且发出去」才是闭环：把这条稿的闸/分与 rpid 绑在一起落账，
    # 否则事后只看到"发过一条"，说不清它是不是过了闸的那条（2026-11-21 CEO 令）。
    try:
        _sc = (best[3] if best and len(best) > 3 else {}) or {}
        log({"action": "qualified", "rpid": res.get("rpid"), "persona": seg,
             "arm": arm, "lane": lane_used, "score": _sc.get("total"),
             "voice": _sc.get("voice"), "human": _sc.get("human"), "text": text,
             # 原型落账：多样性判据要靠"生成时选的是哪一类"，不能事后按文本猜
             "arch": (best[4] if best and len(best) > 4 else None)})
    except Exception:
        pass
    if s_now:
        try:
            sess.bump(s_now["start"], "posted")   # 只有真发出去才消耗预算
        except Exception:
            pass
    try:
        # 三段分开记：gen=纯模型、post=发帖往返、total=从挑视频到发完。
        # 混在一起时 SD08 只能看到"慢"，看不出是模型慢还是浏览器慢。
        _post_s = round(t_post1 - t_post0, 1)
        # 排队（等真人会话腾出浏览器）从 post_s 里扣掉：混在一起时"发帖 90 秒"是假象，
        # 浏览器里其实只跑了三五秒（2026-11-22 实锚：post 97.7s 里 90s 在等锁）。
        _q_s = float(res.get("lock_wait_s") or 0.0)
        _post_s_pure = round(max(0.0, _post_s - _q_s), 1)
        # daemon 自报"真正干活"的秒数：post_s_pure 里还混着 daemon 单线程排队，
        # 不拆开就永远分不清"动作慢"和"排在别人后面"（2026-11-23 实锚）。
        try:
            import social_comment as _sc2
            _svc = round(float(_sc2.last_daemon_svc() or 0.0), 1)
        except Exception:
            _svc = 0.0
        _rec = {"action": "timing", "rpid": res.get("rpid"), "cand": n_cand,
                "gen_s": round(t_gen1 - t_gen0, 1), "dwell_s": dwell,
                "post_s": _post_s_pure, "post_queue_s": _q_s,
                "post_action_s": _svc or None,
                "post_wait_s": round(max(0.0, _post_s_pure - _svc), 1) if _svc else None,
                "total_s": round(time.time() - t_tick0, 1), "pending_verify": True}
        if _post_s > 40:
            # 单条 post 自己只要 3 秒；超过 40 秒多半排在别人的浏览后面（daemon 单线程）
            _rec["note"] = ("post 慢：daemon 排队" if (_svc and (_post_s_pure - _svc) > _svc)
                            else "post 慢：动作本身（人味节奏/翻页）")
        log(_rec)
    except Exception:
        pass
    refresh_screen("本轮 %s 臂已发（%s 车道）：%s" % (arm, lane_used, text[:20]))
    print("[tick] 发出 rpid=%s 可见=%s 车道=%s"
          % (res.get("rpid"), res.get("visible"), lane_used))
    _lane("posted", arm=arm, rpid=str(res.get("rpid") or ""), visible=res.get("visible"))
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

        # F 2026-11-27：共存**窗口授权**不是发文（实锚 00:18:10 那条 coexist-publish
        #   既无 text 也无 rpid，台账读起来像"发过一条"，实际后面是"无文案过闸"）。
        #   两条都要守：①授权不计入发文 ②冷却仍按授权算（否则每拍都能开窗口烧 GPU）。
        write([{"action": "coexist-grant", "why": "coexist", "ts": now}])
        check("F 窗口授权不计入发文", posts() == 0)
        check("F 冷却仍按窗口授权算", _coexist_gap_ok() is False)

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
